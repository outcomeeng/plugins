"""Domain model for verification recipe orchestration.

Defines the Step and Recipe records plus the process Protocols. These are the
only types the orchestrator's main loop depends on; the production adapter that
binds gate-step execution to subprocess.Popen lives in _spawner.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Step:
    """A single recipe step: a human label and the argv to execute."""

    label: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class Recipe:
    """A deterministic verification recipe and its step lists."""

    name: str
    verification_type: str | None
    purpose: str | None
    preflight_steps: tuple[Step, ...]
    steps: tuple[Step, ...]


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
