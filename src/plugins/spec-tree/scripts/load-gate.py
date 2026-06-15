#!/usr/bin/env python3
"""PreToolUse hook: gate a tool call on methodology load-state.

Thin delegator. Forwards the tool name, the tool's path-bearing argument, the
session id, and the transcript path to the `spx` CLI (`spx gate check`) and emits
the CLI's allow-or-deny verdict as the `PreToolUse` decision. The hook holds no
gate logic — the boundary-scoped transcript scan, the marker check, the
path-to-node mapping, and the verdict belong to the `spx` CLI, which owns all
transcript and state I/O. Enforcement keys on tracked load-state — whether the
methodology foundation and the target node's context are loaded since the most
recent session-start or compaction boundary — never on the work category or on
the agent noticing a path.

The hook engages only in a spec-tree repository (an `spx/*.product.md` exists), a
plain read of the durable tree — never `.spx/` state or the transcript. It
degrades to allowing the call (emitting no denial) when the project is not a spec
tree, the payload lacks a tool name, or the CLI is absent, exits non-zero, times
out, or returns an unparseable verdict.

stdlib only (python3); no third-party packages.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _timeout_seconds() -> float:
    """Bound the gate subprocess so a hung `spx` never stalls a tool call.

    `$SPX_GATE_TIMEOUT_SECONDS` overrides the default (tests set it low); a
    missing or malformed value falls back to the default.
    """
    try:
        return float(os.environ.get("SPX_GATE_TIMEOUT_SECONDS") or "")
    except ValueError:
        return 5.0


def _is_spec_tree(project_dir: str) -> bool:
    """True when the project directory holds an `spx/*.product.md` spec.

    A plain filesystem read of the durable tree, the same detection the
    SessionStart understanding directive uses — never `.spx/` state, the
    transcript, or another heuristic.
    """
    if not project_dir:
        return False
    try:
        return any(Path(project_dir).glob("spx/*.product.md"))
    except OSError:
        return False


def _emit_deny(reason: str) -> None:
    """Emit the `PreToolUse` deny decision the harness blocks the call on."""
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )


def _gate_argv(payload: dict) -> list[str] | None:
    """Build the `spx gate check` argv from the payload, or None to allow.

    Returns None — meaning "allow, do not invoke the CLI" — when the payload
    carries no usable tool name. The tool's path-bearing argument (`file_path`
    for file edits, `command` for `Bash`) is forwarded when present so the CLI
    performs the path-to-node mapping; the hook extracts the locator, never the
    node.
    """
    tool_name = payload.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name:
        return None

    argv = [os.environ.get("SPX_BIN", "spx"), "gate", "check", "--tool", tool_name]

    session_id = (payload.get("session_id") or "").strip()
    if session_id:
        argv += ["--session-id", session_id]

    transcript = payload.get("transcript_path")
    if isinstance(transcript, str) and transcript:
        argv += ["--transcript", transcript]

    tool_input = payload.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    path = tool_input.get("file_path")
    if isinstance(path, str) and path:
        argv += ["--path", path]
    command = tool_input.get("command")
    if isinstance(command, str) and command:
        argv += ["--command", command]

    return argv


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ""
    if not _is_spec_tree(project_dir):
        return 0  # not a spec-tree repository — allow, never invoke the CLI

    argv = _gate_argv(payload)
    if argv is None:
        return 0  # no tool name to gate on — allow

    try:
        proc = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=_timeout_seconds(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0  # spx absent or hung — degrade to allowing the call

    if proc.returncode != 0:
        return 0  # a non-zero exit is a CLI error, not a verdict — allow

    try:
        verdict = json.loads(proc.stdout or "")
    except json.JSONDecodeError:
        return 0  # unparseable verdict — degrade to allowing the call

    if isinstance(verdict, dict) and verdict.get("decision") == "deny":
        _emit_deny(str(verdict.get("reason") or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
