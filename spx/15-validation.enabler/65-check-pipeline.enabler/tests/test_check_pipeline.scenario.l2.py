"""Level 2 scenario test for the check-pipeline orchestrator's signal forwarding.

Exercises the real OS process tree: launches the orchestrator's `run()` in a
real subprocess with a single long-sleeping step that ignores SIGTERM, sends
SIGTERM/SIGINT/SIGHUP to the orchestrator, and verifies the child's process
group is terminated within the grace window via SIGKILL.

Marked `l2` because the assertion requires a real OS process group, real
`subprocess.Popen(start_new_session=True)`, and a real `os.killpg`.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import pytest

POLL_INTERVAL_SECONDS: Final = 0.05
ORCHESTRATOR_STARTUP_SECONDS: Final = 3.0
TERMINATION_DEADLINE_SECONDS: Final = 6.0


def _wrapper_program() -> str:
    # Runs the orchestrator with a single step that ignores SIGTERM and sleeps.
    # Prints the child PID to stderr so the test can observe it.
    return r"""
import sys, io
from outcomeeng.scripts.check_pipeline import (
    ProductionSpawner,
    Step,
    run,
)

class PidPrintingSpawner:
    def __init__(self) -> None:
        self._inner = ProductionSpawner()
    def spawn(self, argv):
        handle = self._inner.spawn(argv)
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
    finally:
        if orchestrator.poll() is None:
            os.killpg(os.getpgid(orchestrator.pid), signal.SIGKILL)
            orchestrator.wait(timeout=TERMINATION_DEADLINE_SECONDS)
