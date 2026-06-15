#!/usr/bin/env python3
"""SessionStart hook: persist session metadata, claim the worktree, surface a stale base.

Two outputs on two channels, plus a delegated worktree-occupancy claim:

1. The harness env file ($CLAUDE_ENV_FILE) receives shell `export` lines so every
   subsequent Bash tool call in this conversation can read the values:

     CLAUDE_SESSION_ID   Claude Code session id. spec-tree scopes handoff
                         accumulation under .spx/sessions/$CLAUDE_SESSION_ID/.
     CLAUDE_PROJECT_DIR  Claude Code product root, exposed to Bash tool calls.
     PROJECT_DIR         Short alias for CLAUDE_PROJECT_DIR.

2. Stdout (injected into Claude's context) carries up to two directives, in
   order: an understanding directive, then a base-staleness directive.

   The understanding directive fires when the project directory is a spec tree
   (an `spx/*.product.md` exists), prompting the agent to load the methodology
   foundation before spec-tree work.

   The base-staleness directive fires when the worktree's HEAD trails its
   resolved default branch, so the agent rebases onto a current base before
   building on a stale one. That check is read-only — it resolves the default
   from `origin/HEAD` and counts commits with `git rev-list`; it never fetches or
   mutates git state, and stays silent when the worktree is current, is not a git
   repository, or has no resolvable default.

   Each directive is emitted only when it applies; either, both, or neither may
   appear. Diagnostics still go to stderr, never stdout.

3. The spx CLI records a worktree-occupancy claim for the running worktree via
   `spx worktree claim`, so another agent sharing the pool can tell the worktree
   is held by a live agent rather than inferring "clean ⇒ free". The hook owns no
   .spx/ state — the CLI performs the claim I/O — and an absent, failing, or hung
   spx is a silent no-op.

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
from pathlib import Path

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TRACKING_PREFIX = "refs/remotes/"


def _claim_timeout_seconds() -> float:
    """Bound the worktree-claim subprocess so a hung spx never stalls session start.

    `$SPX_CLAIM_TIMEOUT_SECONDS` overrides the default (tests set it low); a
    missing or malformed value falls back to the default.
    """
    try:
        return float(os.environ.get("SPX_CLAIM_TIMEOUT_SECONDS") or "")
    except ValueError:
        return 5.0


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
    so a missing field never aborts the directives that follow.
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
        # the directives that main() emits next.
        warn(f"could not write $CLAUDE_ENV_FILE ({env_file}): {exc}")


def understanding_directive(project_dir: str) -> str:
    """Return a foundation-priming directive when the project dir is a spec tree, else "".

    A spec tree is detected by the presence of `spx/*.product.md` under the
    project directory — a plain filesystem read of the durable tree, never `.spx/`
    state or any other heuristic.
    """
    if not project_dir:
        return ""
    try:
        product_specs = any(Path(project_dir).glob("spx/*.product.md"))
    except OSError:
        return ""
    if not product_specs:
        return ""
    return "\n".join(
        [
            '<SPEC-TREE_SESSION_START foundation="load"/>',
            "This is a Spec Tree repository. Before any spec-tree work, invoke",
            "/spec-tree:understanding to load the methodology foundation, then",
            "/spec-tree:contextualizing <node> on the node you will work on.",
        ]
    )


def claim_worktree(payload: dict, project_dir: str) -> None:
    """Record a worktree-occupancy claim for the running worktree via the spx CLI.

    The hook owns no `.spx/` state: it invokes `spx worktree claim`, and the CLI
    performs the claim's `.spx/worktrees/` I/O, captures the agent's controlling
    process, and runs the on-demand liveness check. An absent, failing, or hung
    spx is a silent no-op — occupancy detection degrades, it does not error, and
    a bounded timeout keeps a stuck claim from stalling session start — and the
    claim's output never reaches stdout, which is injected into Claude's context.

    No-ops when no session identity or product directory is known, since the
    claim is keyed on the agent and targets its worktree.
    """
    session_id = (payload.get("session_id") or "").strip()
    if not session_id or not project_dir:
        return

    spx = os.environ.get("SPX_BIN", "spx")
    try:
        subprocess.run(
            [spx, "worktree", "claim", "--session-id", session_id],
            check=False,
            capture_output=True,
            cwd=project_dir,
            timeout=_claim_timeout_seconds(),
        )
    except (OSError, subprocess.TimeoutExpired):
        # spx absent, or a claim that stalls past the timeout — degrade silently.
        pass


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
    claim_worktree(payload, project_dir)

    for directive in (
        understanding_directive(project_dir),
        base_staleness_directive(project_dir),
    ):
        if directive:
            print(directive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
