"""Compliance evidence for the unread-scope rules of an agentic verification run.

``l1``: the shipped review runner (the agentic-run sealer) runs as a
subprocess against a synthetic repository, with the journal routed at the
fake ``spx`` the harness writes. Each test leaves one unit of the run's scope
without a scope-advanced event, which is the run's record of an unread unit.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    init_repo_with_branch,
    run_script,
    runner_env,
)

jp = load_journal_projection_module()


def _finish_run_with_unread_unit(tmp_path: pathlib.Path) -> tuple[str, list[dict]]:
    """Start a run, advance no scope unit, finish it; return the unit and events."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_ref = init_repo_with_branch(repo)
    env, journal_path = runner_env(tmp_path, repo, base_ref)

    started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
    assert started.returncode == 0, started.stderr
    state = json.loads(started.stdout)
    unread_units = json.loads(
        pathlib.Path(state["statePath"]).read_text(encoding="utf-8")
    )["metadata"]["scope"]["changedFiles"]
    assert unread_units

    run_script(
        REVIEW_RUN_SCRIPT, "finish", "--state", state["statePath"], env=env, cwd=repo
    )

    events = json.loads(journal_path.read_text(encoding="utf-8"))["events"]
    return unread_units[0], events


def test_a_run_finished_with_an_unread_unit_seals_failed_and_lists_the_unit(
    tmp_path: pathlib.Path,
) -> None:
    """The terminal event of such a run carries the failed status and the unit.

    A runner that finishes without sealing, or seals with any other status,
    or omits the unread unit from the terminal event, fails this check.
    """
    unread_unit, events = _finish_run_with_unread_unit(tmp_path)

    terminal = events[-1]
    assert terminal["type"] == jp.RUN_COMPLETED
    assert terminal["data"][jp.RUN_STATE_STATUS] == str(jp.JournalRunStatus.FAILED)
    assert unread_unit in json.dumps(terminal["data"])


def test_a_run_never_seals_approved_while_a_unit_of_its_scope_is_unread(
    tmp_path: pathlib.Path,
) -> None:
    """No terminal event of a run with an unread unit carries the approved status.

    A runner that rolls up only the findings, which are absent here, seals
    such a run approved and fails this check.
    """
    _unread_unit, events = _finish_run_with_unread_unit(tmp_path)

    terminal_events = [event for event in events if event["type"] == jp.RUN_COMPLETED]
    assert terminal_events
    for event in terminal_events:
        assert event["data"][jp.RUN_STATE_STATUS] != str(jp.JournalRunStatus.APPROVED)
