"""Domain model for the check-pipeline orchestrator.

Defines the Step record, the ProcessHandle Protocol, and the ProcessSpawner
Protocol. These are the only types the orchestrator's main loop depends on;
the production adapter that binds them to subprocess.Popen lives in
_spawner.py, the sole module in this package that imports subprocess.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Step:
    """A single quality-gate step: a human label and the argv to execute."""

    label: str
    argv: tuple[str, ...]


class ProcessHandle(Protocol):
    """Handle to a running child whose lifecycle the orchestrator supervises."""

    @property
    def pid(self) -> int: ...

    def poll(self) -> int | None: ...

    def wait(self) -> int: ...

    def send_signal_to_group(self, sig: int) -> None: ...


class ProcessSpawner(Protocol):
    """Spawns a child process and returns a ProcessHandle for it."""

    def spawn(self, argv: Sequence[str], output_path: Path) -> ProcessHandle: ...
