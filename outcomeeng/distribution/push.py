"""Forward marketplace publication arguments directly to ``git push``."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from typing import Protocol

GIT_TOOL = "git"
GIT_PUSH_COMMAND: tuple[str, ...] = (GIT_TOOL, "push")


class StepRunner(Protocol):
    """Invoke one command and return its exit code."""

    def __call__(self, argv: Sequence[str]) -> int: ...


class ToolProbe(Protocol):
    """Report whether one executable is available on PATH."""

    def __call__(self, name: str) -> bool: ...


def push(
    push_args: Sequence[str],
    *,
    runner: StepRunner,
    tool_probe: ToolProbe,
) -> int:
    """Forward every caller argument to ``git push`` after probing git."""
    if not tool_probe(GIT_TOOL):
        print(f"Missing required tool: {GIT_TOOL}", file=sys.stderr)
        return 1
    return runner((*GIT_PUSH_COMMAND, *push_args))


def parse_push_args(argv: Sequence[str] | None = None) -> tuple[str, ...]:
    """Return caller arguments exactly as ``git push`` should receive them."""
    return tuple(sys.argv[1:] if argv is None else argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for direct marketplace publication."""
    return push(
        parse_push_args(argv),
        runner=_real_runner,
        tool_probe=_real_tool_probe,
    )


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(tuple(argv), check=False).returncode


def _real_tool_probe(name: str) -> bool:
    return shutil.which(name) is not None


__all__ = [
    "GIT_PUSH_COMMAND",
    "GIT_TOOL",
    "StepRunner",
    "ToolProbe",
    "main",
    "parse_push_args",
    "push",
]


if __name__ == "__main__":
    sys.exit(main())
