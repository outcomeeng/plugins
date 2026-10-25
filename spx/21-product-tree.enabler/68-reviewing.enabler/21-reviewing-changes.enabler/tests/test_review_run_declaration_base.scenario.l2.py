"""Scenario test for the declaration base in ``review_run.py``.

Covers the scenario in ``../reviewing-changes.md`` that governs where ``start`` reads
the generated-source declaration: from the file as it stands at the scope's base
commit. A declaration that differs at the head or in the working tree changes no run
exemption, so the run state lists the relations of the base declaration and none of
the edited declaration.

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
    nodes_mentioning,
    render_generated_sources,
    run_state_listing,
    start_changeset_review,
)


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
