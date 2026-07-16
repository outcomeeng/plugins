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

import subprocess

import pytest
from outcomeeng_testing.harnesses.changeset_scope import (
    STALE_BASE_SCENARIO,
    build_repo_without_origin,
    build_stale_local_base_repo,
    detach_head,
    load_changeset_scope_module,
    temporary_changeset_scope,
    write_branch_state_file,
)


def test_detect_base_ref_returns_bare_base_from_origin_head() -> None:
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        stale = build_stale_local_base_repo(paths.repo)
        assert module.detect_base_ref(stale.repo) == stale.base_ref


def test_detect_base_ref_raises_without_origin() -> None:
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        build_repo_without_origin(paths.repo)
        with pytest.raises(module.BaseRefNotConfiguredError):
            module.detect_base_ref(paths.repo)


def test_remote_tracking_ref_composes_origin_prefix() -> None:
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        stale = build_stale_local_base_repo(paths.repo)
        assert (
            module.remote_tracking_ref(stale.base_ref)
            == f"{module.ORIGIN_REF_PREFIX}{stale.base_ref}"
        )


def test_branch_scope_returns_feature_change_against_remote_tracking_base() -> None:
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        stale = build_stale_local_base_repo(paths.repo)
        files = module.branch_scope(stale.base_ref, repo=stale.repo)
        assert stale.feature_file in files


def test_stale_local_base_ref_does_not_widen_scope() -> None:
    # The crux: the feature branch contains a commit already merged into
    # origin/<base>, while the local base ref lags behind it. Scoping against
    # the remote-tracking ref (what branch_scope composes via remote_tracking_ref)
    # excludes the merged commit; scoping against the stale local ref re-includes
    # it. Asserting both directions makes the test falsifying — it fails if
    # branch_scope ever scopes against the bare local ref.
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        stale = build_stale_local_base_repo(paths.repo)

        remote_tracking_scope = module.branch_scope(stale.base_ref, repo=stale.repo)
        assert stale.merged_file not in remote_tracking_scope
        assert stale.feature_file in remote_tracking_scope

        # Control: diffing against the stale local base ref widens the scope to
        # re-include the already-merged commit — the defect remote-tracking scoping
        # avoids.
        local_ref_scope = module.expand_diff_range(
            f"{stale.base_ref}...HEAD", repo=stale.repo
        )
        assert stale.merged_file in local_ref_scope


def test_detect_current_branch_returns_name_then_raises_on_detached_head() -> None:
    # Two arms make the test falsifying: a named checkout yields the branch
    # name, and a detached HEAD raises rather than returning the "HEAD"
    # placeholder that would collide across every detached-checkout invocation.
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        branch = build_repo_without_origin(paths.repo)

        assert module.detect_current_branch(paths.repo) == branch

        detach_head(paths.repo)
        with pytest.raises(module.DetachedHeadError):
            module.detect_current_branch(paths.repo)


def test_commit_oid_resolves_commit_ref() -> None:
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        stale = build_stale_local_base_repo(paths.repo)

        head_oid = module.commit_oid(stale.feature_branch, repo=stale.repo)
        base_oid = module.commit_oid(
            module.remote_tracking_ref(stale.base_ref), repo=stale.repo
        )

        assert len(head_oid) == 40
        assert all(char in "0123456789abcdef" for char in head_oid)
        assert base_oid != head_oid
        subprocess.run(
            ["git", "cat-file", "-e", f"{head_oid}^{{commit}}"],
            cwd=stale.repo,
            check=True,
        )


def test_branch_slug_disambiguates_on_state_dir_collision() -> None:
    # branch_slug appends a deterministic --<sha8> suffix when the state dir
    # already holds a state file (at the base-slug path) recording a different
    # branch; with no such file it returns the bare base slug. Asserting both
    # arms makes the test falsifying — it fails if the collision check is
    # dropped, because the collided slug would then equal the base slug.
    with temporary_changeset_scope() as paths:
        module = load_changeset_scope_module()
        base_slug = module.branch_slug(STALE_BASE_SCENARIO.feature_branch)

        write_branch_state_file(
            paths.repo,
            base_slug,
            STALE_BASE_SCENARIO.base_branch,
        )
        collided = module.branch_slug(
            STALE_BASE_SCENARIO.feature_branch,
            paths.repo,
        )

        assert collided != base_slug
        assert collided.startswith(f"{base_slug}--")
        suffix = collided[len(base_slug) + len("--") :]
        assert len(suffix) == module.BRANCH_SLUG_COLLISION_SUFFIX_LENGTH
        # Deterministic: the same inputs land on the same slug across invocations.
        assert (
            module.branch_slug(STALE_BASE_SCENARIO.feature_branch, paths.repo)
            == collided
        )
        # No state file at the base-slug path → no disambiguation.
        assert (
            module.branch_slug(
                STALE_BASE_SCENARIO.feature_branch,
                paths.empty_state_dir,
            )
            == base_slug
        )
