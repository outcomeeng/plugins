"""Controlled command boundaries, clock, and real resources for the event wait.

Every collaborator here preserves the boundary the shipped script crosses and
exposes observations. The linked tests own every predicate.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, Literal, cast

from hypothesis import given, seed, settings

from outcomeeng.distribution.shipped_scripts import load_shipped_module
from outcomeeng_testing.generators.event_wait import (
    MailReading,
    PaneReading,
    SpendReading,
    TimeoutDefect,
    WorldCase,
    non_object_documents,
    timeout_defects,
    unknown_source_kinds,
    world_cases,
)
from outcomeeng_testing.generators.herdr_environment import agent_item_variant
from outcomeeng_testing.harnesses.agent_mail import (
    captured_inbox_responses_with_bodies,
    common_dir_reply,
    inbox_response_with_ids,
    load_agent_mail,
    wait_request,
    wait_workspace,
    workspace_entries,
)
from outcomeeng_testing.harnesses.consumption_control import (
    AccountingField,
    fixture as consumption_fixture,
    modules as consumption_modules,
)
from outcomeeng_testing.harnesses.herdr_environment import (
    captured_agent_item,
    captured_incomplete_agents,
    inventory_envelope,
    load_herdr_environment,
    request_for,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property
from outcomeeng_testing.harnesses.prowl_environment import load_prowl_environment

ROOT = Path(__file__).parents[2]
WAIT_EVENT_PATH = (
    ROOT / "dist/claude/coding-agents/skills/wait-for-event/scripts/wait_event.py"
)
SPEC_TESTS = "spx/43-coding-agents.enabler/32-event-wait.enabler/tests"
BASE_INSTANT = dt.datetime(2026, 10, 16, 9, 0, 0, tzinfo=dt.timezone.utc)
INSTANT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
WORLD_EXAMPLES = 40
WORLD_SEEDS = {
    "composed": 2026101701,
    "mail": 2026101702,
    "pane": 2026101703,
    "spend": 2026101704,
    "clock": 2026101705,
    "timeout-defect": 2026101706,
    "unknown-kind": 2026101707,
    "document": 2026101708,
}
REPLAY_PATHS = {
    "composed": f"{SPEC_TESTS}/test_event_wait.property.l1.py",
    "mail": f"{SPEC_TESTS}/test_event_wait.mapping.l1.py",
    "pane": f"{SPEC_TESTS}/test_event_wait.mapping.l1.py",
    "spend": f"{SPEC_TESTS}/test_event_wait.mapping.l1.py",
    "clock": f"{SPEC_TESTS}/test_event_wait.mapping.l1.py",
    "timeout-defect": f"{SPEC_TESTS}/test_event_wait.compliance.l1.py",
    "unknown-kind": f"{SPEC_TESTS}/test_event_wait.mapping.l1.py",
    "document": f"{SPEC_TESTS}/test_event_wait.mapping.l1.py",
}
SKIPPED_RUNTIME_ENV = "PYTHONDONTWRITEBYTECODE"
REAL_RUN_TIMEOUT_SECONDS = 1
REAL_RUN_GRACE_SECONDS = 20
REAL_RUN_COMMUNICATE_BOUND_SECONDS = 60
CORRUPT_STATE_BYTES = b"not a database" * 64


class UnexpectedCommandError(RuntimeError):
    """The run executed a command the arrangement scripts no reaction for."""


class UnboundedCommandError(RuntimeError):
    """A command that could hang was run without a time bound."""


@dataclass
class ScriptedClock:
    """Time collaborator: moves only when the run sleeps or a hung command consumes its bound."""

    current: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds

    def instant(self) -> dt.datetime:
        return BASE_INSTANT + dt.timedelta(seconds=self.current)


def instant_text(offset_seconds: int) -> str:
    """The ISO 8601 instant ending in Z that lies `offset_seconds` after the run starts."""
    return (BASE_INSTANT + dt.timedelta(seconds=offset_seconds)).strftime(
        INSTANT_FORMAT
    )


@dataclass(frozen=True)
class Reaction:
    """What one program does when run: answer, be absent, or never answer."""

    kind: Literal["reply", "absent", "hang"]
    result: Any = None


def reply(result: Any) -> Reaction:
    return Reaction("reply", result)


ABSENT = Reaction("absent")
HANG = Reaction("hang")


@dataclass(frozen=True)
class RoutedCall:
    argv: tuple[str, ...]
    bound: float | None
    started: float


@dataclass
class RoutingRunner:
    """Failure-simulation and interaction-protocol collaborator for every command
    boundary the shipped script crosses.

    Each program answers with its scripted reaction. A hung command consumes the
    whole bound it was given on the scripted clock and times out. Every argv,
    bound, and start instant is recorded.
    """

    clock: ScriptedClock
    reactions: Mapping[str, Reaction]
    calls: list[RoutedCall] = field(default_factory=list)

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        env: Mapping[str, str] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> Any:
        self.calls.append(RoutedCall(tuple(argv), timeout_seconds, self.clock.current))
        reaction = self.reactions.get(argv[0])
        if reaction is None:
            raise UnexpectedCommandError(argv)
        if reaction.kind == "absent":
            raise FileNotFoundError(argv[0])
        if reaction.kind == "hang":
            if timeout_seconds is None:
                raise UnboundedCommandError(argv)
            self.clock.current += timeout_seconds
            raise subprocess.TimeoutExpired(argv, timeout_seconds)
        return reaction.result


@dataclass(frozen=True)
class Contracts:
    """The source-owned contracts the evidence is read against."""

    wait_event: ModuleType
    agent_mail: ModuleType
    herdr: ModuleType
    accounting: ModuleType
    foreign_environment: str


def load_wait_event() -> ModuleType:
    """Load the shipped script so linked tests can read its public contract."""
    return load_shipped_module("wait_event", WAIT_EVENT_PATH)


def contracts() -> Contracts:
    return Contracts(
        load_wait_event(),
        load_agent_mail(),
        load_herdr_environment(),
        consumption_modules()[0],
        load_prowl_environment().PROWL_COMMAND,
    )


def source_kinds() -> tuple[str, ...]:
    return tuple(load_wait_event().SOURCE_KINDS)


@dataclass(frozen=True)
class Execution:
    """One run of the shipped entry point."""

    stdout: str
    exit_code: int
    clock: ScriptedClock
    calls: tuple[RoutedCall, ...]
    workspace_after: list[str]


@dataclass(frozen=True)
class WorldObservation(Execution):
    """One run over a case, with the capability results the line is read against."""

    case: WorldCase
    request: dict[str, Any]
    contracts: Contracts
    state_before: dict[str, bytes]
    state_after: dict[str, bytes]
    mail_after_id: int | None
    mail_oracle: dict[str, Any] | None
    pane_requested: tuple[tuple[str, str], ...]
    pane_oracle: dict[str, Any] | None
    spend_stored: tuple[tuple[str, dt.datetime, str, dict[str, Any]], ...]
    spend_cutoff: dt.datetime | None
    spend_oracle: dict[str, Any] | None


def _state_files(root: Path) -> dict[str, bytes]:
    """Snapshot durable state; SQLite reader sidecars hold no state and are excluded."""
    if not root.is_dir():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.name.endswith(("-shm", "-wal"))
    }


@dataclass
class _Arrangement:
    request: dict[str, Any]
    reactions: dict[str, Reaction]
    mail_after_id: int | None = None
    pane_requested: tuple[tuple[str, str], ...] = ()
    pane_reaction: Reaction | None = None
    spend_root: Path | None = None
    spend_stored: tuple[tuple[str, dt.datetime, str, dict[str, Any]], ...] = ()
    spend_cutoff: dt.datetime | None = None


def _arrange_mail(
    c: Contracts, case: WorldCase, arrangement: _Arrangement
) -> dict[str, Any]:
    am, we = c.agent_mail, c.wait_event
    capture = captured_inbox_responses_with_bodies(am)[0]
    ids = sorted(
        cast(int, row[am.STORE_ID_FIELD])
        for row in cast(list[dict[str, Any]], capture.payload[am.STORE_INBOX_FIELD])
    )
    reading = cast(MailReading, case.mail)
    if reading is MailReading.RECORD:
        after_id = ids[0] - 1
        inbox = reply(capture.result)
    else:
        after_id = ids[-1]
        if reading is MailReading.QUIET:
            inbox = reply(capture.result)
        elif reading is MailReading.UNREACHABLE:
            cut_off = inbox_response_with_ids(
                am,
                capture,
                list(range(after_id + 1, after_id + 1 + am.WAIT_LISTING_LIMIT)),
            )
            inbox = reply(cut_off.result)
        elif reading is MailReading.UNAVAILABLE:
            inbox = ABSENT
        else:
            inbox = HANG
    arrangement.reactions[am.GIT_COMMAND] = reply(common_dir_reply(am))
    arrangement.reactions[am.AM_COMMAND] = inbox
    arrangement.mail_after_id = after_id
    return {
        we.KIND_FIELD: we.SOURCE_MAIL,
        we.MAIL_AGENT_FIELD: case.agent,
        we.MAIL_ID_FIELD: after_id,
    }


def _arrange_pane(
    c: Contracts, case: WorldCase, arrangement: _Arrangement
) -> dict[str, Any]:
    hm, we = c.herdr, c.wait_event
    template = captured_agent_item(hm)
    agents = [
        agent_item_variant(hm, template, ordinal, server)
        for ordinal, (server, _) in enumerate(case.session_pairs, start=1)
    ]
    names = [cast(str, agent[hm.NAME_FIELD]) for agent in agents]
    handled = [pair[1] for pair in case.session_pairs]
    requested = list(zip(names, handled, strict=True))
    reading = cast(PaneReading, case.pane)
    source: dict[str, Any] = {we.KIND_FIELD: we.SOURCE_PANE}
    if reading is PaneReading.ABSENT_SESSION:
        requested = [(f"{names[-1]}-absent", handled[0]), *requested]
    elif reading is PaneReading.AMBIGUOUS:
        agents.append(
            agent_item_variant(
                hm, template, len(agents) + 1, case.session_pairs[0][0], name=names[0]
            )
        )
    elif reading is PaneReading.INCOMPLETE:
        agents = captured_incomplete_agents(hm)
        requested = [(cast(str, agents[0][hm.NAME_FIELD]), handled[0])]
    if reading is PaneReading.FOREIGN_ENVIRONMENT:
        source[we.PANE_ENVIRONMENT_FIELD] = c.foreign_environment
    elif reading is PaneReading.UNAVAILABLE:
        arrangement.pane_reaction = ABSENT
    elif reading is PaneReading.HUNG:
        arrangement.pane_reaction = HANG
    else:
        envelope = inventory_envelope(hm, agents)
        arrangement.pane_reaction = reply(hm.CommandResult(0, json.dumps(envelope), ""))
    if arrangement.pane_reaction is not None:
        arrangement.reactions[hm.HERDR_COMMAND] = arrangement.pane_reaction
    source[we.PANE_SESSIONS_FIELD] = [
        {we.PANE_SESSION_FIELD: name, we.PANE_STATE_FIELD: state}
        for name, state in requested
    ]
    arrangement.pane_requested = tuple(requested)
    return source


def _arrange_spend(
    c: Contracts, case: WorldCase, parent: Path, arrangement: _Arrangement
) -> dict[str, Any]:
    accounting, we = c.accounting, c.wait_event
    base = accounting.timestamp(consumption_fixture()[AccountingField.TIMESTAMP])
    root = parent / "state"
    reading = cast(SpendReading, case.spend)
    if reading is SpendReading.RECORDED:
        config = accounting.Config(root, parent / "transcripts", base)
        stored = tuple(
            (
                identity,
                base + dt.timedelta(seconds=offset),
                accounting.iso(base + dt.timedelta(seconds=offset)),
                {
                    AccountingField.KIND: accounting.SignalKind.ROLLING_THRESHOLD.value,
                    AccountingField.API_EQUIVALENT_USD: str(amount),
                },
            )
            for identity, offset, amount in case.alert_records
        )
        with accounting.Evidence(config) as evidence, evidence.db:
            for identity, _, stamp, signal in stored:
                evidence.db.execute(
                    "INSERT INTO signals VALUES(?,?,?)",
                    (identity, accounting.encoded(signal), stamp),
                )
        arrangement.spend_stored = stored
    else:
        root.mkdir()
        if reading is SpendReading.CORRUPT_STATE:
            (root / accounting.STATE_NAME).write_bytes(CORRUPT_STATE_BYTES)
    cutoff = base + dt.timedelta(seconds=case.alert_cutoff)
    arrangement.spend_root = root
    arrangement.spend_cutoff = cutoff
    return {
        we.KIND_FIELD: we.SOURCE_SPEND,
        we.SPEND_AFTER_FIELD: accounting.iso(cutoff),
        we.SPEND_ROOT_FIELD: str(root),
    }


def _arrange(c: Contracts, case: WorldCase, parent: Path) -> _Arrangement:
    we = c.wait_event
    arrangement = _Arrangement({}, {})
    sources: list[dict[str, Any]] = []
    if case.mail is not None:
        sources.append(_arrange_mail(c, case, arrangement))
    if case.pane is not None:
        sources.append(_arrange_pane(c, case, arrangement))
    if case.spend is not None:
        sources.append(_arrange_spend(c, case, parent, arrangement))
    if case.clock_offset is not None:
        sources.append(
            {
                we.KIND_FIELD: we.SOURCE_CLOCK,
                we.CLOCK_AT_FIELD: instant_text(case.clock_offset),
            }
        )
    arrangement.request = {
        we.TIMEOUT_FIELD: case.timeout_seconds,
        we.SOURCES_FIELD: sources,
    }
    return arrangement


def _execute(
    c: Contracts, text: str, reactions: Mapping[str, Reaction]
) -> tuple[Execution, Path]:
    clock = ScriptedClock()
    runner = RoutingRunner(clock, reactions)
    stdout = io.StringIO()
    with wait_workspace() as workspace:
        code = c.wait_event.main(
            [], stdin=io.StringIO(text), stdout=stdout, runner=runner, clock=clock
        )
        entries = workspace_entries(workspace)
    return (
        Execution(stdout.getvalue(), code, clock, tuple(runner.calls), entries),
        workspace,
    )


def observe(case: WorldCase) -> WorldObservation:
    """Run the entry point over the case, then read the same sources through
    their capabilities for the results the line is read against."""
    c = contracts()
    am, hm, accounting = c.agent_mail, c.herdr, c.accounting
    with TemporaryDirectory(prefix="event-wait-") as directory:
        parent = Path(directory)
        arrangement = _arrange(c, case, parent)
        root = arrangement.spend_root
        before = _state_files(root) if root is not None else {}
        execution, _ = _execute(
            c, json.dumps(arrangement.request), arrangement.reactions
        )
        after = _state_files(root) if root is not None else {}
        mail_oracle = None
        if case.mail is not None:
            replica = ScriptedClock()
            mail_oracle = am.execute(
                wait_request(
                    am,
                    case.agent,
                    cast(int, arrangement.mail_after_id),
                    case.timeout_seconds,
                ),
                RoutingRunner(replica, arrangement.reactions),
                replica,
            )
        pane_oracle = None
        if arrangement.pane_reaction is not None:
            pane_oracle = hm.execute(
                request_for(hm, hm.Operation.INVENTORY),
                RoutingRunner(
                    ScriptedClock(), {hm.HERDR_COMMAND: arrangement.pane_reaction}
                ),
            )
        spend_oracle = None
        if root is not None:
            spend_oracle = accounting.recorded_alerts(
                root, cast(dt.datetime, arrangement.spend_cutoff)
            )
        return WorldObservation(
            execution.stdout,
            execution.exit_code,
            execution.clock,
            execution.calls,
            execution.workspace_after,
            case,
            arrangement.request,
            c,
            before,
            after,
            arrangement.mail_after_id,
            mail_oracle,
            arrangement.pane_requested,
            pane_oracle,
            arrangement.spend_stored,
            arrangement.spend_cutoff,
            spend_oracle,
        )


def _run_cases(
    name: str, strategy: Any, check: Callable[..., None], examples: int
) -> None:
    @seed(WORLD_SEEDS[name])
    @settings(max_examples=examples, deadline=None, print_blob=True)
    @given(strategy)
    def generated(case: Any) -> None:
        check(case)

    run_replayable_property(
        generated, seed_value=WORLD_SEEDS[name], replay_path=REPLAY_PATHS[name]
    )


def _worlds(*kinds: str, mandatory: tuple[str, ...] = ()) -> Any:
    c = contracts()
    return world_cases(
        sources=kinds,
        mandatory=mandatory,
        mail=c.wait_event.SOURCE_MAIL,
        pane=c.wait_event.SOURCE_PANE,
        spend=c.wait_event.SOURCE_SPEND,
        clock=c.wait_event.SOURCE_CLOCK,
        states=tuple(str(state) for state in c.herdr.AgentState),
    )


def run_composed_worlds(check: Callable[[WorldObservation], None]) -> None:
    """Drive generated compositions of every source through a linked predicate."""
    _run_cases(
        "composed",
        _worlds(*source_kinds()),
        lambda case: check(observe(case)),
        WORLD_EXAMPLES,
    )


def run_single_source_worlds(
    kind: str, check: Callable[[WorldObservation], None]
) -> None:
    """Drive generated readings of one source kind through a linked predicate."""
    _run_cases(
        kind,
        _worlds(_kind_token(kind), mandatory=(_kind_token(kind),)),
        lambda case: check(observe(case)),
        WORLD_EXAMPLES,
    )


def _kind_token(name: str) -> str:
    return cast(str, getattr(load_wait_event(), f"SOURCE_{name.upper()}"))


@dataclass(frozen=True)
class DefectObservation:
    """One run over a request carrying a defect, with the commands it crossed."""

    execution: Execution
    contracts: Contracts


def run_timeout_defects(check: Callable[[DefectObservation], None]) -> None:
    """Drive requests whose timeout is absent or invalid, naming every source
    kind validly, through a linked predicate."""
    c = contracts()

    def observe_defect(case_and_defect: tuple[WorldCase, TimeoutDefect]) -> None:
        case, defect = case_and_defect
        with TemporaryDirectory(prefix="event-wait-defect-") as directory:
            arrangement = _arrange(c, case, Path(directory))
            request = dict(arrangement.request)
            del request[c.wait_event.TIMEOUT_FIELD]
            if defect.present:
                request[c.wait_event.TIMEOUT_FIELD] = defect.value
            execution, _ = _execute(c, json.dumps(request), arrangement.reactions)
            check(DefectObservation(execution, c))

    from hypothesis import strategies as st

    _run_cases(
        "timeout-defect",
        st.tuples(
            _worlds(*source_kinds(), mandatory=source_kinds()), timeout_defects()
        ),
        observe_defect,
        WORLD_EXAMPLES,
    )


def run_unknown_source_kinds(check: Callable[[DefectObservation, str], None]) -> None:
    c = contracts()

    def observe_kind(kind: str) -> None:
        we = c.wait_event
        request = {
            we.TIMEOUT_FIELD: 1,
            we.SOURCES_FIELD: [{we.KIND_FIELD: kind}],
        }
        execution, _ = _execute(c, json.dumps(request), {})
        check(DefectObservation(execution, c), kind)

    _run_cases(
        "unknown-kind",
        unknown_source_kinds(source_kinds()),
        observe_kind,
        WORLD_EXAMPLES,
    )


def run_non_object_documents(check: Callable[[DefectObservation, str], None]) -> None:
    c = contracts()

    def observe_document(text: str) -> None:
        execution, _ = _execute(c, text, {})
        check(DefectObservation(execution, c), text)

    _run_cases("document", non_object_documents(), observe_document, WORLD_EXAMPLES)


@contextmanager
def detector_state_root(*, recorded: bool) -> Iterator[tuple[Path, dt.datetime]]:
    """A detector state root holding no alert, and the base instant its alerts count from."""
    accounting = consumption_modules()[0]
    base = accounting.timestamp(consumption_fixture()[AccountingField.TIMESTAMP])
    with TemporaryDirectory(prefix="event-wait-real-") as directory:
        parent = Path(directory)
        root = parent / "state"
        if recorded:
            config = accounting.Config(root, parent / "transcripts", base)
            with accounting.Evidence(config):
                pass
        else:
            root.mkdir()
        yield root, base


@dataclass(frozen=True)
class RealRunObservation:
    """One run of the shipped script as a subprocess over a quiet detector."""

    stdout: str
    return_code: int
    elapsed_seconds: float
    timeout_seconds: int
    grace_seconds: int
    survivors: bool
    workspace_after: list[str]
    contracts: Contracts


def real_quiet_run() -> RealRunObservation:
    """Run the script as a real process against a detector that never records,
    so only the timeout ends the run, and report how long it held, whether any
    process of its group remains, and what it left in its working directory."""
    c = contracts()
    we, accounting = c.wait_event, c.accounting
    with detector_state_root(recorded=True) as (root, base):
        request = {
            we.TIMEOUT_FIELD: REAL_RUN_TIMEOUT_SECONDS,
            we.SOURCES_FIELD: [
                {
                    we.KIND_FIELD: we.SOURCE_SPEND,
                    we.SPEND_AFTER_FIELD: accounting.iso(base),
                    we.SPEND_ROOT_FIELD: str(root),
                }
            ],
        }
        with wait_workspace() as workspace:
            started = time.monotonic()
            process = subprocess.Popen(
                [sys.executable, str(WAIT_EVENT_PATH)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=workspace,
                env={**os.environ, SKIPPED_RUNTIME_ENV: "1"},
                start_new_session=True,
            )
            stdout, _ = process.communicate(
                json.dumps(request), timeout=REAL_RUN_COMMUNICATE_BOUND_SECONDS
            )
            elapsed = time.monotonic() - started
            try:
                os.killpg(process.pid, 0)
                survivors = True
            except ProcessLookupError:
                survivors = False
            entries = workspace_entries(workspace)
    return RealRunObservation(
        stdout,
        process.returncode,
        elapsed,
        REAL_RUN_TIMEOUT_SECONDS,
        REAL_RUN_GRACE_SECONDS,
        survivors,
        entries,
        c,
    )


@dataclass(frozen=True)
class LineFormObservation:
    """One run per line form, so the four forms can be compared."""

    executions: Mapping[str, Execution]
    contracts: Contracts


def line_form_runs() -> LineFormObservation:
    """Run the entry point once per line form: an event, a timeout, an
    unreadable source, and an invalid request."""
    c = contracts()
    we = c.wait_event
    runs: dict[str, Execution] = {}
    with detector_state_root(recorded=True) as (quiet_root, base):
        with detector_state_root(recorded=False) as (absent_root, _):
            spend = {
                we.KIND_FIELD: we.SOURCE_SPEND,
                we.SPEND_AFTER_FIELD: c.accounting.iso(base),
            }
            requests = {
                we.LINE_EVENT: {
                    we.TIMEOUT_FIELD: 1,
                    we.SOURCES_FIELD: [
                        {
                            we.KIND_FIELD: we.SOURCE_CLOCK,
                            we.CLOCK_AT_FIELD: instant_text(0),
                        }
                    ],
                },
                we.LINE_TIMEOUT: {
                    we.TIMEOUT_FIELD: 1,
                    we.SOURCES_FIELD: [{**spend, we.SPEND_ROOT_FIELD: str(quiet_root)}],
                },
                we.LINE_UNREADABLE: {
                    we.TIMEOUT_FIELD: 1,
                    we.SOURCES_FIELD: [
                        {**spend, we.SPEND_ROOT_FIELD: str(absent_root)}
                    ],
                },
                we.LINE_INVALID: {we.SOURCES_FIELD: [spend]},
            }
            for form, request in requests.items():
                runs[form], _ = _execute(c, json.dumps(request), {})
    return LineFormObservation(runs, c)
