"""Harness: invoke the spec-tree SessionStart hook as the runtime would.

The shipped hook is the inline-guard command in
``src/plugins/spec-tree/hooks/hooks.json``; it delegates to the ``spx`` CLI hook
runner. This harness reads that command verbatim (so a test exercises the shipped
artifact, not a copy) and runs it through ``/bin/sh`` with a controlled
environment. ``CLAUDE_PROJECT_DIR`` and the working directory are set to the
caller's temp directory, so the ``spx`` hook runner resolves its session storage
(the worktree-occupancy claim) under that temp tree rather than the real
repository — every run is hermetic. ``spx`` is resolved from the inherited
``PATH``; a caller drives the disabled-or-absent guard branches by overriding the
kill-switch env var or the ``PATH``.

Exception case per `plugins/spec-tree/skills/test/references/methodology.md`:
none.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)

_HOOKS_JSON = ("src", "plugins", "spec-tree", "hooks", "hooks.json")
SESSION_START_EVENT = "SessionStart"

# The hook's environment kill switch (hooks.json): set to "1" to short-circuit the
# hook to a valid empty result before it probes for or invokes spx.
KILL_SWITCH_ENV = "SPECTREE_SESSION_HOOK_DISABLED"
KILL_SWITCH_DISABLED = "1"

# Env vars dropped from the child so the hook command sees only what the call
# provides — its own session identity, project dir, and env file, not the runner's.
_SESSION_START_ENV_EXCLUDES = {
    "CLAUDE_PROJECT_DIR",
    "CLAUDE_ENV_FILE",
    "CLAUDE_SESSION_ID",
    "CODEX_THREAD_ID",
}

# The hook declares its own short timeout; the harness bounds the subprocess well
# above it so a hung command surfaces as a harness failure rather than a wedge.
_SUBPROCESS_TIMEOUT_S = 30


def _hooks_config(test_file: str | None = None) -> dict[str, Any]:
    root = (
        marketplace_root_for_spec_tree_root_test(test_file)
        if test_file is not None
        else Path(__file__).resolve().parents[2]
    )
    config: dict[str, Any] = json.loads(
        root.joinpath(*_HOOKS_JSON).read_text(encoding="utf-8")
    )
    return config


def session_start_events(test_file: str | None = None) -> list[str]:
    """Return the hook event names the spec-tree plugin declares, in order."""
    return list(_hooks_config(test_file)["hooks"])


def session_start_command(test_file: str | None = None) -> str:
    """Return the single shipped ``SessionStart`` hook command string."""
    entries = _hooks_config(test_file)["hooks"][SESSION_START_EVENT]
    commands = [hook["command"] for entry in entries for hook in entry["hooks"]]
    if len(commands) != 1:
        msg = (
            f"expected exactly one {SESSION_START_EVENT} command, found {len(commands)}"
        )
        raise ValueError(msg)
    command = commands[0]
    if not isinstance(command, str):
        msg = f"{SESSION_START_EVENT} command must be a string, got {type(command).__name__}"
        raise TypeError(msg)
    return command


def run_session_start(
    payload: dict[str, object],
    *,
    env_file: Path | None = None,
    project_dir: Path | str | None = None,
    env_overrides: dict[str, str] | None = None,
    path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the shipped ``SessionStart`` hook command with ``payload`` on stdin.

    The ambient ``CLAUDE_PROJECT_DIR``, ``CLAUDE_ENV_FILE``, and session-identity
    env vars are dropped so the hook sees only what the call provides. ``env_file``
    is exported as ``CLAUDE_ENV_FILE``; ``project_dir`` is exported as
    ``CLAUDE_PROJECT_DIR`` and used as the working directory, so the ``spx`` hook
    runner resolves its session storage there. ``env_overrides`` overlays extra
    variables (such as the kill switch); ``path`` overrides ``PATH`` so a caller
    can withhold ``spx`` to drive the absent-dependency branch.
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
    if path is not None:
        env["PATH"] = path
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(  # noqa: S603 — command is the shipped hook artifact under test.
        ["/bin/sh", "-c", session_start_command()],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_dir) if project_dir is not None else None,
        timeout=_SUBPROCESS_TIMEOUT_S,
    )


__all__ = [
    "KILL_SWITCH_DISABLED",
    "KILL_SWITCH_ENV",
    "SESSION_START_EVENT",
    "run_session_start",
    "session_start_command",
    "session_start_events",
]
