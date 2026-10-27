"""Scenario test for the declaration base in ``review_run.py``.

Covers the scenario in ``../reviewing-changes.md`` that governs where ``start`` reads
the generated-source declaration: from the file as it stands at the scope's base
commit, so the run state lists the relations of the base declaration and none of the
edited declaration, whether the edit sits at the head commit or in the working tree.
The review input carries the working tree's unstaged changes beside the committed
ones, so a declaration edited at either site is itself a changed path, and exemption
defers to the changed-declaration scenario: ``start`` reports the declaration as
changed and flags every listed relation with it as the reason, and ``finish`` skips no
file by declaration, naming the extents of the base relation among the unexamined
files.

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
    build_changeset_repo,
    compute_diff,
    finish_changeset_review,
    jp,
    nodes_mentioning,
    render_generated_sources,
    review_run,
    run_completed_event,
    run_state_listing,
    start_changeset_review,
)

DECLARATION = str(compute_diff.GENERATED_SOURCES_PATH)


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

    def test_an_edit_at_either_site_is_a_changed_path_and_defers_exemption_to_the_changed_declaration(
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

            assert DECLARATION in started.start_payload["changedFiles"], case.site
            assert started.start_payload[review_run.DECLARATION_CHANGED_KEY] is True, (
                case.site
            )
            assert nodes_mentioning(
                listing, case.base_relation.regenerate, DECLARATION
            ), case.site
            assert not nodes_mentioning(listing, case.edited_relation.regenerate), (
                case.site
            )

            unexamined = finish_changeset_review(started, scope=[DECLARATION])

            assert unexamined.finished.returncode != 0, case.site
            assert case.base_extent in unexamined.finished.stderr, case.site
            assert case.edited_extent in unexamined.finished.stderr, case.site

            examined_run = start_changeset_review(
                tmp_path / f"examined-run-{index}", repo, base_ref
            )
            examined = finish_changeset_review(
                examined_run, scope=examined_run.start_payload["changedFiles"]
            )

            assert examined.finished.returncode == 0, examined.finished.stderr
            review = run_completed_event(examined.events)[jp.EVENT_DATA_FIELD][
                review_run.REVIEW_KEY
            ]
            assert review[review_run.DECLARATION_CHANGED_KEY] == DECLARATION, case.site
            assert not review.get(review_run.REVIEW_SKIPPED_GENERATED), case.site
