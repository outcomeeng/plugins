"""Scenario tests for 21-queued-work-discoverability.enabler (queued-work-discoverability.md scenario).

L1: the real `session-start.py` hook is run as a subprocess against a fake `spx`
CLI in a temp directory, with no test doubles. The fake comes from
`outcomeeng_testing.harnesses.spx_cli` and answers `session todo` with a
controlled projection.

Assertion covered:
  - A pool holding one or more `todo` sessions yields a stdout directive listing
    each claimable session's id, goal, and next step and naming /spec-tree:pickup.
"""

from outcomeeng_testing.harnesses.hooks import make_spec_tree, run_session_start
from outcomeeng_testing.harnesses.spx_cli import fake_spx, sample_todo_session

SESSION_ID = "11111111-2222-3333-4444-555555555555"

_TODO = [
    sample_todo_session(id="2026-06-15_19-21-23", git_ref="feat/discoverability"),
    sample_todo_session(
        id="2026-06-14_16-58-25",
        goal="Continue the named-subject voice sweep",
        next_step="Branch from origin/main and survey",
        git_ref="main",
    ),
]


def test_queued_sessions_emit_discoverability_directive(tmp_path):
    make_spec_tree(tmp_path)
    with fake_spx(todo=_TODO) as spx:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
    assert result.returncode == 0
    # Directive marker and command token asserted inline; their source-ownership
    # is tracked cross-hook in spx/21-spec-tree.enabler/ISSUES.md item 20.
    assert "<SPEC-TREE_SESSION_START" in result.stdout
    assert "/spec-tree:pickup" in result.stdout
    for session in _TODO:
        assert session["id"] in result.stdout
        assert session["goal"] in result.stdout
        assert session["next_step"] in result.stdout
