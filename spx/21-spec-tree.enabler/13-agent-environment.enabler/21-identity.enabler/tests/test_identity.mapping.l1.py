"""Mapping test for 21-identity.enabler (identity.md mapping).

L1: a SessionStart payload maps to the identity write — distinct session UUIDs map
to distinct env-file writes; a missing or empty session id maps to no export.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import run_session_start


def test_distinct_session_ids_map_to_distinct_writes(tmp_path: Path) -> None:
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
    assert "session-one" in first_env.read_text(encoding="utf-8")
    assert "session-two" in second_env.read_text(encoding="utf-8")


def test_missing_session_id_maps_to_no_export(tmp_path: Path) -> None:
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    assert "CLAUDE_SESSION_ID" not in content
