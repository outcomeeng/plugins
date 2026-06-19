"""Scenario test for 13-agent-environment.enabler (agent-environment.md scenarios).

L1: runs the shipped `SessionStart` hook command — which delegates to `spx hook
run session-start` — as a subprocess against real filesystem I/O in pytest
tmp_path directories, with no test doubles. The harness runs the command from
`hooks.json` with the temp directory as the project dir, so spx's session storage
stays hermetic.

Assertions covered (the plugin's integration with the spx hook runner — not spx's
internal formatting, which is spx's own suite):
  - On the normal path the hook delivers the session environment: the agent
    identity and the worktree-occupancy claim.
  - On the disabled path the kill switch short-circuits to a clean no-op.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import (
    KILL_SWITCH_DISABLED,
    KILL_SWITCH_ENV,
    run_session_start,
)

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_delivers_identity_and_worktree_claim(tmp_path: Path) -> None:
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8")
    # Identity reaches the env file every later Bash tool call sources.
    assert f"export CLAUDE_SESSION_ID={SESSION_ID}" in content
    # The worktree-occupancy claim is recorded: the env flag plus the claim file
    # the spx hook runner writes under the project's .spx tree.
    assert "export CLAUDE_WORKTREE_CLAIMED=1" in content
    claims = list((tmp_path / ".spx" / "worktrees").glob("*.claim"))
    assert claims, "the hook must record a worktree-occupancy claim"


def test_kill_switch_short_circuits_to_a_clean_no_op(tmp_path: Path) -> None:
    env_file = tmp_path / "claude.env"
    env_file.write_text("", encoding="utf-8")
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
        env_overrides={KILL_SWITCH_ENV: KILL_SWITCH_DISABLED},
    )
    assert result.returncode == 0
    # Disabled: no identity, no claim, no .spx state.
    assert env_file.read_text(encoding="utf-8") == ""
    assert not (tmp_path / ".spx").exists()


def test_absent_spx_degrades_to_a_clean_no_op(tmp_path: Path) -> None:
    # An empty PATH leaves spx unresolvable, so the command's `command -v` probe
    # fails and the guard floors to a valid empty result — the safety net for a
    # consumer who installs the plugin without spx on PATH.
    env_file = tmp_path / "claude.env"
    env_file.write_text("", encoding="utf-8")
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
        path="",
    )
    assert result.returncode == 0
    assert env_file.read_text(encoding="utf-8") == ""
    assert not (tmp_path / ".spx").exists()
