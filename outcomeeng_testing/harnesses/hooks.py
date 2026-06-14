"""Harness: invoke the spec-tree SessionStart hook as a subprocess.

Mediates access to the real ``session-start.py`` hook (L1: a python subprocess
plus tmp files), owning argument and environment setup so tests assert on the
hook's two real outputs — the harness env file and stdout — without a test
double. It does not replace the hook's behavior.

Exception case per `plugins/spec-tree/skills/testing/references/methodology.md`:
none.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
SESSION_START = (
    _REPO_ROOT / "src" / "plugins" / "spec-tree" / "scripts" / "session-start.py"
)


def run_session_start(
    payload: dict[str, object],
    *,
    env_file: Path | None = None,
    project_dir: Path | str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the real SessionStart hook with ``payload`` on stdin.

    The ambient ``CLAUDE_PROJECT_DIR`` and ``CLAUDE_ENV_FILE`` are dropped so the
    hook sees only what the call provides, isolating the result from the runner's
    own session environment.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("CLAUDE_PROJECT_DIR", "CLAUDE_ENV_FILE")
    }
    if env_file is not None:
        env["CLAUDE_ENV_FILE"] = str(env_file)
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(SESSION_START)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


__all__ = ["SESSION_START", "run_session_start"]
