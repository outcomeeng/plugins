"""Test infrastructure for the usage controller's `control-positions` entry point.

The harness drives the shipped entry point against a configuration file, frozen
screens, and frozen token measurements, through a recording Prowl collaborator
(`/test` Stage 5, interaction protocols) and a fake pass clock (Stage 5, time).
It returns observations; every predicate lives in the linked tests.

Contract the entry point exposes, and this harness consumes:

- `Collaborators(runner, tokens, clock, now, data_root, platform, launch_agents_dir)`
- `run_pass(config_path, collaborators)` returning an object with `reports`
  (each with `kind` and `subject`) and `unfinished` (worktree paths)
- `main(argv, environ, collaborators)` returning an exit code; `argv == ["pass"]`
  runs one pass
- `schedule(operation, collaborators)` returning an object with `status`
- `read_records(data_root)` returning the durable records, oldest first
- `ConfigurationError` carrying the rejected `field`
- enumerations `ConfigField`, `RecordField`, `Action`, `ReportKind`,
  `ScheduleOperation`, `ScheduleStatus`
- `PASS_BOUND_SECONDS`
- the token source protocol `tokens(worktree, start, end) -> int | None` over the
  half-open window of the pass, and the clock protocol `clock() -> float` seconds
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import plistlib
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any

from outcomeeng_testing.generators.control_positions import (
    COMPACTION_CONTEXT_PERCENT,
    COMPACTION_MULTIPLE,
    PACE_TOKENS,
    PASS_INTERVAL_MINUTES,
    PAUSE_MULTIPLE,
    WEEKLY_CEILING_PERCENT,
    AgentKind,
    PositionSpec,
)
from outcomeeng_testing.harnesses.prowl_environment import load_prowl_environment

ROOT = Path(__file__).parents[2]
CONTROL_POSITIONS_PATH = (
    ROOT / "src/plugins/coding-agents/skills/control-positions/scripts"
    "/control_positions.py"
)
FIXTURES = ROOT / "outcomeeng_testing/fixtures/control_positions"
BASE_TIME = dt.datetime(2026, 1, 5, 9, 0, tzinfo=dt.timezone.utc)
PASS_INTERVAL = dt.timedelta(minutes=PASS_INTERVAL_MINUTES)
CONFIG_DIRECTORY = "outcome-engineering"
CONFIG_FILE = "control-positions.toml"
INVALID_VALUE = "invalid"
SCALAR_CONFIG_FIELDS = (
    "COMPACTION_CONTEXT_PERCENT",
    "COMPACTION_MULTIPLE",
    "PAUSE_MULTIPLE",
    "WEEKLY_CEILING_PERCENT",
    "KEY_AUTHORIZED",
    "STOP_AUTHORIZED",
    "SKIP",
)


def load_control_positions() -> ModuleType:
    """Load the shipped entry point by path, as the installed plugin runs it."""
    spec = importlib.util.spec_from_file_location(
        "coding_agents_control_positions", CONTROL_POSITIONS_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load control-positions entry point: {CONTROL_POSITIONS_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(CONTROL_POSITIONS_PATH.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(CONTROL_POSITIONS_PATH.parent))
    return module


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ProwlCall:
    operation: str
    pane: str | None
    argument: str | None


@dataclass(frozen=True)
class ConfigSpec:
    """The operator's configuration file as a structured value."""

    positions: tuple[PositionSpec, ...]
    pace: Mapping[str, int] = field(default_factory=lambda: {})
    skip: tuple[str, ...] = ()
    compaction_context_percent: float = COMPACTION_CONTEXT_PERCENT
    compaction_multiple: float = COMPACTION_MULTIPLE
    pause_multiple: float = PAUSE_MULTIPLE
    weekly_ceiling_percent: float = WEEKLY_CEILING_PERCENT
    key_authorized: bool = True
    stop_authorized: bool = True
    overrides: Mapping[str, object] = field(default_factory=lambda: {})

    def subscriptions(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.subscription for item in self.positions))


@dataclass(frozen=True)
class PassStep:
    """The frozen world one pass measures; absent entries default to idle and low."""

    contexts: Mapping[str, int] = field(default_factory=lambda: {})
    weekly: Mapping[str, int] = field(default_factory=lambda: {})
    busy: frozenset[str] = frozenset()
    tokens: Mapping[str, int | None] = field(default_factory=lambda: {})
    config: ConfigSpec | None = None


def toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    raise TypeError(f"Unsupported TOML value: {value!r}")


def render_config(module: ModuleType, spec: ConfigSpec) -> str:
    fields = module.ConfigField
    scalars: dict[str, object] = {
        fields.COMPACTION_CONTEXT_PERCENT: spec.compaction_context_percent,
        fields.COMPACTION_MULTIPLE: spec.compaction_multiple,
        fields.PAUSE_MULTIPLE: spec.pause_multiple,
        fields.WEEKLY_CEILING_PERCENT: spec.weekly_ceiling_percent,
        fields.KEY_AUTHORIZED: spec.key_authorized,
        fields.STOP_AUTHORIZED: spec.stop_authorized,
        fields.SKIP: list(spec.skip),
    }
    scalars.update(spec.overrides)
    lines = [f"{key} = {toml_value(value)}" for key, value in scalars.items()]
    for subscription in spec.subscriptions():
        lines.append(f"\n[{fields.SUBSCRIPTIONS}.{subscription}]")
        lines.append(
            f"{fields.PACE_TOKENS} = "
            f"{toml_value(spec.pace.get(subscription, PACE_TOKENS))}"
        )
    for item in spec.positions:
        lines.append(f"\n[[{fields.POSITIONS}]]")
        lines.append(f"{fields.WORKTREE} = {toml_value(item.worktree)}")
        lines.append(f"{fields.SUBSCRIPTION} = {toml_value(item.subscription)}")
    return "\n".join(lines) + "\n"


def screen_text(item: PositionSpec, step: PassStep) -> str:
    """Render the frozen status line or footer a Prowl read returns for a position."""
    used = step.contexts.get(item.worktree, 0)
    weekly = step.weekly.get(item.subscription, 0)
    if item.kind is AgentKind.CODEX:
        template = (FIXTURES / "codex_idle.txt").read_text(encoding="utf-8")
        return template.format(context_left=100 - used, weekly_left=100 - weekly)
    name = "claude_busy.txt" if item.worktree in step.busy else "claude_idle.txt"
    template = (FIXTURES / name).read_text(encoding="utf-8")
    return template.format(context_used=used, weekly_used=weekly)


class FakeClock:
    """Stage 5 time exception: every Prowl command consumes a fixed span."""

    def __init__(self, seconds_per_command: float) -> None:
        self.seconds_per_command = seconds_per_command
        self.elapsed = 0.0

    def __call__(self) -> float:
        return self.elapsed


class ProwlRecorder:
    """Recording Prowl collaborator that answers from the frozen inventory."""

    def __init__(
        self,
        positions: Sequence[PositionSpec],
        step: PassStep,
        clock: FakeClock,
    ) -> None:
        self.positions = tuple(positions)
        self.step = step
        self.clock = clock
        self.calls: list[ProwlCall] = []
        self.commands: list[tuple[str, ...]] = []
        self.adapter = load_prowl_environment()

    def _inventory(self) -> tuple[PositionSpec, ...]:
        return tuple(item for item in self.positions if item.in_prowl)

    def _operation(self, argv: tuple[str, ...]) -> str | None:
        prefixes = self.adapter.PUBLIC_PROWL_COMMAND_PREFIXES
        matches = [
            (operation, prefix)
            for operation, prefix in prefixes.items()
            if argv[: len(prefix)] == prefix
        ]
        if not matches:
            return None
        return str(max(matches, key=lambda match: len(match[1]))[0].value)

    def _pane(self, argv: tuple[str, ...]) -> str | None:
        for option, selector in (
            ("--pane", "pane"),
            ("--worktree", "worktree"),
            ("--target", "pane"),
        ):
            if option in argv:
                value = argv[argv.index(option) + 1]
                if selector == "pane":
                    return value
                for item in self.positions:
                    if item.worktree == value:
                        return item.pane
                return value
        return None

    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult:
        self.clock.elapsed += self.clock.seconds_per_command
        self.commands.append(argv)
        operation = self._operation(argv)
        pane = self._pane(argv)
        argument = argv[-1] if operation in {"send", "key"} else None
        if operation is None:
            return CommandResult(2, "", "unsupported command")
        self.calls.append(ProwlCall(operation, pane, argument))
        known = {item.pane: item for item in self._inventory()}
        if operation == "agents":
            return CommandResult(0, self._json({"agents": self._agents()}), "")
        if operation == "list":
            return CommandResult(0, self._json({"panes": self._panes()}), "")
        if pane not in known:
            return CommandResult(1, "", f"no pane {pane}")
        if operation == "read":
            text = screen_text(known[pane], self.step)
            return CommandResult(0, self._json({"text": text}), "")
        payload = {"input": {"trailing_enter_sent": operation == "send"}}
        return CommandResult(0, self._json(payload), "")

    @staticmethod
    def _json(data: object) -> str:
        return json.dumps({"ok": True, "data": data})

    def _agents(self) -> list[dict[str, object]]:
        return [
            {
                "id": f"agent-{item.ordinal}",
                "pane": {"id": item.pane, "title": item.title},
                "worktree": {
                    "id": item.worktree,
                    "path": item.worktree,
                    "root_path": item.worktree,
                },
                "project": {"path": item.worktree, "branch": "main"},
                "run": {"id": f"run-{item.ordinal}"},
            }
            for item in self._inventory()
        ]

    def _panes(self) -> list[dict[str, object]]:
        return [
            {
                "id": item.pane,
                "title": item.title,
                "worktree": {"path": item.worktree},
            }
            for item in self._inventory()
        ]


class FrozenTokens:
    """Frozen consumption fixtures keyed by pass window and worktree."""

    def __init__(self, step: PassStep, now: dt.datetime) -> None:
        self.step = step
        self.now = now
        self.queries: list[tuple[str, dt.datetime, dt.datetime]] = []

    def tokens(self, worktree: str, start: dt.datetime, end: dt.datetime) -> int | None:
        self.queries.append((worktree, start, end))
        return self.step.tokens.get(worktree)


@dataclass(frozen=True)
class PassObservation:
    calls: tuple[ProwlCall, ...]
    commands: tuple[tuple[str, ...], ...]
    reports: tuple[Any, ...]
    unfinished: tuple[str, ...]
    token_queries: tuple[tuple[str, dt.datetime, dt.datetime], ...]
    records: tuple[dict[str, Any], ...]
    new_records: tuple[dict[str, Any], ...]
    record_files: tuple[Path, ...]
    error: Exception | None
    exit_code: int | None
    elapsed_seconds: float


def run_passes(
    module: ModuleType,
    config: ConfigSpec,
    steps: Sequence[PassStep],
    *,
    seconds_per_command: float = 0.0,
    via_main: bool = False,
) -> list[PassObservation]:
    """Run one pass per step against one persistent configuration and data root."""
    observations: list[PassObservation] = []
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        config_home = root / "config"
        data_root = root / "data"
        data_root.mkdir()
        config_path = config_home / CONFIG_DIRECTORY / CONFIG_FILE
        config_path.parent.mkdir(parents=True)
        current = config
        seen = 0
        for index, step in enumerate(steps):
            if step.config is not None:
                current = step.config
            config_path.write_text(render_config(module, current), encoding="utf-8")
            now = BASE_TIME + index * PASS_INTERVAL
            clock = FakeClock(seconds_per_command)
            runner = ProwlRecorder(current.positions, step, clock)
            tokens = FrozenTokens(step, now)
            collaborators = module.Collaborators(
                runner=runner,
                tokens=tokens,
                clock=clock,
                now=now,
                data_root=data_root,
                platform="darwin",
                launch_agents_dir=root / "launch-agents",
            )
            error: Exception | None = None
            reports: tuple[Any, ...] = ()
            unfinished: tuple[str, ...] = ()
            exit_code: int | None = None
            try:
                if via_main:
                    exit_code = module.main(
                        ["pass"],
                        environ={"XDG_CONFIG_HOME": str(config_home)},
                        collaborators=collaborators,
                    )
                else:
                    result = module.run_pass(config_path, collaborators)
                    reports = tuple(result.reports)
                    unfinished = tuple(result.unfinished)
            except module.ConfigurationError as raised:
                error = raised
            records = tuple(module.read_records(data_root))
            observations.append(
                PassObservation(
                    calls=tuple(runner.calls),
                    commands=tuple(runner.commands),
                    reports=reports,
                    unfinished=unfinished,
                    token_queries=tuple(tokens.queries),
                    records=records,
                    new_records=records[seen:],
                    record_files=tuple(sorted((data_root / "positions").rglob("*"))),
                    error=error,
                    exit_code=exit_code,
                    elapsed_seconds=clock.elapsed,
                )
            )
            seen = len(records)
    return observations


@dataclass(frozen=True)
class ScheduleObservation:
    status: object
    calls: tuple[tuple[str, ...], ...]
    plist: dict[str, Any] | None
    plist_name: str | None
    launch_agent_files: tuple[str, ...]


def schedule_observation(
    module: ModuleType, operation: object, platform: str
) -> ScheduleObservation:
    """Run one scheduling operation through a recording launchctl collaborator."""
    with TemporaryDirectory(prefix="control-positions-evidence-") as temporary:
        root = Path(temporary)
        launch_agents = root / "launch-agents"
        clock = FakeClock(0.0)
        step = PassStep()
        recorder = LaunchctlRecorder()
        collaborators = module.Collaborators(
            runner=recorder,
            tokens=FrozenTokens(step, BASE_TIME),
            clock=clock,
            now=BASE_TIME,
            data_root=root / "data",
            platform=platform,
            launch_agents_dir=launch_agents,
        )
        result = module.schedule(operation, collaborators)
        files = sorted(launch_agents.rglob("*.plist")) if launch_agents.exists() else []
        plist = None
        name = None
        if files:
            name = files[0].name
            plist = plistlib.loads(files[0].read_bytes())
        return ScheduleObservation(
            status=result.status,
            calls=tuple(recorder.calls),
            plist=plist,
            plist_name=name,
            launch_agent_files=tuple(path.name for path in files),
        )


class LaunchctlRecorder:
    """Recording scheduler collaborator; no shared launchd job is touched."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult:
        self.calls.append(argv)
        return CommandResult(0, "state = waiting", "")


def with_config(config: ConfigSpec, **changes: Any) -> ConfigSpec:
    return replace(config, **changes)
