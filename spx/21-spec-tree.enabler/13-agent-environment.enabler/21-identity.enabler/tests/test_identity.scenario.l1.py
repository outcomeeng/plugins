"""Scenario test for 21-identity.enabler (identity.md scenario).

L1: runs ``spx hooks session-start`` as a subprocess and asserts the session
identity is written into the harness env file.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_writes_session_id_to_env_file(tmp_path: Path) -> None:
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
