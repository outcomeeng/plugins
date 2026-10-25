"""Scenario test for ``review_run.py finish --unread-file``.

Given a file that lists one changed path per line, ``finish --unread-file`` marks each
listed path as unread exactly as one ``--unread`` argument per path does. The test
finishes the same changeset once per channel and compares the two runs. It is ``l2``
because it spawns ``git`` and the runner against synthetic git repositories under
``tmp_path``.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.generators.reviewing_changes_runs import unread_set_case
from outcomeeng_testing.harnesses.reviewing_changes_runs import (
    UnreadChannel,
    build_changeset_repo,
    completed_unread,
    finish_changeset_review,
    jp,
    review_run,
    run_completed_event,
    scope_advanced_units,
    start_changeset_review,
)


def test_unread_file_marks_each_listed_path_exactly_as_unread_arguments_do(
    tmp_path: pathlib.Path,
) -> None:
    case = unread_set_case()
    repo = tmp_path / "repo"
    base_ref = build_changeset_repo(
        repo, declaration=None, changed_paths=[*case.unread, case.read]
    )

    by_arguments = finish_changeset_review(
        start_changeset_review(tmp_path / "arguments-run", repo, base_ref),
        scope=[case.read],
        unread=case.unread,
        channel=UnreadChannel.ARGUMENTS,
    )
    by_file = finish_changeset_review(
        start_changeset_review(tmp_path / "file-run", repo, base_ref),
        scope=[case.read],
        unread=case.unread,
        channel=UnreadChannel.FILE,
    )

    assert by_arguments.finished.returncode == 0, by_arguments.finished.stderr
    assert by_file.finished.returncode == 0, by_file.finished.stderr
    arguments_completed = run_completed_event(by_arguments.events)
    file_completed = run_completed_event(by_file.events)
    assert completed_unread(file_completed) == sorted(case.unread)
    assert completed_unread(file_completed) == completed_unread(arguments_completed)
    assert (
        file_completed[jp.EVENT_DATA_FIELD][review_run.REVIEW_KEY]
        == arguments_completed[jp.EVENT_DATA_FIELD][review_run.REVIEW_KEY]
    )
    assert file_completed[jp.EVENT_DATA_FIELD][jp.RUN_STATE_STATUS] == str(
        jp.JournalRunStatus.FAILED
    )
    assert scope_advanced_units(by_file.events) == [case.read]
