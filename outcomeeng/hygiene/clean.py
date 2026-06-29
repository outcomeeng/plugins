"""On-demand removal of gitignored cache directories and artifacts.

Replaces the Justfile `clean` recipe's `find -delete` chain with `git clean
-fdX`. The semantics:

- `-f`  force (required by git when not configured otherwise)
- `-d`  recurse into untracked directories
- `-X`  remove only files ignored by git (preserving untracked-but-not-ignored
  files)
- pathspecs limit the cleanup to top-level entries outside the active Python
  environment

The module's contract:

- `CLEAN_BASE_ARGV` names the `git clean` argv that gives gitignored-only
  cleanup semantics.
- `build_clean_argv()` appends generated top-level pathspecs that omit the
  active environment when needed.
- `Runner` Protocol describes the injected subprocess boundary; `clean()`
  accepts it as a keyword argument.
- `main()` wires a real `subprocess.run` adapter.
"""

from __future__ import annotations

import subprocess
import sys
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

CLEAN_BASE_ARGV: tuple[str, ...] = ("git", "clean", "-fdX")
PATHSPEC_SEPARATOR = "--"
GIT_METADATA_DIR = ".git"
GIT_IGNORE_FILE = ".gitignore"
SUCCESS_EXIT_CODE = 0


class Runner(Protocol):
    """Invokes the underlying git command. Returns its exit code."""

    def __call__(self, argv: Sequence[str]) -> int: ...


def clean(
    *,
    runner: Runner,
    repo_root: Path | None = None,
    active_python_prefix: Path | None = None,
) -> int:
    """Run the workspace cleanup. Returns the process exit code."""
    argv = build_clean_argv(
        repo_root=repo_root if repo_root is not None else Path.cwd(),
        active_python_prefix=active_python_prefix
        if active_python_prefix is not None
        else Path(sys.prefix),
    )
    if not argv:
        return SUCCESS_EXIT_CODE
    return runner(argv)


def build_clean_argv(
    *,
    repo_root: Path,
    active_python_prefix: Path,
) -> tuple[str, ...]:
    """Build the cleanup argv without deleting the active Python environment."""
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
    """Return top-level pathspecs safe for git clean."""
    repo_root_absolute = Path(os.path.abspath(repo_root))
    active_python_prefix_absolute = Path(os.path.abspath(active_python_prefix))
    active_python_prefix_real = Path(os.path.realpath(active_python_prefix))
    preserved_names = {GIT_IGNORE_FILE, GIT_METADATA_DIR}

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

    return tuple(
        entry.name
        for entry in sorted(repo_root.iterdir(), key=lambda path: path.name)
        if entry.name not in preserved_names
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Ignores `argv` — clean takes no arguments."""
    del argv
    return clean(runner=_real_runner)


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


__all__ = [
    "CLEAN_BASE_ARGV",
    "GIT_IGNORE_FILE",
    "GIT_METADATA_DIR",
    "PATHSPEC_SEPARATOR",
    "Runner",
    "SUCCESS_EXIT_CODE",
    "build_clean_pathspecs",
    "build_clean_argv",
    "clean",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
