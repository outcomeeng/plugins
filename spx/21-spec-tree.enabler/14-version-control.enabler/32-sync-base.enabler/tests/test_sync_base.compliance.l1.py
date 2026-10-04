"""Real Git compliance evidence for base synchronization."""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.generators.sync_base import (
    TrackedEdit,
    remote_name,
    tracked_edits,
)
from outcomeeng_testing.harnesses.changeset_scope import load_changeset_scope_module
from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    build_conflicting_repo,
    build_detached_behind_base_repo,
    build_detached_dirty_behind_base_repo,
    build_dirty_behind_base_repo,
    detach_head,
    head_oid,
    head_parent_oids,
    load_sync_base_module,
    load_sync_base_with_remote_name,
    repository_root,
    resolve_ref,
    tracked_changes,
    unmerged_index_entries,
)


def test_base_derivation_primitives_are_identity_equal_to_canonical() -> None:
    canonical = load_changeset_scope_module()
    sync = load_sync_base_module()
    assert sync.detect_base_ref is canonical.detect_base_ref
    assert sync.remote_tracking_ref is canonical.remote_tracking_ref
    assert sync.detect_current_branch is canonical.detect_current_branch


def test_synchronization_follows_the_shared_contract_remote_vocabulary(
    tmp_path: pathlib.Path,
) -> None:
    # The installed synchronizer's changeset-scope contract names a generated
    # remote in place of the shipped one, and the repository's only remote
    # carries that generated name. A synchronizer that resolves its base and
    # remote-tracking ref through the shared primitives follows the contract
    # to that remote; one that derives them itself reaches a remote the
    # repository does not have.
    relocated = load_sync_base_with_remote_name(
        repository_root(tmp_path), remote_name()
    )
    module = relocated.module
    handle = build_behind_base_repo(repository_root(tmp_path), remote=relocated.remote)

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.base_ref == handle.base_ref
    assert result.remote_ref == handle.remote_ref
    assert head_parent_oids(handle.repo) == [
        resolve_ref(handle.repo, handle.remote_ref)
    ]


def test_rebase_preserves_branch_commit_rather_than_resetting(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    # A rebase replays the feature commit onto the advanced base; a reset onto
    # the base would discard it. HEAD sits one replayed commit above the fetched
    # base tip, and the feature file present alongside the base advance proves
    # the branch commit survived.
    assert result.status is module.SyncStatus.REBASED
    assert head_parent_oids(handle.repo) == [
        resolve_ref(handle.repo, handle.remote_ref)
    ]
    assert (handle.repo / handle.feature_file).exists()
    assert (handle.repo / handle.base_file).exists()


def test_clean_rebase_has_no_conflict_details_conflict_stays_active(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()

    clean = module.sync_base(build_behind_base_repo(repository_root(tmp_path)).repo)
    assert clean.status is module.SyncStatus.REBASED
    assert clean.conflict is None

    handle = build_conflicting_repo(repository_root(tmp_path))
    conflict = module.sync_base(handle.repo)
    assert conflict.status is module.SyncStatus.CONFLICT
    assert conflict.conflict is not None
    assert conflict.conflict.summary == module.CONFLICT_SUMMARY
    assert conflict.conflict.conflicted_paths == [handle.conflict_file]
    assert handle.conflict_file in conflict.conflict.git_output
    # Synchronization hands the conflict over without aborting it: the index
    # still holds the unmerged stages and the working file both sides.
    assert handle.conflict_file in unmerged_index_entries(handle.repo)
    conflicted_text = (handle.repo / handle.conflict_file).read_text(encoding="utf-8")
    assert handle.base_content in conflicted_text
    assert handle.feature_content in conflicted_text


@pytest.mark.parametrize("edit", tracked_edits())
def test_dirty_tree_is_neither_committed_stashed_nor_a_conflict(
    tmp_path: pathlib.Path, edit: TrackedEdit
) -> None:
    # An unstaged change and a staged-but-uncommitted change are both dirty: in
    # neither case does sync-base commit, stash, or surface a rebase conflict.
    module = load_sync_base_module()
    handle = build_dirty_behind_base_repo(repository_root(tmp_path), edit=edit)

    result = module.sync_base(handle.repo)

    # A dirty tree is reported as its own precondition, never as a conflict, and
    # synchronization does not clear it.
    assert result.status is module.SyncStatus.DIRTY_TREE
    assert result.conflict is None
    # The edited file is still an uncommitted tracked change: sync-base neither
    # committed it (Git would report no change) nor stashed it (the edit would be
    # gone). Both the reported change and the edit's content confirm it is
    # untouched.
    assert handle.dirty_file in tracked_changes(handle.repo)
    assert handle.dirty_marker in (handle.repo / handle.dirty_file).read_text(
        encoding="utf-8"
    )


def test_clean_behind_detached_head_is_advanced_not_waved_through(
    tmp_path: pathlib.Path,
) -> None:
    # A clean detached worktree behind the base is brought current — advanced to
    # the remote-tracking base — rather than waved through as a hard git
    # failure, the gap that let context loading and pickup read a stale base.
    module = load_sync_base_module()
    handle = build_detached_behind_base_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.status is not module.SyncStatus.GIT_FAILURE
    assert handle.base_file is not None
    assert (handle.repo / handle.base_file).exists()


@pytest.mark.parametrize("edit", tracked_edits())
def test_dirty_detached_head_is_never_advanced(
    tmp_path: pathlib.Path, edit: TrackedEdit
) -> None:
    # A behind-base detached worktree with an uncommitted tracked edit is never
    # advanced: sync-base reports dirty_tree and leaves the worktree untouched.
    module = load_sync_base_module()
    handle = build_detached_dirty_behind_base_repo(repository_root(tmp_path), edit=edit)

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.DIRTY_TREE
    assert result.conflict is None
    # The worktree did not advance, and the uncommitted edit is untouched.
    assert head_oid(handle.repo) == handle.detached_oid
    assert handle.dirty_file is not None
    assert handle.dirty_file in tracked_changes(handle.repo)


def test_diverged_detached_head_is_never_advanced_commits_preserved(
    tmp_path: pathlib.Path,
) -> None:
    # A diverged detached HEAD carries the feature commit the base lacks.
    # Advancing it would orphan that commit, so sync-base reports git_failure and
    # leaves HEAD — and the feature commit — intact.
    module = load_sync_base_module()
    handle = build_behind_base_repo(repository_root(tmp_path))
    feature_oid_before = head_oid(handle.repo)
    detach_head(handle.repo)

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert head_oid(handle.repo) == feature_oid_before
    assert (handle.repo / handle.feature_file).exists()
