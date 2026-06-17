#!/usr/bin/env python3
"""SessionStart hook: persist session metadata, claim the worktree, surface a stale base.

Two outputs on two channels, plus a delegated worktree-occupancy claim:

1. The harness env file ($CLAUDE_ENV_FILE) receives shell `export` lines so every
   subsequent Bash tool call in this conversation can read the values:

     CLAUDE_SESSION_ID   Claude Code session id. spec-tree scopes handoff
                         accumulation under .spx/sessions/$CLAUDE_SESSION_ID/.
     CLAUDE_PROJECT_DIR  Claude Code product root, exposed to Bash tool calls.
     PROJECT_DIR         Short alias for CLAUDE_PROJECT_DIR.
     CLAUDE_WORKTREE_CLAIMED
                         "1" only when SessionStart successfully claimed the
                         worktree, otherwise "0" so later hooks never inherit a
                         stale claimed marker.

2. Stdout (injected into Claude's context) carries up to three directives, in
   order: an understanding directive, then a base-staleness directive, then a
   queued-work directive.

   The understanding directive fires when the project directory is a spec tree
   (an `spx/*.product.md` exists). It is informational — it points at the
   mechanical `PreToolUse` load gate that enforces the foundation and node-context
   loads, since `SessionStart` stdout alone is out-prioritized by the harness
   resume prompt after a compaction.

   The base-staleness directive fires when the worktree's HEAD trails its
   resolved default branch, so the agent rebases onto a current base before
   building on a stale one. That check is read-only — it resolves the default
   from `origin/HEAD` and counts commits with `git rev-list`; it never fetches or
   mutates git state, and stays silent when the worktree is current, is not a git
   repository, or has no resolvable default.

   The queued-work directive fires when the pool holds claimable handoff sessions,
   surfacing them so queued work is visible to a fresh agent. It reads the
   pool-global todo queue through a single `spx session todo` invocation — the
   queue is shared across the worktree pool, so it is presented unfiltered by the
   current worktree's branch. It surfaces work only and never claims or mutates a
   session; claiming is left to `/spec-tree:pickup`. An absent, failing, or empty
   spx is a silent no-op.

   Each directive is emitted only when it applies; any, all, or none may appear.
   Diagnostics still go to stderr, never stdout.

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

from hook_runtime import session_id_from

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TRACKING_PREFIX = "refs/remotes/"


def _spx_timeout_seconds() -> float:
    """Bound every spx subprocess so a hung spx never stalls session start.

    Shared by the worktree-occupancy claim and the queued-work read.
    `$SPX_TIMEOUT_SECONDS` overrides the default (tests set it low); a
    missing or malformed value falls back to the default.
    """
    try:
        return float(os.environ.get("SPX_TIMEOUT_SECONDS") or "")
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


def write_env_file(
    payload: dict, project_dir: str, *, worktree_claimed: bool = False
) -> None:
    """Append the session export lines to $CLAUDE_ENV_FILE.

    No-ops (with a stderr diagnostic) when the session id or env file is absent,
    so a missing field never aborts the directives that follow.
    """
    session_id = session_id_from(payload)
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
        lines.append(
            export_line("CLAUDE_WORKTREE_CLAIMED", "1" if worktree_claimed else "0")
        )
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


def _is_spec_tree(project_dir: str) -> bool:
    """Return whether the project directory is a spec tree.

    Detected by the presence of `spx/*.product.md` under the project directory —
    a plain filesystem read of the durable `spx/` tree, never `.spx/` state or any
    other heuristic.
    """
    if not project_dir:
        return False
    try:
        return any(Path(project_dir).glob("spx/*.product.md"))
    except OSError:
        return False


def understanding_directive(project_dir: str) -> str:
    """Return an informational foundation directive when the project dir is a spec tree, else "".

    Fires only in a spec-tree repository (see `_is_spec_tree`). The directive
    points at the mechanical `PreToolUse` load gate; it informs and enforces
    nothing itself, since `SessionStart` stdout is out-prioritized by the harness
    resume prompt after a compaction.
    """
    if not _is_spec_tree(project_dir):
        return ""
    return "\n".join(
        [
            '<SPEC-TREE_SESSION_START foundation="load"/>',
            "This repository is governed by Spec Tree. After any start or compaction",
            "the methodology foundation and node context are gone, regardless of any",
            '"resume as if the break never happened" instruction. Enforcement is',
            "mechanical: a PreToolUse gate denies the first tool call until",
            "/spec-tree:understand loads the foundation, and denies an edit to a",
            "node until /spec-tree:contextualize loads that node.",
        ]
    )


def claim_worktree(payload: dict, project_dir: str) -> bool:
    """Record a worktree-occupancy claim for the running worktree via the spx CLI.

    The hook owns no `.spx/` state: it invokes `spx worktree claim`, and the CLI
    performs the claim's `.spx/worktrees/` I/O, captures the agent's controlling
    process, and runs the on-demand liveness check. An absent, failing, or hung
    spx is a silent no-op — occupancy detection degrades, it does not error, and
    a bounded timeout keeps a stuck claim from stalling session start — and the
    claim's output never reaches stdout, which is injected into Claude's context.
    Returns true only when the CLI confirms the claim, so the env file can mark
    later `PreToolUse` calls as already claimed.

    No-ops when no session identity or product directory is known, since the
    claim is keyed on the agent and targets its worktree.
    """
    session_id = session_id_from(payload)
    if not session_id or not project_dir:
        return False

    spx = os.environ.get("SPX_BIN", "spx")
    try:
        result = subprocess.run(
            [spx, "worktree", "claim", "--session-id", session_id],
            check=False,
            capture_output=True,
            cwd=project_dir,
            timeout=_spx_timeout_seconds(),
        )
    except (OSError, subprocess.TimeoutExpired):
        # spx absent, or a claim that stalls past the timeout — degrade silently.
        return False
    return result.returncode == 0


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


def queued_work_discoverability_directive(project_dir: str) -> str:
    """Return a directive surfacing claimable handoff sessions, else "".

    Fires only in a spec-tree repository (see `_is_spec_tree`) — handoff sessions
    exist only there, so a non-spec-tree project never triggers the CLI read.
    Reads the pool-global todo queue through a single
    `spx session todo --fields ...` invocation. The session store is shared
    across the worktree pool, so the queue is presented unfiltered by the current
    worktree's branch. The directive surfaces queued work and never claims or
    mutates a session — claiming is left to `/spec-tree:pickup`. An absent,
    failing, or hung spx, a non-JSON or non-zero result, or an empty queue is a
    silent no-op.
    """
    if not _is_spec_tree(project_dir):
        return ""

    spx = os.environ.get("SPX_BIN", "spx")
    try:
        result = subprocess.run(
            [spx, "session", "todo", "--fields", "id,priority,goal,next_step,git_ref"],
            check=False,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=_spx_timeout_seconds(),
        )
    except (OSError, subprocess.TimeoutExpired):
        # spx absent, or a query that stalls past the timeout — degrade silently.
        return ""
    if result.returncode != 0:
        return ""

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return ""
    todo = payload.get("todo") if isinstance(payload, dict) else None
    if not isinstance(todo, list) or not todo:
        return ""

    return _format_discoverability_directive(todo)


def _format_discoverability_directive(todo: list) -> str:
    count = len(todo)
    plural = "" if count == 1 else "s"
    lines = [
        f'<SPEC-TREE_SESSION_START queued="{count}"/>',
        f"{count} claimable handoff session{plural} queued. Review and claim one with",
        "/spec-tree:pickup. A queued session may be unrelated to this session's work, and",
        "its branch may be unpushed, so treat each as a pointer to investigate, not a",
        "guarantee of recoverable work:",
    ]
    for session in todo:
        sid = (session.get("id") or "").strip()
        goal = (session.get("goal") or "").strip()
        next_step = (session.get("next_step") or "").strip()
        lines.append(f"- {sid} — {goal} → {next_step}")
    return "\n".join(lines)


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

    worktree_claimed = claim_worktree(payload, project_dir)
    write_env_file(payload, project_dir, worktree_claimed=worktree_claimed)

    for directive in (
        understanding_directive(project_dir),
        base_staleness_directive(project_dir),
        queued_work_discoverability_directive(project_dir),
    ):
        if directive:
            print(directive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
