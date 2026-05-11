"""Concrete adapter constructors wired into Click command handlers.

Command handlers under ``outcomeeng_evals.cli.commands`` import these to
build concrete ``ClaudeCliRunner`` instances and other adapters. Keeping
construction out of the command modules makes the wiring point a single
file to scan when a CLI flag or environment variable changes its meaning.
"""

from __future__ import annotations

import os
from pathlib import Path

from outcomeeng_evals.runner import ClaudeCliRunner


CLAUDE_BIN_ENV = "CLAUDE_BIN"
DEFAULT_CLAUDE_BIN = "claude"


def build_claude_runner(
    *,
    plugin_dir: Path,
    max_budget_usd: float | None = 0.50,
    timeout_seconds: float = 120.0,
) -> ClaudeCliRunner:
    """Build a ``ClaudeCliRunner`` with the binary from the environment."""
    return ClaudeCliRunner(
        plugin_dir=plugin_dir,
        binary=os.environ.get(CLAUDE_BIN_ENV, DEFAULT_CLAUDE_BIN),
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
    )
