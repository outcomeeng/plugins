"""Pytest plugin that bounds every temp file of a run under one run root.

The run creates its run root under ``RUN_ROOTS_RELATIVE`` in the worktree it
runs from, points ``TMPDIR`` and Python's default temp directory at that root so
that ``tempfile`` and every child process write there without naming it, sets a
Git ceiling at the root, removes ``tmp_path`` directories as their tests end,
removes the root when the run ends, and sweeps every root a killed run left.

The root ``conftest.py`` registers this module; it holds no other logic.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

RUN_ROOTS_RELATIVE: Final = Path(".spx/worktree/test-runs")
TEMP_VARIABLE: Final = "TMPDIR"
GIT_CEILING_VARIABLE: Final = "GIT_CEILING_DIRECTORIES"
RUN_ROOT_PREFIX: Final = "run-"
TMP_PATH_FIXTURE: Final = "tmp_path"
DISTRIBUTED_WORKER_ATTRIBUTE: Final = "workerinput"


@dataclass(frozen=True)
class _Saved:
    """Process state the run root displaces, restored when the run ends."""

    temp_variable: str | None
    git_ceiling: str | None
    default_tempdir: str | None


@dataclass
class _ActiveRun:
    root: Path
    saved: _Saved


_active: _ActiveRun | None = None


def run_roots_directory(worktree: Path) -> Path:
    """Directory that holds the run roots of ``worktree``."""
    return worktree / RUN_ROOTS_RELATIVE


def _remove(path: Path) -> None:
    """Remove ``path`` without following a symlink out of the worktree."""
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def sweep_stale_roots(worktree: Path) -> None:
    """Remove every entry under the worktree's run-roots directory."""
    roots = run_roots_directory(worktree)
    if not roots.is_dir() or roots.is_symlink():
        return
    for entry in roots.iterdir():
        _remove(entry)


def create_run_root(worktree: Path) -> Path:
    """Create a fresh run root under the worktree's run-roots directory."""
    roots = run_roots_directory(worktree)
    roots.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=RUN_ROOT_PREFIX, dir=roots)).resolve()


def _restore(saved: _Saved) -> None:
    for variable, value in (
        (TEMP_VARIABLE, saved.temp_variable),
        (GIT_CEILING_VARIABLE, saved.git_ceiling),
    ):
        if value is None:
            os.environ.pop(variable, None)
        else:
            os.environ[variable] = value
    tempfile.tempdir = saved.default_tempdir


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Sweep stale roots, create the run root, and point temp locations at it."""
    global _active
    if hasattr(config, DISTRIBUTED_WORKER_ATTRIBUTE) or _active is not None:
        return
    worktree = config.rootpath.resolve()
    sweep_stale_roots(worktree)
    root = create_run_root(worktree)
    saved = _Saved(
        temp_variable=os.environ.get(TEMP_VARIABLE),
        git_ceiling=os.environ.get(GIT_CEILING_VARIABLE),
        default_tempdir=tempfile.tempdir,
    )
    os.environ[TEMP_VARIABLE] = str(root)
    os.environ[GIT_CEILING_VARIABLE] = str(root)
    tempfile.tempdir = str(root)
    _active = _ActiveRun(root=root, saved=saved)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: pytest.Item) -> Generator[None]:
    """Remove the test's ``tmp_path`` directory once its teardown has run."""
    funcargs = getattr(item, "funcargs", None) or {}
    directory = funcargs.get(TMP_PATH_FIXTURE)
    yield
    if isinstance(directory, Path):
        _remove(directory)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore process state and remove the run root."""
    global _active
    if _active is None:
        return
    active, _active = _active, None
    _restore(active.saved)
    shutil.rmtree(active.root, ignore_errors=True)
