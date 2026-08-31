"""Compliance tests for the sync-base base-synchronization module.

Covers the Compliance assertions in ``../sync-base.md``:

- sync-base resolves the base ref and remote-tracking form through the shared
  changeset-scope primitives, never re-implementing them — proved by object
  identity between the sync-base re-exports and the canonical symbols.
- sync-base brings a behind-base branch current by rebasing, preserving the
  branch's commits — never by ``git reset``, which would strand the working
  tree at the old base and drop the branch's commit.
- sync-base surfaces no operator decision for a routine, clean rebase; conflict
  stops carry structured details instead of an opaque action token.
- sync-base neither commits nor stashes a dirty working tree and does not
  surface it as a conflict — a dirty tree is a distinct precondition the caller
  clears through the commit workflow.
- sync-base advances a clean ancestor-behind detached HEAD rather than waving it
  through; it never advances a dirty or diverged detached HEAD, preserving the
  diverged commits.

These are ``l1`` — direct in-process calls into ``sync_base`` against real git
repositories seeded under ``tmp_path``.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.changeset_scope import load_changeset_scope_module
from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    build_conflicting_repo,
    build_detached_behind_base_repo,
    build_detached_dirty_behind_base_repo,
    build_dirty_behind_base_repo,
    detach_head,
    head_oid,
    load_sync_base_module,
    resolve_ref,
    working_tree_has_tracked_changes,
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


def test_clean_rebase_has_no_conflict_details_conflict_does(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()

    clean_root = tmp_path / "clean"
    clean_root.mkdir()
    clean = module.sync_base(build_behind_base_repo(clean_root).repo)
    assert clean.status is module.SyncStatus.REBASED
    assert clean.conflict is None

    conflict_root = tmp_path / "conflict"
    conflict_root.mkdir()
    conflict_handle = build_conflicting_repo(conflict_root)
    old_head_oid = head_oid(conflict_handle.repo)
    conflict = module.sync_base(conflict_handle.repo)
    assert conflict.status is module.SyncStatus.CONFLICT
    assert conflict.conflict is not None
    assert conflict.conflict.summary == module.CONFLICT_SUMMARY
    assert conflict.conflict.conflicted_paths == [conflict_handle.conflict_file]
    assert conflict.conflict.old_head_oid == old_head_oid
    assert conflict.conflict.new_base_oid == resolve_ref(
        conflict_handle.repo, conflict_handle.remote_ref
    )
    assert conflict.conflict.base_delta_paths == [conflict_handle.conflict_file]
    assert conflict.conflict.branch_paths_before == [conflict_handle.conflict_file]
    assert conflict.conflict.path_overlap == [conflict_handle.conflict_file]
    assert "CONFLICT (content): Merge conflict in" in conflict.conflict.git_output
    assert conflict.conflict.operator_options == [
        module.CONFLICT_INSPECT_STATUS,
        module.CONFLICT_INSPECT_DIFF,
        module.CONFLICT_INSPECT_STAGES,
        module.CONFLICT_CONTINUE,
        module.CONFLICT_ABORT,
    ]
    assert (conflict_handle.repo / ".git" / "rebase-merge").exists() or (
        conflict_handle.repo / ".git" / "rebase-apply"
    ).exists()


@pytest.mark.parametrize("stage", [False, True], ids=["unstaged", "staged"])
def test_dirty_tree_is_neither_committed_stashed_nor_a_conflict(
    tmp_path: pathlib.Path, stage: bool
) -> None:
    # An unstaged change and a staged-but-uncommitted change are both dirty: in
    # neither case does sync-base commit, stash, or surface a rebase conflict.
    module = load_sync_base_module()
    handle = build_dirty_behind_base_repo(_root(tmp_path), stage=stage)

    result = module.sync_base(handle.repo)

    # A dirty tree is reported as its own precondition, never as a conflict, and
    # synchronization does not clear it.
    assert result.status is module.SyncStatus.DIRTY_TREE
    assert result.conflict is None
    # The edit is still an uncommitted tracked change: sync-base neither
    # committed it (the tree would be clean) nor stashed it (the edit would be
    # gone). Both the dirty state and the edit's content confirm it is untouched.
    assert working_tree_has_tracked_changes(handle.repo)
    assert handle.dirty_marker in (handle.repo / handle.dirty_file).read_text(
        encoding="utf-8"
    )


def test_clean_behind_detached_head_is_advanced_not_waved_through(
    tmp_path: pathlib.Path,
) -> None:
    # A clean detached worktree behind the base is brought current — advanced to
    # origin/<base> — rather than waved through as a hard git failure, the gap
    # that let context loading and pickup read a stale base.
    module = load_sync_base_module()
    handle = build_detached_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.status is not module.SyncStatus.GIT_FAILURE
    assert handle.base_file is not None
    assert (handle.repo / handle.base_file).exists()


def test_dirty_detached_head_is_never_advanced(
    tmp_path: pathlib.Path,
) -> None:
    # A behind-base detached worktree with an uncommitted tracked edit is never
    # advanced: sync-base reports dirty_tree and leaves the worktree untouched.
    module = load_sync_base_module()
    handle = build_detached_dirty_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.DIRTY_TREE
    assert result.conflict is None
    # The worktree did not advance, and the uncommitted edit is untouched.
    assert head_oid(handle.repo) == handle.detached_oid
    assert working_tree_has_tracked_changes(handle.repo)


def test_diverged_detached_head_is_never_advanced_commits_preserved(
    tmp_path: pathlib.Path,
) -> None:
    # A diverged detached HEAD carries the feature commit the base lacks.
    # Advancing it would orphan that commit, so sync-base reports git_failure and
    # leaves HEAD — and the feature commit — intact.
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))
    feature_oid_before = head_oid(handle.repo)
    detach_head(handle.repo)

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert head_oid(handle.repo) == feature_oid_before
    assert (handle.repo / handle.feature_file).exists()
