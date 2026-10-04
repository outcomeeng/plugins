"""Test infrastructure for the position-direction scripts.

The scripts ship in the direct-positions skill and import one another by bare
name, so the harness loads them with their directory on the import path and
leaves the importing process's module table as it found it. The controlled
backends, inbox, and clock expose what a poll observed; the linked tests own
every predicate.
"""

from __future__ import annotations

import functools
import importlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any

from hypothesis import HealthCheck, given, seed, settings
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
SCRIPTS_DIR = ROOT / "src/plugins/coding-agents/skills/direct-positions/scripts"
FIXTURE_ROOT = ROOT / "outcomeeng_testing/fixtures/position_direction"
WATCH_FIXTURES = FIXTURE_ROOT / "watch"
STATE_FIXTURES = FIXTURE_ROOT / "state"
VALID_WATCH_FIXTURE = WATCH_FIXTURES / "valid.json"
NODE_TESTS = "spx/43-coding-agents.enabler/43-position-direction.enabler/tests"

SCRIPT_MODULES = ("environment", "position_mail", "watch_file", "roster", "monitor")
ROSTER_SCRIPT = "roster.py"
MONITOR_SCRIPT = "monitor.py"

# A shipped script run as a process leaves no bytecode in the skill directory.
NO_BYTECODE_ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

# The clock a rig advances between polls.
CLOCK_START = datetime(2026, 10, 4, 0, 0, tzinfo=timezone.utc)
POLL_INTERVAL = timedelta(minutes=1)

# How long a trial of real processes waits for an observation, and how long it
# lets a late loser exit after the expected ones have.
OBSERVATION_TIMEOUT_SECONDS = 20.0
GRACE_SECONDS = 1.0
POLL_PERIOD_SECONDS = 0.05
LOOP_INTERVAL_SECONDS = "0.2"


@dataclass(frozen=True)
class Scripts:
    environment: ModuleType
    position_mail: ModuleType
    watch_file: ModuleType
    roster: ModuleType
    monitor: ModuleType


@functools.cache
def load_scripts() -> Scripts:
    """The shipped scripts, imported once with the module table left as found."""
    saved = {
        name: sys.modules.pop(name) for name in SCRIPT_MODULES if name in sys.modules
    }
    sys.path.insert(0, str(SCRIPTS_DIR))
    keep_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        loaded = {name: importlib.import_module(name) for name in SCRIPT_MODULES}
    finally:
        sys.dont_write_bytecode = keep_bytecode
        sys.path.remove(str(SCRIPTS_DIR))
        for name in SCRIPT_MODULES:
            sys.modules.pop(name, None)
        sys.modules.update(saved)
    return Scripts(**loaded)


# --- generated domains -------------------------------------------------------


@dataclass(frozen=True)
class Budget:
    """Seed and run count of one generated domain, with the command that replays it."""

    seed_value: int
    examples: int
    replay_path: str


ROSTER_ROWS = Budget(
    2026100401, 60, f"just test {NODE_TESTS}/test_roster.mapping.l1.py"
)
MAIL_EDGES = Budget(
    2026100402, 40, f"just test {NODE_TESTS}/test_monitor.mapping.l1.py"
)
CONTEXT_STEPS = Budget(
    2026100403, 3, f"just test {NODE_TESTS}/test_monitor.mapping.l1.py"
)
STALL_EDGES = Budget(
    2026100404, 40, f"just test {NODE_TESTS}/test_monitor.mapping.l1.py"
)
REMIND_EDGES = Budget(
    2026100405, 40, f"just test {NODE_TESTS}/test_monitor.mapping.l1.py"
)
INVALID_INTERVALS = Budget(
    2026100406, 12, f"just test {NODE_TESTS}/test_watch_input.compliance.l1.py"
)
LOOP_RACES = Budget(
    2026100407, 4, f"just test {NODE_TESTS}/test_monitor_lock.compliance.l1.py"
)


def check_examples(
    strategy: st.SearchStrategy[Any],
    check: Callable[[Any], None],
    budget: Budget,
) -> None:
    """Run `check` over examples of a domain, reporting the seed and replay path on failure."""

    @seed(budget.seed_value)
    @settings(
        max_examples=budget.examples,
        deadline=None,
        print_blob=True,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
    )
    @given(strategy)
    def run(example: Any) -> None:
        check(example)

    run_replayable_property(
        run, seed_value=budget.seed_value, replay_path=budget.replay_path
    )


# --- controlled collaborators for the monitor --------------------------------


@dataclass
class ControlledBackend:
    """A backend whose inventory and pane texts the rig sets between polls.

    Stands in for a live Prowl or herdr so that every session state and pane
    text is reachable on demand (combinatorial cost) and a failing adapter can
    be produced (failure simulation). It records every pane read.
    """

    name: str
    scripts: Scripts
    inventory: list[Any] | str = field(
        default_factory=list
    )  # a str is the failure message
    texts: dict[str, str] = field(default_factory=dict)
    read_failures: dict[str, str] = field(default_factory=dict)
    reads: list[str] = field(default_factory=list)

    def sessions(self) -> list[Any]:
        if isinstance(self.inventory, str):
            raise self.scripts.environment.AdapterError(self.inventory)
        return list(self.inventory)

    def read(self, session: Any, lines: int = 0) -> str:
        self.reads.append(session.handle)
        if session.handle in self.read_failures:
            raise self.scripts.environment.AdapterError(
                self.read_failures[session.handle]
            )
        return self.texts.get(session.handle, "")


@dataclass
class ControlledInbox:
    """The Director's inbox as the mail adapter would answer it."""

    scripts: Scripts
    records: list[Any] = field(default_factory=list)
    failure: str | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def __call__(self, channel: str, agent: str) -> list[Any]:
        self.calls.append((channel, agent))
        if self.failure is not None:
            raise self.scripts.position_mail.MailError(self.failure)
        return list(self.records)

    def deliver(self, record_id: int, sender: str, subject: str) -> None:
        self.records.append(
            self.scripts.position_mail.Record(
                id=record_id, sender=sender, subject=subject, correlation=None
            )
        )


class Rig:
    """One watch file polled over controlled backends, inbox, and clock.

    State is carried between polls through a JSON round trip, as the state
    file carries it between monitor runs.
    """

    def __init__(self, watch: dict[str, Any]) -> None:
        self.scripts = load_scripts()
        self.watch = watch
        self.backends = {
            name: ControlledBackend(name, self.scripts)
            for name in self.scripts.environment.BACKENDS
        }
        self.inbox = ControlledInbox(self.scripts)
        self.production_inbox = False
        self.state: dict[str, Any] = {}
        self.now = CLOCK_START

    @classmethod
    def watching(cls, position: str, backend: str, cwd: str, **entry: Any) -> Rig:
        """A rig whose watch file names one session entry, with the given thresholds."""
        return cls(
            watch_with(
                sessions=[
                    {"position": position, "backend": backend, "cwd": cwd, **entry}
                ]
            )
        )

    def place(
        self, state: Any, handle: str, *, detail: str = "", text: str | None = None
    ) -> None:
        """Make the first entry's session live in `state`, with its pane showing `text`."""
        entry = self.watch["sessions"][0]
        backend = self.backends[entry["backend"]]
        backend.inventory = [
            self.session(entry["backend"], handle, entry["cwd"], state, detail)
        ]
        if text is not None:
            backend.texts[handle] = text

    def read_mail_through_the_adapter(self) -> None:
        """Poll with the production inbox reader, which runs the mail adapter in the channel."""
        self.production_inbox = True

    def vacate(self) -> None:
        """End the first entry's session."""
        self.backends[self.watch["sessions"][0]["backend"]].inventory = []

    def session(
        self, backend: str, handle: str, cwd: str, state: Any, detail: str = ""
    ) -> Any:
        return self.scripts.environment.Session(
            backend=backend,
            handle=handle,
            cwd=cwd,
            state=state,
            changed_at=None,
            detail=detail,
        )

    def poll(self, advance: timedelta = POLL_INTERVAL) -> list[Any]:
        """Advance the clock, then poll once; the events that poll emitted."""
        self.now += advance
        self.state = json.loads(json.dumps(self.state))
        return self.scripts.monitor.poll(
            self.watch,
            self.state,
            self.now,
            backends=self.backends,
            inbox=None if self.production_inbox else self.inbox,
        )


# --- real processes ----------------------------------------------------------


@dataclass(frozen=True)
class Completed:
    returncode: int
    stdout: str
    stderr: str


def run_script(script: str, args: Sequence[str | Path]) -> Completed:
    """Run a shipped script as a process and capture its exit and output."""
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script), *map(str, args)],
        capture_output=True,
        text=True,
        timeout=OBSERVATION_TIMEOUT_SECONDS,
        check=False,
        env=NO_BYTECODE_ENV,
    )
    return Completed(completed.returncode, completed.stdout, completed.stderr)


def scratch_dir() -> TemporaryDirectory[str]:
    return TemporaryDirectory(prefix="position-direction-")


def violating_watch_fixtures() -> tuple[str, ...]:
    """The names of the watch fixtures that violate the file contract, one per defect."""
    return tuple(sorted(path.stem for path in WATCH_FIXTURES.glob("*.defect")))


def _fixture(directory: Path, name: str) -> Path:
    """The fixture file named `name`, whatever its extension: only the defect sidecar shares the stem."""
    (found,) = [
        path for path in directory.glob(f"{name}.*") if path.suffix != ".defect"
    ]
    return found


def watch_fixture(name: str) -> Path:
    return _fixture(WATCH_FIXTURES, name)


def watch_fixture_defect(name: str) -> str:
    """What the fixture's own author recorded as the defect its content carries."""
    return (WATCH_FIXTURES / f"{name}.defect").read_text().strip()


def invocation(script: str, watch: Path, state: Path) -> list[Path]:
    """The arguments a script takes: the roster reads a watch file; the monitor also writes a state file."""
    return [watch] if script == ROSTER_SCRIPT else [watch, state]


def copy_into(directory: Path, source: Path) -> Path:
    """A copy of an inert fixture inside a scratch directory, for a script that writes its argument."""
    target = directory / source.name
    target.write_bytes(source.read_bytes())
    return target


def state_fixture(name: str) -> Path:
    return _fixture(STATE_FIXTURES, name)


def state_fixture_defect(name: str) -> str:
    return (STATE_FIXTURES / f"{name}.defect").read_text().strip()


def _wait_until(condition: Callable[[], bool]) -> bool:
    deadline = time.monotonic() + OBSERVATION_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(POLL_PERIOD_SECONDS)
    return condition()


def _spawn_loop(watch: Path, state: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            str(SCRIPTS_DIR / MONITOR_SCRIPT),
            str(watch),
            str(state),
            "--every",
            LOOP_INTERVAL_SECONDS,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=NO_BYTECODE_ENV,
    )


def _end(loops: Sequence[subprocess.Popen[str]]) -> None:
    for loop in loops:
        if loop.poll() is None:
            loop.kill()
        loop.wait()
        if loop.stdout is not None:
            loop.stdout.close()


def _lock_text(state: Path) -> str:
    try:
        return Path(f"{state}.lock").read_text().strip()
    except OSError:
        return ""


@dataclass(frozen=True)
class LoopRace:
    """What `started` monitor loops on one state file did."""

    started: int
    exited_outputs: tuple[str, ...]
    running_pids: tuple[int, ...]
    lock_holder: str


def race_loops(started: int) -> LoopRace:
    """Start loops together on one state file and observe who exited and who ran on."""
    with scratch_dir() as directory:
        state = Path(directory) / "state.json"
        loops = [_spawn_loop(VALID_WATCH_FIXTURE, state) for _ in range(started)]
        try:
            _wait_until(
                lambda: (
                    sum(1 for loop in loops if loop.poll() is not None) >= started - 1
                )
            )
            time.sleep(GRACE_SECONDS)
            exited = tuple(
                (loop.stdout.read() if loop.stdout is not None else "")
                for loop in loops
                if loop.poll() is not None
            )
            running = tuple(loop.pid for loop in loops if loop.poll() is None)
            return LoopRace(started, exited, running, _lock_text(state))
        finally:
            _end(loops)


@dataclass(frozen=True)
class LoopTakeover:
    """A loop started on a state file whose lock an earlier holder left behind."""

    left_behind: str
    pid: int
    lock_holder: str
    exited: bool
    output: str


def _dead_pid() -> int:
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait()
    return process.pid


def take_over_stale_lock() -> LoopTakeover:
    """A loop started where the lock file names a process that is gone."""
    with scratch_dir() as directory:
        state = Path(directory) / "state.json"
        left = str(_dead_pid())
        Path(f"{state}.lock").write_text(left)
        loop = _spawn_loop(VALID_WATCH_FIXTURE, state)
        try:
            _wait_until(
                lambda: _lock_text(state) == str(loop.pid) or loop.poll() is not None
            )
            exited = loop.poll() is not None
            output = loop.stdout.read() if exited and loop.stdout is not None else ""
            return LoopTakeover(left, loop.pid, _lock_text(state), exited, output)
        finally:
            _end([loop])


def take_over_killed_holder() -> LoopTakeover:
    """A loop started after the previous holder was killed without cleaning up."""
    with scratch_dir() as directory:
        state = Path(directory) / "state.json"
        first = _spawn_loop(VALID_WATCH_FIXTURE, state)
        try:
            _wait_until(lambda: _lock_text(state) == str(first.pid))
            left = _lock_text(state)
            first.kill()
            first.wait()
        finally:
            _end([first])
        second = _spawn_loop(VALID_WATCH_FIXTURE, state)
        try:
            _wait_until(
                lambda: (
                    _lock_text(state) == str(second.pid) or second.poll() is not None
                )
            )
            exited = second.poll() is not None
            output = (
                second.stdout.read() if exited and second.stdout is not None else ""
            )
            return LoopTakeover(left, second.pid, _lock_text(state), exited, output)
        finally:
            _end([second])


def watch_with(**fields: Any) -> dict[str, Any]:
    """A watch file naming one watching position, with the given top-level fields."""
    return {"position": "Director", **fields}
