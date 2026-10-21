"""Compliance evidence for the branch identity a review run records.

``l2``: the shipped review runner runs as a subprocess against a synthetic
repository, with the journal routed at the fake ``spx`` the harness writes.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    BranchExport,
    start_review_run_exporting,
)

jp = load_journal_projection_module()


def test_a_branch_value_naming_a_commit_records_the_checked_out_branch_and_its_slug(
    tmp_path: pathlib.Path,
) -> None:
    """A commit-range input's commit value never becomes the identity or slug.

    A runner that records the exported commit as the branch identity, or
    derives the slug from it, fails this check.
    """
    committed = start_review_run_exporting(
        tmp_path / "commit", BranchExport.HEAD_COMMIT
    )
    reference = start_review_run_exporting(
        tmp_path / "branch", BranchExport.CHECKED_OUT_BRANCH
    )

    assert committed.exported == committed.head_commit
    assert committed.metadata[jp.RUN_STATE_BRANCH_NAME] == committed.checked_out_branch
    assert (
        committed.metadata[jp.RUN_STATE_BRANCH_SLUG]
        == reference.metadata[jp.RUN_STATE_BRANCH_SLUG]
    )


def test_a_branch_value_naming_a_branch_is_recorded_as_the_identity(
    tmp_path: pathlib.Path,
) -> None:
    """The commit rule leaves a branch value alone.

    The exported value names an existing branch that is not the checked-out
    branch, so a runner that discards every exported value in favor of the
    checked-out branch fails this check.
    """
    exported = start_review_run_exporting(
        tmp_path / "branch", BranchExport.OTHER_BRANCH
    )

    assert exported.exported != exported.checked_out_branch
    assert exported.metadata[jp.RUN_STATE_BRANCH_NAME] == exported.exported
