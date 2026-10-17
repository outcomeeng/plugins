#!/usr/bin/env python3
"""Run one finite control pass over the coding positions hosted in Prowl panes.

A pass reads the Prowl agent inventory, measures each configured position that is
hosted in a Prowl pane and is not on the skip list, compacts, pauses, resumes, or
stops positions at the operator's configured pace, records each action durably,
and exits. The same entry point installs and manages the launchd job that starts a
pass every thirty minutes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import ModuleType
from typing import Final, Protocol

from positions_config import (
    ConfigField,
    ConfigurationError,
    Position,
    Settings,
    config_path,
    load_settings,
)
from positions_schedule import (
    PASS_INTERVAL_MINUTES,
    CommandOutcome,
    ScheduleOperation,
    ScheduleResult,
    ScheduleStatus,
    run_schedule,
)
from positions_store import (
    Action,
    PassState,
    RecordField,
    append_record,
    load_state,
    read_records,
    save_state,
)

__all__ = [
    "Action",
    "Collaborators",
    "ConfigField",
    "ConfigurationError",
    "PASS_BOUND_SECONDS",
    "PassResult",
    "RecordField",
    "Report",
    "ReportKind",
    "ScheduleOperation",
    "ScheduleStatus",
    "config_path",
    "main",
    "read_records",
    "run_pass",
    "schedule",
]

PASS_BOUND_SECONDS: Final = 300
COMMAND_TIMEOUT_SECONDS: Final = 30
# The token step occupies the sibling accounting module's `collect` and `measure`,
# each capped at its MAX_SECONDS deadline, plus the construction of its `Evidence`,
# whose sqlite connection waits at most one second for a lock. The import of the
# sibling is done before the pass clock starts, so it occupies no span of the pass.
TOKEN_STEP_DEADLINES: Final = 2
TOKEN_SETUP_SECONDS: Final = 1
SCREEN_LINES: Final = 40
PAUSE_STREAK_PASSES: Final = 2
COMPACT_TEXT: Final = "/compact"
STOP_TEXT: Final = "/exit"
CONTINUE_TEXT: Final = "continue"
ESCAPE_KEY: Final = "escape"
TITLE_KEY: Final = "title"
TEXT_KEY: Final = "text"
UNREADABLE_EXIT_CODE: Final = 2
LAUNCH_AGENTS_RELATIVE: Final = Path("Library") / "LaunchAgents"
BUSY_PATTERN: Final = re.compile(r"esc to interrupt", re.IGNORECASE)
NUMBER: Final = r"(\d+(?:\.\d+)?)"
CLAUDE_CONTEXT: Final = re.compile(rf"Context:\s*{NUMBER}%\s*used")
CLAUDE_WEEKLY: Final = re.compile(rf"Weekly:\s*{NUMBER}%\s*used")
CODEX_CONTEXT: Final = re.compile(rf"{NUMBER}%\s*context left")
CODEX_WEEKLY: Final = re.compile(rf"weekly limit\s*{NUMBER}%\s*left")
PERCENT_TOTAL: Final = 100

SKILLS_ROOT: Final = Path(__file__).resolve().parents[2]
PROWL_ADAPTER: Final = ("operate-prowl", "prowl_environment")
TOKEN_ACCOUNTING: Final = ("control-token-spend", "usage_accounting")


class ReportKind(StrEnum):
    SWITCH_ACCOUNT = "switch-account"
    STOP_UNAUTHORIZED = "stop-unauthorized"
    KEY_UNAUTHORIZED = "key-unauthorized"
    PAUSE_NOTICE = "pause-notice"
    UNMEASURED_PACE = "unmeasured-pace"
    NOT_IN_PROWL = "not-in-prowl"
    SCREEN_UNREADABLE = "screen-unreadable"
    ACTION_FAILED = "action-failed"
    PROWL_UNAVAILABLE = "prowl-unavailable"
    UNFINISHED = "unfinished"


@dataclass(frozen=True)
class Report:
    kind: ReportKind
    subject: str
    message: str


@dataclass(frozen=True)
class PassResult:
    reports: tuple[Report, ...]
    unfinished: tuple[str, ...]


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandOutcome: ...


class TokenState(StrEnum):
    MEASURED = "measured"
    NO_SESSION = "no-session"
    UNMEASURED = "unmeasured"


@dataclass(frozen=True)
class TokenReading:
    """One token measurement: a spend, a readable source with no session, or none."""

    state: TokenState
    spend: int | None = None


class TokenSource(Protocol):
    def tokens(
        self, worktree: str, start: dt.datetime, end: dt.datetime
    ) -> int | None: ...


def read_tokens(
    source: TokenSource, worktree: str, start: dt.datetime, end: dt.datetime
) -> TokenReading:
    """Read a source's tokens, using its richer `reading` when it offers one.

    A source that offers only `tokens` answers a spend or nothing; nothing is an
    unmeasured pace, since that interface cannot say a readable source holds no
    session for the worktree.
    """
    reading = getattr(source, "reading", None)
    if callable(reading):
        return reading(worktree, start, end)
    spend = source.tokens(worktree, start, end)
    if spend is None:
        return TokenReading(TokenState.UNMEASURED)
    return TokenReading(TokenState.MEASURED, spend)


@dataclass(frozen=True)
class Collaborators:
    runner: CommandRunner
    tokens: TokenSource
    clock: Callable[[], float]
    now: dt.datetime
    data_root: Path
    platform: str
    launch_agents_dir: Path


@dataclass(frozen=True)
class SubprocessRunner:
    """Default runner: bounded, argument-vector, fully reaped, no shell."""

    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandResult:
        applied = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        try:
            completed = subprocess.run(
                argv,
                input=stdin,
                stdin=subprocess.DEVNULL if stdin is None else None,
                capture_output=True,
                text=True,
                timeout=applied,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return CommandResult(UNREADABLE_EXIT_CODE, "", f"{argv[0]}: {error}")
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def load_sibling(skill: str, module_name: str) -> ModuleType:
    """Import a script of a sibling skill of this plugin by a `__file__`-relative path."""
    directory = SKILLS_ROOT / skill / "scripts"
    path = directory / f"{module_name}.py"
    cached = sys.modules.get(module_name)
    if cached is not None and Path(getattr(cached, "__file__", "")) == path:
        return cached
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing; install the sibling skill {skill} in the same plugin"
        )
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(directory))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(directory))


class ConsumptionTokens:
    """Token source: the consumption-control accounting, keyed by the pane's worktree."""

    def tokens(self, worktree: str, start: dt.datetime, end: dt.datetime) -> int | None:
        return self.reading(worktree, start, end).spend

    def reading(
        self, worktree: str, start: dt.datetime, end: dt.datetime
    ) -> TokenReading:
        """Measure the worktree; a readable source without its session is distinct."""
        try:
            accounting = load_sibling(*TOKEN_ACCOUNTING)
            config = accounting.Config.from_environment(
                os.environ, accounting.DEFAULT_ROOT, accounting.DEFAULT_PROJECTS
            )
            with accounting.Evidence(config) as evidence:
                collected = evidence.collect(end)
                measured = evidence.measure(start, end)
            group = measured.get(accounting.AccountingField.WORKSPACES, {}).get(
                worktree
            )
            if group is None:
                # Absence shows no session only when the collection saw every source.
                complete = (
                    isinstance(collected, Mapping)
                    and collected.get(accounting.AccountingField.HISTORY_COMPLETE)
                    is True
                )
                return TokenReading(
                    TokenState.NO_SESSION if complete else TokenState.UNMEASURED
                )
            spend = int(sum(group[key] for key in accounting.TOKEN_KEYS))
            return TokenReading(TokenState.MEASURED, spend)
        except (
            OSError,
            ValueError,
            LookupError,
            TypeError,
            AttributeError,
            ImportError,
            RuntimeError,
            sqlite3.Error,
        ):
            return TokenReading(TokenState.UNMEASURED)


def token_step_seconds() -> float:
    """The longest span one token measurement can occupy, from the sibling's limits.

    Loading the sibling here, before the pass clock starts, keeps its import out of
    the pass. A sibling that cannot be read measures nothing and returns at once.
    """
    try:
        deadline = load_sibling(*TOKEN_ACCOUNTING).MAX_SECONDS
        return float(TOKEN_STEP_DEADLINES * deadline + TOKEN_SETUP_SECONDS)
    except (
        OSError,
        ImportError,
        SyntaxError,
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
    ):
        return 0.0


class PassBound(Exception):
    """The pass reached its time bound."""


@dataclass
class Budget:
    clock: Callable[[], float]
    started: float

    def left(self) -> float:
        """Seconds left before the pass bound; negative once the bound is passed."""
        return PASS_BOUND_SECONDS - (self.clock() - self.started)

    def remaining(self) -> float:
        """Seconds left before the pass bound; raises PassBound once none is left."""
        left = self.left()
        if left <= 0:
            raise PassBound
        return left

    def check(self) -> None:
        self.remaining()


@dataclass(frozen=True)
class _Capped:
    """A runner whose commands never outlast the time the pass has left."""

    runner: CommandRunner
    timeout_seconds: float

    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandOutcome:
        return self.runner.run(argv, stdin, timeout_seconds=self.timeout_seconds)


@dataclass(frozen=True)
class Response:
    ok: bool
    data: Mapping[str, object]
    detail: str


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, dict) else {}


def _items(value: object) -> list[object]:
    return value if isinstance(value, list) else []


class ProwlClient:
    """Acts on panes only through the operation surface of the Prowl adapter."""

    def __init__(
        self, adapter: ModuleType, runner: CommandRunner, budget: Budget
    ) -> None:
        self.adapter = adapter
        self.runner = runner
        self.budget = budget

    def call(self, operation: object, **arguments: object) -> Response:
        timeout = min(COMMAND_TIMEOUT_SECONDS, self.budget.remaining())
        adapter = self.adapter
        try:
            request = adapter.operation_request(operation, **arguments)
            result = adapter.execute(request, _Capped(self.runner, timeout))
        except adapter.ProwlEnvironmentError as error:
            return Response(False, {}, str(error))
        if result[adapter.STATUS_FIELD] is not adapter.ExecutionStatus.SUCCEEDED:
            return Response(False, {}, str(result.get(adapter.DETAIL_FIELD, "")))
        payload = _mapping(result[adapter.RESPONSE_FIELD])
        return Response(True, _mapping(payload.get(adapter.DATA_FIELD)), "")

    def agents(self) -> Response:
        return self.call(self.adapter.Operation.AGENTS)

    def read(self, pane: str) -> Response:
        return self.call(self.adapter.Operation.READ, pane=pane, last=SCREEN_LINES)

    def send(self, pane: str, text: str) -> Response:
        return self.call(
            self.adapter.Operation.SEND, pane=pane, text=text, no_wait=True
        )

    def key(self, pane: str, key: str) -> Response:
        return self.call(
            self.adapter.Operation.KEY,
            pane=pane,
            key=key,
            mutation_authorized=True,
        )


@dataclass(frozen=True)
class Screen:
    context_used: float | None
    weekly_used: float | None
    busy: bool


def _last_number(pattern: re.Pattern[str], text: str) -> float | None:
    matches = pattern.findall(text)
    return float(matches[-1]) if matches else None


def parse_screen(text: str) -> Screen:
    """Read the Claude Code status line or the Codex footer from a frozen screen."""
    context = _last_number(CLAUDE_CONTEXT, text)
    if context is None:
        left = _last_number(CODEX_CONTEXT, text)
        context = None if left is None else PERCENT_TOTAL - left
    weekly = _last_number(CLAUDE_WEEKLY, text)
    if weekly is None:
        left = _last_number(CODEX_WEEKLY, text)
        weekly = None if left is None else PERCENT_TOTAL - left
    return Screen(context, weekly, BUSY_PATTERN.search(text) is not None)


def _percent(value: float) -> str:
    return f"{value:g}%"


@dataclass(frozen=True)
class Target:
    position: Position
    pane: str


@dataclass
class Measurement:
    screen: Screen | None
    spend: int | None
    share: float | None
    skipped: str = ""
    no_session: bool = False

    @property
    def ratio(self) -> float | None:
        if self.spend is None or not self.share:
            return None
        return self.spend / self.share


class ControlPass:
    """One finite pass: measure, act, record, and leave the rest to the next pass."""

    def __init__(
        self,
        settings: Settings,
        collaborators: Collaborators,
        prowl: ProwlClient,
        state: PassState,
        token_reserve: float,
    ) -> None:
        self.token_reserve = token_reserve
        self.settings = settings
        self.collaborators = collaborators
        self.prowl = prowl
        self.state = state
        self.reports: list[Report] = []
        self.unfinished: list[str] = []
        self.streaks: dict[str, int] = {}
        self.weekly: dict[str, float] = {}
        self.members: dict[str, int] = {}
        self.window_end = collaborators.now
        self.window_start = collaborators.now - dt.timedelta(
            minutes=PASS_INTERVAL_MINUTES
        )

    def run(self) -> PassResult:
        previous = set(self.state.unfinished)
        # A worktree the configuration no longer lists is no longer held paused by
        # this controller; a configured one that Prowl or the skip list leaves out
        # keeps its entry, since its pane may return.
        configured = {position.worktree for position in self.settings.positions}
        self.state.paused.intersection_update(configured)
        try:
            targets = self._targets()
            targets.sort(key=lambda target: target.position.worktree not in previous)
            self._control(targets)
        except PassBound:
            self._leave(
                position.worktree
                for position in self.settings.positions
                if position.worktree not in self.settings.skip
            )
        finally:
            # An action already taken stays remembered even when a later write fails.
            # Only a position this pass measured heavy keeps its streak: a pass that
            # did not measure it is not one of the consecutive passes.
            self.state.streaks = {
                worktree: streak for worktree, streak in self.streaks.items() if streak
            }
            self.state.unfinished = list(self.unfinished)
            save_state(self.collaborators.data_root, self.state)
        for worktree in self.unfinished:
            self._report(
                ReportKind.UNFINISHED,
                worktree,
                "The pass reached its time bound before finishing this position; "
                "the next pass handles it first.",
            )
        return PassResult(tuple(self.reports), tuple(self.unfinished))

    def _report(self, kind: ReportKind, subject: str, message: str) -> None:
        self.reports.append(Report(kind, subject, message))

    def _leave(self, worktrees: Iterable[str]) -> None:
        for worktree in worktrees:
            if worktree not in self.unfinished:
                self.unfinished.append(worktree)

    def _targets(self) -> list[Target]:
        adapter = self.prowl.adapter
        response = self.prowl.agents()
        if not response.ok:
            self._report(
                ReportKind.PROWL_UNAVAILABLE,
                "prowl",
                f"The Prowl agent inventory is unavailable: {response.detail}",
            )
            return []
        panes: dict[str, tuple[str, str]] = {}
        for item in _items(response.data.get(adapter.AGENTS_FIELD)):
            agent = _mapping(item)
            pane = _mapping(agent.get(adapter.PANE_FIELD))
            path = _mapping(agent.get(adapter.WORKTREE_FIELD)).get(adapter.PATH_FIELD)
            pane_id = pane.get(adapter.ID_FIELD)
            if isinstance(path, str) and isinstance(pane_id, str):
                title = pane.get(TITLE_KEY)
                panes[path] = (pane_id, title if isinstance(title, str) else "")
        targets: list[Target] = []
        for position in self.settings.positions:
            hosted = panes.get(position.worktree)
            if hosted is None:
                self._report(
                    ReportKind.NOT_IN_PROWL,
                    position.worktree,
                    "No Prowl pane hosts this position, so it receives no action.",
                )
                continue
            pane_id, title = hosted
            if {position.worktree, title} & self.settings.skip:
                continue
            targets.append(Target(position, pane_id))
            subscription = position.subscription
            self.members[subscription] = self.members.get(subscription, 0) + 1
        return targets

    def _control(self, targets: list[Target]) -> None:
        for index, target in enumerate(targets):
            try:
                self._handle(target)
            except PassBound:
                self._leave(item.position.worktree for item in targets[index:])
                break
        try:
            self._stop_at_ceiling(targets)
        except PassBound:
            return

    def _measure(self, target: Target) -> Measurement:
        position = target.position
        screen: Screen | None = None
        response = self.prowl.read(target.pane)
        text = response.data.get(TEXT_KEY)
        if response.ok and isinstance(text, str):
            screen = parse_screen(text)
        else:
            self._report(
                ReportKind.SCREEN_UNREADABLE,
                position.worktree,
                f"The pane screen could not be read: {response.detail or 'no text'}",
            )
        if screen is not None and screen.weekly_used is not None:
            known = self.weekly.get(position.subscription, 0.0)
            self.weekly[position.subscription] = max(known, screen.weekly_used)
        spend: int | None = None
        no_session = False
        reason = ""
        if self.prowl.budget.left() >= self.token_reserve:
            reading = read_tokens(
                self.collaborators.tokens,
                position.worktree,
                self.window_start,
                self.window_end,
            )
            spend = reading.spend
            no_session = reading.state is TokenState.NO_SESSION
        else:
            reason = (
                " The token measurement was skipped because its longest duration "
                "does not fit in the time left in the pass."
            )
        pace = self.settings.pace.get(position.subscription)
        count = self.members[position.subscription]
        share = None if pace is None else pace / count
        return Measurement(screen, spend, share, reason, no_session)

    def _handle(self, target: Target) -> None:
        position = target.position
        worktree = position.worktree
        measurement = self._measure(target)
        ratio = measurement.ratio
        if ratio is None and worktree not in self.state.paused:  # paused: see resume
            self._report(
                ReportKind.UNMEASURED_PACE,
                worktree,
                "No token measurement or pace is available for this position; "
                "its pace is unmeasured and only context compaction and the "
                "weekly ceiling apply." + measurement.skipped,
            )
        if worktree in self.state.paused:
            self._resume_if_under_share(target, measurement)
            return
        heavy = ratio is not None and ratio > self.settings.pause_multiple
        streak = self.state.streaks.get(worktree, 0) + 1 if heavy else 0
        self.streaks[worktree] = streak
        if streak >= PAUSE_STREAK_PASSES and self._pause(target, measurement):
            return
        self._compact(target, measurement)

    def _resume_if_under_share(self, target: Target, measurement: Measurement) -> None:
        worktree = target.position.worktree
        ratio = measurement.ratio
        share = measurement.share
        idle = measurement.no_session and bool(share)
        if ratio is None and not idle:
            self._report(
                ReportKind.UNMEASURED_PACE,
                worktree,
                "No token measurement or pace is available for this paused "
                "position, so nothing shows its spend is back under its share; it "
                "stays paused." + measurement.skipped,
            )
            return
        if ratio is not None and ratio >= 1:
            return
        if not self._act(self.prowl.send(target.pane, CONTINUE_TEXT), worktree):
            return
        self.state.paused.discard(worktree)
        if ratio is None:
            self._record(
                Action.RESUME,
                worktree,
                "no session of the position in the last pass window",
                "spend back under the position's share",
                f"The position {worktree} made no requests while paused: the "
                "consumption-control accounting is readable and holds no session "
                "for it over the last pass, so its spend is zero and under its "
                "share, and it received `continue` and resumes.",
            )
            return
        self._record(
            Action.RESUME,
            worktree,
            f"{measurement.spend} tokens over the last pass against a share of "
            f"{share:g}",
            "spend back under the position's share",
            f"The position {worktree} spent less than its share of the "
            f"subscription's pace over the last pass, so it received `continue` "
            "and resumes.",
        )

    def _pause(self, target: Target, measurement: Measurement) -> bool:
        worktree = target.position.worktree
        if not self.settings.key_authorized:
            self._report(
                ReportKind.KEY_UNAUTHORIZED,
                worktree,
                "The position exceeded the pause multiple on consecutive passes, "
                "but the configuration does not authorize the Prowl key "
                "operation, so nothing was paused.",
            )
            return False
        if not self._act(self.prowl.key(target.pane, ESCAPE_KEY), worktree):
            return False
        self.state.paused.add(worktree)
        multiple = self.settings.pause_multiple
        self._record(
            Action.PAUSE,
            worktree,
            f"{measurement.spend} tokens over the last pass against a share of "
            f"{measurement.share:g}",
            f"{multiple:g} times the share on {PAUSE_STREAK_PASSES} consecutive passes",
            f"The position {worktree} spent more than {multiple:g} times its share "
            f"of the subscription's pace on {PAUSE_STREAK_PASSES} consecutive "
            "passes, so it received the Escape key.",
        )
        self._report(
            ReportKind.PAUSE_NOTICE,
            worktree,
            "The position is paused; it resumes at the first pass where its "
            "spend is back under its share.",
        )
        return True

    def _compact(self, target: Target, measurement: Measurement) -> None:
        screen = measurement.screen
        if screen is None or screen.busy:
            return
        worktree = target.position.worktree
        settings = self.settings
        context = screen.context_used
        ratio = measurement.ratio
        if context is not None and context >= settings.compaction_context_percent:
            observed = f"context use {_percent(context)} of the window"
            threshold = f"{_percent(settings.compaction_context_percent)} of the window"
            reason = (
                f"The position {worktree} used {_percent(context)} of its context "
                f"window, at or above the {threshold} compaction threshold, so it "
                "received `/compact`."
            )
        elif ratio is not None and ratio > settings.compaction_multiple:
            observed = (
                f"{measurement.spend} tokens over the last pass against a share "
                f"of {measurement.share:g}"
            )
            threshold = f"{settings.compaction_multiple:g} times the share"
            reason = (
                f"The position {worktree} spent more than "
                f"{settings.compaction_multiple:g} times its share of the "
                "subscription's pace over the last pass, so it received `/compact`."
            )
        else:
            return
        if self._act(self.prowl.send(target.pane, COMPACT_TEXT), worktree):
            self._record(Action.COMPACT, worktree, observed, threshold, reason)

    def _stop_at_ceiling(self, targets: list[Target]) -> None:
        settings = self.settings
        for subscription, weekly in self.weekly.items():
            if weekly < settings.weekly_ceiling_percent:
                continue
            if not settings.stop_authorized:
                self._report(
                    ReportKind.STOP_UNAUTHORIZED,
                    subscription,
                    f"Weekly use of {subscription} reached {_percent(weekly)}, but "
                    "the configuration does not authorize stopping positions, so "
                    "nothing was stopped.",
                )
                continue
            members = [t for t in targets if t.position.subscription == subscription]
            stopped_worktrees: list[str] = []
            for index, target in enumerate(members):
                try:
                    stopped = self._act(
                        self.prowl.send(target.pane, STOP_TEXT),
                        target.position.worktree,
                    )
                except PassBound:
                    self._leave(item.position.worktree for item in members[index:])
                    raise
                if stopped:
                    stopped_worktrees.append(target.position.worktree)
                    self.state.paused.discard(target.position.worktree)
                    self._record(
                        Action.STOP,
                        target.position.worktree,
                        f"weekly use {_percent(weekly)} of the {subscription} "
                        "subscription",
                        f"{_percent(settings.weekly_ceiling_percent)} weekly ceiling",
                        f"Weekly use of {subscription} reached {_percent(weekly)}, "
                        f"at or above the {_percent(settings.weekly_ceiling_percent)} "
                        f"ceiling, so {target.position.worktree} received `/exit` "
                        "and its pane stays open.",
                    )
            unstopped = [t.position.worktree for t in members]
            unstopped = [name for name in unstopped if name not in stopped_worktrees]
            outcome = (
                "its positions were stopped"
                if not unstopped
                else f"{len(stopped_worktrees)} of {len(members)} positions were "
                f"stopped; these were not: {', '.join(unstopped)}"
            )
            self._report(
                ReportKind.SWITCH_ACCOUNT,
                subscription,
                f"Weekly use of {subscription} reached {_percent(weekly)}; "
                f"{outcome}. Switch accounts to continue.",
            )

    def _act(self, response: Response, worktree: str) -> bool:
        if not response.ok:
            self._report(
                ReportKind.ACTION_FAILED,
                worktree,
                f"The Prowl operation failed: {response.detail}",
            )
        return response.ok

    def _record(
        self,
        action: Action,
        worktree: str,
        measurement: str,
        threshold: str,
        reason: str,
    ) -> None:
        append_record(
            self.collaborators.data_root,
            {
                RecordField.RECORDED_UTC: self.collaborators.now.isoformat(),
                RecordField.ACTION: action,
                RecordField.POSITION: worktree,
                RecordField.MEASUREMENT: measurement,
                RecordField.THRESHOLD: threshold,
                RecordField.REASON: reason,
            },
        )


def run_pass(path: Path, collaborators: Collaborators) -> PassResult:
    """Run one finite pass with the configuration at `path`."""
    settings = load_settings(path)
    adapter = load_sibling(*PROWL_ADAPTER)
    token_reserve = token_step_seconds()
    budget = Budget(collaborators.clock, collaborators.clock())
    prowl = ProwlClient(adapter, collaborators.runner, budget)
    collaborators.data_root.mkdir(parents=True, exist_ok=True)
    state = load_state(collaborators.data_root)
    return ControlPass(settings, collaborators, prowl, state, token_reserve).run()


def schedule(
    operation: ScheduleOperation, collaborators: Collaborators
) -> ScheduleResult:
    """Install, report, stop, or restart the launchd job; macOS only."""
    program = (sys.executable, str(Path(__file__).resolve()), "pass")
    return run_schedule(
        operation,
        collaborators.runner,
        collaborators.platform,
        collaborators.launch_agents_dir,
        program,
    )


def default_collaborators() -> Collaborators:
    data_root = load_sibling(*TOKEN_ACCOUNTING).DEFAULT_ROOT
    return Collaborators(
        runner=SubprocessRunner(),
        tokens=ConsumptionTokens(),
        clock=time.monotonic,
        now=dt.datetime.now(dt.timezone.utc),
        data_root=data_root,
        platform=sys.platform,
        launch_agents_dir=Path.home() / LAUNCH_AGENTS_RELATIVE,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="control_positions", description=__doc__)
    parser.add_argument(
        "command",
        choices=["pass", *(operation.value for operation in ScheduleOperation)],
        help="run one pass, or manage the launchd job",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
    collaborators: Collaborators | None = None,
) -> int:
    arguments = _parser().parse_args(argv)
    environment = os.environ if environ is None else environ
    active = collaborators or default_collaborators()
    if arguments.command == "pass":
        try:
            result = run_pass(config_path(environment, Path.home()), active)
        except ConfigurationError as error:
            print(f"control-positions: invalid configuration: {error}", file=sys.stderr)
            return UNREADABLE_EXIT_CODE
        print(
            json.dumps(
                {
                    "reports": [
                        {
                            "kind": report.kind,
                            "subject": report.subject,
                            "message": report.message,
                        }
                        for report in result.reports
                    ],
                    "unfinished": list(result.unfinished),
                }
            )
        )
        return 0
    outcome = schedule(ScheduleOperation(arguments.command), active)
    print(f"{outcome.status}: {outcome.detail}")
    return 0 if outcome.status is ScheduleStatus.SUCCEEDED else 1


if __name__ == "__main__":
    sys.exit(main())
