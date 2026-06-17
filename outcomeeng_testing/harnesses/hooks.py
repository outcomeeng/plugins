"""Harness: invoke the spec-tree SessionStart hook as a subprocess.

Runs the real ``session-start.py`` hook (L1: a python subprocess plus tmp files),
owning argument and environment setup so tests assert on its one effect — the
agent session identity written to the harness env file. The spec-tree plugin ships
no other hook.

Exception case per `plugins/spec-tree/skills/test/references/methodology.md`:
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

_SESSION_START_ENV_EXCLUDES = {
    "CLAUDE_PROJECT_DIR",
    "CLAUDE_ENV_FILE",
    "CLAUDE_SESSION_ID",
    "CODEX_THREAD_ID",
}


def run_session_start(
    payload: dict[str, object],
    *,
    env_file: Path | None = None,
    project_dir: Path | str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the real SessionStart hook with ``payload`` on stdin.

    The ambient ``CLAUDE_PROJECT_DIR``, ``CLAUDE_ENV_FILE``, and session-identity
    env vars are dropped so the hook sees only what the call provides, isolating
    the result from the runner's own session environment.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _SESSION_START_ENV_EXCLUDES
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


__all__ = [
    "SESSION_START",
    "run_session_start",
]
