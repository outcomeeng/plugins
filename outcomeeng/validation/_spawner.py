"""Production adapter binding ProcessSpawner to subprocess.Popen.

This module is the only file in the check_pipeline package that imports
subprocess. The compliance test `TestSubprocessImportContainment` enforces
this — moving the import anywhere else breaks the test.

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
        return self._proc.poll()

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
