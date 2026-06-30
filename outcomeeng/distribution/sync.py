"""Marketplace sync orchestration.

Reconciles local runtime marketplace configuration, refreshes the local Claude
marketplace, and re-validates installed plugins when plugin distribution paths
changed since a reference commit or configuration repair changed runtime state.

The module's contract:

- `REQUIRED_TOOLS` names the external binaries the orchestration shells out to.
- `DISTRIBUTION_PATHS` names the repository paths whose change drives a sync.
- `STEPS` is the ordered tuple of named subprocess calls executed when a refresh runs.
- `StepRunner`, `ToolProbe`, `ChangeProbe`, and `ConfigRepairer` Protocols describe
  the injected side-effecting boundaries; `sync()` accepts them as keyword arguments.
- `main()` wires real subprocess, `shutil.which`, and `git diff` adapters.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from outcomeeng.distribution.marketplace_sources import (
    DEFAULT_MARKETPLACE,
    MarketplaceSourceError,
    ensure_local_marketplace_sources,
)

REQUIRED_TOOLS: tuple[str, ...] = ("claude", "codex", "uv")

DISTRIBUTION_PATHS: tuple[str, ...] = (
    "src",
    "dist",
    ".claude-plugin",
    ".agents/plugins",
)


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
        name="codex_local_refresh",
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
        name="codex_agent_install",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.distribution.agents",
            "install",
        ),
    ),
    SyncStep(
        name="install_validate",
        argv=("uv", "run", "python", "-m", "outcomeeng.validation.install"),
    ),
    SyncStep(
        name="codex_local_refresh_final",
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


class ConfigRepairer(Protocol):
    """Reconciles runtime marketplace source config; returns True if changed."""

    def __call__(self) -> bool: ...


def sync(
    base_ref: str | None,
    *,
    runner: StepRunner | None = None,
    tool_probe: ToolProbe | None = None,
    change_probe: ChangeProbe | None = None,
    config_repairer: ConfigRepairer | None = None,
) -> int:
    """Run the marketplace sync orchestration. Returns the process exit code."""
    runner = runner or _real_runner
    tool_probe = tool_probe or _real_tool_probe
    change_probe = change_probe or _real_change_probe
    config_repairer = config_repairer or _real_config_repairer
    for tool in REQUIRED_TOOLS:
        if not tool_probe(tool):
            print(f"Missing required tool: {tool}", file=sys.stderr)
            return 1
    try:
        config_changed = config_repairer()
    except MarketplaceSourceError as exc:
        print(f"Marketplace source configuration failed: {exc}", file=sys.stderr)
        return 1
    if base_ref and not change_probe(base_ref) and not config_changed:
        print(
            f"No plugin distribution changes since {base_ref}; "
            "runtime marketplace sources already configured; "
            "skipping marketplace refresh",
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
        config_repairer=_real_config_repairer,
    )


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


def _real_tool_probe(name: str) -> bool:
    return shutil.which(name) is not None


def _real_change_probe(base_ref: str) -> bool:
    tracked_result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            base_ref,
            "--",
            *DISTRIBUTION_PATHS,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    if tracked_result.stdout.strip():
        return True
    untracked_result = subprocess.run(
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            *DISTRIBUTION_PATHS,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(untracked_result.stdout.strip())


def _real_config_repairer() -> bool:
    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=_real_source_root(),
    )
    return result.changed


def _real_source_root() -> Path:
    default_branch = _real_default_branch_name()
    if default_branch is not None:
        worktree_root = _real_worktree_root_for_branch(default_branch)
        if worktree_root is not None:
            return worktree_root
    return _real_git_toplevel()


def _real_default_branch_name() -> str | None:
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return "main"
    ref = result.stdout.strip()
    if not ref:
        return "main"
    return ref.rsplit("/", maxsplit=1)[-1]


def _real_worktree_root_for_branch(branch: str) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return _worktree_path_for_branch(result.stdout, branch)


def _worktree_path_for_branch(porcelain: str, branch: str) -> Path | None:
    current_path: Path | None = None
    branch_ref = f"branch refs/heads/{branch}"
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line.removeprefix("worktree "))
            continue
        if line == branch_ref and current_path is not None:
            return current_path
        if not line:
            current_path = None
    return None


def _real_git_toplevel() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return Path.cwd()
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return Path.cwd()


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
            "Optional git ref to compare against the working tree. "
            "When omitted, all sync steps run unconditionally."
        ),
    )
    return parser


__all__ = [
    "DISTRIBUTION_PATHS",
    "REQUIRED_TOOLS",
    "STEPS",
    "ChangeProbe",
    "ConfigRepairer",
    "StepRunner",
    "SyncStep",
    "ToolProbe",
    "main",
    "sync",
]


if __name__ == "__main__":
    sys.exit(main())
