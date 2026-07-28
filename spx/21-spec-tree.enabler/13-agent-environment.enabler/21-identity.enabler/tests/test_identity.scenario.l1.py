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

from pathlib import Path
from uuid import uuid4

from outcomeeng.validation.hook_contract import session_start_payload
from outcomeeng_testing.harnesses.hooks import run_session_start


def test_session_start_writes_session_id_to_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / "claude.env"
    session_id = str(uuid4())
    result = run_session_start(
        session_start_payload(
            session_id=session_id,
            current_working_directory=tmp_path,
        ),
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert f"export CLAUDE_SESSION_ID={session_id}" in env_file.read_text(
        encoding="utf-8"
    )
