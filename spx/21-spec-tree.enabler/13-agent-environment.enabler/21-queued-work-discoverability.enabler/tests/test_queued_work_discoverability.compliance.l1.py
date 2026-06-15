"""Compliance tests for 21-queued-work-discoverability.enabler (queued-work-discoverability.md compliance).

L1: the real `session-start.py` hook is run as a subprocess against a fake `spx`
CLI in a temp directory, with no test doubles.

Assertions covered:
  - The queue is gathered through a single `spx session todo --fields ...` call
    that degrades to a silent no-op when the CLI is absent, exits non-zero, or
    returns no sessions.
  - The pool-global queue is presented unfiltered by the current worktree's
    branch.
  - The directive never claims, picks up, or otherwise mutates a session.
"""

import pytest

from outcomeeng_testing.harnesses.hooks import make_spec_tree, run_session_start
from outcomeeng_testing.harnesses.spx_cli import fake_spx, sample_todo_session

SESSION_ID = "cccccccc-dddd-eeee-ffff-000000000000"

# The CLI-degradation cases call make_spec_tree first so the spec-tree gate
# passes and the no-op they assert is attributable to the CLI condition under
# test rather than to a non-spec-tree project.
_SESSION = sample_todo_session()


def test_absent_cli_is_silent_no_op(tmp_path):
    make_spec_tree(tmp_path)
    # No env_overrides: the hooks harness defaults SPX_BIN to a missing binary.
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert "/spec-tree:pickup" not in result.stdout


def test_nonzero_cli_is_silent_no_op(tmp_path):
    make_spec_tree(tmp_path)
    with fake_spx(todo=[_SESSION], todo_exit_code=1) as spx:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
    assert result.returncode == 0
    assert "/spec-tree:pickup" not in result.stdout


def test_empty_queue_is_silent_no_op(tmp_path):
    make_spec_tree(tmp_path)
    with fake_spx(todo=[]) as spx:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
    assert result.returncode == 0
    assert "/spec-tree:pickup" not in result.stdout


def test_no_directive_outside_spec_tree(tmp_path):
    # No product spec: the project is not a spec tree, so the directive must not
    # fire and the hook must not even query the CLI, even with a non-empty queue.
    with fake_spx(todo=[_SESSION]) as spx:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
        session_calls = spx.session_invocations()
    assert result.returncode == 0
    assert "/spec-tree:pickup" not in result.stdout
    assert session_calls == []


def test_queue_gathered_through_single_fields_projection(tmp_path):
    make_spec_tree(tmp_path)
    with fake_spx(todo=[_SESSION]) as spx:
        run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
        session_calls = spx.session_invocations()
    assert session_calls == [
        ["session", "todo", "--fields", "id,priority,goal,next_step,git_ref"]
    ]


def test_pool_global_queue_is_unfiltered_by_branch(tmp_path):
    make_spec_tree(tmp_path)
    # Two sessions on different branches, neither the worktree's own; both appear.
    todo = [
        {**_SESSION, "id": "2026-06-15_19-21-23", "git_ref": "feat/one"},
        {**_SESSION, "id": "2026-06-14_16-58-25", "git_ref": "work/two"},
    ]
    with fake_spx(todo=todo) as spx:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
    assert result.returncode == 0
    assert "2026-06-15_19-21-23" in result.stdout
    assert "2026-06-14_16-58-25" in result.stdout


@pytest.mark.parametrize(
    "mutating", ["pickup", "release", "archive", "delete", "handoff"]
)
def test_directive_never_mutates_session_state(mutating, tmp_path):
    make_spec_tree(tmp_path)
    with fake_spx(todo=[_SESSION]) as spx:
        run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
        session_calls = spx.session_invocations()
    # The only `session` subcommand the hook issues is the read-only `todo`.
    assert all(argv[1] != mutating for argv in session_calls)
    assert all(argv[1] == "todo" for argv in session_calls)
