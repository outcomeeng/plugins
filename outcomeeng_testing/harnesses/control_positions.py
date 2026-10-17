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
- `SubprocessRunner`, whose default `timeout_seconds` is the span a hung command
  occupies when the pass applies no tighter timeout; a pass that caps a command's
  timeout passes it to the runner's `run` as the optional keyword `timeout_seconds`
- `ConsumptionTokens()`, the production token source, and `load_sibling`
- the token source protocol `tokens(worktree, start, end) -> int | None` over the
  half-open window of the pass, and the clock protocol `clock() -> float` seconds
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import plistlib
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
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
    TOKEN_MEASUREMENT_DEADLINES,
    WEEKLY_CEILING_PERCENT,
    AgentKind,
    PositionSpec,
    SiblingApiChange,
)
from outcomeeng_testing.harnesses.prowl_environment import load_prowl_environment

ROOT = Path(__file__).parents[2]
CONTROL_POSITIONS_PATH = (
    ROOT / "src/plugins/coding-agents/skills/control-positions/scripts"
    "/control_positions.py"
)
BUILT_CONTROL_POSITIONS_PATH = (
    ROOT / "dist/claude/coding-agents/skills/control-positions/scripts"
    "/control_positions.py"
)
FIXTURES = ROOT / "outcomeeng_testing/fixtures/control_positions"
BASE_TIME = dt.datetime(2026, 1, 5, 9, 0, tzinfo=dt.timezone.utc)
PASS_INTERVAL = dt.timedelta(minutes=PASS_INTERVAL_MINUTES)
CONFIG_DIRECTORY = "outcome-engineering"
CONFIG_FILE = "control-positions.toml"
INVALID_VALUE = "invalid"
HUNG_COMMAND_EXIT_CODE = 124
RECORDS_DIRECTORY = "positions"
READ_ONLY_MODE = 0o500
WRITABLE_MODE = 0o700
NUMERIC_CONFIG_FIELDS = (
    "COMPACTION_CONTEXT_PERCENT",
    "COMPACTION_MULTIPLE",
    "PAUSE_MULTIPLE",
    "WEEKLY_CEILING_PERCENT",
)
SCALAR_CONFIG_FIELDS = (
    "COMPACTION_CONTEXT_PERCENT",
    "COMPACTION_MULTIPLE",
    "PAUSE_MULTIPLE",
    "WEEKLY_CEILING_PERCENT",
    "KEY_AUTHORIZED",
    "STOP_AUTHORIZED",
    "SKIP",
)


def load_control_positions(*, built: bool = False) -> ModuleType:
    """Load the shipped entry point by path, as the installed plugin runs it.

    `built` loads the generated plugin tree, whose sibling skills carry the rendered
    price table the consumption-control parser needs; the authored tree carries the
    unrendered template.
    """
    path = BUILT_CONTROL_POSITIONS_PATH if built else CONTROL_POSITIONS_PATH
    name = (
        "coding_agents_control_positions_built"
        if built
        else "coding_agents_control_positions"
    )
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load control-positions entry point: {path}")
    module = importlib.util.module_from_spec(spec)
    sibling_names = {item.stem for item in path.parent.glob("*.py")} - {path.stem}
    saved = {item: sys.modules.get(item) for item in sibling_names} if built else {}
    for item in saved:
        sys.modules.pop(item, None)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
        for item, previous in saved.items():
            if previous is None:
                sys.modules.pop(item, None)
            else:
                sys.modules[item] = previous
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
    pace: Mapping[str, float] = field(default_factory=lambda: {})
    skip: tuple[str, ...] = ()
    compaction_context_percent: float = COMPACTION_CONTEXT_PERCENT
    compaction_multiple: float = COMPACTION_MULTIPLE
    pause_multiple: float = PAUSE_MULTIPLE
    weekly_ceiling_percent: float = WEEKLY_CEILING_PERCENT
    key_authorized: bool = True
    stop_authorized: bool = True
    overrides: Mapping[str, object] = field(default_factory=lambda: {})
    unpaced: tuple[str, ...] = ()  # subscriptions declared with no configured pace

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
    # When set, the fake-clock `leading_seconds` of this pass alone, replacing the
    # value `run_passes` applies to every pass.
    leading_seconds: Sequence[float] | None = None
    # When set, the token source of this pass alone, replacing the frozen source.
    token_source: Any | None = None
    # Prowl operations the recorder refuses, as (operation, pane) pairs: the command
    # fails for that pane and the call is still recorded (Stage 5 failure simulation).
    refused: frozenset[tuple[str, str]] = frozenset()
    # Fake seconds that pass between the pass clock's start and its first use, so the
    # pass bound is reached before the inventory command starts (Stage 5 time).
    stall_seconds: float = 0.0
    # When set, the durable record directory refuses writes during this pass alone, so
    # a pass that records an action raises; the raised error is observed.
    records_blocked: bool = False


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
        if subscription not in spec.unpaced:
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
    """Stage 5 time exception: every Prowl command consumes a span of fake time.

    The first commands consume the listed `leading_seconds`. Later commands consume
    `seconds_per_command`, or, when `hangs` is set, never return on their own: a
    hung command consumes the timeout applied to it and is then killed, the span a
    real subprocess with that timeout occupies.
    """

    def __init__(
        self,
        seconds_per_command: float,
        leading_seconds: Sequence[float] = (),
        hangs: bool = False,
        command_timeout: float = 0.0,
        stall_seconds: float = 0.0,
    ) -> None:
        self.seconds_per_command = seconds_per_command
        self.leading_seconds = tuple(leading_seconds)
        self.hangs = hangs
        self.command_timeout = command_timeout
        self.stall_seconds = stall_seconds
        self.commands = 0
        self.elapsed = 0.0
        self.reads = 0

    def __call__(self) -> float:
        # The first read starts the pass clock; the stall lands before the second.
        self.reads += 1
        if self.reads == 2:
            self.elapsed += self.stall_seconds
        return self.elapsed

    def consume(self, timeout_seconds: float | None) -> bool:
        """Advance by one command's span; return False when the timeout killed it."""
        index = self.commands
        self.commands += 1
        if index < len(self.leading_seconds):
            self.elapsed += self.leading_seconds[index]
            return True
        if self.hangs:
            applied = (
                self.command_timeout if timeout_seconds is None else timeout_seconds
            )
            self.elapsed += max(applied, 0.0)
            return False
        self.elapsed += self.seconds_per_command
        return True


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
        self.refused = step.refused
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

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandResult:
        completed = self.clock.consume(timeout_seconds)
        self.commands.append(argv)
        operation = self._operation(argv)
        pane = self._pane(argv)
        argument = argv[-1] if operation in {"send", "key"} else None
        if operation is None:
            return CommandResult(2, "", "unsupported command")
        self.calls.append(ProwlCall(operation, pane, argument))
        if not completed:
            return CommandResult(HUNG_COMMAND_EXIT_CODE, "", "command timed out")
        known = {item.pane: item for item in self._inventory()}
        if operation == "agents":
            return CommandResult(0, self._json({"agents": self._agents()}), "")
        if operation == "list":
            return CommandResult(0, self._json({"panes": self._panes()}), "")
        if pane not in known:
            return CommandResult(1, "", f"no pane {pane}")
        if (operation, pane) in self.refused:
            return CommandResult(1, "", f"{operation} refused for {pane}")
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

    def __init__(
        self,
        step: PassStep,
        now: dt.datetime,
        clock: FakeClock | None = None,
        seconds: float = 0.0,
    ) -> None:
        self.step = step
        self.now = now
        self.clock = clock
        self.seconds = seconds
        self.queries: list[tuple[str, dt.datetime, dt.datetime]] = []

    def tokens(self, worktree: str, start: dt.datetime, end: dt.datetime) -> int | None:
        self.queries.append((worktree, start, end))
        if self.clock is not None:
            self.clock.elapsed += self.seconds  # Stage 5 time: a measurement's span
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


def pass_time(start_time: dt.datetime, index: int) -> dt.datetime:
    """The time of pass `index` when the first pass runs at `start_time`."""
    return start_time + index * PASS_INTERVAL


def pass_window(start_time: dt.datetime, index: int) -> tuple[dt.datetime, dt.datetime]:
    """The span one pass measures: the pass interval ending at the pass time."""
    end = pass_time(start_time, index)
    return end - PASS_INTERVAL, end


def run_passes(
    module: ModuleType,
    config: ConfigSpec,
    steps: Sequence[PassStep],
    *,
    seconds_per_command: float = 0.0,
    leading_seconds: Sequence[float] = (),
    hangs: bool = False,
    via_main: bool = False,
    token_seconds: float = 0.0,
    token_source: Any | None = None,
    start_time: dt.datetime = BASE_TIME,
) -> list[PassObservation]:
    """Run one pass per step against one persistent configuration and data root.

    Pass `index` runs at `pass_time(start_time, index)`; `start_time` defaults to
    `BASE_TIME`.

    `leading_seconds` and `hangs` shape the fake clock of every pass (see
    `FakeClock`); a hung command's applied timeout is the optional keyword
    `timeout_seconds` of the runner's `run`, or the default timeout of the entry
    point's own subprocess runner when the pass passes none. `token_seconds` is the
    span of fake time each frozen token measurement consumes; `token_source`
    replaces the frozen token source with a caller-supplied one.
    """
    command_timeout = float(module.SubprocessRunner().timeout_seconds)
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
            now = pass_time(start_time, index)
            clock = FakeClock(
                seconds_per_command,
                leading_seconds
                if step.leading_seconds is None
                else step.leading_seconds,
                hangs,
                command_timeout,
                step.stall_seconds,
            )
            runner = ProwlRecorder(current.positions, step, clock)
            tokens = FrozenTokens(step, now, clock, token_seconds)
            chosen = (
                step.token_source if step.token_source is not None else token_source
            )
            collaborators = module.Collaborators(
                runner=runner,
                tokens=tokens if chosen is None else chosen,
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
            records_directory = data_root / RECORDS_DIRECTORY
            if step.records_blocked:
                records_directory.mkdir(exist_ok=True)
                records_directory.chmod(READ_ONLY_MODE)
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
            except Exception as raised:
                if not (
                    isinstance(raised, module.ConfigurationError)
                    or step.records_blocked
                ):
                    raise
                error = raised
            finally:
                if step.records_blocked:
                    records_directory.chmod(WRITABLE_MODE)
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


TRANSCRIPT_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/consumption_control/assistant.json"
)
TRANSCRIPT_WORKSPACE_KEY = "cwd"
TOKEN_ENVIRONMENT_NAMES = ("ALERT_ENV", "BUDGET_ENV", "PRICE_OVERRIDE_ENV")


@dataclass
class ParserWorld:
    """The real consumption-control accounting over a disposable home directory.

    Transcripts are captured assistant rows written under the home's transcript
    directory; the accounting database is built by the production token source
    from them. Handles and observations only: the linked test owns every verdict.
    """

    accounting: ModuleType
    tokens: Any
    projects: Path
    window: tuple[dt.datetime, dt.datetime]
    after_rows_window: tuple[dt.datetime, dt.datetime]
    tokens_per_row: int
    stamp: dt.datetime
    appended: int = 0

    def start_time_for(self, index: int) -> dt.datetime:
        """The first-pass time that puts the fixture row inside pass `index`'s window.

        Pass `index` runs one second after the row's stamp, so the pass is at or
        after the reset anchor and its window holds the row.
        """
        return self.stamp + dt.timedelta(seconds=1) - index * PASS_INTERVAL

    def collection(self) -> Mapping[str, Any]:
        """Run one real collection and return the accounting's own result."""
        accounting = self.accounting
        config = accounting.Config.from_environment(
            os.environ, accounting.DEFAULT_ROOT, accounting.DEFAULT_PROJECTS
        )
        with accounting.Evidence(config) as evidence:
            collected: Mapping[str, Any] = evidence.collect(self.window[1])
        return collected

    def add_transcript_row(self, worktree: str) -> None:
        """Append one captured assistant row whose workspace is `worktree`."""
        row = json.loads(TRANSCRIPT_FIXTURE.read_text(encoding="utf-8"))
        fields = self.accounting.AccountingField
        self.appended += 1
        row[TRANSCRIPT_WORKSPACE_KEY] = worktree
        row[fields.UUID] = f"{row[fields.UUID]}-{self.appended}"
        row[fields.MESSAGE][fields.ID] = (
            f"{row[fields.MESSAGE][fields.ID]}-{self.appended}"
        )
        session = worktree.strip("/").replace("/", "_")
        row[fields.SESSIONID] = session
        with (self.projects / f"{session}.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")


@contextmanager
def real_parser_world(
    module: ModuleType, *, transcript_root: bool = True
) -> Iterator[ParserWorld]:
    """Run the production token source against a real accounting database.

    The sibling accounting module is imported fresh under a disposable home so its
    default state and transcript roots lie inside it; the process environment and
    the module registry are restored afterwards. With `transcript_root` false the
    transcript directory is never created, so every collection leaves the
    accounting history incomplete.
    """
    sibling_name = module.TOKEN_ACCOUNTING[1]
    saved_module = sys.modules.get(sibling_name)
    saved_environment = dict(os.environ)
    with TemporaryDirectory(prefix="control-positions-parser-") as temporary:
        home = Path(temporary).resolve()
        sys.modules.pop(sibling_name, None)
        os.environ["HOME"] = str(home)
        try:
            accounting = module.load_sibling(*module.TOKEN_ACCOUNTING)
            for name in TOKEN_ENVIRONMENT_NAMES:
                os.environ.pop(getattr(accounting, name), None)
            fields = accounting.AccountingField
            row = json.loads(TRANSCRIPT_FIXTURE.read_text(encoding="utf-8"))
            stamp = accounting.timestamp(row[fields.TIMESTAMP])
            start, end = stamp - accounting.HOUR, stamp + accounting.HOUR
            os.environ[accounting.RESET_ENV] = accounting.iso(start)
            projects = accounting.DEFAULT_PROJECTS
            if transcript_root:
                projects.mkdir(parents=True)
            usage = row[fields.MESSAGE][fields.USAGE]
            yield ParserWorld(
                accounting=accounting,
                tokens=module.ConsumptionTokens(),
                projects=projects,
                window=(start, end),
                after_rows_window=(stamp + dt.timedelta(seconds=1), end),
                tokens_per_row=sum(usage[name] for name in accounting.FIELDS),
                stamp=stamp,
            )
        finally:
            os.environ.clear()
            os.environ.update(saved_environment)
            if saved_module is None:
                sys.modules.pop(sibling_name, None)
            else:
                sys.modules[sibling_name] = saved_module


def token_measurement_limit_seconds() -> float:
    """The longest span one token measurement can occupy, from the sibling's limits.

    The built sibling accounting module owns the per-step deadline; collecting and
    measuring each carry one. The module registry is restored afterwards.
    """
    built = load_control_positions(built=True)
    sibling_name = built.TOKEN_ACCOUNTING[1]
    saved_module = sys.modules.get(sibling_name)
    try:
        accounting = built.load_sibling(*built.TOKEN_ACCOUNTING)
        return float(
            TOKEN_MEASUREMENT_DEADLINES * accounting.MAX_SECONDS
            + built.TOKEN_LOCK_SECONDS
        )
    finally:
        if saved_module is None:
            sys.modules.pop(sibling_name, None)
        else:
            sys.modules[sibling_name] = saved_module


_REMOVED = object()


@contextmanager
def changed_sibling_api(
    accounting: ModuleType, change: SiblingApiChange, worktree: str
) -> Iterator[None]:
    """Change the loaded sibling accounting module's API as a sibling release would.

    The change is undone on exit. Handles only: the linked test decides what the
    controller must do under the change.
    """
    workspaces = accounting.AccountingField.WORKSPACES

    def measuring(value: object) -> Any:
        def measure(self: object, start: object, end: object) -> object:
            return value

        return measure

    evidence, config = accounting.Evidence, accounting.Config
    plan: dict[SiblingApiChange, tuple[object, str, object]] = {
        SiblingApiChange.MEASURE_RETURNS_LIST: (evidence, "measure", measuring([])),
        SiblingApiChange.MEASURE_RETURNS_NUMBER: (evidence, "measure", measuring(7)),
        SiblingApiChange.MEASURE_RETURNS_NONE: (evidence, "measure", measuring(None)),
        SiblingApiChange.WORKSPACES_NOT_MAPPING: (
            evidence,
            "measure",
            measuring({workspaces: [worktree]}),
        ),
        SiblingApiChange.GROUP_MISSING_KEY: (
            evidence,
            "measure",
            measuring({workspaces: {worktree: {}}}),
        ),
        SiblingApiChange.GROUP_NOT_MAPPING: (
            evidence,
            "measure",
            measuring({workspaces: {worktree: 5}}),
        ),
        SiblingApiChange.CONFIG_CONSTRUCTOR_REMOVED: (
            config,
            "from_environment",
            _REMOVED,
        ),
        SiblingApiChange.DEFAULT_PROJECTS_REMOVED: (
            accounting,
            "DEFAULT_PROJECTS",
            _REMOVED,
        ),
        SiblingApiChange.EVIDENCE_REMOVED: (accounting, "Evidence", _REMOVED),
        SiblingApiChange.MEASURE_REMOVED: (evidence, "measure", _REMOVED),
    }
    owner, name, replacement = plan[change]
    previous = vars(owner)[name]
    if replacement is _REMOVED:
        delattr(owner, name)
    else:
        setattr(owner, name, replacement)
    try:
        yield
    finally:
        setattr(owner, name, previous)


class ChangedApiTokens:
    """The production token source measured while the sibling API is changed.

    Each measurement runs the production source under `changed_sibling_api`, so a
    pass using this source meets the changed API at its token step. Observations
    only: the linked test decides what the controller must do.
    """

    def __init__(
        self,
        module: ModuleType,
        accounting: ModuleType,
        change: SiblingApiChange,
        worktree: str,
    ) -> None:
        self.module = module
        self.accounting = accounting
        self.change = change
        self.worktree = worktree

    def tokens(self, worktree: str, start: dt.datetime, end: dt.datetime) -> int | None:
        with changed_sibling_api(self.accounting, self.change, self.worktree):
            measured: int | None = self.module.ConsumptionTokens().tokens(
                worktree, start, end
            )
        return measured


SIBLING_SKILLS_ROOTS = (
    CONTROL_POSITIONS_PATH.parents[2],
    BUILT_CONTROL_POSITIONS_PATH.parents[2],
)
FOREIGN_SIBLING_FILE = "/nonexistent/foreign_sibling.py"


@dataclass
class RegistryObservation:
    """The sibling module names of the controller and the registry around a pass.

    `before` holds the registered object (or None) of each name when the pass
    window opened; `after` holds the same names when it closed, before the harness
    restores the registry. Observations only: the linked test decides what the
    controller may leave behind.
    """

    names: frozenset[str]
    before: Mapping[str, object | None]
    after: Mapping[str, object | None] = field(default_factory=lambda: {})


def sibling_module_names(module: ModuleType) -> frozenset[str]:
    """Every module name the sibling skills the controller loads can be imported as.

    Both the authored and the built tree contribute, because the suite loads the
    controller from either.
    """
    skills = (module.TOKEN_ACCOUNTING[0], module.PROWL_ADAPTER[0])
    return frozenset(
        path.stem
        for root in SIBLING_SKILLS_ROOTS
        for skill in skills
        for path in (root / skill / "scripts").glob("*.py")
    )


@contextmanager
def sibling_registry(
    module: ModuleType, *, foreign: bool = False, isolated: bool = True
) -> Iterator[RegistryObservation]:
    """Open a pass window over a disposable home and observe the sibling registry.

    The home is disposable so a sibling imported inside the window keeps its state
    and transcript roots inside it. `isolated` unregisters every sibling name when
    the window opens, so the pass imports each sibling afresh; without it the
    registrations the suite already holds stay. `foreign` registers a module that
    belongs to no skill under each sibling name the controller loads. On exit the
    harness records `after`, then restores the registry and the environment the
    window found, whatever the pass left behind.
    """
    names = sibling_module_names(module)
    loaded = {module.TOKEN_ACCOUNTING[1], module.PROWL_ADAPTER[1]}
    saved = {name: sys.modules.get(name) for name in names}
    saved_environment = dict(os.environ)
    with TemporaryDirectory(prefix="control-positions-registry-") as temporary:
        os.environ["HOME"] = str(Path(temporary).resolve())
        try:
            if isolated:
                for name in names:
                    sys.modules.pop(name, None)
            if foreign:
                for name in loaded:
                    stand_in = ModuleType(name)
                    stand_in.__file__ = FOREIGN_SIBLING_FILE
                    sys.modules[name] = stand_in
            observation = RegistryObservation(
                names=names,
                before={name: sys.modules.get(name) for name in names},
            )
            try:
                yield observation
            finally:
                observation.after = {name: sys.modules.get(name) for name in names}
        finally:
            os.environ.clear()
            os.environ.update(saved_environment)
            for name, previous in saved.items():
                if previous is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous
