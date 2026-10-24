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
    WORKTREE_CLAIMED_ENV,
    WORKTREE_CLAIM_PATH_ENV,
    has_worktree_claim_export,
    read_env_exports,
    run_session_start,
    worktree_claim_path_from_env,
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
    env = read_env_exports(
        env_file,
        ["CLAUDE_SESSION_ID", WORKTREE_CLAIMED_ENV, WORKTREE_CLAIM_PATH_ENV],
    )
    # Identity reaches the env file every later Bash tool call sources.
    assert env["CLAUDE_SESSION_ID"] == SESSION_ID
    assert has_worktree_claim_export(env)
    # The worktree-occupancy claim is recorded: the hook exports an indicator and
    # the spx hook runner writes the claim file under the project's .spx tree.
    claim_path = worktree_claim_path_from_env(env_file, tmp_path)
    assert claim_path.parent == tmp_path.resolve() / ".spx" / "worktrees"
    assert claim_path.exists()


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
