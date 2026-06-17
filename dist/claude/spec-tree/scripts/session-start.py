#!/usr/bin/env python3
"""SessionStart hook: export the agent session identity into the harness env file.

Reads the SessionStart JSON payload on stdin and writes `CLAUDE_SESSION_ID` to the
harness-provided `$CLAUDE_ENV_FILE`, so every later Bash tool call in the session
reads one stable identity. This is the spec-tree plugin's only hook: it captures
session identity and does nothing else — no directives, no git inspection, no
`.spx/` access, no subprocess.

stdlib only (python3); no third-party packages.
"""

import json
import os
import shlex
import sys


def session_id_from(payload: dict) -> str:
    """Return the session id from the hook payload, falling back to runtime env vars."""
    value = payload.get("session_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    for name in ("CODEX_THREAD_ID", "CLAUDE_SESSION_ID"):
        env_value = os.environ.get(name)
        if env_value and env_value.strip():
            return env_value.strip()
    return ""


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    session_id = session_id_from(payload)
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not session_id or not env_file:
        return 0

    # Degrade rather than crash: an unwritable or missing-parent env-file path
    # raises OSError, and a non-zero hook exit would surface as a harness hook
    # failure. Identity capture is best-effort, so a write failure is a no-op.
    try:
        with open(env_file, "a", encoding="utf-8") as handle:
            handle.write(f"export CLAUDE_SESSION_ID={shlex.quote(session_id)}\n")
    except OSError:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
