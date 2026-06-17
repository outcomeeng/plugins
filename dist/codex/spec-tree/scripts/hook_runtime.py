"""Shared helpers for spec-tree hook scripts.

stdlib only (python3); imported by plugin-root hook entrypoints.
"""

from __future__ import annotations

import os


def session_id_from(payload: dict) -> str:
    """Return the current hook session identity.

    Hook stdin's ``session_id`` is the portable runtime contract. Environment
    fallbacks support manual runs and runtime drift without changing the primary
    contract.
    """
    value = payload.get("session_id")
    if isinstance(value, str) and value.strip():
        return value.strip()

    for name in ("CODEX_THREAD_ID", "CLAUDE_SESSION_ID"):
        env_value = os.environ.get(name)
        if env_value and env_value.strip():
            return env_value.strip()
    return ""
