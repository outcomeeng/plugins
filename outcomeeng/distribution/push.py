"""Marketplace publish orchestration.

Pushes the current branch to its remote and refreshes the local marketplace
install via `outcomeeng.distribution.sync` when the pushed range changed
plugin distribution paths. Replaces the `just push-marketplace` heredoc
with an injectable, observable orchestration.

The module's contract:

- `REQUIRED_TOOLS` names the external binaries the orchestration shells out to.
- `StepRunner`, `ToolProbe`, and `UpstreamProbe` Protocols describe the
  injected side-effecting boundaries; `push()` accepts them as keyword
  arguments.
- `push()` captures the upstream ref, runs `git push`, then invokes
  `outcomeeng.distribution.sync` with the captured ref as `base_ref` (or
  with no argument when the branch has no upstream).
- `main()` wires real subprocess, `shutil.which`, and `git rev-parse`
  adapters.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from typing import Protocol

REQUIRED_TOOLS: tuple[str, ...] = ("git", "claude", "codex", "ps", "uv")


class StepRunner(Protocol):
    """Invokes one orchestration step. Returns the step's exit code."""

    def __call__(self, argv: Sequence[str]) -> int: ...


class ToolProbe(Protocol):
    """Returns True when `name` resolves to an executable on PATH."""

    def __call__(self, name: str) -> bool: ...


class UpstreamProbe(Protocol):
    """Returns the upstream ref of the current branch, or None when unset."""

    def __call__(self) -> str | None: ...


def push(
    push_args: Sequence[str],
    *,
    runner: StepRunner,
    tool_probe: ToolProbe,
    upstream_probe: UpstreamProbe,
) -> int:
    """Run the publish-and-sync orchestration. Returns the process exit code."""
    for tool in REQUIRED_TOOLS:
        if not tool_probe(tool):
            print(f"Missing required tool: {tool}", file=sys.stderr)
            return 1
    before_ref = upstream_probe()
    push_rc = runner(("git", "push", *push_args))
    if push_rc != 0:
        return push_rc
    sync_argv: tuple[str, ...] = (
        "uv",
        "run",
        "python",
        "-m",
        "outcomeeng.distribution.sync",
    )
    if before_ref:
        sync_argv = (*sync_argv, before_ref)
    return runner(sync_argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Forwards positional args to `git push` and runs `push`."""
    args = _build_parser().parse_args(argv)
    return push(
        args.push_args,
        runner=_real_runner,
        tool_probe=_real_tool_probe,
        upstream_probe=_real_upstream_probe,
    )


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


def _real_tool_probe(name: str) -> bool:
    return shutil.which(name) is not None


def _real_upstream_probe() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "@{upstream}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    ref = result.stdout.strip()
    return ref or None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outcomeeng.distribution.push",
        description=(
            "Push the current branch and refresh the local marketplace install "
            "when plugin distribution paths changed in the pushed range."
        ),
    )
    parser.add_argument(
        "push_args",
        nargs="*",
        help="Positional arguments forwarded to `git push`.",
    )
    return parser


__all__ = [
    "REQUIRED_TOOLS",
    "StepRunner",
    "ToolProbe",
    "UpstreamProbe",
    "main",
    "push",
]


if __name__ == "__main__":
    sys.exit(main())
