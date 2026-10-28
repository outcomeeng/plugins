"""Real process-group infrastructure for gate signal scenario evidence.

Each entry point drives the production orchestrator or spawner in real
processes and returns what those processes showed: liveness readings, the
signal a grandchild received, exit codes, the parsed run summary, and the
timing and reap state of a live orchestrator's direct child. The linked tests
own every predicate over those observations. A process that fails to start or
announce itself raises `SignalHarnessLifecycleError`.
"""

from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.distribution.shipped_scripts import NO_BYTECODE_OPTION
from outcomeeng.validation import ProductionSpawner, SUMMARY_PATH_LABEL

ORCHESTRATOR_STARTUP_SECONDS: Final = 8.0
TERMINATION_DEADLINE_SECONDS: Final = 6.0
CONTROLLED_CHILD_SLEEP_SECONDS: Final = 60.0
GROUP_MARKER_WAIT_SECONDS: Final = ORCHESTRATOR_STARTUP_SECONDS
GROUP_MARKER_POLL_SECONDS: Final = 0.01
# The orchestrator's own process signals itself this long after it enters the
# child wait, so the signal lands while the interrupted wait holds the lock.
WAIT_ENTRY_SIGNAL_DELAY_SECONDS: Final = 0.2


class SignalHarnessLifecycleError(RuntimeError):
    """A real process the signal harness drives failed to start or announce itself."""


@dataclass(frozen=True)
class SignalRunObservation:
    """One forwarded signal delivered to a real orchestrator with a child group."""

    delivered_signal: signal.Signals
    child_alive_before_signal: bool
    grandchild_alive_before_signal: bool
    grandchild_received_signal: int | None
    child_alive_after_exit: bool
    orchestrator_exit_code: int
    summary: Mapping[str, object]


@dataclass(frozen=True)
class DirectReapObservation:
    """A live orchestrator's view of its direct child after `run` returns."""

    delivered_signal: signal.Signals
    child_exits_on_sigterm: bool
    child_reaped_before_orchestrator_exit: bool
    seconds_from_signal_to_return: float
    run_exit_code: int


@dataclass(frozen=True)
class SpawnerOutputObservation:
    """A real child's printed text, exit code, and the file the spawner captured."""

    printed: str
    exit_code: int
    captured: str


@dataclass(frozen=True)
class SpawnerGroupSignalObservation:
    """A real child's poll result before a group signal and exit code after it."""

    poll_before_signal: int | None
    exit_code_after_signal: int


def _process_group_command(pid_path: Path, signal_path: Path) -> tuple[str, ...]:
    """Return a child command with an observable grandchild in its process group."""
    grandchild_program = (
        "import os\n"
        "import pathlib\n"
        "import signal\n"
        "import time\n"
        f"pid_marker = pathlib.Path({str(pid_path)!r})\n"
        f"signal_marker = pathlib.Path({str(signal_path)!r})\n"
        "def announce(marker, value):\n"
        "    staged = marker.with_name(marker.name + '.staged')\n"
        "    staged.write_text(value, encoding='utf-8')\n"
        "    os.replace(staged, marker)\n"
        "def handle_term(signum, _frame):\n"
        "    announce(signal_marker, str(signum))\n"
        "    raise SystemExit(0)\n"
        "signal.signal(signal.SIGTERM, handle_term)\n"
        "announce(pid_marker, str(os.getpid()))\n"
        f"time.sleep({CONTROLLED_CHILD_SLEEP_SECONDS})\n"
    )
    return (
        sys.executable,
        "-c",
        "import pathlib, signal, subprocess, sys, time; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        f"grandchild = subprocess.Popen({[sys.executable, '-c', grandchild_program]!r}); "
        f"time.sleep({CONTROLLED_CHILD_SLEEP_SECONDS})",
    )


def _direct_child_command(
    ready_path: Path, *, exits_on_sigterm: bool
) -> tuple[str, ...]:
    """Return a direct child that announces readiness, then sleeps."""
    disposition = (
        "" if exits_on_sigterm else "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    )
    return (
        sys.executable,
        "-c",
        "import pathlib, signal, time; "
        f"{disposition}"
        f"pathlib.Path({str(ready_path)!r}).write_text('ready', encoding='utf-8'); "
        f"time.sleep({CONTROLLED_CHILD_SLEEP_SECONDS})",
    )


def _wrapper_program(pid_path: Path, signal_path: Path) -> str:
    """Return a wrapper that announces when the orchestrator waits on its child."""
    return f"""
import sys
from outcomeeng.validation import ProductionSpawner, Step, run

class PidPrintingSpawner:
    def __init__(self) -> None:
        self._inner = ProductionSpawner()
    def spawn(self, argv, output_path):
        handle = self._inner.spawn(argv, output_path)
        sys.stderr.write(f"CHILD_PID={{handle.pid}}\\n")
        sys.stderr.flush()
        return AnnouncingHandle(handle)

class AnnouncingHandle:
    def __init__(self, inner) -> None:
        self._inner = inner
    @property
    def pid(self):
        return self._inner.pid
    def poll(self):
        return self._inner.poll()
    def wait(self):
        sys.stderr.write("HANDLE_WAITING\\n")
        sys.stderr.flush()
        return self._inner.wait()
    def send_signal_to_group(self, sig):
        self._inner.send_signal_to_group(sig)

steps = (Step(label="long-sleep", argv={_process_group_command(pid_path, signal_path)!r}),)
sys.exit(run(spawner=PidPrintingSpawner(), sink=sys.stdout, steps=steps))
"""


def _spawn_signal_wrapper_program(
    delivered_signal: signal.Signals, pid_path: Path, signal_path: Path
) -> str:
    """Return a wrapper that raises a forwarded signal during production spawn."""
    return f"""
import pathlib, signal, sys, time
from outcomeeng.validation import ProductionSpawner, Step, run

class SignalDuringSpawnSpawner:
    def __init__(self) -> None:
        self._inner = ProductionSpawner()
    def spawn(self, argv, output_path):
        handle = self._inner.spawn(argv, output_path)
        sys.stderr.write(f"CHILD_PID={{handle.pid}}\\n")
        sys.stderr.flush()
        marker = pathlib.Path({str(pid_path)!r})
        deadline = time.monotonic() + {GROUP_MARKER_WAIT_SECONDS!r}
        while time.monotonic() < deadline and not marker.exists():
            time.sleep({GROUP_MARKER_POLL_SECONDS!r})
        if not marker.exists():
            raise RuntimeError("grandchild did not become signal-ready")
        signal.raise_signal({int(delivered_signal)})
        return handle

steps = (Step(label="spawn-window-sleep", argv={_process_group_command(pid_path, signal_path)!r}),)
sys.exit(run(spawner=SignalDuringSpawnSpawner(), sink=sys.stdout, steps=steps))
"""


def _direct_reap_wrapper_program(
    delivered_signal: signal.Signals,
    child_argv: tuple[str, ...],
    ready_path: Path,
    observation_path: Path,
) -> str:
    """Return an orchestrator that signals itself mid-wait and inspects its child.

    The wrapper keeps every handle it spawned alive until it has inspected the
    child, so no garbage-collected `Popen` reaps the child on its behalf.
    """
    return f"""
import json, os, pathlib, signal, sys, threading, time
from outcomeeng.validation import ProductionSpawner, Step, run

held_handles = []
record = {{}}
main_thread = threading.main_thread().ident

def deliver():
    marker = pathlib.Path({str(ready_path)!r})
    deadline = time.monotonic() + {GROUP_MARKER_WAIT_SECONDS!r}
    while time.monotonic() < deadline and not marker.exists():
        time.sleep({GROUP_MARKER_POLL_SECONDS!r})
    time.sleep({WAIT_ENTRY_SIGNAL_DELAY_SECONDS!r})
    record["signalled_at"] = time.monotonic()
    signal.pthread_kill(main_thread, {int(delivered_signal)})

class SelfSignallingSpawner:
    def __init__(self) -> None:
        self._inner = ProductionSpawner()
    def spawn(self, argv, output_path):
        handle = SelfSignallingHandle(self._inner.spawn(argv, output_path))
        held_handles.append(handle)
        record["child_pid"] = handle.pid
        return handle

class SelfSignallingHandle:
    def __init__(self, inner) -> None:
        self._inner = inner
    @property
    def pid(self):
        return self._inner.pid
    def poll(self):
        return self._inner.poll()
    def wait(self):
        threading.Thread(target=deliver, daemon=True).start()
        return self._inner.wait()
    def send_signal_to_group(self, sig):
        self._inner.send_signal_to_group(sig)

steps = (Step(label="direct-child", argv={child_argv!r}),)
exit_code = run(spawner=SelfSignallingSpawner(), sink=sys.stderr, steps=steps)
returned_at = time.monotonic()
try:
    os.waitpid(record["child_pid"], os.WNOHANG)
except ChildProcessError:
    reaped = True
else:
    reaped = False
try:
    os.killpg(record["child_pid"], signal.SIGKILL)
except (ProcessLookupError, PermissionError):
    pass
pathlib.Path({str(observation_path)!r}).write_text(
    json.dumps(
        {{
            "reaped": reaped,
            "seconds": returned_at - record["signalled_at"],
            "exit_code": exit_code,
        }}
    ),
    encoding="utf-8",
)
"""


def _process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_grandchild_pid(pid_path: Path) -> int:
    deadline = time.monotonic() + GROUP_MARKER_WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            return int(pid_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            time.sleep(GROUP_MARKER_POLL_SECONDS)
    raise SignalHarnessLifecycleError("child did not announce grandchild PID in time")


def _read_grandchild_signal(signal_path: Path) -> int | None:
    """Return the signal the grandchild announced receiving, or None in time."""
    deadline = time.monotonic() + GROUP_MARKER_WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            return int(signal_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            time.sleep(GROUP_MARKER_POLL_SECONDS)
    return None


def _terminate_child_group(child_pid: int | None) -> None:
    if child_pid is None:
        return
    try:
        os.killpg(child_pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _read_child_pid_marker(
    stderr_reader: subprocess.Popen[bytes],
    *,
    wait_for_handle: bool,
) -> int:
    deadline = time.monotonic() + ORCHESTRATOR_STARTUP_SECONDS
    buffer = b""
    child_pid: int | None = None
    if stderr_reader.stderr is None:
        raise SignalHarnessLifecycleError("orchestrator stderr is unavailable")
    file_descriptor = stderr_reader.stderr.fileno()
    wait_marker_seen = False
    while time.monotonic() < deadline:
        timeout = max(0.0, deadline - time.monotonic())
        readable, _, _ = select.select([file_descriptor], [], [], timeout)
        if not readable:
            break
        chunk = os.read(file_descriptor, 4096)
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            raw_line, buffer = buffer.split(b"\n", 1)
            if raw_line.startswith(b"CHILD_PID="):
                child_pid = int(raw_line.removeprefix(b"CHILD_PID=").strip())
            if raw_line == b"HANDLE_WAITING":
                wait_marker_seen = True
            if child_pid is not None and (wait_marker_seen or not wait_for_handle):
                return child_pid
    if wait_for_handle:
        raise SignalHarnessLifecycleError(
            "orchestrator did not enter child wait in time"
        )
    raise SignalHarnessLifecycleError("orchestrator did not announce child PID in time")


def _spawn_wrapper(path: Path, program: str) -> subprocess.Popen[bytes]:
    path.write_text(program, encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, NO_BYTECODE_OPTION, str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def _terminate_wrapper(orchestrator: subprocess.Popen[bytes]) -> None:
    if orchestrator.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(orchestrator.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass
    orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)


def _read_summary(orchestrator: subprocess.Popen[bytes]) -> Mapping[str, object]:
    if orchestrator.stdout is None:
        raise SignalHarnessLifecycleError("orchestrator stdout is unavailable")
    stdout_text = orchestrator.stdout.read().decode()
    summary_line = next(
        (
            line
            for line in stdout_text.splitlines()
            if line.startswith(SUMMARY_PATH_LABEL)
        ),
        None,
    )
    if summary_line is None:
        raise SignalHarnessLifecycleError("orchestrator printed no summary path")
    summary_path = Path(summary_line.removeprefix(SUMMARY_PATH_LABEL).strip())
    parsed = cast(object, json.loads(summary_path.read_text(encoding="utf-8")))
    if not isinstance(parsed, dict):
        raise SignalHarnessLifecycleError("orchestrator summary is not a JSON object")
    return cast(dict[str, object], parsed)


def _observe_signal_run(
    delivered_signal: signal.Signals,
    program_name: str,
    program: str,
    pid_path: Path,
    signal_path: Path,
    *,
    harness_delivers_signal: bool,
) -> SignalRunObservation:
    orchestrator = _spawn_wrapper(pid_path.parent / program_name, program)
    child_pid: int | None = None
    try:
        child_pid = _read_child_pid_marker(
            orchestrator, wait_for_handle=harness_delivers_signal
        )
        grandchild_pid = _read_grandchild_pid(pid_path)
        child_alive_before = _process_is_alive(child_pid)
        grandchild_alive_before = _process_is_alive(grandchild_pid)
        if harness_delivers_signal:
            os.kill(orchestrator.pid, delivered_signal)
        orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
        return SignalRunObservation(
            delivered_signal=delivered_signal,
            child_alive_before_signal=child_alive_before,
            grandchild_alive_before_signal=grandchild_alive_before,
            grandchild_received_signal=_read_grandchild_signal(signal_path),
            child_alive_after_exit=_process_is_alive(child_pid),
            orchestrator_exit_code=orchestrator.returncode,
            summary=_read_summary(orchestrator),
        )
    finally:
        _terminate_wrapper(orchestrator)
        _terminate_child_group(child_pid)


def observe_in_flight_signal_run(
    delivered_signal: signal.Signals,
) -> SignalRunObservation:
    """Deliver a signal to a real orchestrator waiting on a child group."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        pid_path = root / "grandchild.pid"
        signal_path = root / "grandchild.signal"
        return _observe_signal_run(
            delivered_signal,
            "wrapper.py",
            _wrapper_program(pid_path, signal_path),
            pid_path,
            signal_path,
            harness_delivers_signal=True,
        )


def observe_spawn_window_signal_run(
    delivered_signal: signal.Signals,
) -> SignalRunObservation:
    """Raise a signal inside a real orchestrator during production child spawn."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        pid_path = root / "grandchild.pid"
        signal_path = root / "grandchild.signal"
        return _observe_signal_run(
            delivered_signal,
            "spawn_signal_wrapper.py",
            _spawn_signal_wrapper_program(delivered_signal, pid_path, signal_path),
            pid_path,
            signal_path,
            harness_delivers_signal=False,
        )


def observe_direct_child_reap(
    delivered_signal: signal.Signals, *, child_exits_on_sigterm: bool
) -> DirectReapObservation:
    """Signal a live orchestrator mid-wait and read its direct child's reap state."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        ready_path = root / "child.ready"
        observation_path = root / "observation.json"
        orchestrator = _spawn_wrapper(
            root / "direct_reap_wrapper.py",
            _direct_reap_wrapper_program(
                delivered_signal,
                _direct_child_command(
                    ready_path, exits_on_sigterm=child_exits_on_sigterm
                ),
                ready_path,
                observation_path,
            ),
        )
        try:
            orchestrator.wait(
                timeout=ORCHESTRATOR_STARTUP_SECONDS + TERMINATION_DEADLINE_SECONDS
            )
        finally:
            _terminate_wrapper(orchestrator)
        if not observation_path.exists():
            stderr = b"" if orchestrator.stderr is None else orchestrator.stderr.read()
            raise SignalHarnessLifecycleError(
                f"orchestrator recorded no observation: {stderr.decode()}"
            )
        recorded = cast(
            dict[str, object],
            json.loads(observation_path.read_text(encoding="utf-8")),
        )
    return DirectReapObservation(
        delivered_signal=delivered_signal,
        child_exits_on_sigterm=child_exits_on_sigterm,
        child_reaped_before_orchestrator_exit=bool(recorded["reaped"]),
        seconds_from_signal_to_return=float(cast(float, recorded["seconds"])),
        run_exit_code=int(cast(int, recorded["exit_code"])),
    )


def observe_production_spawner_output() -> SpawnerOutputObservation:
    """Run a real child that prints one line through the production spawner."""
    with TemporaryDirectory() as directory:
        output_path = Path(directory) / "child.log"
        printed = ProductionSpawner.__name__
        handle = ProductionSpawner().spawn(
            (sys.executable, "-c", f"print({printed!r})"),
            output_path,
        )
        exit_code = handle.wait()
        return SpawnerOutputObservation(
            printed=printed,
            exit_code=exit_code,
            captured=output_path.read_text(encoding="utf-8"),
        )


def observe_production_spawner_group_signal() -> SpawnerGroupSignalObservation:
    """Send SIGTERM to a real sleeping child's group through the production handle."""
    with TemporaryDirectory() as directory:
        output_path = Path(directory) / "sleep.log"
        handle = ProductionSpawner().spawn(
            (
                sys.executable,
                "-c",
                f"import time; time.sleep({CONTROLLED_CHILD_SLEEP_SECONDS})",
            ),
            output_path,
        )
        try:
            poll_before_signal = handle.poll()
            handle.send_signal_to_group(signal.SIGTERM)
            exit_code_after_signal = handle.wait()
        finally:
            if handle.poll() is None:
                handle.send_signal_to_group(signal.SIGKILL)
                handle.wait()
        return SpawnerGroupSignalObservation(
            poll_before_signal=poll_before_signal,
            exit_code_after_signal=exit_code_after_signal,
        )


__all__ = [
    "DirectReapObservation",
    "SignalHarnessLifecycleError",
    "SignalRunObservation",
    "SpawnerGroupSignalObservation",
    "SpawnerOutputObservation",
    "observe_direct_child_reap",
    "observe_in_flight_signal_run",
    "observe_production_spawner_group_signal",
    "observe_production_spawner_output",
    "observe_spawn_window_signal_run",
]
