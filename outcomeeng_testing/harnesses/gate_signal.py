"""Real process-group infrastructure for gate signal scenario evidence."""

from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.validation import (
    FORWARDED_SIGNALS,
    ProductionSpawner,
    RUN_FAIL_STATUS,
    SUMMARY_KEY_EXIT_CODE,
    SUMMARY_KEY_LOG_PATH,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
    SUMMARY_PATH_LABEL,
)

ORCHESTRATOR_STARTUP_SECONDS: Final = 8.0
TERMINATION_DEADLINE_SECONDS: Final = 6.0
CONTROLLED_CHILD_SLEEP_SECONDS: Final = 60.0
GROUP_MARKER_WAIT_SECONDS: Final = ORCHESTRATOR_STARTUP_SECONDS
GROUP_MARKER_POLL_SECONDS: Final = 0.01


def _process_group_command(pid_path: Path, signal_path: Path) -> tuple[str, ...]:
    """Return a child command with an observable grandchild in its process group."""
    grandchild_program = (
        "import os\n"
        "import pathlib\n"
        "import signal\n"
        "import time\n"
        f"pid_marker = pathlib.Path({str(pid_path)!r})\n"
        f"signal_marker = pathlib.Path({str(signal_path)!r})\n"
        "def handle_term(signum, _frame):\n"
        "    signal_marker.write_text(str(signum), encoding='utf-8')\n"
        "    raise SystemExit(0)\n"
        "signal.signal(signal.SIGTERM, handle_term)\n"
        "pid_marker.write_text(str(os.getpid()), encoding='utf-8')\n"
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
        except FileNotFoundError:
            time.sleep(GROUP_MARKER_POLL_SECONDS)
    raise AssertionError("child did not announce grandchild PID in time")


def _assert_grandchild_received_group_signal(signal_path: Path) -> None:
    deadline = time.monotonic() + GROUP_MARKER_WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            delivered_signal = int(signal_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            time.sleep(GROUP_MARKER_POLL_SECONDS)
            continue
        assert delivered_signal == int(signal.SIGTERM)
        return
    raise AssertionError("grandchild did not receive process-group SIGTERM")


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
        raise AssertionError("orchestrator stderr is unavailable")
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
        raise AssertionError("orchestrator did not enter child wait in time")
    raise AssertionError("orchestrator did not announce child PID in time")


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


def _read_summary(orchestrator: subprocess.Popen[bytes]) -> dict[str, object]:
    if orchestrator.stdout is None:
        raise AssertionError("orchestrator stdout is unavailable")
    stdout_text = orchestrator.stdout.read().decode()
    summary_line = next(
        line for line in stdout_text.splitlines() if line.startswith(SUMMARY_PATH_LABEL)
    )
    summary_path = Path(summary_line.removeprefix(SUMMARY_PATH_LABEL).strip())
    parsed = cast(object, json.loads(summary_path.read_text(encoding="utf-8")))
    if not isinstance(parsed, dict):
        raise AssertionError("orchestrator summary is not a JSON object")
    return cast(dict[str, object], parsed)


def _assert_failed_signal_summary(
    orchestrator: subprocess.Popen[bytes], delivered_signal: signal.Signals
) -> None:
    expected_exit_code = 128 + int(delivered_signal)
    assert orchestrator.returncode == expected_exit_code
    summary = _read_summary(orchestrator)
    assert summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert summary[SUMMARY_KEY_EXIT_CODE] == expected_exit_code
    steps = cast(list[dict[str, object]], summary[SUMMARY_KEY_STEPS])
    assert steps[0][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert steps[0][SUMMARY_KEY_EXIT_CODE] == expected_exit_code
    assert SUMMARY_KEY_LOG_PATH in steps[0]


def assert_signals_terminate_process_groups_within_grace() -> None:
    """Exercise every forwarded signal against a real in-flight child group."""
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
                assert _process_is_alive(child_pid)
                assert _process_is_alive(grandchild_pid)
                os.kill(orchestrator.pid, delivered_signal)
                orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
                _assert_grandchild_received_group_signal(grandchild_signal_path)
                assert not _process_is_alive(child_pid), (
                    f"child PID {child_pid} survived signal {delivered_signal}"
                )
                _assert_failed_signal_summary(orchestrator, delivered_signal)
            finally:
                _terminate_wrapper(orchestrator)
                _terminate_child_group(child_pid)


def assert_spawn_window_signals_reach_child_groups() -> None:
    """Exercise every forwarded signal raised during production child spawn."""
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
                assert _process_is_alive(child_pid)
                assert _process_is_alive(grandchild_pid)
                orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
                _assert_grandchild_received_group_signal(grandchild_signal_path)
                assert not _process_is_alive(child_pid), (
                    f"child PID {child_pid} survived spawn-window signal {delivered_signal}"
                )
                _assert_failed_signal_summary(orchestrator, delivered_signal)
            finally:
                _terminate_wrapper(orchestrator)
                _terminate_child_group(child_pid)


def assert_production_spawner_captures_child_output() -> None:
    """Exercise the production spawner's real file-backed output capture."""
    with TemporaryDirectory() as directory:
        output_path = Path(directory) / "child.log"
        captured_output = ProductionSpawner.__name__
        handle = ProductionSpawner().spawn(
            (sys.executable, "-c", f"print({captured_output!r})"),
            output_path,
        )
        assert handle.wait() == 0
        assert output_path.read_text(encoding="utf-8") == f"{captured_output}\n"


def assert_production_spawner_signal_terminates_child() -> None:
    """Exercise production process-group signalling against a real child."""
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
            assert handle.poll() is None
            handle.send_signal_to_group(signal.SIGTERM)
            assert handle.wait() != 0
        finally:
            if handle.poll() is None:
                handle.send_signal_to_group(signal.SIGKILL)
                handle.wait()


__all__ = [
    "assert_production_spawner_captures_child_output",
    "assert_production_spawner_signal_terminates_child",
    "assert_signals_terminate_process_groups_within_grace",
    "assert_spawn_window_signals_reach_child_groups",
]
