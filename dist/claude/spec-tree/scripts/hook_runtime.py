"""Shared helpers for spec-tree hook scripts."""

from __future__ import annotations

import os


def session_id_from(payload: dict) -> str:
    """Return the session id from hook stdin, falling back to runtime env vars."""
    value = payload.get("session_id")
    if isinstance(value, str) and value.strip():
        return value.strip()

    for name in ("CODEX_THREAD_ID", "CLAUDE_SESSION_ID"):
        env_value = os.environ.get(name)
        if env_value and env_value.strip():
            return env_value.strip()
    return ""
