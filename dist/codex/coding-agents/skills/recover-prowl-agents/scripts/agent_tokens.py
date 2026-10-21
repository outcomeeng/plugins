"""The coding-agents agent tokens, declared once."""

from __future__ import annotations

from enum import StrEnum


class AgentToken(StrEnum):
    """One token per coding agent the marketplace names."""

    CLAUDE = "claude"
    CODEX = "codex"
    PI = "pi"
