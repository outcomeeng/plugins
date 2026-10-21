"""Compliance evidence for the unread-scope rules of an agentic verification run.

``l1``: the shipped review runner (the agentic-run sealer) runs as a
subprocess against a synthetic repository, with the journal routed at the
fake ``spx`` the harness writes. Each test leaves the run's changed files without
scope-advanced events and either marks them unread at finish or marks nothing.
"""

from __future__ import annotations

import json
import pathlib
from typing import NamedTuple

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


class _StartedRun(NamedTuple):
    """A started run: the scope's changed files and what a finish needs."""

    changed_files: list[str]
    state_path: str
    env: dict[str, str]
    journal_path: pathlib.Path
    repo: pathlib.Path


def _start_run(tmp_path: pathlib.Path) -> _StartedRun:
    """Start a run over a synthetic repository and advance no scope unit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    base_ref = init_repo_with_branch(repo)
    env, journal_path = runner_env(tmp_path, repo, base_ref)

    started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
    assert started.returncode == 0, started.stderr
    state_path = json.loads(started.stdout)["statePath"]
    changed_files = json.loads(pathlib.Path(state_path).read_text(encoding="utf-8"))[
        "metadata"
    ]["scope"]["changedFiles"]
    assert changed_files
    return _StartedRun(changed_files, state_path, env, journal_path, repo)


def _events(run: _StartedRun) -> list[dict]:
    return json.loads(run.journal_path.read_text(encoding="utf-8"))["events"]


def _finish_run_marking_unread(tmp_path: pathlib.Path) -> tuple[list[str], list[dict]]:
    """Finish a run with each changed file passed once as ``--unread``."""
    run = _start_run(tmp_path)
    unread_args = [arg for unit in run.changed_files for arg in ("--unread", unit)]
    finished = run_script(
        REVIEW_RUN_SCRIPT,
        "finish",
        "--state",
        run.state_path,
        *unread_args,
        env=run.env,
        cwd=run.repo,
    )
    assert finished.returncode == 0, finished.stderr
    return run.changed_files, _events(run)


def test_a_run_finished_with_an_unread_unit_seals_failed_and_lists_the_unit(
    tmp_path: pathlib.Path,
) -> None:
    """The terminal event of such a run carries the failed status and each unit.

    A runner that finishes without sealing, or seals with any other status,
    or omits an unread unit from the terminal event, fails this check.
    """
    unread_units, events = _finish_run_marking_unread(tmp_path)

    terminal = events[-1]
    assert terminal["type"] == jp.RUN_COMPLETED
    assert terminal["data"][jp.RUN_STATE_STATUS] == str(jp.JournalRunStatus.FAILED)
    for unit in unread_units:
        assert unit in json.dumps(terminal["data"])


def test_a_run_never_seals_approved_while_a_unit_of_its_scope_is_unread(
    tmp_path: pathlib.Path,
) -> None:
    """No terminal event of a run with an unread-marked unit carries approved.

    A runner that rolls up only the findings, which are absent here, seals
    such a run approved and fails this check.
    """
    _unread_units, events = _finish_run_marking_unread(tmp_path)

    terminal_events = [event for event in events if event["type"] == jp.RUN_COMPLETED]
    assert terminal_events
    for event in terminal_events:
        assert event["data"][jp.RUN_STATE_STATUS] != str(jp.JournalRunStatus.APPROVED)


def test_a_finish_with_a_unit_neither_advanced_nor_marked_unread_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """Such a finish exits nonzero and appends no terminal event.

    A runner that seals a run whose scope holds a unit with neither a
    scope-advanced event nor an unread mark fails this check.
    """
    run = _start_run(tmp_path)

    finished = run_script(
        REVIEW_RUN_SCRIPT,
        "finish",
        "--state",
        run.state_path,
        env=run.env,
        cwd=run.repo,
    )

    assert finished.returncode != 0
    assert all(event["type"] != jp.RUN_COMPLETED for event in _events(run))
