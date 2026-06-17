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
_SCRIPTS = _REPO_ROOT / "src" / "plugins" / "spec-tree" / "scripts"
SESSION_START = _SCRIPTS / "session-start.py"
LOAD_GATE = _SCRIPTS / "load-gate.py"

# A path that does not resolve, so the hook's worktree-occupancy claim delegates
# to a missing `spx` and no-ops. Defaulted for every run so the hook's other
# outputs (env file, stdout) stay hermetic; a test that exercises the claim
# passes a fake via ``env_overrides={"SPX_BIN": ...}`` (and
# ``SPX_TIMEOUT_SECONDS`` to bound a deliberately slow fake).
MISSING_SPX = "/nonexistent/spx"
_SESSION_START_ENV_EXCLUDES = {
    "CLAUDE_PROJECT_DIR",
    "CLAUDE_ENV_FILE",
    "CLAUDE_SESSION_ID",
    "CODEX_THREAD_ID",
    "SPX_BIN",
}
_PRETOOL_ENV_EXCLUDES = {
    "CLAUDE_PROJECT_DIR",
    "CLAUDE_SESSION_ID",
    "CLAUDE_WORKTREE_CLAIMED",
    "CODEX_THREAD_ID",
    "SPX_BIN",
}


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
    own session environment. ``SPX_BIN`` defaults to a missing binary so the
    worktree-occupancy claim no-ops; pass ``env_overrides={"SPX_BIN": ...}`` to
    exercise it.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _SESSION_START_ENV_EXCLUDES
    }
    env["SPX_BIN"] = MISSING_SPX
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


def make_spec_tree(root: Path) -> None:
    """Mark ``root`` a spec tree so the hook's spec-tree directives fire.

    The SessionStart directives that gate on a spec-tree repository detect it by
    an ``spx/*.product.md`` product spec under the project directory; this writes
    a minimal one so a directive under test reaches its CLI read or its output.
    """
    spx = root / "spx"
    spx.mkdir(parents=True)
    (spx / "demo.product.md").write_text("# Demo product\n", encoding="utf-8")


def run_pretool_gate(
    payload: dict[str, object],
    *,
    project_dir: Path | str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the real ``PreToolUse`` load-gate hook with ``payload`` on stdin.

    Mediates the same hook→CLI boundary as ``run_session_start``: the ambient
    ``CLAUDE_PROJECT_DIR`` and ``SPX_BIN`` are dropped so the hook sees only what
    the call provides, and ``SPX_BIN`` defaults to a missing binary so the gate's
    verdict delegation no-ops (degrading to allow). Pass
    ``env_overrides={"SPX_BIN": ...}`` to point the gate at a fake ``spx`` that
    returns a crafted verdict.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _PRETOOL_ENV_EXCLUDES
    }
    env["SPX_BIN"] = MISSING_SPX
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(LOAD_GATE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


__all__ = [
    "LOAD_GATE",
    "MISSING_SPX",
    "SESSION_START",
    "make_spec_tree",
    "run_pretool_gate",
    "run_session_start",
]
