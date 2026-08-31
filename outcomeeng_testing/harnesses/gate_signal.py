"""Real process-group infrastructure for gate signal scenario evidence."""

from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation import (
    FORWARDED_SIGNALS,
    ProductionSpawner,
    SUMMARY_PATH_LABEL,
)

ORCHESTRATOR_STARTUP_SECONDS: Final = 8.0
TERMINATION_DEADLINE_SECONDS: Final = 6.0
CONTROLLED_CHILD_SLEEP_SECONDS: Final = 60.0
GROUP_MARKER_WAIT_SECONDS: Final = ORCHESTRATOR_STARTUP_SECONDS
GROUP_MARKER_POLL_SECONDS: Final = 0.01


@dataclass(frozen=True)
class SignalGroupObservation:
    """Observed state from one forwarded signal reaching a real child group."""

    delivered_signal: signal.Signals
    child_alive_before: bool
    grandchild_alive_before: bool
    received_group_signal: int
    child_alive_after: bool
    orchestrator_exit_code: int | None
    summary: object


@dataclass(frozen=True)
class SpawnerOutputObservation:
    """Observed output and exit status from the production spawner."""

    exit_code: int
    output: str


@dataclass(frozen=True)
class SpawnerSignalObservation:
    """Observed child state around production process-group signalling."""

    alive_before: bool
    exit_code: int


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
    raise RuntimeError("child did not announce grandchild PID in time")


def _read_grandchild_received_group_signal(signal_path: Path) -> int:
    deadline = time.monotonic() + GROUP_MARKER_WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            delivered_signal = int(signal_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            time.sleep(GROUP_MARKER_POLL_SECONDS)
            continue
        return delivered_signal
    raise RuntimeError("grandchild did not receive process-group SIGTERM")


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
        raise RuntimeError("orchestrator stderr is unavailable")
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
        raise RuntimeError("orchestrator did not enter child wait in time")
    raise RuntimeError("orchestrator did not announce child PID in time")


def _spawn_wrapper(path: Path, program: str) -> subprocess.Popen[bytes]:
    path.write_text(program, encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, str(path)],
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


def _read_summary(orchestrator: subprocess.Popen[bytes]) -> object:
    if orchestrator.stdout is None:
        raise RuntimeError("orchestrator stdout is unavailable")
    stdout_text = orchestrator.stdout.read().decode()
    summary_line = next(
        line for line in stdout_text.splitlines() if line.startswith(SUMMARY_PATH_LABEL)
    )
    summary_path = Path(summary_line.removeprefix(SUMMARY_PATH_LABEL).strip())
    return json.loads(summary_path.read_text(encoding="utf-8"))


def observe_signals_terminate_process_groups_within_grace() -> tuple[
    SignalGroupObservation, ...
]:
    """Observe every forwarded signal against a real in-flight child group."""
    observations: list[SignalGroupObservation] = []
    for delivered_signal in FORWARDED_SIGNALS:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            grandchild_pid_path = root / "grandchild.pid"
            grandchild_signal_path = root / "grandchild.signal"
            orchestrator = _spawn_wrapper(
                root / "wrapper.py",
                _wrapper_program(grandchild_pid_path, grandchild_signal_path),
            )
            child_pid: int | None = None
            try:
                child_pid = _read_child_pid_marker(orchestrator, wait_for_handle=True)
                grandchild_pid = _read_grandchild_pid(grandchild_pid_path)
                child_alive_before = _process_is_alive(child_pid)
                grandchild_alive_before = _process_is_alive(grandchild_pid)
                os.kill(orchestrator.pid, delivered_signal)
                orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
                received_group_signal = _read_grandchild_received_group_signal(
                    grandchild_signal_path
                )
                observations.append(
                    SignalGroupObservation(
                        delivered_signal=delivered_signal,
                        child_alive_before=child_alive_before,
                        grandchild_alive_before=grandchild_alive_before,
                        received_group_signal=received_group_signal,
                        child_alive_after=_process_is_alive(child_pid),
                        orchestrator_exit_code=orchestrator.returncode,
                        summary=_read_summary(orchestrator),
                    )
                )
            finally:
                _terminate_wrapper(orchestrator)
                _terminate_child_group(child_pid)
    return tuple(observations)


def observe_spawn_window_signals_reach_child_groups() -> tuple[
    SignalGroupObservation, ...
]:
    """Observe every forwarded signal raised during production child spawn."""
    observations: list[SignalGroupObservation] = []
    for delivered_signal in FORWARDED_SIGNALS:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            grandchild_pid_path = root / "grandchild.pid"
            grandchild_signal_path = root / "grandchild.signal"
            orchestrator = _spawn_wrapper(
                root / "spawn_signal_wrapper.py",
                _spawn_signal_wrapper_program(
                    delivered_signal, grandchild_pid_path, grandchild_signal_path
                ),
            )
            child_pid: int | None = None
            try:
                child_pid = _read_child_pid_marker(orchestrator, wait_for_handle=False)
                grandchild_pid = _read_grandchild_pid(grandchild_pid_path)
                child_alive_before = _process_is_alive(child_pid)
                grandchild_alive_before = _process_is_alive(grandchild_pid)
                orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
                received_group_signal = _read_grandchild_received_group_signal(
                    grandchild_signal_path
                )
                observations.append(
                    SignalGroupObservation(
                        delivered_signal=delivered_signal,
                        child_alive_before=child_alive_before,
                        grandchild_alive_before=grandchild_alive_before,
                        received_group_signal=received_group_signal,
                        child_alive_after=_process_is_alive(child_pid),
                        orchestrator_exit_code=orchestrator.returncode,
                        summary=_read_summary(orchestrator),
                    )
                )
            finally:
                _terminate_wrapper(orchestrator)
                _terminate_child_group(child_pid)
    return tuple(observations)


def observe_production_spawner_captures_child_output() -> SpawnerOutputObservation:
    """Observe the production spawner's real file-backed output capture."""
    with TemporaryDirectory() as directory:
        output_path = Path(directory) / "child.log"
        captured_output = ProductionSpawner.__name__
        handle = ProductionSpawner().spawn(
            (sys.executable, "-c", f"print({captured_output!r})"),
            output_path,
        )
        return SpawnerOutputObservation(
            exit_code=handle.wait(),
            output=output_path.read_text(encoding="utf-8"),
        )


def observe_production_spawner_signal_terminates_child() -> SpawnerSignalObservation:
    """Observe production process-group signalling against a real child."""
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
            alive_before = handle.poll() is None
            handle.send_signal_to_group(signal.SIGTERM)
            exit_code = handle.wait()
            return SpawnerSignalObservation(
                alive_before=alive_before,
                exit_code=exit_code,
            )
        finally:
            if handle.poll() is None:
                handle.send_signal_to_group(signal.SIGKILL)
                handle.wait()


__all__ = [
    "SignalGroupObservation",
    "SpawnerOutputObservation",
    "SpawnerSignalObservation",
    "observe_production_spawner_captures_child_output",
    "observe_production_spawner_signal_terminates_child",
    "observe_signals_terminate_process_groups_within_grace",
    "observe_spawn_window_signals_reach_child_groups",
]
