"""Recording double for the clean orchestrator.

Implements the `Runner` Protocol declared in `outcomeeng.hygiene.clean`.
The double is a spy (recording calls) and a stub (returning a scripted
exit code), used by `l1` tests to verify clean's argv contract without
invoking the real cleanup command against the test machine.

- Stage 5 #2 (Interaction protocols): clean's correctness is the argv it
  passes to `git`.
- Stage 5 #4 (Safety): the real cleanup command mutates the test machine's
  working tree.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
import os
import subprocess
import sys

from outcomeeng.hygiene.clean import (
    CLEAN_BASE_ARGV,
    GIT_IGNORE_FILE,
    LOCAL_WORK_PATHS,
    SPX_STORE_DIR,
    Runner,
)

IGNORED_CACHE_DIR = ".cache"
IGNORED_PYTHON_ENV_DIR = ".venv"
EXTERNAL_PYTHON_ENV_DIR = "external-venv"
GIT_DRY_RUN_OPTION = "--dry-run"
GIT_END_OF_OPTIONS = "--"
REMOVAL_LINE_PREFIX = "Would remove "
NESTED_WORKING_DIR = "nested"
WORKSPACE_DIR = "workspace"
LOCAL_WORK_FILE = "kept"
GIT_PATTERN_WILDCARD = "*"
GITIGNORE_ESCAPE = "\\"
RECORDING_RUNNER_FAILURE_EXIT_CODE = os.EX_OK + 1


class EnvironmentPlacement(StrEnum):
    """Where the active Python environment sits relative to the repository."""

    INSIDE = "inside"
    SYMLINKED = "symlinked"
    SYMLINK_TARGET = "symlink-target"
    OUTSIDE = "outside"
    RUNNING_INTERPRETER = "running-interpreter"


@dataclass(frozen=True)
class RunnerCall:
    """One recorded invocation: the argv and the directory it ran in."""

    argv: tuple[str, ...]
    cwd: Path


@dataclass
class RecordingRunner:
    """Runner that returns a scripted exit code and records every call.

    The default scripts success; `failing()` scripts the one non-success code
    this double returns, so a case that needs a failed run receives its code
    from the double rather than choosing one.
    """

    exit_code: int = os.EX_OK
    calls: list[RunnerCall] = field(default_factory=list)

    @classmethod
    def failing(cls) -> RecordingRunner:
        """Return a double scripted to report a failed run."""
        return cls(exit_code=RECORDING_RUNNER_FAILURE_EXIT_CODE)

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
    caches_beside_local_work: frozenset[str] = frozenset()
    pattern_named_entries: frozenset[str] = frozenset()
    files_at_holder_positions: frozenset[str] = frozenset()


def create_clean_repo(
    tmp_path: Path,
    *,
    include_cache: bool = True,
    include_local_work: bool = False,
    local_work_holders_as_files: bool = False,
    environment: EnvironmentPlacement = EnvironmentPlacement.INSIDE,
) -> CleanRepo:
    """Create a repository with ignored environment, session store, and cache.

    `environment` selects where the active Python environment sits: directly
    inside the repository, inside it as a symlink to an external directory
    (addressed by the link or by its target), wholly outside it, or inside it
    as a link to the environment of the interpreter running this process. The
    returned `active_python_prefix` is the prefix that placement hands the
    cleanup command; for the running interpreter it is that interpreter's own
    prefix, which the command resolves without being handed it.

    `include_local_work` adds every local-work path the module declares as an
    ignored directory holding one file, so a case covers each declared path
    without restating it. Beside each nested one it places an ignored cache,
    whose repository-relative path `caches_beside_local_work` reports. Beside
    each top-level one it places an ignored file whose name is a Git pattern
    matching that path, reported by `pattern_named_entries`.

    `local_work_holders_as_files` instead makes the first entry of each nested
    local-work path an ignored plain file, reported by `files_at_holder_positions`,
    so that path and its neighbours do not exist.
    """
    repo_root = tmp_path / "repo"
    ignored_cache = repo_root / IGNORED_CACHE_DIR
    session_store = repo_root / SPX_STORE_DIR
    repo_root.mkdir(parents=True)
    session_store.mkdir()
    if include_cache:
        ignored_cache.mkdir()
    active_python_prefix = _place_environment(tmp_path, repo_root, environment)
    ignore_lines = [
        f"{IGNORED_PYTHON_ENV_DIR}/",
        f"{IGNORED_CACHE_DIR}/",
        f"{SPX_STORE_DIR}/",
    ]
    caches_beside_local_work: set[str] = set()
    pattern_named_entries: set[str] = set()
    files_at_holder_positions: set[str] = set()
    if include_local_work:
        for local_path in LOCAL_WORK_PATHS:
            holder = Path(local_path).parent
            if holder.parts and local_work_holders_as_files:
                holder_file = holder.parts[0]
                (repo_root / holder_file).write_text(local_path, encoding="utf-8")
                ignore_lines.append(f"/{holder_file}")
                files_at_holder_positions.add(holder_file)
                continue
            local_dir = repo_root / local_path
            local_dir.mkdir(parents=True)
            (local_dir / LOCAL_WORK_FILE).write_text(local_path, encoding="utf-8")
            ignore_lines.append(f"/{local_path}/")
            if holder.parts:
                (repo_root / holder / IGNORED_CACHE_DIR).mkdir(exist_ok=True)
                caches_beside_local_work.add((holder / IGNORED_CACHE_DIR).as_posix())
            else:
                pattern_name = f"{local_path[:-1]}{GIT_PATTERN_WILDCARD}"
                (repo_root / pattern_name).write_text(local_path, encoding="utf-8")
                escaped = pattern_name.replace(
                    GIT_PATTERN_WILDCARD, f"{GITIGNORE_ESCAPE}{GIT_PATTERN_WILDCARD}"
                )
                ignore_lines.append(f"/{escaped}")
                pattern_named_entries.add(pattern_name)
    (repo_root / GIT_IGNORE_FILE).write_text(
        "".join(f"{line}\n" for line in ignore_lines),
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
        caches_beside_local_work=frozenset(caches_beside_local_work),
        pattern_named_entries=frozenset(pattern_named_entries),
        files_at_holder_positions=frozenset(files_at_holder_positions),
    )


def create_directory_without_repository(tmp_path: Path) -> Path:
    """Create a directory with no repository metadata in it or up to `tmp_path`.

    `tmp_path` is the search ceiling a linked test hands root resolution, so
    the host's own directories above it never take part.
    """
    directory = tmp_path / WORKSPACE_DIR / NESTED_WORKING_DIR
    directory.mkdir(parents=True)
    return directory


@contextmanager
def working_directory_below_root(repo: CleanRepo) -> Iterator[Path]:
    """Run the enclosed block from a directory nested below the repository root.

    The directory sits inside the ignored cache, so the repository's top-level
    entries stay as arranged. The previous working directory is restored on
    every exit path.
    """
    nested = repo.ignored_cache / NESTED_WORKING_DIR
    nested.mkdir()
    previous = Path.cwd()
    os.chdir(nested)
    try:
        yield nested
    finally:
        os.chdir(previous)


def observe_dry_run_removals(
    *,
    repo: CleanRepo,
    argv: Sequence[str],
) -> frozenset[str]:
    """Return the repository-relative paths Git reports it would remove for `argv`.

    Inserts Git's dry-run option directly after the base command the module
    composed, so the dry run exercises the exact flags the module emits, then
    runs it against the arranged repository and reports each listed path with
    its trailing separator stripped. The linked test owns the comparison
    against the paths it expects.
    """
    base_length = len(CLEAN_BASE_ARGV)
    dry_run_argv = (*argv[:base_length], GIT_DRY_RUN_OPTION, *argv[base_length:])
    result = subprocess.run(
        dry_run_argv,
        cwd=repo.root,
        check=True,
        capture_output=True,
        text=True,
    )
    return frozenset(
        line.removeprefix(REMOVAL_LINE_PREFIX).rstrip("/")
        for line in result.stdout.splitlines()
        if line.startswith(REMOVAL_LINE_PREFIX)
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
    if environment is EnvironmentPlacement.RUNNING_INTERPRETER:
        running_prefix = Path(sys.prefix)
        in_repo_prefix.symlink_to(running_prefix, target_is_directory=True)
        return running_prefix
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
    "GIT_DRY_RUN_OPTION",
    "GIT_END_OF_OPTIONS",
    "IGNORED_CACHE_DIR",
    "IGNORED_PYTHON_ENV_DIR",
    "RecordingRunner",
    "RunnerCall",
    "create_clean_repo",
    "create_directory_without_repository",
    "observe_dry_run_removals",
    "working_directory_below_root",
]


_: type[Runner] = RecordingRunner
