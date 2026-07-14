"""Concrete adapter constructors wired into Click command handlers.

Command handlers under ``outcomeeng_evals.cli.commands`` import these to
build concrete ``ClaudeCliRunner`` instances and other adapters. Keeping
construction out of the command modules makes the wiring point a single
file to scan when a CLI flag or environment variable changes its meaning.
"""

from __future__ import annotations

import os
from pathlib import Path

from outcomeeng_evals.definition import DEFAULT_MODEL
from outcomeeng_evals.runner import ClaudeCliRunner
from outcomeeng_evals.settings import DEFAULT_MAX_BUDGET_USD, DEFAULT_TIMEOUT_SECONDS


CLAUDE_BIN_ENV = "CLAUDE_BIN"
DEFAULT_CLAUDE_BIN = "claude"


def build_claude_runner(
    *,
    plugin_dir: Path,
    model: str = DEFAULT_MODEL,
    max_budget_usd: float | None = DEFAULT_MAX_BUDGET_USD,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> ClaudeCliRunner:
    """Build a ``ClaudeCliRunner`` with the binary from the environment."""
    return ClaudeCliRunner(
        plugin_dir=plugin_dir,
        model=model,
        binary=os.environ.get(CLAUDE_BIN_ENV, DEFAULT_CLAUDE_BIN),
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
    )
