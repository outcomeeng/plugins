#!/usr/bin/env python3
"""PreCompact hook: delegate capture of the active spec-tree node to the spx CLI.

Before compaction the spx CLI reads the transcript, extracts the most recent
contextualized node, and stashes it under `.spx/sessions/<session_id>/` so the
PostCompact hook can re-anchor the resuming agent. The CLI owns `.spx/`
resolution (shared across a bare-repository worktree pool), transcript parsing,
and stash placement; this hook only forwards the session id and transcript path.

Reads (from the PreCompact JSON payload on stdin):
  .session_id       Conversation id; keys the stash.
  .transcript_path  Path to the conversation transcript (JSONL).

Invokes: spx compact stash --session-id <id> --transcript <path>
($SPX_BIN overrides the `spx` executable; tests point it at a fake.)

A missing or pre-command spx CLI is a silent no-op — re-anchoring degrades, it
does not error.

stdlib only (python3); no third-party packages.
"""

import json
import os
import subprocess
import sys


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return 0

    session_id = (payload.get("session_id") or "").strip()
    transcript = payload.get("transcript_path") or ""
    if not session_id or not transcript:
        return 0

    spx = os.environ.get("SPX_BIN", "spx")
    try:
        subprocess.run(
            [
                spx,
                "compact",
                "stash",
                "--session-id",
                session_id,
                "--transcript",
                transcript,
            ],
            check=False,
            capture_output=True,
        )
    except OSError:
        # spx not installed — re-anchoring degrades silently.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
