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
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass


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

    def spawn(self, argv: Sequence[str]) -> _PopenHandle:
        proc = subprocess.Popen(
            list(argv),
            start_new_session=True,
        )
        return _PopenHandle(_proc=proc)
