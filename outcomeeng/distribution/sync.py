"""Marketplace sync orchestration.

Refreshes the local Claude marketplace and re-validates installed plugins
when plugin distribution paths changed since a reference commit. Replaces
the `just sync-marketplace` heredoc with an injectable, observable
orchestration that tests verify through recording doubles.

The module's contract:

- `REQUIRED_TOOLS` names the external binaries the orchestration shells out to.
- `DISTRIBUTION_PATHS` names the repository paths whose change drives a sync.
- `STEPS` is the ordered tuple of named subprocess calls executed when a sync runs.
- `StepRunner`, `ToolProbe`, and `ChangeProbe` Protocols describe the injected
  side-effecting boundaries; `sync()` accepts them as keyword arguments.
- `main()` wires real subprocess, `shutil.which`, and `git diff` adapters.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

REQUIRED_TOOLS: tuple[str, ...] = ("claude", "codex", "uv")

DISTRIBUTION_PATHS: tuple[str, ...] = ("plugins", ".claude-plugin", ".agents/plugins")


@dataclass(frozen=True)
class SyncStep:
    """A named orchestration step with its argv tuple."""

    name: str
    argv: tuple[str, ...]


STEPS: tuple[SyncStep, ...] = (
    SyncStep(
        name="claude_marketplace_update",
        argv=("claude", "plugin", "marketplace", "update", "outcomeeng"),
    ),
    SyncStep(
        name="codex_cache_preserve",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.distribution.codex_cache",
            "outcomeeng",
        ),
    ),
    SyncStep(
        name="install_validate",
        argv=("uv", "run", "python", "-m", "outcomeeng.validation.install"),
    ),
    SyncStep(
        name="installed_check",
        argv=("just", "check-installed"),
    ),
)


class StepRunner(Protocol):
    """Invokes one orchestration step. Returns the step's exit code."""

    def __call__(self, argv: Sequence[str]) -> int: ...


class ToolProbe(Protocol):
    """Returns True when `name` resolves to an executable on PATH."""

    def __call__(self, name: str) -> bool: ...


class ChangeProbe(Protocol):
    """Returns True when distribution paths changed since `base_ref`.

    When `base_ref` is None or empty, no diff baseline exists and the probe
    is not consulted; orchestration proceeds unconditionally.
    """

    def __call__(self, base_ref: str) -> bool: ...


def sync(
    base_ref: str | None,
    *,
    runner: StepRunner,
    tool_probe: ToolProbe,
    change_probe: ChangeProbe,
) -> int:
    """Run the marketplace sync orchestration. Returns the process exit code."""
    for tool in REQUIRED_TOOLS:
        if not tool_probe(tool):
            print(f"Missing required tool: {tool}", file=sys.stderr)
            return 1
    if base_ref and not change_probe(base_ref):
        print(
            f"No plugin distribution changes since {base_ref}; "
            "skipping marketplace sync",
        )
        return 0
    for step in STEPS:
        rc = runner(step.argv)
        if rc != 0:
            return rc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Parses `base_ref` and runs `sync` with real adapters."""
    args = _build_parser().parse_args(argv)
    return sync(
        args.base_ref or None,
        runner=_real_runner,
        tool_probe=_real_tool_probe,
        change_probe=_real_change_probe,
    )


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


def _real_tool_probe(name: str) -> bool:
    return shutil.which(name) is not None


def _real_change_probe(base_ref: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            base_ref,
            "HEAD",
            "--",
            *DISTRIBUTION_PATHS,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(result.stdout.strip())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outcomeeng.distribution.sync",
        description=(
            "Refresh local marketplace installs and re-validate installed plugins "
            "when plugin distribution paths changed since base_ref."
        ),
    )
    parser.add_argument(
        "base_ref",
        nargs="?",
        default="",
        help=(
            "Optional git ref to compare against HEAD. "
            "When omitted, all sync steps run unconditionally."
        ),
    )
    return parser


__all__ = [
    "DISTRIBUTION_PATHS",
    "REQUIRED_TOOLS",
    "STEPS",
    "ChangeProbe",
    "StepRunner",
    "SyncStep",
    "ToolProbe",
    "main",
    "sync",
]


if __name__ == "__main__":
    sys.exit(main())
