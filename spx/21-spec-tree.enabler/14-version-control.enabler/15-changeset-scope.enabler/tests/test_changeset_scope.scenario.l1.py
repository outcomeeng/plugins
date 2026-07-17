"""Scenario tests for the changeset-scope git-derivation primitives.

Covers the Scenario assertions in ``../changeset-scope.md``:

- ``detect_base_ref`` returns the bare base-branch name from ``origin/HEAD`` and
  raises ``BaseRefNotConfiguredError`` when it is unset.
- ``remote_tracking_ref`` composes the remote-tracking ref ``origin/<base>``.
- ``branch_scope`` diffs the three-dot range ``origin/<base>...HEAD``.
- A local branch ref that lags its remote-tracking ref does not widen the
  scope: scoping against ``origin/<base>`` excludes commits already merged into
  the base, while scoping against the stale local ref re-includes them.
- ``detect_current_branch`` returns the branch name on a named checkout and
  raises ``DetachedHeadError`` on a detached HEAD.
- ``branch_slug`` appends the deterministic ``--<sha8>`` suffix when the state
  dir holds a state file (at the base-slug path) recording a different branch,
  and returns the bare base slug otherwise.

These are ``l1`` — direct in-process calls into ``changeset_scope`` against a
synthetic git repository owned by the changeset-scope harness; git and temp
dirs are expected on a working machine.
"""

from __future__ import annotations

import hashlib

import pytest

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    CHANGESET_SCOPE_CONTRACT,
    base_advanced_after_branch_repo,
    branch_collision_state,
    detach_head,
    generated_changeset_scope_cases,
    git_commit_oid,
    git_three_dot_scope,
    repo_without_origin,
    stale_local_base_repo,
)


def test_detect_base_ref_returns_bare_base_from_origin_head() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            assert CHANGESET_SCOPE.detect_base_ref(stale.repo) == stale.base_ref


def test_detect_base_ref_raises_without_origin() -> None:
    for scenario in generated_changeset_scope_cases():
        with repo_without_origin(scenario) as repo:
            with pytest.raises(CHANGESET_SCOPE.BaseRefNotConfiguredError):
                CHANGESET_SCOPE.detect_base_ref(repo)


def test_remote_tracking_ref_composes_origin_prefix() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            assert CHANGESET_SCOPE.remote_tracking_ref(stale.base_ref) == (
                CHANGESET_SCOPE_CONTRACT.ORIGIN_REF_PREFIX + stale.base_ref
            )


def test_branch_scope_returns_feature_change_against_remote_tracking_base() -> None:
    for scenario in generated_changeset_scope_cases():
        with base_advanced_after_branch_repo(scenario) as advanced:
            assert tuple(
                CHANGESET_SCOPE.branch_scope(
                    advanced.base_ref,
                    repo=advanced.repo,
                )
            ) == git_three_dot_scope(
                advanced.repo,
                CHANGESET_SCOPE_CONTRACT.ORIGIN_REF_PREFIX + advanced.base_ref,
            )


def test_stale_local_base_ref_does_not_widen_scope() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            assert tuple(
                CHANGESET_SCOPE.branch_scope(stale.base_ref, repo=stale.repo)
            ) == git_three_dot_scope(
                stale.repo,
                CHANGESET_SCOPE_CONTRACT.ORIGIN_REF_PREFIX + stale.base_ref,
            )
            assert git_three_dot_scope(stale.repo, stale.base_ref) == tuple(
                sorted((stale.feature_file, stale.merged_file))
            )


def test_detect_current_branch_returns_name_then_raises_on_detached_head() -> None:
    for scenario in generated_changeset_scope_cases():
        with repo_without_origin(scenario) as repo:
            assert CHANGESET_SCOPE.detect_current_branch(repo) == scenario.base_branch
            detach_head(repo)
            with pytest.raises(CHANGESET_SCOPE.DetachedHeadError):
                CHANGESET_SCOPE.detect_current_branch(repo)


def test_commit_oid_resolves_commit_ref() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            assert CHANGESET_SCOPE.commit_oid(
                stale.feature_branch,
                repo=stale.repo,
            ) == git_commit_oid(stale.repo, stale.feature_branch)
            assert CHANGESET_SCOPE.commit_oid(
                CHANGESET_SCOPE_CONTRACT.ORIGIN_REF_PREFIX + stale.base_ref,
                repo=stale.repo,
            ) == git_commit_oid(
                stale.repo,
                CHANGESET_SCOPE_CONTRACT.ORIGIN_REF_PREFIX + stale.base_ref,
            )


def test_branch_slug_disambiguates_on_state_dir_collision() -> None:
    for scenario in generated_changeset_scope_cases():
        with branch_collision_state(scenario) as collision:
            assert CHANGESET_SCOPE.branch_slug(collision.feature_branch) == (
                collision.feature_branch.replace(
                    CHANGESET_SCOPE_CONTRACT.BRANCH_REF_PATH_SEPARATOR,
                    CHANGESET_SCOPE_CONTRACT.BRANCH_SLUG_PATH_SUBSTITUTE,
                )
            )
            assert CHANGESET_SCOPE.branch_slug(
                collision.feature_branch,
                collision.state_dir,
            ) == (
                collision.feature_branch.replace(
                    CHANGESET_SCOPE_CONTRACT.BRANCH_REF_PATH_SEPARATOR,
                    CHANGESET_SCOPE_CONTRACT.BRANCH_SLUG_PATH_SUBSTITUTE,
                )
                + CHANGESET_SCOPE_CONTRACT.BRANCH_SLUG_SUFFIX_SEPARATOR
                + hashlib.sha256(collision.feature_branch.encode()).hexdigest()[
                    : CHANGESET_SCOPE_CONTRACT.BRANCH_SLUG_COLLISION_SUFFIX_LENGTH
                ]
            )
            assert CHANGESET_SCOPE.branch_slug(
                collision.feature_branch,
                collision.empty_state_dir,
            ) == collision.feature_branch.replace(
                CHANGESET_SCOPE_CONTRACT.BRANCH_REF_PATH_SEPARATOR,
                CHANGESET_SCOPE_CONTRACT.BRANCH_SLUG_PATH_SUBSTITUTE,
            )
