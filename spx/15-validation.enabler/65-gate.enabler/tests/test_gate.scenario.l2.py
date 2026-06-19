"""Level 2 scenario test for the gate orchestrator's signal forwarding.

Exercises the real OS process tree: launches the orchestrator's `run()` in a
real subprocess with a single long-sleeping step that ignores SIGTERM, sends
SIGTERM/SIGINT/SIGHUP to the orchestrator, and verifies the child's process
group is terminated within the grace window via SIGKILL.

Marked `l2` because the assertion requires a real OS process group, real
`subprocess.Popen(start_new_session=True)`, and a real `os.killpg`.
"""

from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import pytest

from outcomeeng.validation import (
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


def _wrapper_program() -> str:
    # Runs the orchestrator with a single step that ignores SIGTERM and sleeps.
    # Prints the child PID to stderr so the test can observe it.
    return r"""
import sys, io
from outcomeeng.validation import (
    ProductionSpawner,
    Step,
    run,
)

class PidPrintingSpawner:
    def __init__(self) -> None:
        self._inner = ProductionSpawner()
    def spawn(self, argv, output_path):
        handle = self._inner.spawn(argv, output_path)
        sys.stderr.write(f"CHILD_PID={handle.pid}\n")
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
        sys.stderr.write("HANDLE_WAITING\n")
        sys.stderr.flush()
        return self._inner.wait()
    def send_signal_to_group(self, sig):
        self._inner.send_signal_to_group(sig)

ignore_term = (
    sys.executable,
    "-c",
    "import signal, time; "
    "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    "time.sleep(60)",
)
steps = (Step(label="long-sleep", argv=ignore_term),)
sys.exit(run(spawner=PidPrintingSpawner(), sink=sys.stdout, steps=steps))
"""


def _spawn_signal_wrapper_program(delivered_signal: signal.Signals) -> str:
    return f"""
import signal, sys
from outcomeeng.validation import (
    ProductionSpawner,
    Step,
    run,
)

class SignalDuringSpawnSpawner:
    def __init__(self) -> None:
        self._inner = ProductionSpawner()
    def spawn(self, argv, output_path):
        handle = self._inner.spawn(argv, output_path)
        sys.stderr.write(f"CHILD_PID={{handle.pid}}\\n")
        sys.stderr.flush()
        signal.raise_signal({int(delivered_signal)})
        return handle

ignore_term = (
    sys.executable,
    "-c",
    "import signal, time; "
    "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    "time.sleep(60)",
)
steps = (Step(label="spawn-window-sleep", argv=ignore_term),)
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


def _read_child_pid_marker(
    stderr_reader: subprocess.Popen[bytes],
    *,
    wait_for_handle: bool,
) -> int:
    deadline = time.monotonic() + ORCHESTRATOR_STARTUP_SECONDS
    buffer = b""
    child_pid: int | None = None
    assert stderr_reader.stderr is not None
    fd = stderr_reader.stderr.fileno()
    wait_marker_seen = False
    while time.monotonic() < deadline:
        timeout = max(0.0, deadline - time.monotonic())
        readable, _, _ = select.select([fd], [], [], timeout)
        if not readable:
            break
        chunk = os.read(fd, 4096)
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


def _read_child_pid(stderr_reader: subprocess.Popen[bytes]) -> int:
    return _read_child_pid_marker(stderr_reader, wait_for_handle=False)


def _read_child_pid_at_wait(stderr_reader: subprocess.Popen[bytes]) -> int:
    return _read_child_pid_marker(stderr_reader, wait_for_handle=True)


@pytest.mark.parametrize(
    "delivered_signal",
    [signal.SIGTERM, signal.SIGINT, signal.SIGHUP],
)
def test_signal_terminates_process_group_within_grace(
    delivered_signal: int,
    tmp_path: Path,
) -> None:
    wrapper = tmp_path / "wrapper.py"
    wrapper.write_text(_wrapper_program(), encoding="utf-8")

    orchestrator = subprocess.Popen(
        [sys.executable, str(wrapper)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        child_pid = _read_child_pid_at_wait(orchestrator)
        assert _process_is_alive(child_pid)

        os.kill(orchestrator.pid, delivered_signal)

        orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
        assert not _process_is_alive(child_pid), (
            f"child PID {child_pid} survived signal {delivered_signal}"
        )

        assert orchestrator.returncode == 128 + delivered_signal
        assert orchestrator.stdout is not None
        stdout_text = orchestrator.stdout.read().decode()
        summary_line = next(
            line
            for line in stdout_text.splitlines()
            if line.startswith(SUMMARY_PATH_LABEL)
        )
        summary_path = Path(summary_line.removeprefix(SUMMARY_PATH_LABEL).strip())
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert summary[SUMMARY_KEY_EXIT_CODE] == 128 + delivered_signal
        steps = summary[SUMMARY_KEY_STEPS]
        assert isinstance(steps, list)
        assert steps[0][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert steps[0][SUMMARY_KEY_EXIT_CODE] == 128 + delivered_signal
        assert SUMMARY_KEY_LOG_PATH in steps[0]
    finally:
        if orchestrator.poll() is None:
            os.killpg(os.getpgid(orchestrator.pid), signal.SIGKILL)
            orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)


@pytest.mark.parametrize(
    "delivered_signal",
    [signal.SIGTERM, signal.SIGINT, signal.SIGHUP],
)
def test_signal_during_production_spawn_reaches_child_group(
    delivered_signal: signal.Signals,
    tmp_path: Path,
) -> None:
    wrapper = tmp_path / "spawn_signal_wrapper.py"
    wrapper.write_text(
        _spawn_signal_wrapper_program(delivered_signal), encoding="utf-8"
    )

    orchestrator = subprocess.Popen(
        [sys.executable, str(wrapper)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        child_pid = _read_child_pid(orchestrator)
        assert _process_is_alive(child_pid)

        orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
        assert not _process_is_alive(child_pid), (
            f"child PID {child_pid} survived spawn-window signal {delivered_signal}"
        )

        assert orchestrator.returncode == 128 + delivered_signal
        assert orchestrator.stdout is not None
        stdout_text = orchestrator.stdout.read().decode()
        summary_line = next(
            line
            for line in stdout_text.splitlines()
            if line.startswith(SUMMARY_PATH_LABEL)
        )
        summary_path = Path(summary_line.removeprefix(SUMMARY_PATH_LABEL).strip())
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert summary[SUMMARY_KEY_EXIT_CODE] == 128 + delivered_signal
        steps = summary[SUMMARY_KEY_STEPS]
        assert isinstance(steps, list)
        assert steps[0][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert steps[0][SUMMARY_KEY_EXIT_CODE] == 128 + delivered_signal
        assert SUMMARY_KEY_LOG_PATH in steps[0]
    finally:
        if orchestrator.poll() is None:
            os.killpg(os.getpgid(orchestrator.pid), signal.SIGKILL)
            orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)


def test_production_spawner_captures_child_output(tmp_path: Path) -> None:
    output_path = tmp_path / "child.log"

    handle = ProductionSpawner().spawn(
        (sys.executable, "-c", "print('captured')"),
        output_path,
    )

    assert handle.wait() == 0
    assert output_path.read_text(encoding="utf-8") == "captured\n"


def test_production_spawner_signal_to_group_terminates_child(tmp_path: Path) -> None:
    output_path = tmp_path / "sleep.log"
    handle = ProductionSpawner().spawn(
        (sys.executable, "-c", "import time; time.sleep(30)"),
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
