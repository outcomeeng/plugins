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
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import pytest

from outcomeeng.validation import ProductionSpawner, SUMMARY_PATH_LABEL

POLL_INTERVAL_SECONDS: Final = 0.05
ORCHESTRATOR_STARTUP_SECONDS: Final = 3.0
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
        return handle

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


def _process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_child_pid(stderr_reader: subprocess.Popen[bytes]) -> int:
    deadline = time.monotonic() + ORCHESTRATOR_STARTUP_SECONDS
    buffer = b""
    while time.monotonic() < deadline:
        assert stderr_reader.stderr is not None
        chunk = stderr_reader.stderr.readline()
        if chunk:
            buffer += chunk
            if b"CHILD_PID=" in buffer:
                line = buffer.split(b"CHILD_PID=")[1].split(b"\n")[0]
                return int(line.strip())
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError("orchestrator did not announce child PID in time")


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
        child_pid = _read_child_pid(orchestrator)
        assert _process_is_alive(child_pid)

        os.kill(orchestrator.pid, delivered_signal)

        deadline = time.monotonic() + TERMINATION_DEADLINE_SECONDS
        while time.monotonic() < deadline:
            if not _process_is_alive(child_pid):
                break
            time.sleep(POLL_INTERVAL_SECONDS)
        assert not _process_is_alive(child_pid), (
            f"child PID {child_pid} survived signal {delivered_signal}"
        )

        orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
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
        assert summary["status"] == "fail"
        assert summary["exit_code"] == 128 + delivered_signal
        assert summary["steps"][0]["status"] == "fail"
        assert summary["steps"][0]["exit_code"] == 128 + delivered_signal
        assert "log_path" in summary["steps"][0]
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
