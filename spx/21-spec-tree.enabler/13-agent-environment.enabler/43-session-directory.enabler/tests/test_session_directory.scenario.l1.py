"""Scenario test for 43-session-directory.enabler (session-directory.md scenario).

L1: runs ``spx hooks session-start`` as a subprocess against real filesystem I/O
in pytest ``tmp_path`` directories.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_creates_no_per_runtime_session_directory(tmp_path: Path) -> None:
    (tmp_path / ".spx" / "sessions").mkdir(parents=True)
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert not (tmp_path / ".spx" / "sessions" / SESSION_ID).exists()
    assert list((tmp_path / ".spx" / "sessions").iterdir()) == []
