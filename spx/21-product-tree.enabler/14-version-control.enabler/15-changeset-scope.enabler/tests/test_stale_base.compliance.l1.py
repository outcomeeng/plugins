"""Compliance tests: neither the classifier nor sync-base carries the refusal.

Covers the Compliance assertions in ``../changeset-scope.md``: a head is fixed to a
commit id before any fetch moves ``FETCH_HEAD`` or a remote-tracking ref; a branch behind
the fetched base still classifies to its changed paths, because
classification partitions paths rather than verifying them, and base
synchronization rebases that same head, because it is the remedy.

``l1``: the shipped classifier runs as a subprocess and the shipped
synchronizer in-process, each against a synthetic repository with a real
bare origin.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    FETCH_HEAD_REF,
    MERGE_CLASSIFIER,
    base_advanced_after_branch_repo,
    fetch_head_feature_repo,
    generated_changeset_scope_cases,
    git_commit_oid,
    git_three_dot_scope,
    lagging_remote_tracking_repo,
    run_changeset_scope,
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


def test_a_fetch_that_rewrites_fetch_head_moves_no_head() -> None:
    for scenario in generated_changeset_scope_cases():
        with fetch_head_feature_repo(scenario) as fetched:
            selector = (
                f"{CHANGESET_SCOPE.remote_tracking_ref(fetched.base_ref)}"
                f"{CHANGESET_SCOPE.RANGE_SEPARATOR}{FETCH_HEAD_REF}"
            )

            result = run_changeset_scope(fetched.repo, selector)

            assert git_commit_oid(fetched.repo, FETCH_HEAD_REF) == fetched.base_oid
            assert result.returncode == 0
            resolved = json.loads(result.stdout)
            assert resolved[CHANGESET_SCOPE.ScopeField.HEAD] == fetched.feature_oid
            assert resolved[CHANGESET_SCOPE.ScopeField.CHANGED_PATHS] == [
                fetched.feature_file
            ]


def test_a_fetch_that_advances_a_remote_tracking_head_moves_no_head() -> None:
    for scenario in generated_changeset_scope_cases():
        with lagging_remote_tracking_repo(scenario) as lagging:
            tracking_ref = CHANGESET_SCOPE.remote_tracking_ref(lagging.base_ref)
            head_before_fetch = git_commit_oid(lagging.repo, tracking_ref)
            selector = f"{tracking_ref}{CHANGESET_SCOPE.RANGE_SEPARATOR}{tracking_ref}"

            result = run_changeset_scope(lagging.repo, selector)

            assert git_commit_oid(lagging.repo, tracking_ref) != head_before_fetch
            assert result.returncode == CHANGESET_SCOPE.EXIT_STALE_BASE
            diagnostic = json.loads(result.stderr.strip().splitlines()[-1])
            assert (
                diagnostic[CHANGESET_SCOPE.StaleBaseField.MERGE_BASE]
                == head_before_fetch
            )
