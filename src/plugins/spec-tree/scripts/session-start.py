#!/usr/bin/env python3
"""SessionStart hook: persist session metadata and surface a stale base.

Two outputs, on two channels:

1. The harness env file ($CLAUDE_ENV_FILE) receives shell `export` lines so every
   subsequent Bash tool call in this conversation can read the values:

     CLAUDE_SESSION_ID   Claude Code session id. spec-tree scopes handoff
                         accumulation under .spx/sessions/$CLAUDE_SESSION_ID/.
     CLAUDE_PROJECT_DIR  Claude Code product root, exposed to Bash tool calls.
     PROJECT_DIR         Short alias for CLAUDE_PROJECT_DIR.

2. Stdout (injected into Claude's context) carries a base-staleness directive
   when the worktree's HEAD trails its resolved default branch, so the agent
   rebases onto a current base before building on a stale one. The check is
   read-only — it resolves the default from `origin/HEAD` and counts commits with
   `git rev-list`; it never fetches or mutates git state, and stays silent (no
   stdout) when the worktree is current, is not a git repository, or has no
   resolvable default. Diagnostics still go to stderr, never stdout.

The per-runtime .spx/sessions/$CLAUDE_SESSION_ID directory is created lazily by
`spx session pickup` on first successful claim — not here, so conversations that
never claim a session leave no empty directories.

stdlib only (python3); no third-party packages.
"""

import json
import os
import re
import shlex
import subprocess
import sys

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TRACKING_PREFIX = "refs/remotes/"


def warn(message: str) -> None:
    # Do not write diagnostics to stdout from a SessionStart hook: stdout is
    # injected into Claude's context. Use stderr for diagnostics.
    print(f"session-start: {message}", file=sys.stderr)


def export_line(name: str, value: str) -> str:
    if not _ENV_NAME.match(name):
        raise ValueError(f"invalid environment variable name: {name}")
    # shlex.quote emits a shell-safe representation for an env-file preamble.
    return f"export {name}={shlex.quote(value)}"


def write_env_file(payload: dict, project_dir: str) -> None:
    """Append the session export lines to $CLAUDE_ENV_FILE.

    No-ops (with a stderr diagnostic) when the session id or env file is absent,
    so a missing field never aborts the base-staleness directive that follows.
    """
    session_id = (payload.get("session_id") or "").strip()
    if not session_id:
        warn("missing or invalid .session_id; not exporting CLAUDE_SESSION_ID")
        return

    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        # Expected when run manually; avoid noisy failures.
        return

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

    try:
        with open(env_file, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    except OSError as exc:
        # Degrade like every other failure path so a write error never aborts
        # the base-staleness directive that main() emits next.
        warn(f"could not write $CLAUDE_ENV_FILE ({env_file}): {exc}")


def _git(project_dir: str, *args: str) -> subprocess.CompletedProcess | None:
    """Run a read-only `git -C project_dir` command; None when git is unavailable."""
    try:
        return subprocess.run(
            ["git", "-C", project_dir, *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None


def base_staleness_directive(project_dir: str) -> str:
    """Return a stale-base directive when HEAD trails the resolved default, else ""."""
    if not project_dir:
        return ""

    head = _git(project_dir, "symbolic-ref", "refs/remotes/origin/HEAD")
    if head is None or head.returncode != 0:
        return ""
    ref = head.stdout.strip()
    if not ref.startswith(_TRACKING_PREFIX):
        return ""
    tracking = ref[len(_TRACKING_PREFIX) :]  # e.g. "origin/main"

    counted = _git(project_dir, "rev-list", "--count", f"HEAD..{tracking}")
    if counted is None or counted.returncode != 0:
        return ""
    try:
        behind = int(counted.stdout.strip())
    except ValueError:
        return ""
    if behind <= 0:
        return ""

    return _format_directive(behind, tracking)


def _format_directive(behind: int, tracking: str) -> str:
    plural = "" if behind == 1 else "s"
    return "\n".join(
        [
            f'<SPEC-TREE_SESSION_START base="stale" behind="{behind}" default="{tracking}"/>',
            f"This worktree's HEAD is {behind} commit{plural} behind {tracking}. Before",
            f"starting work, bring it current: fetch and rebase onto {tracking} — never",
            "reset (a reset moves the branch pointer but leaves the working tree on the",
            "old base).",
        ]
    )


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        warn("invalid JSON on stdin; not exporting")
        return 0
    if not isinstance(payload, dict):
        warn("stdin payload is not a JSON object; not exporting")
        return 0

    # Prefer Claude Code's project-root variable; fall back to .cwd defensively.
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ""
    if not os.environ.get("CLAUDE_PROJECT_DIR") and project_dir:
        warn(
            "CLAUDE_PROJECT_DIR unset; falling back to .cwd, which may not be the product root"
        )

    write_env_file(payload, project_dir)

    directive = base_staleness_directive(project_dir)
    if directive:
        print(directive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
