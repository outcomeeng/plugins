"""Scenario tests for 43-session-directory.enabler (session-directory.md scenario).

L1: the real `session-start.py` hook is run as a subprocess against real
filesystem I/O in pytest tmp_path directories, with no test doubles.

Assertion covered:
  - SessionStart in a directory containing .spx/ creates no per-runtime session
    directory (lazy creation is spx session pickup's job).
"""

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_creates_no_per_runtime_session_directory(tmp_path):
    (tmp_path / ".spx" / "sessions").mkdir(parents=True)
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert not (tmp_path / ".spx" / "sessions" / SESSION_ID).exists()
    assert list((tmp_path / ".spx" / "sessions").iterdir()) == []
