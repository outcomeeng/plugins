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

from outcomeeng_testing.harnesses.changeset_scope import (
    assert_branch_scope_uses_merge_base,
    assert_branch_slug_disambiguates_state_collision,
    assert_commit_oid_resolves_exact_ref,
    assert_detect_base_ref_raises_without_origin,
    assert_detect_base_ref_returns_bare_base_from_origin_head,
    assert_detect_current_branch_named_and_detached,
    assert_remote_tracking_ref_composes_origin_prefix,
    assert_stale_local_base_ref_does_not_widen_scope,
)


def test_detect_base_ref_returns_bare_base_from_origin_head() -> None:
    assert_detect_base_ref_returns_bare_base_from_origin_head()


def test_detect_base_ref_raises_without_origin() -> None:
    assert_detect_base_ref_raises_without_origin()


def test_remote_tracking_ref_composes_origin_prefix() -> None:
    assert_remote_tracking_ref_composes_origin_prefix()


def test_branch_scope_returns_feature_change_against_remote_tracking_base() -> None:
    assert_branch_scope_uses_merge_base()


def test_stale_local_base_ref_does_not_widen_scope() -> None:
    assert_stale_local_base_ref_does_not_widen_scope()


def test_detect_current_branch_returns_name_then_raises_on_detached_head() -> None:
    assert_detect_current_branch_named_and_detached()


def test_commit_oid_resolves_commit_ref() -> None:
    assert_commit_oid_resolves_exact_ref()


def test_branch_slug_disambiguates_on_state_dir_collision() -> None:
    assert_branch_slug_disambiguates_state_collision()
