"""Scenario test for a changed declaration in ``review_run.py``.

Covers the scenario in ``../reviewing-changes.md`` that governs a changeset whose
changed paths include the generated-source declaration itself:

1. ``start`` flags every listed relation with the changed declaration as the reason
   and reports the declaration as changed in the run state.
2. ``finish`` exempts no changed file by declaration: it names the unexamined extents
   when they lack a scope-advanced event or an unread mark, and when every changed
   file is examined it carries the declaration's repository-relative path as the
   changed declaration on the run-completed event and lists no skipped generated
   file.

The test is ``l2`` because it spawns ``git`` and the runner against synthetic git
repositories under ``tmp_path``. The runner's field names for extents are its own, so
the predicates locate the smallest JSON objects that carry the values under judgment.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.generators.reviewing_changes_runs import (
    single_relation_case,
)
from outcomeeng_testing.harnesses.reviewing_changes_runs import (
    COMPLETED_REVIEW_KEY,
    DECLARATION_CHANGED_KEY,
    GENERATED_SOURCES_PATH,
    SKIPPED_GENERATED_KEY,
    build_changeset_repo,
    edited_declaration,
    finish_changeset_review,
    nodes_mentioning,
    render_generated_sources,
    run_completed_event,
    run_state_listing,
    start_changeset_review,
)

DECLARATION = str(GENERATED_SOURCES_PATH)


class TestChangedDeclarationScenarios:
    def test_start_flags_every_relation_with_the_changed_declaration(
        self, tmp_path: pathlib.Path
    ) -> None:
        case = single_relation_case()
        declaration = render_generated_sources(case.relations)
        changed = [path for path, _ in case.extents] + list(case.ordinary)

        changed_repo = tmp_path / "changed-repo"
        changed_base = build_changeset_repo(
            changed_repo,
            declaration=declaration,
            changed_paths=changed,
            head_declaration=edited_declaration(declaration),
        )
        changed_run = start_changeset_review(
            tmp_path / "changed-run", changed_repo, changed_base
        )

        control_repo = tmp_path / "control-repo"
        control_base = build_changeset_repo(
            control_repo, declaration=declaration, changed_paths=changed
        )
        control_run = start_changeset_review(
            tmp_path / "control-run", control_repo, control_base
        )

        assert DECLARATION in changed_run.start_payload["changedFiles"]
        assert changed_run.start_payload[DECLARATION_CHANGED_KEY] is True
        assert control_run.start_payload[DECLARATION_CHANGED_KEY] is False
        for relation in case.relations:
            assert nodes_mentioning(
                run_state_listing(changed_run), relation.regenerate, DECLARATION
            ), relation.regenerate
            assert not nodes_mentioning(
                run_state_listing(control_run), relation.regenerate, DECLARATION
            ), relation.regenerate

    def test_finish_exempts_no_file_and_names_the_changed_declaration(
        self, tmp_path: pathlib.Path
    ) -> None:
        case = single_relation_case()
        extent_paths = [path for path, _ in case.extents]
        declaration = render_generated_sources(case.relations)
        repo = tmp_path / "repo"
        base_ref = build_changeset_repo(
            repo,
            declaration=declaration,
            changed_paths=[*extent_paths, *case.ordinary],
            head_declaration=edited_declaration(declaration),
        )
        started = start_changeset_review(tmp_path / "run", repo, base_ref)

        unexamined = finish_changeset_review(
            started, scope=[*case.ordinary, DECLARATION]
        )

        assert unexamined.finished.returncode != 0
        for path in extent_paths:
            assert path in unexamined.finished.stderr

        examined_run = start_changeset_review(tmp_path / "examined-run", repo, base_ref)
        examined = finish_changeset_review(
            examined_run, scope=examined_run.start_payload["changedFiles"]
        )

        assert examined.finished.returncode == 0, examined.finished.stderr
        review = run_completed_event(examined.events)["data"][COMPLETED_REVIEW_KEY]
        assert review[DECLARATION_CHANGED_KEY] == DECLARATION
        assert not review.get(SKIPPED_GENERATED_KEY)

        control_repo = tmp_path / "control-repo"
        control_base = build_changeset_repo(
            control_repo,
            declaration=declaration,
            changed_paths=[*extent_paths, *case.ordinary],
        )
        control_run = start_changeset_review(
            tmp_path / "control-run", control_repo, control_base
        )
        control = finish_changeset_review(control_run, scope=case.ordinary)

        assert control.finished.returncode == 0, control.finished.stderr
        control_review = run_completed_event(control.events)["data"][
            COMPLETED_REVIEW_KEY
        ]
        assert not control_review.get(DECLARATION_CHANGED_KEY)
        assert control_review[SKIPPED_GENERATED_KEY]
