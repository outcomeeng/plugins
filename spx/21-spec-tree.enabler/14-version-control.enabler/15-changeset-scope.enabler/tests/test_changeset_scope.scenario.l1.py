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

import pytest
from outcomeeng_testing.harnesses.changeset_scope import (
    base_advanced_after_branch_repo,
    branch_collision_state,
    detach_head,
    generated_changeset_scope_cases,
    git_commit_oid,
    git_three_dot_scope,
    git_two_dot_scope,
    load_changeset_scope_module,
    repo_without_origin,
    stale_local_base_repo,
)


def test_detect_base_ref_returns_bare_base_from_origin_head() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            assert (
                load_changeset_scope_module().detect_base_ref(stale.repo)
                == stale.base_ref
            )


def test_detect_base_ref_raises_without_origin() -> None:
    for scenario in generated_changeset_scope_cases():
        with repo_without_origin(scenario) as repo:
            module = load_changeset_scope_module()
            with pytest.raises(module.BaseRefNotConfiguredError):
                module.detect_base_ref(repo)


def test_remote_tracking_ref_composes_origin_prefix() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            module = load_changeset_scope_module()
            assert module.remote_tracking_ref(stale.base_ref) == (
                module.ORIGIN_REF_PREFIX + stale.base_ref
            )


def test_branch_scope_returns_feature_change_against_remote_tracking_base() -> None:
    for scenario in generated_changeset_scope_cases():
        with base_advanced_after_branch_repo(scenario) as advanced:
            module = load_changeset_scope_module()
            files = module.branch_scope(advanced.base_ref, repo=advanced.repo)
            control = git_two_dot_scope(
                advanced.repo,
                module.remote_tracking_ref(advanced.base_ref),
            )
            assert advanced.base_file not in files
            assert advanced.feature_file in files
            assert advanced.base_file in control


def test_stale_local_base_ref_does_not_widen_scope() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            module = load_changeset_scope_module()
            remote_tracking_scope = module.branch_scope(stale.base_ref, repo=stale.repo)
            local_ref_scope = git_three_dot_scope(stale.repo, stale.base_ref)
            assert stale.merged_file not in remote_tracking_scope
            assert stale.feature_file in remote_tracking_scope
            assert stale.merged_file in local_ref_scope


def test_detect_current_branch_returns_name_then_raises_on_detached_head() -> None:
    for scenario in generated_changeset_scope_cases():
        with repo_without_origin(scenario) as repo:
            module = load_changeset_scope_module()
            assert module.detect_current_branch(repo) == scenario.base_branch
            detach_head(repo)
            with pytest.raises(module.DetachedHeadError):
                module.detect_current_branch(repo)


def test_commit_oid_resolves_commit_ref() -> None:
    for scenario in generated_changeset_scope_cases():
        with stale_local_base_repo(scenario) as stale:
            module = load_changeset_scope_module()
            base_ref = module.remote_tracking_ref(stale.base_ref)
            assert module.commit_oid(stale.feature_branch, repo=stale.repo) == (
                git_commit_oid(stale.repo, stale.feature_branch)
            )
            assert module.commit_oid(base_ref, repo=stale.repo) == git_commit_oid(
                stale.repo,
                base_ref,
            )


def test_branch_slug_disambiguates_on_state_dir_collision() -> None:
    for scenario in generated_changeset_scope_cases():
        with branch_collision_state(scenario) as collision:
            module = load_changeset_scope_module()
            base_slug = module.branch_slug(collision.feature_branch)
            collided = module.branch_slug(
                collision.feature_branch,
                collision.state_dir,
            )
            prefix = base_slug + module.BRANCH_SLUG_SUFFIX_SEPARATOR
            suffix = collided.removeprefix(prefix)
            assert collided != base_slug
            assert collided.startswith(prefix)
            assert len(suffix) == module.BRANCH_SLUG_COLLISION_SUFFIX_LENGTH
            assert (
                module.branch_slug(
                    collision.feature_branch,
                    collision.state_dir,
                )
                == collided
            )
            assert (
                module.branch_slug(
                    collision.feature_branch,
                    collision.empty_state_dir,
                )
                == base_slug
            )
