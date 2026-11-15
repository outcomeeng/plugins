"""Compliance evidence that the module's command line honors the switch.

The test runs the module as `just build-instructions` and the drift gate run
it, in a child process whose environment sets the switch variable to `off`. It
observes the exit code, the stderr notice, and the bytes of both root
instruction files before and after. The test is ``l2`` because it spawns a
Python process.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from outcomeeng.distribution import instruction_block as gate

ROOT_FILES = ("CLAUDE.md", "AGENTS.md")


@pytest.mark.parametrize("argv", [[], ["--write"]], ids=["check", "write"])
def test_command_line_with_switch_off_leaves_root_files(argv: list[str]) -> None:
    before = {name: (gate.REPO_ROOT / name).read_bytes() for name in ROOT_FILES}
    completed = subprocess.run(
        [sys.executable, "-m", "outcomeeng.distribution.instruction_block", *argv],
        cwd=gate.REPO_ROOT,
        env={**os.environ, gate.SWITCH_VARIABLE: gate.SWITCH_OFF},
        capture_output=True,
        text=True,
        check=False,
    )
    after = {name: (gate.REPO_ROOT / name).read_bytes() for name in ROOT_FILES}
    assert completed.returncode == 0
    assert f"{gate.SWITCH_VARIABLE}={gate.SWITCH_OFF}" in completed.stderr
    assert after == before
