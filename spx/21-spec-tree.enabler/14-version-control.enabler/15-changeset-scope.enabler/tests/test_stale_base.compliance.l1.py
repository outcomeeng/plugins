"""Compliance test: the merge classifier never carries the stale-base refusal.

Covers the Compliance assertion in ``../changeset-scope.md``: a branch behind
the fetched base still classifies to its changed paths, because
classification partitions paths rather than verifying them.

``l1``: the shipped classifier runs as a subprocess against a synthetic
repository with a real bare origin.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    MERGE_CLASSIFIER,
    base_advanced_after_branch_repo,
    generated_changeset_scope_cases,
    git_three_dot_scope,
    run_merge_classifier,
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
