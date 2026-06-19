"""Scenario tests for 21-identity.enabler (identity.md scenario).

L1: the shipped `SessionStart` hook command — which delegates to `spx hook run
session-start` — is run as a subprocess against real filesystem I/O in pytest
tmp_path directories, with no test doubles. The invocation comes from
`outcomeeng_testing.harnesses.hooks`, which runs the command from `hooks.json`
with the temp directory as the project dir so spx's session storage stays
hermetic.

Assertion covered:
  - SessionStart writes $CLAUDE_SESSION_ID to the harness env file.
"""

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_writes_session_id_to_env_file(tmp_path):
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert f"export CLAUDE_SESSION_ID={SESSION_ID}" in env_file.read_text(
        encoding="utf-8"
    )
