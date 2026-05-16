"""On-demand removal of gitignored cache directories and artifacts.

Replaces the Justfile `clean` recipe's `find -delete` chain with `git clean
-fdX`. The new semantics:

- `-f`  force (required by git when not configured otherwise)
- `-d`  recurse into untracked directories
- `-X`  remove only files ignored by git (preserving untracked-but-not-ignored
  files)

The module's contract:

- `CLEAN_ARGV` names the exact `git` argv invoked by the recipe.
- `Runner` Protocol describes the injected subprocess boundary; `clean()`
  accepts it as a keyword argument.
- `main()` wires a real `subprocess.run` adapter.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from typing import Protocol

CLEAN_ARGV: tuple[str, ...] = ("git", "clean", "-fdX")


class Runner(Protocol):
    """Invokes the underlying git command. Returns its exit code."""

    def __call__(self, argv: Sequence[str]) -> int: ...


def clean(*, runner: Runner) -> int:
    """Run the workspace cleanup. Returns the process exit code."""
    return runner(CLEAN_ARGV)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Ignores `argv` — clean takes no arguments."""
    del argv
    return clean(runner=_real_runner)


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


__all__ = ["CLEAN_ARGV", "Runner", "clean", "main"]


if __name__ == "__main__":
    sys.exit(main())
