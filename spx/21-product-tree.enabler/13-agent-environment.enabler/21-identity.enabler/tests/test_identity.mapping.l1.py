"""Mapping tests for 21-identity.enabler (identity.md mapping).

L1: the shipped `SessionStart` hook command — which delegates to `spx hook run
session-start` — is run as a subprocess against real filesystem I/O in pytest
tmp_path directories, with no test doubles. The invocation comes from
`outcomeeng_testing.harnesses.hooks`.

Assertion covered:
  - A SessionStart payload with a missing or empty session_id maps to no
    $CLAUDE_SESSION_ID export.
"""

from pathlib import Path

from outcomeeng.validation.hook_contract import session_start_payload
from outcomeeng_testing.harnesses.hooks import run_session_start


def test_missing_session_id_maps_to_no_export(tmp_path: Path) -> None:
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        session_start_payload(
            session_id=None,
            current_working_directory=tmp_path,
        ),
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    assert "CLAUDE_SESSION_ID" not in content


def test_empty_session_id_maps_to_no_export(tmp_path: Path) -> None:
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        session_start_payload(
            session_id="",
            current_working_directory=tmp_path,
        ),
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    assert "CLAUDE_SESSION_ID" not in content
