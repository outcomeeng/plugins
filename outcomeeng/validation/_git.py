"""Git command runner seam for validation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from outcomeeng.validation._spawner import run_captured

GIT_COMMAND_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class GitCommandResult:
    """Captured output from one git command."""

    returncode: int
    stdout: str
    stderr: str = ""


class GitRunner(Protocol):
    """Runs one git command in a repository and returns captured stdout."""

    def __call__(self, command: Sequence[str], repo: Path) -> GitCommandResult: ...


def run_git_command(command: Sequence[str], repo: Path) -> GitCommandResult:
    """Run one bounded git command for local gate path discovery."""

    completed = run_captured(
        command,
        cwd=repo,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    )
    return GitCommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
