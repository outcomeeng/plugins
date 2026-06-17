"""Harness: invoke the spec-tree runtime hooks through the ``spx`` CLI.

The converted spec-tree hooks (SessionStart, PreToolUse) are owned by
``spx hooks <event>``; the plugin ships only the ``hooks.json`` wiring. This
harness runs those subcommands as subprocesses and parses the JSON document each
emits, so tests assert on the process exit signal and the document's key values
— never by scanning stdout for substrings — per
``spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md``.

The behavior these tests assert is implemented in ``@outcomeeng/spx``; until that
release publishes, the owning nodes stay in ``spx/EXCLUDE`` and these tests do not
run in the quality gate.

Exception case per `plugins/spec-tree/skills/test/references/methodology.md`:
none.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

#: ``spx`` executable; tests override via ``env_overrides={"SPX_BIN": ...}`` to
#: point at a published binary or a fake emitting a crafted JSON document.
DEFAULT_SPX_BIN = "spx"

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


def _hook_env(
    excludes: set[str], env_overrides: dict[str, str] | None
) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in excludes}
    env["SPX_BIN"] = DEFAULT_SPX_BIN
    if env_overrides:
        env.update(env_overrides)
    return env


def _run_hook(
    event: str, env: dict[str, str], payload: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    spx = env.get("SPX_BIN", DEFAULT_SPX_BIN)
    return subprocess.run(  # noqa: S603 — argv is a source-owned command contract.
        [spx, "hooks", event],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def run_session_start(
    payload: dict[str, object],
    *,
    env_file: Path | None = None,
    project_dir: Path | str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``spx hooks session-start`` with ``payload`` on stdin.

    The ambient ``CLAUDE_PROJECT_DIR`` and ``CLAUDE_ENV_FILE`` are dropped so the
    hook sees only what the call provides, isolating the result from the runner's
    own session environment.
    """
    env = _hook_env(_SESSION_START_ENV_EXCLUDES, env_overrides)
    if env_file is not None:
        env["CLAUDE_ENV_FILE"] = str(env_file)
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return _run_hook("session-start", env, payload)


def run_pretool_gate(
    payload: dict[str, object],
    *,
    project_dir: Path | str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``spx hooks pre-tool-use`` with ``payload`` on stdin."""
    env = _hook_env(_PRETOOL_ENV_EXCLUDES, env_overrides)
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return _run_hook("pre-tool-use", env, payload)


def hook_document(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    """Parse a hook's stdout as the JSON document the integration contract requires."""
    document: dict[str, Any] = json.loads(result.stdout)
    return document


def session_directives(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the ``specTree.directives`` descriptor list from a session-start document."""
    spec_tree = document.get("specTree", {})
    directives = spec_tree.get("directives", [])
    return list(directives)


def directive_of_kind(document: dict[str, Any], kind: str) -> dict[str, Any] | None:
    """Return the first ``specTree.directives`` entry of ``kind``, or ``None``."""
    for directive in session_directives(document):
        if directive.get("kind") == kind:
            return directive
    return None


def make_spec_tree(root: Path) -> None:
    """Mark ``root`` a spec tree so the hook's spec-tree directives fire.

    The hooks detect a spec-tree repository by an ``spx/*.product.md`` product
    spec under the project directory; this writes a minimal one.
    """
    spx = root / "spx"
    spx.mkdir(parents=True)
    (spx / "demo.product.md").write_text("# Demo product\n", encoding="utf-8")


__all__ = [
    "DEFAULT_SPX_BIN",
    "directive_of_kind",
    "hook_document",
    "make_spec_tree",
    "run_pretool_gate",
    "run_session_start",
    "session_directives",
]
