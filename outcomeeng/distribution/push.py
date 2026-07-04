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

import shutil
import subprocess
import sys
from collections.abc import Sequence
from typing import Protocol

REQUIRED_TOOLS: tuple[str, ...] = ("git", "claude", "codex", "ps", "uv")
UPSTREAM_REF_COMMAND: tuple[str, ...] = ("git", "rev-parse", "@{upstream}")
DRY_RUN_PUSH_FLAGS: frozenset[str] = frozenset(("-n", "--dry-run"))
HELP_PUSH_FLAGS: frozenset[str] = frozenset(("-h", "--help"))
NO_DRY_RUN_PUSH_FLAG = "--no-dry-run"
PUSH_OPTION_FLAGS: frozenset[str] = frozenset(("-o", "--push-option"))
VALUE_TAKING_PUSH_FLAGS: frozenset[str] = frozenset(
    (
        "--exec",
        "--receive-pack",
        "--recurse-submodules",
        "--repo",
        *PUSH_OPTION_FLAGS,
    )
)
SYNC_COMMAND: tuple[str, ...] = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.distribution.sync",
)


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
    if _is_help_request(push_args):
        return runner(("git", "push", *push_args))
    for tool in REQUIRED_TOOLS:
        if not tool_probe(tool):
            print(f"Missing required tool: {tool}", file=sys.stderr)
            return 1
    before_ref = upstream_probe()
    push_rc = runner(("git", "push", *push_args))
    if push_rc != 0:
        return push_rc
    if _is_dry_run(push_args):
        return 0
    sync_argv: tuple[str, ...] = SYNC_COMMAND
    if before_ref:
        sync_argv = (*sync_argv, before_ref)
    return runner(sync_argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Forwards positional args to `git push` and runs `push`."""
    return push(
        parse_push_args(argv),
        runner=_real_runner,
        tool_probe=_real_tool_probe,
        upstream_probe=_real_upstream_probe,
    )


def parse_push_args(argv: Sequence[str] | None = None) -> tuple[str, ...]:
    """Return caller arguments exactly as `git push` should receive them."""
    return tuple(sys.argv[1:] if argv is None else argv)


def _is_dry_run(push_args: Sequence[str]) -> bool:
    is_dry_run = False
    skip_next = False
    for arg in push_args:
        if skip_next:
            skip_next = False
            continue
        if arg == "--":
            break
        if arg == NO_DRY_RUN_PUSH_FLAG:
            is_dry_run = False
        elif arg in VALUE_TAKING_PUSH_FLAGS:
            skip_next = True
        elif _has_inline_value(arg, VALUE_TAKING_PUSH_FLAGS):
            continue
        elif arg.startswith("-o") and arg != "-o":
            continue
        elif _is_dry_run_arg(arg):
            is_dry_run = True
    return is_dry_run


def _is_help_request(push_args: Sequence[str]) -> bool:
    skip_next = False
    for arg in push_args:
        if skip_next:
            skip_next = False
            continue
        if arg == "--":
            break
        if arg in VALUE_TAKING_PUSH_FLAGS:
            skip_next = True
        elif _has_inline_value(arg, VALUE_TAKING_PUSH_FLAGS):
            continue
        elif arg.startswith("-o") and arg != "-o":
            continue
        elif arg in HELP_PUSH_FLAGS:
            return True
    return False


def _is_dry_run_arg(arg: str) -> bool:
    if arg == "--dry-run":
        return True
    if arg.startswith("--"):
        return False
    return arg.startswith("-") and "n" in arg[1:]


def _has_inline_value(arg: str, value_taking_flags: frozenset[str]) -> bool:
    return any(
        arg.startswith(f"{flag}=")
        for flag in value_taking_flags
        if flag.startswith("--")
    )


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


def _real_tool_probe(name: str) -> bool:
    return shutil.which(name) is not None


def _real_upstream_probe() -> str | None:
    result = subprocess.run(
        list(UPSTREAM_REF_COMMAND),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    ref = result.stdout.strip()
    return ref or None


__all__ = [
    "DRY_RUN_PUSH_FLAGS",
    "HELP_PUSH_FLAGS",
    "REQUIRED_TOOLS",
    "SYNC_COMMAND",
    "StepRunner",
    "ToolProbe",
    "UPSTREAM_REF_COMMAND",
    "UpstreamProbe",
    "main",
    "parse_push_args",
    "push",
]


if __name__ == "__main__":
    sys.exit(main())
