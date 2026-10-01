"""On-demand removal of gitignored cache directories and artifacts.

Replaces the Justfile `clean` recipe's `find -delete` chain with `git
--literal-pathspecs clean -fdX`. The semantics:

- `--literal-pathspecs`  read every pathspec as one path, never as a pattern
- `-f`  force (required by git when not configured otherwise)
- `-d`  recurse into untracked directories
- `-X`  remove only files ignored by git (preserving untracked-but-not-ignored
  files)
- pathspecs limit the cleanup to top-level entries outside the protected set:
  the repository metadata and ignore file, the session store, the local-work
  paths, and the active Python environment; an entry holding a nested
  local-work path is replaced by its other children, level by level

The module's contract:

- `CLEAN_BASE_ARGV` names the `git` argv that gives literal, gitignored-only
  cleanup semantics.
- `build_clean_argv()` appends the pathspecs `build_clean_pathspecs()`
  generates, which omit every protected path and every directory holding a
  nested one.
- `Runner` Protocol describes the injected subprocess boundary; `clean()`
  accepts it as a keyword argument and hands it the repository root the
  pathspecs were computed for, so the command runs in that tree rather than
  in whatever directory the calling process happens to sit in.
- `find_repository_root()` supplies that root when the caller names none:
  the nearest directory at or above the working directory holding Git
  metadata.
- `main()` wires a real `subprocess.run` adapter.
"""

from __future__ import annotations

import subprocess
import sys
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

CLEAN_BASE_ARGV: tuple[str, ...] = ("git", "--literal-pathspecs", "clean", "-fdX")
PATHSPEC_SEPARATOR = "--"
GIT_METADATA_DIR = ".git"
GIT_IGNORE_FILE = ".gitignore"
SPX_STORE_DIR = ".spx"
LOCAL_WORK_PATHS: tuple[str, ...] = (
    ".claude",
    ".codex",
    ".agents",
    ".mcp.json",
    ".env",
    "methodology/memories",
)


class Runner(Protocol):
    """Invokes the underlying git command from `cwd`. Returns its exit code."""

    def __call__(self, argv: Sequence[str], *, cwd: Path) -> int: ...


def clean(
    *,
    runner: Runner,
    repo_root: Path | None = None,
    active_python_prefix: Path | None = None,
) -> int:
    """Run the workspace cleanup. Returns the process exit code."""
    root = repo_root if repo_root is not None else find_repository_root(Path.cwd())
    argv = build_clean_argv(
        repo_root=root,
        active_python_prefix=active_python_prefix
        if active_python_prefix is not None
        else Path(sys.prefix),
    )
    if not argv:
        return os.EX_OK
    return runner(argv, cwd=root)


def find_repository_root(start: Path, *, ceiling: Path | None = None) -> Path:
    """Return the nearest directory at or above `start` holding Git metadata.

    A linked worktree carries its metadata as a file, so any entry of that name
    marks a root. The search climbs no higher than `ceiling`, the filesystem
    root when none is named. When no directory up to it holds metadata, `start`
    is returned and Git reports the missing repository through the command's
    own exit code.
    """
    for directory in (start, *start.parents):
        if (directory / GIT_METADATA_DIR).exists():
            return directory
        if directory == ceiling:
            break
    return start


def build_clean_argv(
    *,
    repo_root: Path,
    active_python_prefix: Path,
) -> tuple[str, ...]:
    """Build the cleanup argv that spares every protected path.

    The protected set is the repository metadata and ignore file, the session
    store, the local-work paths, and the active environment. Returns an empty
    argv when no pathspec remains, so the bare base command never runs.
    """
    pathspecs = build_clean_pathspecs(
        repo_root=repo_root,
        active_python_prefix=active_python_prefix,
    )
    if not pathspecs:
        return ()
    return (*CLEAN_BASE_ARGV, PATHSPEC_SEPARATOR, *pathspecs)


def build_clean_pathspecs(
    *,
    repo_root: Path,
    active_python_prefix: Path,
) -> tuple[str, ...]:
    """Return pathspecs safe for git clean.

    Every top-level entry outside the protected set is a pathspec, except one
    that contains a nested local-work path: its other children stand in its
    place, level by level, so no pathspec names the protected path or a
    directory that holds it.
    """
    repo_root_absolute = Path(os.path.abspath(repo_root))
    active_python_prefix_absolute = Path(os.path.abspath(active_python_prefix))
    active_python_prefix_real = Path(os.path.realpath(active_python_prefix))
    local_work = [Path(path) for path in LOCAL_WORK_PATHS]
    nested_local_work = frozenset(path for path in local_work if len(path.parts) > 1)
    preserved_names = {
        GIT_IGNORE_FILE,
        GIT_METADATA_DIR,
        SPX_STORE_DIR,
        *(path.name for path in local_work if len(path.parts) == 1),
    }

    try:
        relative_active_prefix = active_python_prefix_absolute.relative_to(
            repo_root_absolute,
        )
    except ValueError:
        relative_active_prefix = None

    if relative_active_prefix is not None and relative_active_prefix.parts:
        preserved_names.add(relative_active_prefix.parts[0])

    for entry in repo_root.iterdir():
        if Path(os.path.realpath(entry)) == active_python_prefix_real:
            preserved_names.add(entry.name)

    return _pathspecs_below(
        repo_root,
        Path(),
        excluded=frozenset(Path(name) for name in preserved_names) | nested_local_work,
        holders=frozenset(
            parent
            for path in nested_local_work
            for parent in path.parents
            if parent.parts
        ),
    )


def _pathspecs_below(
    directory: Path,
    relative: Path,
    *,
    excluded: frozenset[Path],
    holders: frozenset[Path],
) -> tuple[str, ...]:
    pathspecs: list[str] = []
    for entry in sorted(directory.iterdir(), key=lambda path: path.name):
        entry_relative = relative / entry.name
        if entry_relative in excluded:
            continue
        if entry_relative in holders and entry.is_dir():
            pathspecs.extend(
                _pathspecs_below(
                    entry, entry_relative, excluded=excluded, holders=holders
                )
            )
            continue
        pathspecs.append(entry_relative.as_posix())
    return tuple(pathspecs)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Ignores `argv` — clean takes no arguments."""
    del argv
    return clean(runner=_real_runner)


def _real_runner(argv: Sequence[str], *, cwd: Path) -> int:
    return subprocess.run(list(argv), cwd=cwd, check=False).returncode


__all__ = [
    "CLEAN_BASE_ARGV",
    "GIT_IGNORE_FILE",
    "GIT_METADATA_DIR",
    "LOCAL_WORK_PATHS",
    "SPX_STORE_DIR",
    "PATHSPEC_SEPARATOR",
    "Runner",
    "build_clean_pathspecs",
    "build_clean_argv",
    "clean",
    "find_repository_root",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
