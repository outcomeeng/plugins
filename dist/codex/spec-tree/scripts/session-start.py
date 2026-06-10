#!/usr/bin/env python3
"""SessionStart hook: persist session-scoped Claude Code metadata.

Reads a JSON payload on stdin and appends shell `export` lines to the file named
by $CLAUDE_ENV_FILE so every subsequent Bash tool call in this conversation can
read the values:

  CLAUDE_SESSION_ID   Claude Code session id. spec-tree scopes handoff
                      accumulation under .spx/sessions/$CLAUDE_SESSION_ID/.
  CLAUDE_PROJECT_DIR  Claude Code product root, exposed to Bash tool calls.
  PROJECT_DIR         Short alias for CLAUDE_PROJECT_DIR.

The per-runtime .spx/sessions/$CLAUDE_SESSION_ID directory is still created
lazily by `spx session pickup` on first successful claim — not here, so that
conversations which never claim a session leave no empty directories.

stdlib only (python3); no third-party packages.
"""

import json
import os
import re
import shlex
import sys

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def warn(message: str) -> None:
    # Do not write to stdout from a SessionStart hook: stdout is injected into
    # Claude's context. Use stderr for diagnostics.
    print(f"session-start: {message}", file=sys.stderr)


def export_line(name: str, value: str) -> str:
    if not _ENV_NAME.match(name):
        raise ValueError(f"invalid environment variable name: {name}")
    # shlex.quote emits a shell-safe representation for an env-file preamble.
    return f"export {name}={shlex.quote(value)}"


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        warn("invalid JSON on stdin; not exporting")
        return 0

    session_id = (payload.get("session_id") or "").strip()
    if not session_id:
        warn("missing or invalid .session_id; not exporting CLAUDE_SESSION_ID")
        return 0

    # Prefer Claude Code's project-root variable; fall back to .cwd defensively.
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ""
    if not os.environ.get("CLAUDE_PROJECT_DIR") and project_dir:
        warn(
            "CLAUDE_PROJECT_DIR unset; falling back to .cwd, which may not be the product root"
        )

    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        # Expected when run manually; avoid noisy failures.
        return 0

    lines = [
        "",
        "# Managed by plugins/spec-tree/scripts/session-start.py",
        export_line("CLAUDE_SESSION_ID", session_id),
    ]
    if project_dir:
        lines.append(export_line("CLAUDE_PROJECT_DIR", project_dir))
        lines.append(export_line("PROJECT_DIR", project_dir))
    else:
        warn(
            "product directory unavailable; not exporting CLAUDE_PROJECT_DIR or PROJECT_DIR"
        )

    with open(env_file, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
