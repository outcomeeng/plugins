"""Recording double for the clean orchestrator.

Implements the `Runner` Protocol declared in `outcomeeng.hygiene.clean`.
The double is a spy (recording calls) and a stub (returning a scripted
exit code), used by `l1` tests to verify clean's argv contract without
invoking real `git clean -fdX` against the test machine.

- Stage 5 #2 (Interaction protocols): clean's correctness is the argv it
  passes to `git`.
- Stage 5 #4 (Safety): real `git clean -fdX` mutates the test machine's
  working tree.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
import subprocess

from outcomeeng.hygiene.clean import GIT_IGNORE_FILE, SPX_STORE_DIR, Runner

IGNORED_CACHE_DIR = ".cache"
IGNORED_PYTHON_ENV_DIR = ".venv"
EXTERNAL_PYTHON_ENV_DIR = "external-venv"


class EnvironmentPlacement(StrEnum):
    """Where the active Python environment sits relative to the repository."""

    INSIDE = "inside"
    SYMLINKED = "symlinked"
    SYMLINK_TARGET = "symlink-target"
    OUTSIDE = "outside"


@dataclass(frozen=True)
class RunnerCall:
    """One recorded invocation: the argv and the directory it ran in."""

    argv: tuple[str, ...]
    cwd: Path


@dataclass
class RecordingRunner:
    """Runner that returns a scripted exit code and records every call."""

    exit_code: int = 0
    calls: list[RunnerCall] = field(default_factory=list)

    def __call__(self, argv: Sequence[str], *, cwd: Path) -> int:
        self.calls.append(RunnerCall(argv=tuple(argv), cwd=cwd))
        return self.exit_code


@dataclass(frozen=True)
class CleanRepo:
    """Temporary git repository arranged for clean-command evidence."""

    root: Path
    active_python_prefix: Path
    ignored_cache: Path
    session_store: Path


def create_clean_repo(
    tmp_path: Path,
    *,
    include_cache: bool = True,
    environment: EnvironmentPlacement = EnvironmentPlacement.INSIDE,
) -> CleanRepo:
    """Create a repository with ignored environment, session store, and cache.

    `environment` selects where the active Python environment sits: directly
    inside the repository, inside it as a symlink to an external directory
    (addressed by the link or by its target), or wholly outside it. The
    returned `active_python_prefix` is the prefix that placement hands the
    cleanup command.
    """
    repo_root = tmp_path / "repo"
    ignored_cache = repo_root / IGNORED_CACHE_DIR
    session_store = repo_root / SPX_STORE_DIR
    repo_root.mkdir(parents=True)
    session_store.mkdir()
    if include_cache:
        ignored_cache.mkdir()
    active_python_prefix = _place_environment(tmp_path, repo_root, environment)
    (repo_root / GIT_IGNORE_FILE).write_text(
        f"{IGNORED_PYTHON_ENV_DIR}/\n{IGNORED_CACHE_DIR}/\n{SPX_STORE_DIR}/\n",
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
        session_store=session_store,
    )


def _place_environment(
    tmp_path: Path,
    repo_root: Path,
    environment: EnvironmentPlacement,
) -> Path:
    in_repo_prefix = repo_root / IGNORED_PYTHON_ENV_DIR
    external_prefix = tmp_path / EXTERNAL_PYTHON_ENV_DIR
    if environment is EnvironmentPlacement.INSIDE:
        in_repo_prefix.mkdir()
        return in_repo_prefix
    if environment is EnvironmentPlacement.OUTSIDE:
        external_prefix.mkdir()
        return external_prefix
    external_prefix.mkdir()
    in_repo_prefix.symlink_to(external_prefix, target_is_directory=True)
    if environment is EnvironmentPlacement.SYMLINKED:
        return in_repo_prefix
    return external_prefix


__all__ = [
    "CleanRepo",
    "EXTERNAL_PYTHON_ENV_DIR",
    "EnvironmentPlacement",
    "IGNORED_CACHE_DIR",
    "IGNORED_PYTHON_ENV_DIR",
    "RecordingRunner",
    "RunnerCall",
    "create_clean_repo",
]


_: type[Runner] = RecordingRunner
