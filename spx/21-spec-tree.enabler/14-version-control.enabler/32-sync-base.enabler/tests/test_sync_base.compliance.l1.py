"""Compliance tests for the sync-base base-synchronization module.

Covers the Compliance assertions in ``../sync-base.md``:

- sync-base resolves the base ref and remote-tracking form through the shared
  changeset-scope primitives, never re-implementing them — proved by object
  identity between the sync-base re-exports and the canonical symbols.
- sync-base brings a behind-base branch current by rebasing, preserving the
  branch's commits — never by ``git reset``, which would strand the working
  tree at the old base and drop the branch's commit.
- sync-base surfaces no operator decision for a routine, clean rebase — the
  ``SYNC_BASE`` action token appears only on a conflict.

These are ``l1`` — direct in-process calls into ``sync_base`` against real git
repositories seeded under ``tmp_path``.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.changeset_scope import load_changeset_scope_module
from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    build_conflicting_repo,
    load_sync_base_module,
)


def _root(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "pool"
    root.mkdir()
    return root


def test_base_derivation_primitives_are_identity_equal_to_canonical() -> None:
    canonical = load_changeset_scope_module()
    sync = load_sync_base_module()
    assert sync.detect_base_ref is canonical.detect_base_ref
    assert sync.remote_tracking_ref is canonical.remote_tracking_ref
    assert sync.detect_current_branch is canonical.detect_current_branch


def test_rebase_preserves_branch_commit_rather_than_resetting(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    # A rebase replays the feature commit onto the advanced base; a reset onto
    # the base would discard it. The feature file present alongside the base
    # advance proves the branch commit survived.
    assert result.status is module.SyncStatus.REBASED
    assert (handle.repo / handle.feature_file).exists()
    assert (handle.repo / handle.base_file).exists()


def test_clean_rebase_surfaces_no_operator_token_only_conflict_does(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()

    clean_root = tmp_path / "clean"
    clean_root.mkdir()
    clean = module.sync_base(build_behind_base_repo(clean_root).repo)
    assert clean.status is module.SyncStatus.REBASED
    assert clean.action_token is None

    conflict_root = tmp_path / "conflict"
    conflict_root.mkdir()
    conflict = module.sync_base(build_conflicting_repo(conflict_root).repo)
    assert conflict.status is module.SyncStatus.CONFLICT
    assert conflict.action_token == module.SYNC_BASE_TOKEN
