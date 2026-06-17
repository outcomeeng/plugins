"""Scenario test for 21-queued-work-discoverability.enabler (queued-work-discoverability.md scenario).

L1: runs ``spx hooks session-start`` against a spec-tree project whose pool holds
``todo`` sessions, and parses the ``queued-work`` descriptor.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import (
    directive_of_kind,
    hook_document,
    make_spec_tree,
    run_session_start,
)

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def _seed_todo(
    project: Path, sid: str, goal: str, next_step: str, git_ref: str
) -> None:
    todo = project / ".spx" / "sessions" / "todo"
    todo.mkdir(parents=True, exist_ok=True)
    (todo / f"{sid}.md").write_text(
        f"---\npriority: medium\ngit_ref: {git_ref}\n"
        f"goal: {goal}\nnext_step: {next_step}\n---\n",
        encoding="utf-8",
    )


def test_queued_sessions_emit_discoverability_directive(tmp_path: Path) -> None:
    make_spec_tree(tmp_path)
    seeded = {
        "2026-06-15_19-21-23": ("Ship discoverability", "Branch and survey"),
        "2026-06-14_16-58-25": ("Voice sweep", "Branch from origin/main"),
    }
    for sid, (goal, next_step) in seeded.items():
        _seed_todo(tmp_path, sid, goal, next_step, git_ref="feat/x")

    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    directive = directive_of_kind(hook_document(result), "queued-work")
    assert directive is not None
    listed = {entry["id"]: entry for entry in directive["sessions"]}
    assert set(listed) == set(seeded)
    for sid, (goal, next_step) in seeded.items():
        assert listed[sid]["goal"] == goal
        assert listed[sid]["next_step"] == next_step
