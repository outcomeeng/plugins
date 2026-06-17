"""Compliance test for 21-queued-work-discoverability.enabler (queued-work-discoverability.md compliance).

L1: runs ``spx hooks session-start`` against a spec-tree project. Asserts the
directive fires only in a spec-tree repository, presents the pool-global queue
unfiltered by branch, and never mutates session state (the seeded ``todo``
sessions stay in ``todo``).

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

SESSION_ID = "cccccccc-dddd-eeee-ffff-000000000000"


def _seed_todo(project: Path, sid: str, git_ref: str) -> None:
    todo = project / ".spx" / "sessions" / "todo"
    todo.mkdir(parents=True, exist_ok=True)
    (todo / f"{sid}.md").write_text(
        f"---\npriority: medium\ngit_ref: {git_ref}\n"
        "goal: Do the thing\nnext_step: Next step\n---\n",
        encoding="utf-8",
    )


def test_no_directive_outside_spec_tree(tmp_path: Path) -> None:
    # No `spx/*.product.md`: the project is not a spec tree, so even with a queue
    # the directive must not fire.
    _seed_todo(tmp_path, "2026-06-15_19-21-23", git_ref="feat/x")
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert directive_of_kind(hook_document(result), "queued-work") is None


def test_pool_global_queue_is_unfiltered_by_branch(tmp_path: Path) -> None:
    make_spec_tree(tmp_path)
    # Two sessions on different branches, neither the worktree's own; both appear.
    _seed_todo(tmp_path, "2026-06-15_19-21-23", git_ref="feat/one")
    _seed_todo(tmp_path, "2026-06-14_16-58-25", git_ref="work/two")
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    directive = directive_of_kind(hook_document(result), "queued-work")
    assert directive is not None
    ids = {entry["id"] for entry in directive["sessions"]}
    assert ids == {"2026-06-15_19-21-23", "2026-06-14_16-58-25"}


def test_directive_never_mutates_session_state(tmp_path: Path) -> None:
    make_spec_tree(tmp_path)
    _seed_todo(tmp_path, "2026-06-15_19-21-23", git_ref="feat/x")
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    todo = tmp_path / ".spx" / "sessions" / "todo"
    doing = tmp_path / ".spx" / "sessions" / "doing"
    # The surfaced session stays claimable — never moved to `doing/`.
    assert (todo / "2026-06-15_19-21-23.md").exists()
    assert not doing.exists() or list(doing.iterdir()) == []
