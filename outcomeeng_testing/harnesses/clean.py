"""Recording double for the clean orchestrator.

Implements the `Runner` Protocol declared in `outcomeeng.hygiene.clean`.
The double is a spy (recording calls) and a stub (returning a scripted
exit code), used by `l1` tests to verify clean's argv contract without
invoking real `git clean -fdX` against the test machine.

Exception case per `plugins/spec-tree/skills/test/references/methodology.md`:
- Stage 5 #2 (Interaction protocols): clean's correctness is the argv it
  passes to `git`.
- Stage 5 #4 (Safety): real `git clean -fdX` mutates the test machine's
  working tree.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
import subprocess

from outcomeeng.hygiene.clean import Runner

IGNORED_CACHE_DIR = ".cache"
IGNORED_PYTHON_ENV_DIR = ".venv"


@dataclass
class RecordingRunner:
    """Runner that returns a scripted exit code and records every call."""

    exit_code: int = 0
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, argv: Sequence[str]) -> int:
        self.calls.append(tuple(argv))
        return self.exit_code


@dataclass(frozen=True)
class CleanRepo:
    """Temporary git repository arranged for clean-command evidence."""

    root: Path
    active_python_prefix: Path
    ignored_cache: Path


def create_clean_repo(tmp_path: Path, *, include_cache: bool = True) -> CleanRepo:
    """Create a git repository with ignored active-env and cache directories."""
    repo_root = tmp_path / "repo"
    active_python_prefix = repo_root / IGNORED_PYTHON_ENV_DIR
    ignored_cache = repo_root / IGNORED_CACHE_DIR
    active_python_prefix.mkdir(parents=True)
    if include_cache:
        ignored_cache.mkdir()
    (repo_root / ".gitignore").write_text(
        f"{IGNORED_PYTHON_ENV_DIR}/\n{IGNORED_CACHE_DIR}/\n",
        encoding="utf-8",
    )
    subprocess.run(
        ("git", "init"),
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return CleanRepo(
        root=repo_root,
        active_python_prefix=active_python_prefix,
        ignored_cache=ignored_cache,
    )


__all__ = [
    "CleanRepo",
    "IGNORED_CACHE_DIR",
    "IGNORED_PYTHON_ENV_DIR",
    "RecordingRunner",
    "create_clean_repo",
]


_: type[Runner] = RecordingRunner
