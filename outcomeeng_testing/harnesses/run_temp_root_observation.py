"""Observations of a pytest run in a scratch worktree.

The harness builds a scratch worktree holding stale run roots and neighbouring
files, runs a whole-payload pytest module in it with a sandbox as the user temp
folder, and returns what the run left behind and what the run recorded about
itself. It states no expectation; the linked tests decide what the observations
mean.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng_testing.harnesses.run_temp_root import (
    BASETEMP_OPTION,
    GIT_CEILING_VARIABLE,
    TEMP_VARIABLE,
    run_root_prefix,
    run_roots_directory,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
CASE_MODULE: Final = (
    REPO_ROOT
    / "outcomeeng_testing"
    / "fixtures"
    / "run_temp_root"
    / "case_temp_runs.py"
)
PLUGIN_MODULE: Final = "outcomeeng_testing.harnesses.run_temp_root"
REPORT_VARIABLE: Final = "RUN_TEMP_ROOT_REPORT"
REPORT_NAME: Final = "report.json"

CHANNEL_TEMPFILE: Final = "tempfile"
CHANNEL_TMP_PATH: Final = "tmp_path"
CHANNEL_CHILD: Final = "child"
CHANNELS: Final = (CHANNEL_TEMPFILE, CHANNEL_TMP_PATH, CHANNEL_CHILD)
PASSING_TEST: Final = "passing"
FAILING_TEST: Final = "failing"

_LEAKING_VARIABLES: Final = (
    GIT_CEILING_VARIABLE,
    "PYTEST_ADDOPTS",
    "PYTEST_CURRENT_TEST",
    "PYTEST_PLUGINS",
    "GIT_DIR",
    "GIT_WORK_TREE",
)
_DEAD_OWNER_SUFFIX: Final = "left-by-a-killed-run"
_LIVE_OWNER_SUFFIX: Final = "held-by-a-run-in-progress"
_BASETEMP_DIRECTORY: Final = "chosen-basetemp"
_STALE_DIRECTORY: Final = "stale-directory"
_STALE_FILE: Final = "stale-file"
_STALE_LINK: Final = "stale-link"
_STALE_NESTED: Final = "nested/artifact.txt"
_OUTSIDE_SENTINEL: Final = "sentinel.txt"
_OUTSIDE_TEXT: Final = "outside the worktree"
_NEIGHBOUR: Final = Path(".spx/worktree/neighbour/keep.txt")
_ENDED_PROCESS_SOURCE: Final = "pass"
_RUNNING_PROCESS_SOURCE: Final = "import sys; sys.stdin.read()"


@dataclass(frozen=True)
class PytestRunObservation:
    """What a scratch pytest run left behind and recorded about itself."""

    returncode: int
    output: str
    worktree: Path
    user_temp_entries_before: tuple[str, ...]
    user_temp_entries_after: tuple[str, ...]
    run_roots_after: tuple[str, ...]
    outside_sentinel_before: str
    outside_sentinel_after: str | None
    neighbour_exists_after: bool
    first_test: dict[str, object]
    created: dict[str, str]
    retained: dict[str, bool]
    live_root_name: str | None
    live_root_exists_after: bool


@dataclass(frozen=True)
class BasetempRunObservation:
    """What a scratch pytest run given a ``--basetemp`` option did."""

    returncode: int
    output: str
    basetemp_created: bool


def _entries(directory: Path) -> tuple[str, ...]:
    return tuple(sorted(entry.name for entry in directory.iterdir()))


def _run_environment(user_temp: Path, report: Path) -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if key not in _LEAKING_VARIABLES
    }
    environment[TEMP_VARIABLE] = str(user_temp)
    environment[REPORT_VARIABLE] = str(report)
    environment["PYTHONPATH"] = str(REPO_ROOT)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _ended_process_id() -> int:
    """Process id of a process that has run and ended."""
    ended = subprocess.Popen((sys.executable, "-c", _ENDED_PROCESS_SOURCE))
    ended.wait()
    return ended.pid


@contextmanager
def _running_process_id() -> Iterator[int]:
    """Process id of a process that stays alive until the context closes."""
    running = subprocess.Popen(
        (sys.executable, "-c", _RUNNING_PROCESS_SOURCE), stdin=subprocess.PIPE
    )
    try:
        yield running.pid
    finally:
        if running.stdin is not None:
            running.stdin.close()
        running.wait()


def _prepare_worktree(scratch: Path) -> tuple[Path, Path]:
    """Create a Git worktree holding stale run roots, and its outside sentinel."""
    worktree = scratch / "worktree"
    worktree.mkdir()
    subprocess.run(
        ("git", "init", "--quiet", str(worktree)), check=True, capture_output=True
    )
    (worktree / "pytest.ini").write_text("[pytest]\n")
    (worktree / "conftest.py").write_text(f'pytest_plugins = ["{PLUGIN_MODULE}"]\n')
    (worktree / CASE_MODULE.name).write_text(CASE_MODULE.read_text())
    roots = run_roots_directory(worktree)
    (roots / _STALE_DIRECTORY / Path(_STALE_NESTED).parent).mkdir(parents=True)
    (roots / _STALE_DIRECTORY / _STALE_NESTED).write_text("left by a killed run")
    (roots / _STALE_FILE).write_text("left by a killed run")
    dead_owner_root = roots / (
        run_root_prefix(_ended_process_id()) + _DEAD_OWNER_SUFFIX
    )
    dead_owner_root.mkdir()
    (dead_owner_root / _STALE_FILE).write_text("left by a killed run")
    outside = scratch / "outside"
    outside.mkdir()
    sentinel = outside / _OUTSIDE_SENTINEL
    sentinel.write_text(_OUTSIDE_TEXT)
    (roots / _STALE_LINK).symlink_to(outside, target_is_directory=True)
    neighbour = worktree / _NEIGHBOUR
    neighbour.parent.mkdir(parents=True)
    neighbour.write_text("neighbouring worktree state")
    return worktree, sentinel


def _run_scratch(
    scratch: Path,
    worktree: Path,
    report: Path,
    extra_arguments: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (
            sys.executable,
            "-m",
            "pytest",
            CASE_MODULE.name,
            "-p",
            "no:cacheprovider",
            *extra_arguments,
        ),
        cwd=worktree,
        env=_run_environment(scratch / "user-temp", report),
        capture_output=True,
        text=True,
        check=False,
    )


def _observe(scratch: Path, live_owner_pid: int | None) -> PytestRunObservation:
    user_temp = scratch / "user-temp"
    user_temp.mkdir()
    worktree, sentinel = _prepare_worktree(scratch)
    roots = run_roots_directory(worktree)
    live_root: Path | None = None
    if live_owner_pid is not None:
        live_root = roots / (run_root_prefix(live_owner_pid) + _LIVE_OWNER_SUFFIX)
        live_root.mkdir()
    report = scratch / REPORT_NAME
    before = _entries(user_temp)
    completed = _run_scratch(scratch, worktree, report, ())
    recorded = json.loads(report.read_text())
    return PytestRunObservation(
        returncode=completed.returncode,
        output=completed.stdout + completed.stderr,
        worktree=worktree.resolve(),
        user_temp_entries_before=before,
        user_temp_entries_after=_entries(user_temp),
        run_roots_after=_entries(roots) if roots.is_dir() else (),
        outside_sentinel_before=_OUTSIDE_TEXT,
        outside_sentinel_after=(sentinel.read_text() if sentinel.exists() else None),
        neighbour_exists_after=(worktree / _NEIGHBOUR).exists(),
        first_test=recorded["first_test"],
        created=recorded["created"],
        retained=recorded["retained"],
        live_root_name=live_root.name if live_root is not None else None,
        live_root_exists_after=live_root.is_dir() if live_root is not None else False,
    )


def observe_pytest_run(scratch: Path) -> PytestRunObservation:
    """Run the scratch module in a fresh scratch worktree under ``scratch``."""
    return _observe(scratch, None)


def observe_concurrent_pytest_run(scratch: Path) -> PytestRunObservation:
    """Run the scratch module while a live process owns another run root.

    The owner stays alive for the whole run, so the run starts in a worktree in
    which another run is in progress.
    """
    with _running_process_id() as owner:
        return _observe(scratch, owner)


def observe_basetemp_run(scratch: Path) -> BasetempRunObservation:
    """Run the scratch module with ``--basetemp`` naming a scratch directory."""
    (scratch / "user-temp").mkdir()
    worktree, _ = _prepare_worktree(scratch)
    basetemp = scratch / _BASETEMP_DIRECTORY
    completed = _run_scratch(
        scratch,
        worktree,
        scratch / REPORT_NAME,
        (f"{BASETEMP_OPTION}={basetemp}",),
    )
    return BasetempRunObservation(
        returncode=completed.returncode,
        output=completed.stdout + completed.stderr,
        basetemp_created=basetemp.exists(),
    )
