"""Scenario test for the declaration base in ``review_run.py``.

Covers the scenario in ``../reviewing-changes.md`` that governs where ``start`` reads
the generated-source declaration: from the file as it stands at the scope's base
commit, so the run state lists the relations of the base declaration and none of the
edited declaration. Two cases compose that claim with the changed-declaration scenario:

1. A declaration edited only in the working tree is not a changed path, so the run
   exemption holds: ``start`` reports the declaration as unchanged and ``finish`` skips
   the extent of the base relation by declaration.
2. A declaration edited at the head commit is itself a changed path, so exemption
   defers to the changed-declaration scenario: ``start`` reports the declaration as
   changed and flags every listed relation with it as the reason, and ``finish`` skips
   no file by declaration, naming the extents of the base relation among the
   unexamined files.

The test is ``l2`` because it spawns ``git`` and the runner against synthetic git
repositories under ``tmp_path``. The runner's field names for extents are its own, so
the predicates locate the smallest JSON objects that carry the values under judgment.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.generators.reviewing_changes_runs import (
    EditSite,
    declaration_edit_cases,
)
from outcomeeng_testing.harnesses.reviewing_changes_runs import (
    COMPLETED_REVIEW_KEY,
    DECLARATION_CHANGED_KEY,
    GENERATED_SOURCES_PATH,
    SKIPPED_GENERATED_KEY,
    build_changeset_repo,
    finish_changeset_review,
    nodes_mentioning,
    render_generated_sources,
    run_completed_event,
    run_state_listing,
    start_changeset_review,
)

DECLARATION = str(GENERATED_SOURCES_PATH)


class TestDeclarationBaseScenarios:
    def test_start_reads_the_declaration_at_the_base_commit(
        self, tmp_path: pathlib.Path
    ) -> None:
        for index, case in enumerate(declaration_edit_cases()):
            edited = render_generated_sources([case.edited_relation])
            repo = tmp_path / f"repo-{index}"
            base_ref = build_changeset_repo(
                repo,
                declaration=render_generated_sources([case.base_relation]),
                changed_paths=[case.base_extent, case.edited_extent],
                head_declaration=edited if case.site is EditSite.HEAD else None,
                working_tree_declaration=(
                    edited if case.site is EditSite.WORKING_TREE else None
                ),
            )

            started = start_changeset_review(tmp_path / f"run-{index}", repo, base_ref)
            listing = run_state_listing(started)

            assert nodes_mentioning(
                listing, case.base_relation.regenerate, case.base_extent
            ), case.site
            assert not nodes_mentioning(listing, case.edited_relation.regenerate), (
                case.site
            )
            assert not nodes_mentioning(listing, case.edited_extent), case.site

    def test_working_tree_edit_is_no_changed_path_and_the_exemption_holds(
        self, tmp_path: pathlib.Path
    ) -> None:
        for index, case in enumerate(declaration_edit_cases()):
            if case.site is not EditSite.WORKING_TREE:
                continue
            repo = tmp_path / f"repo-{index}"
            base_ref = build_changeset_repo(
                repo,
                declaration=render_generated_sources([case.base_relation]),
                changed_paths=[case.base_extent, case.edited_extent],
                working_tree_declaration=render_generated_sources(
                    [case.edited_relation]
                ),
            )
            started = start_changeset_review(tmp_path / f"run-{index}", repo, base_ref)

            finished = finish_changeset_review(started, scope=[case.edited_extent])

            assert DECLARATION not in started.start_payload["changedFiles"]
            assert started.start_payload[DECLARATION_CHANGED_KEY] is False
            assert not nodes_mentioning(
                run_state_listing(started), case.base_relation.regenerate, DECLARATION
            )
            assert finished.finished.returncode == 0, finished.finished.stderr
            review = run_completed_event(finished.events)["data"][COMPLETED_REVIEW_KEY]
            assert not review.get(DECLARATION_CHANGED_KEY)
            assert nodes_mentioning(
                review[SKIPPED_GENERATED_KEY],
                case.base_relation.regenerate,
                case.base_extent,
            )
            assert not nodes_mentioning(
                review[SKIPPED_GENERATED_KEY], case.edited_extent
            )

    def test_head_edit_is_a_changed_path_and_defers_exemption_to_the_changed_declaration(
        self, tmp_path: pathlib.Path
    ) -> None:
        for index, case in enumerate(declaration_edit_cases()):
            if case.site is not EditSite.HEAD:
                continue
            repo = tmp_path / f"repo-{index}"
            base_ref = build_changeset_repo(
                repo,
                declaration=render_generated_sources([case.base_relation]),
                changed_paths=[case.base_extent, case.edited_extent],
                head_declaration=render_generated_sources([case.edited_relation]),
            )
            started = start_changeset_review(tmp_path / f"run-{index}", repo, base_ref)
            listing = run_state_listing(started)

            assert DECLARATION in started.start_payload["changedFiles"]
            assert started.start_payload[DECLARATION_CHANGED_KEY] is True
            assert nodes_mentioning(
                listing, case.base_relation.regenerate, DECLARATION
            ), case.site
            assert not nodes_mentioning(listing, case.edited_relation.regenerate), (
                case.site
            )

            unexamined = finish_changeset_review(started, scope=[DECLARATION])

            assert unexamined.finished.returncode != 0
            assert case.base_extent in unexamined.finished.stderr
            assert case.edited_extent in unexamined.finished.stderr

            examined_run = start_changeset_review(
                tmp_path / f"examined-run-{index}", repo, base_ref
            )
            examined = finish_changeset_review(
                examined_run, scope=examined_run.start_payload["changedFiles"]
            )

            assert examined.finished.returncode == 0, examined.finished.stderr
            review = run_completed_event(examined.events)["data"][COMPLETED_REVIEW_KEY]
            assert review[DECLARATION_CHANGED_KEY] == DECLARATION
            assert not review.get(SKIPPED_GENERATED_KEY)
