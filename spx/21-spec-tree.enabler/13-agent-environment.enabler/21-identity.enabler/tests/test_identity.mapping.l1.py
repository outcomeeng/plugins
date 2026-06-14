"""Mapping tests for 21-identity.enabler (identity.md mapping).

L1: the real `session-start.py` hook is run as a subprocess against real
filesystem I/O in pytest tmp_path directories, with no test doubles.

Assertion covered:
  - A SessionStart payload maps to the identity write: distinct session UUIDs map
    to distinct $CLAUDE_SESSION_ID writes; a missing session_id maps to no export.
"""

from outcomeeng_testing.harnesses.hooks import run_session_start


def test_distinct_session_ids_map_to_distinct_writes(tmp_path):
    first_env = tmp_path / "first.env"
    second_env = tmp_path / "second.env"
    run_session_start(
        {"session_id": "session-one", "cwd": str(tmp_path)},
        env_file=first_env,
        project_dir=tmp_path,
    )
    run_session_start(
        {"session_id": "session-two", "cwd": str(tmp_path)},
        env_file=second_env,
        project_dir=tmp_path,
    )
    assert "export CLAUDE_SESSION_ID=session-one" in first_env.read_text(
        encoding="utf-8"
    )
    assert "export CLAUDE_SESSION_ID=session-two" in second_env.read_text(
        encoding="utf-8"
    )


def test_missing_session_id_maps_to_no_export(tmp_path):
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    assert "CLAUDE_SESSION_ID" not in content
