"""Mapping tests for 21-queued-work-discoverability.enabler (queued-work-discoverability.md mapping).

L1: the real `session-start.py` hook is run as a subprocess against a fake `spx`
CLI in a temp directory, with no test doubles.

Assertion covered:
  - The `spx session todo` projection maps to the directive output: a non-empty
    `todo` set maps to a directive surfacing each session's id, goal, and next
    step; an empty set maps to no directive.
"""

import pytest

from outcomeeng_testing.harnesses.hooks import make_spec_tree, run_session_start
from outcomeeng_testing.harnesses.spx_cli import fake_spx, sample_todo_session

SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

_SESSION = sample_todo_session()


@pytest.mark.parametrize("has_queue", [True, False])
def test_queue_presence_maps_to_directive(has_queue, tmp_path):
    make_spec_tree(tmp_path)
    todo = [_SESSION] if has_queue else []
    with fake_spx(todo=todo) as spx:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(tmp_path)},
            env_file=tmp_path / "claude.env",
            project_dir=tmp_path,
            env_overrides=spx.env,
        )
    assert result.returncode == 0
    # Directive tokens asserted inline; source-ownership tracked cross-hook in
    # spx/21-spec-tree.enabler/ISSUES.md item 20. Each of the three fields the
    # mapping assertion names — id, goal, next step — maps to the directive.
    assert ("/spec-tree:pickup" in result.stdout) is has_queue
    assert (_SESSION["id"] in result.stdout) is has_queue
    assert (_SESSION["goal"] in result.stdout) is has_queue
    assert (_SESSION["next_step"] in result.stdout) is has_queue
