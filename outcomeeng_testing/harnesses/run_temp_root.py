"""Pytest plugin that bounds every temp file of a run under one run root.

The run creates its run root under ``RUN_ROOTS_RELATIVE`` in the worktree it
runs from, points ``TMPDIR`` and Python's default temp directory at that root so
that ``tempfile`` and every child process write there without naming it, sets a
Git ceiling at the root, removes ``tmp_path`` directories as their tests end,
removes the root when the run ends, and sweeps every root whose run has ended.

A run root's name carries the process id of the run that owns it, so the owner
is known from the moment the root exists. The sweep keeps a root whose owner is
alive, so a second run in the same worktree never removes the root of a run still
in progress, and removes every other entry, including a root a killed run left.
A ``--basetemp`` option is refused, because pytest places ``tmp_path`` there
without consulting ``TMPDIR``.

The root ``conftest.py`` registers this module; it holds no other logic.
"""

from __future__ import annotations

import os
import re
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
RUN_ROOT_OWNER_PATTERN: Final = re.compile(rf"^{RUN_ROOT_PREFIX}(?P<pid>[0-9]+)-")
BASETEMP_OPTION: Final = "--basetemp"
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


def run_root_prefix(pid: int) -> str:
    """Name prefix that marks a run root as owned by process ``pid``."""
    return f"{RUN_ROOT_PREFIX}{pid}-"


def is_process_alive(pid: int) -> bool:
    """Whether a process with id ``pid`` exists."""
    if pid < 1:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _is_live_run_root(entry: Path) -> bool:
    """Whether ``entry`` is a run root whose owning run is still in progress."""
    if entry.is_symlink() or not entry.is_dir():
        return False
    owner = RUN_ROOT_OWNER_PATTERN.match(entry.name)
    return owner is not None and is_process_alive(int(owner.group("pid")))


def sweep_stale_roots(worktree: Path) -> None:
    """Remove every entry under the worktree's run-roots directory whose run has ended."""
    roots = run_roots_directory(worktree)
    if not roots.is_dir() or roots.is_symlink():
        return
    for entry in roots.iterdir():
        if not _is_live_run_root(entry):
            _remove(entry)


def create_run_root(worktree: Path) -> Path:
    """Create a fresh run root under the worktree's run-roots directory."""
    roots = run_roots_directory(worktree)
    roots.mkdir(parents=True, exist_ok=True)
    prefix = run_root_prefix(os.getpid())
    return Path(tempfile.mkdtemp(prefix=prefix, dir=roots)).resolve()


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
    """Refuse ``--basetemp``, sweep ended runs' roots, create the run root, and point temp locations at it."""
    global _active
    if hasattr(config, DISTRIBUTED_WORKER_ATTRIBUTE) or _active is not None:
        return
    if config.option.basetemp is not None:
        raise pytest.UsageError(
            f"{BASETEMP_OPTION} places tmp_path outside the run root that bounds "
            f"every temp file of the run; remove {BASETEMP_OPTION} and let the run "
            "root hold the run's temp files"
        )
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
