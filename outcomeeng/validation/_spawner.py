"""Production adapter binding ProcessSpawner to subprocess.Popen.

This module is the validation package subprocess boundary. The compliance test
`TestSubprocessImportContainment` enforces this boundary for validation code.

The adapter passes `start_new_session=True` so that the child runs in its
own process group, enabling `os.killpg` to forward signals to the entire
descendant tree from the orchestrator's signal handler.
"""

from __future__ import annotations

import os
import signal
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_CHILD_UNBLOCK_SIGNALS: Final = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)


@dataclass(frozen=True)
class CapturedProcessResult:
    """Captured output from a bounded subprocess run."""

    returncode: int
    stdout: str
    stderr: str


def _restore_child_signal_mask() -> None:
    signal.pthread_sigmask(signal.SIG_UNBLOCK, _CHILD_UNBLOCK_SIGNALS)


@dataclass
class _PopenHandle:
    """Wraps a subprocess.Popen to implement the ProcessHandle Protocol."""

    _proc: subprocess.Popen[bytes]

    @property
    def pid(self) -> int:
        return self._proc.pid

    def poll(self) -> int | None:
        """Report the child's exit status without blocking.

        ``Popen.poll`` returns ``None`` whenever another call holds the
        handle's waitpid lock. The orchestrator's signal handler runs inside
        the interrupted ``Popen.wait`` that holds that lock, so the handle
        reaps the child directly when ``Popen.poll`` cannot observe it.
        """
        returncode = self._proc.poll()
        if returncode is not None:
            return returncode
        try:
            reaped_pid, wait_status = os.waitpid(self._proc.pid, os.WNOHANG)
        except ChildProcessError:
            return self._proc.returncode
        if reaped_pid == 0:
            return None
        self._proc.returncode = os.waitstatus_to_exitcode(wait_status)
        return self._proc.returncode

    def wait(self) -> int:
        return self._proc.wait()

    def send_signal_to_group(self, sig: int) -> None:
        try:
            pgid = os.getpgid(self._proc.pid)
        except ProcessLookupError:
            return
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return


class ProductionSpawner:
    """Spawns real subprocesses for the orchestrator's quality-gate steps."""

    def spawn(self, argv: Sequence[str], output_path: Path) -> _PopenHandle:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as output:
            proc = subprocess.Popen(
                list(argv),
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                preexec_fn=_restore_child_signal_mask,
            )
        return _PopenHandle(_proc=proc)


def run_captured(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> CapturedProcessResult:
    """Run a bounded command and capture stdout through the package subprocess seam."""

    completed = subprocess.run(
        tuple(argv),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return CapturedProcessResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
