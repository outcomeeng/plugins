"""Compliance tests: neither the classifier nor sync-base carries the refusal.

Covers the Compliance assertions in ``../changeset-scope.md``: a branch behind
the fetched base still classifies to its changed paths, because
classification partitions paths rather than verifying them, and base
synchronization rebases that same head, because it is the remedy.

``l1``: the shipped classifier runs as a subprocess and the shipped
synchronizer in-process, each against a synthetic repository with a real
bare origin.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    MERGE_CLASSIFIER,
    base_advanced_after_branch_repo,
    generated_changeset_scope_cases,
    git_three_dot_scope,
    run_merge_classifier,
)
from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    load_sync_base_module,
    repository_root,
)


def test_the_classifier_resolves_a_behind_branch_without_refusing() -> None:
    for scenario in generated_changeset_scope_cases():
        with base_advanced_after_branch_repo(scenario) as advanced:
            result = run_merge_classifier(advanced.repo)

            assert result.returncode == 0
            assert frozenset(MERGE_CLASSIFIER.changed_paths(advanced.repo)) == (
                frozenset(
                    git_three_dot_scope(
                        advanced.repo,
                        CHANGESET_SCOPE.remote_tracking_ref(advanced.base_ref),
                    )
                )
            )


def test_base_synchronization_resolves_a_behind_branch_without_refusing(
    tmp_path: pathlib.Path,
) -> None:
    """The remedy runs on the very head the resolver refuses.

    Routing the synchronizer through the committed-scope resolver would
    raise the refusal here instead of rebasing.
    """
    module = load_sync_base_module()
    handle = build_behind_base_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.remote_ref
