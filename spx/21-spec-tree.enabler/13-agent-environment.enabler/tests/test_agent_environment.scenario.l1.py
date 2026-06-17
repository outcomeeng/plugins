"""Scenario test for 13-agent-environment.enabler (agent-environment.md scenario).

L1: runs the real `session-start.py` hook as a subprocess and asserts its only
effect is the `CLAUDE_SESSION_ID` env-file write — it emits no stdout directive
and creates no `.spx/` state (no worktree claim, no session directory). This is
the positive evidence that the four removed hooks left only session-identity
capture behind.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_only_writes_identity(tmp_path: Path) -> None:
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8")
    assert "CLAUDE_SESSION_ID" in content
    assert SESSION_ID in content
    # The hook's only effect is the identity write: no stdout directive, and no
    # `.spx/` state (a worktree claim or session directory would create it).
    assert result.stdout == ""
    assert not (tmp_path / ".spx").exists()
