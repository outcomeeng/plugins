"""Mapping test for 21-queued-work-discoverability.enabler (queued-work-discoverability.md mapping).

L1: the ``todo`` projection maps to the directive — a non-empty ``todo`` set maps to
a ``queued-work`` descriptor surfacing each session's id/goal/next_step; an empty set
maps to no ``queued-work`` directive.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.hooks import (
    directive_of_kind,
    hook_document,
    make_spec_tree,
    run_session_start,
)

SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _seed_todo(project: Path, sid: str) -> None:
    todo = project / ".spx" / "sessions" / "todo"
    todo.mkdir(parents=True, exist_ok=True)
    (todo / f"{sid}.md").write_text(
        "---\npriority: medium\ngit_ref: feat/x\n"
        "goal: Do the thing\nnext_step: Next step\n---\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("has_queue", [True, False])
def test_queue_presence_maps_to_directive(has_queue: bool, tmp_path: Path) -> None:
    make_spec_tree(tmp_path)
    if has_queue:
        _seed_todo(tmp_path, "2026-06-15_19-21-23")

    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    directive = directive_of_kind(hook_document(result), "queued-work")
    if has_queue:
        assert directive is not None
        entry = directive["sessions"][0]
        assert entry["id"] == "2026-06-15_19-21-23"
        assert entry["goal"] == "Do the thing"
        assert entry["next_step"] == "Next step"
    else:
        assert directive is None
