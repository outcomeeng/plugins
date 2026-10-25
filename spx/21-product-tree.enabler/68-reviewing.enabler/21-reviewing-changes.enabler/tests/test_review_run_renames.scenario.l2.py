"""Scenario tests for renamed files in ``review_run.py``.

Covers the scenarios in ``../reviewing-changes.md`` that govern renames:

1. A rename with unchanged content lists the file once under its new path with its former
   path recorded; ``finish`` records it as renamed without content change and needs
   neither a scope-advanced event nor an unread mark for it.
2. A rename with content changes needs a scope-advanced event or an unread mark under the
   new path, exactly as any other changed file.

The tests are ``l2`` because they spawn ``git`` and the runner against synthetic git
repositories under ``tmp_path``.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.generators.reviewing_changes_runs import (
    modified_rename_case,
    pure_rename_case,
)
from outcomeeng_testing.harnesses.reviewing_changes_runs import (
    build_changeset_repo,
    completed_unread,
    finish_changeset_review,
    jp,
    nodes_mentioning,
    run_completed_event,
    run_state_listing,
    scope_advanced_units,
    start_changeset_review,
)


class TestRenameScenarios:
    def test_pure_rename_is_listed_once_and_needs_no_review_event(
        self, tmp_path: pathlib.Path
    ) -> None:
        case = pure_rename_case()
        repo = tmp_path / "repo"
        base_ref = build_changeset_repo(
            repo, declaration=None, changed_paths=[case.companion_path], rename=case
        )
        started = start_changeset_review(tmp_path / "run", repo, base_ref)

        changed = started.start_payload["changedFiles"]
        assert sorted(changed) == sorted([case.new_path, case.companion_path])
        assert changed.count(case.new_path) == 1
        assert nodes_mentioning(
            [started.manifest, run_state_listing(started)],
            case.new_path,
            case.old_path,
        )

        finished = finish_changeset_review(started, scope=[case.companion_path])

        assert finished.finished.returncode == 0, finished.finished.stderr
        completed = run_completed_event(finished.events)
        advanced = scope_advanced_units(finished.events)
        for path in (case.new_path, case.old_path):
            assert path not in advanced
            assert path not in completed_unread(completed)
        assert nodes_mentioning(completed, case.new_path)
        assert completed["data"]["status"] == str(jp.JournalRunStatus.APPROVED)

    def test_rename_with_content_changes_needs_scope_or_unread_mark(
        self, tmp_path: pathlib.Path
    ) -> None:
        case = modified_rename_case()
        repo = tmp_path / "repo"
        base_ref = build_changeset_repo(
            repo, declaration=None, changed_paths=[case.companion_path], rename=case
        )

        unexamined = finish_changeset_review(
            start_changeset_review(tmp_path / "unexamined-run", repo, base_ref),
            scope=[case.companion_path],
        )
        assert unexamined.finished.returncode != 0
        assert case.new_path in unexamined.finished.stderr
        assert case.old_path not in unexamined.finished.stderr

        scoped = finish_changeset_review(
            start_changeset_review(tmp_path / "scoped-run", repo, base_ref),
            scope=[case.companion_path, case.new_path],
        )
        assert scoped.finished.returncode == 0, scoped.finished.stderr
        assert case.new_path in scope_advanced_units(scoped.events)
        assert case.old_path not in scope_advanced_units(scoped.events)

        marked = finish_changeset_review(
            start_changeset_review(tmp_path / "unread-run", repo, base_ref),
            scope=[case.companion_path],
            unread=[case.new_path],
        )
        assert marked.finished.returncode == 0, marked.finished.stderr
        assert completed_unread(run_completed_event(marked.events)) == [case.new_path]
