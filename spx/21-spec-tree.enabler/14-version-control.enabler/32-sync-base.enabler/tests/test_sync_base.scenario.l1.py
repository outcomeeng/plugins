"""Scenario tests for the sync-base base-synchronization module.

Covers the Scenario assertions in ``../sync-base.md``:

- A branch behind its fetched base has its own commits replayed onto
  ``origin/<base>`` with the base's changes present.
- A branch already current with its fetched base performs no rebase.
- A rebase conflict stops with an active rebase state and structured conflict
  details, leaving stages inspectable for reconciliation.
- A dirty working tree behind its base reports the distinct ``dirty_tree``
  outcome without rebasing, leaving the uncommitted edit untouched.
- A behind-base tree carrying only an untracked file rebases normally — an
  untracked file does not block a rebase and is not a dirty tree.
- A base ref that does not resolve reports a hard git failure.
- A clean detached HEAD that is an ancestor of the fetched base and behind it is
  advanced to the base tip and reported ``rebased``.
- A clean detached HEAD already at the base tip is reported ``already_current``.
- A detached HEAD behind the base with an uncommitted tracked edit reports
  ``dirty_tree`` without advancing.
- A diverged detached HEAD — carrying commits the base lacks — reports a hard git
  failure rather than advancing and orphaning those commits.
- A detached HEAD with no resolvable remote base reports a hard git failure.
- A clean detached HEAD behind the base whose only change is an untracked file is
  advanced rather than reported ``dirty_tree``.
- A clean rebase reports whether the base delta overlaps the branch and whether
  the branch diff remains reusable.
- An already-current branch or detached HEAD reports an empty base delta and an
  unchanged branch patch identity.
- A caller that fetched before synchronization still receives the base delta
  measured from the branch fork point.
- A base rename reports both its old and new paths in the base delta.

These are ``l1`` — direct in-process calls into ``sync_base`` against real git
repositories (a bare origin and working clones) seeded under ``tmp_path``; git
and temp dirs are expected on a working machine.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.sync_base import (
    build_alternate_base_repo,
    build_behind_base_repo,
    build_conflicting_repo,
    build_current_repo,
    build_detached_behind_base_repo,
    build_detached_current_repo,
    build_detached_dirty_behind_base_repo,
    build_detached_no_remote_repo,
    build_detached_untracked_only_behind_base_repo,
    build_dirty_behind_base_repo,
    build_overlapping_base_repo,
    build_rename_base_repo,
    build_untracked_only_behind_base_repo,
    create_repository_pool as _root,
    detach_head,
    fetch_base,
    head_oid,
    load_sync_base_module,
    resolve_ref,
)


def test_behind_base_branch_is_rebased_onto_remote_tracking_base(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.remote_ref
    assert result.branch == handle.feature_branch
    # The feature commit's effect survives the rebase (it was replayed)...
    assert (handle.repo / handle.feature_file).exists()
    # ...and the base advance the branch was behind is now present.
    assert (handle.repo / handle.base_file).exists()


def test_branch_already_current_performs_no_rebase(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_current_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert result.branch == handle.feature_branch
    assert result.conflict is None


def test_rebase_conflict_stops_with_active_conflict_details(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_conflicting_repo(_root(tmp_path))
    old_head_oid = head_oid(handle.repo)

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.CONFLICT
    assert result.conflict is not None
    assert result.conflict.summary == module.CONFLICT_SUMMARY
    assert result.conflict.conflicted_paths == [handle.conflict_file]
    assert result.conflict.old_head_oid == old_head_oid
    assert result.conflict.new_base_oid == resolve_ref(handle.repo, handle.remote_ref)
    assert result.conflict.base_delta_paths == [handle.conflict_file]
    assert result.conflict.branch_paths_before == [handle.conflict_file]
    assert result.conflict.path_overlap == [handle.conflict_file]
    assert f"CONFLICT (content): Merge conflict in {handle.conflict_file}" in (
        result.conflict.git_output
    )
    assert result.conflict.operator_options == [
        module.CONFLICT_INSPECT_STATUS,
        module.CONFLICT_INSPECT_DIFF,
        module.CONFLICT_INSPECT_STAGES,
        module.CONFLICT_CONTINUE,
        module.CONFLICT_ABORT,
    ]
    # The rebase remains active so the operator can inspect, continue, or abort.
    assert (handle.repo / ".git" / "rebase-merge").exists() or (
        handle.repo / ".git" / "rebase-apply"
    ).exists()
    assert "<<<<<<<" in (handle.repo / handle.conflict_file).read_text(encoding="utf-8")
    payload = result.to_json_dict()
    assert payload["conflict"] is not None
    assert "git_output" in payload["conflict"]
    assert "stderr" not in payload["conflict"]
    assert "action_token" not in payload


@pytest.mark.parametrize("stage", [False, True], ids=["unstaged", "staged"])
def test_dirty_tree_behind_base_reports_dirty_tree_without_rebasing(
    tmp_path: pathlib.Path, stage: bool
) -> None:
    # Both an unstaged and a staged-but-uncommitted tracked change block the
    # rebase and must report dirty_tree — git refuses to replay over either.
    module = load_sync_base_module()
    handle = build_dirty_behind_base_repo(_root(tmp_path), stage=stage)

    result = module.sync_base(handle.repo)

    # A dirty tree is a distinct precondition, not a conflict.
    assert result.status is module.SyncStatus.DIRTY_TREE
    assert result.conflict is None
    assert result.branch == handle.feature_branch
    # The rebase never ran, so the base advance did not enter the working tree...
    assert not (handle.repo / handle.base_file).exists()
    # ...and the uncommitted edit is left untouched — not committed, not stashed.
    assert handle.dirty_marker in (handle.repo / handle.dirty_file).read_text(
        encoding="utf-8"
    )


def test_untracked_only_behind_base_rebases_not_dirty_tree(
    tmp_path: pathlib.Path,
) -> None:
    # Untracked files do not block a rebase, so they are not a dirty tree: a
    # behind-base branch carrying only an untracked file rebases normally. This
    # proves the dirty check's --untracked-files=no scope is necessary — without
    # it the untracked file would read as dirty and force dirty_tree.
    module = load_sync_base_module()
    handle = build_untracked_only_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.conflict is None
    # The rebase ran: the base advance is present and the feature commit survived.
    assert (handle.repo / handle.base_file).exists()
    assert (handle.repo / handle.feature_file).exists()


def test_diverged_detached_head_reports_hard_git_failure(
    tmp_path: pathlib.Path,
) -> None:
    # The detached commit carries the feature commit, which the base lacks, so
    # HEAD has diverged from origin/<base>. Advancing would orphan that commit,
    # and a detached HEAD has no branch to rebase it onto, so the outcome is a
    # hard git failure — the feature commit is preserved, not discarded.
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))
    feature_oid_before = head_oid(handle.repo)
    detach_head(handle.repo)

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert result.branch is None
    assert result.conflict is None
    # The detached commit is untouched: its feature commit was not discarded.
    assert head_oid(handle.repo) == feature_oid_before
    assert (handle.repo / handle.feature_file).exists()


def test_clean_behind_detached_head_is_advanced_to_base_tip(
    tmp_path: pathlib.Path,
) -> None:
    # A pool worktree parked detached at a commit that is an ancestor of the
    # advanced base, with a clean tree, is brought current rather than waved
    # through: synchronization advances the worktree to origin/<base> and reports
    # rebased, with the base advance now present.
    module = load_sync_base_module()
    handle = build_detached_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.branch is None
    assert result.conflict is None
    # The worktree advanced to the fetched base tip...
    assert head_oid(handle.repo) == resolve_ref(handle.repo, handle.remote_ref)
    # ...so the base advance the worktree was behind is now present.
    assert handle.base_file is not None
    assert (handle.repo / handle.base_file).exists()


def test_clean_detached_head_at_base_tip_is_already_current(
    tmp_path: pathlib.Path,
) -> None:
    # A detached worktree already at the base tip (no base advance) performs no
    # advance and reports already_current.
    module = load_sync_base_module()
    handle = build_detached_current_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert result.branch is None
    assert result.conflict is None
    assert head_oid(handle.repo) == handle.detached_oid


def test_dirty_behind_detached_head_reports_dirty_tree_without_advancing(
    tmp_path: pathlib.Path,
) -> None:
    # A behind-base detached worktree carrying an uncommitted tracked edit reports
    # the distinct dirty_tree outcome with the edit and the parked commit left
    # untouched for the caller to commit.
    module = load_sync_base_module()
    handle = build_detached_dirty_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.DIRTY_TREE
    assert result.conflict is None
    # The worktree did not advance: HEAD is still the parked commit...
    assert head_oid(handle.repo) == handle.detached_oid
    # ...the base advance never entered the tree...
    assert handle.base_file is not None
    assert not (handle.repo / handle.base_file).exists()
    # ...and the uncommitted edit is left untouched, not committed or stashed.
    assert handle.dirty_file is not None and handle.dirty_marker is not None
    assert handle.dirty_marker in (handle.repo / handle.dirty_file).read_text(
        encoding="utf-8"
    )


def test_detached_untracked_only_behind_base_is_advanced(
    tmp_path: pathlib.Path,
) -> None:
    # A clean detached worktree behind the base carrying only an untracked file is
    # advanced, not reported dirty_tree: an untracked file does not block the
    # advance, the detached analogue of the branch untracked-only case. Proves the
    # advance's --untracked-files=no scope — without it the file would read as
    # dirty and force dirty_tree.
    module = load_sync_base_module()
    handle = build_detached_untracked_only_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.conflict is None
    # The worktree advanced to the fetched base tip, base advance now present.
    assert head_oid(handle.repo) == resolve_ref(handle.repo, handle.remote_ref)
    assert handle.base_file is not None
    assert (handle.repo / handle.base_file).exists()


def test_detached_head_with_no_remote_reports_hard_git_failure(
    tmp_path: pathlib.Path,
) -> None:
    # A detached worktree with no origin remote cannot fetch or resolve a base, so
    # the detached case stays a hard git failure — the only genuinely
    # non-advanceable detached outcome alongside divergence.
    module = load_sync_base_module()
    handle = build_detached_no_remote_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert result.branch is None
    assert result.conflict is None


def test_explicit_base_ref_overrides_origin_head(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_current_repo(_root(tmp_path))

    # An explicit base name is used instead of the origin/HEAD default: the run
    # targets origin/<given> and fails to resolve a base that does not exist,
    # rather than syncing against the detected default.
    result = module.sync_base(handle.repo, base_ref="not-a-branch", fetch=False)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert result.base_ref == "not-a-branch"
    assert result.remote_ref == module.remote_tracking_ref("not-a-branch")


def test_explicit_valid_base_rebases_onto_that_base_not_origin_head(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_alternate_base_repo(_root(tmp_path))

    # The feature is current with the origin/HEAD default, so syncing onto the
    # default does nothing...
    default_result = module.sync_base(handle.repo, base_ref=handle.default_ref)
    assert default_result.status is module.SyncStatus.ALREADY_CURRENT

    # ...but it is behind the caller-supplied alternate base, so syncing onto
    # that base rebases the feature onto origin/<alternate> and brings the
    # alternate's advance into the working tree.
    result = module.sync_base(handle.repo, base_ref=handle.alternate_ref)
    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.alternate_remote_ref
    assert (handle.repo / handle.alternate_file).exists()
    assert (handle.repo / handle.feature_file).exists()


def test_non_overlapping_rebase_preserves_local_review(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.base_file in proof.base_delta_paths
    assert handle.feature_file in proof.branch_paths_after
    assert proof.path_overlap == []
    assert proof.branch_patch_changed is False
    assert proof.branch_diff_unchanged is True


def test_overlapping_rebase_does_not_preserve_local_review(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_overlapping_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.overlap_file in proof.path_overlap
    assert proof.branch_diff_unchanged is False


def test_already_current_preserves_all_readiness(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_current_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert proof is not None
    assert proof.base_delta_paths == []
    assert proof.branch_patch_changed is False
    assert proof.branch_diff_unchanged is True
    assert proof.old_head_oid == proof.new_head_oid


def test_base_delta_accurate_when_caller_prefetched(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))
    fetch_base(handle.repo)

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.base_file in proof.base_delta_paths
    assert proof.path_overlap == []
    assert proof.branch_diff_unchanged is True


def test_advanced_detached_head_emits_preservation_proof(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_detached_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.base_file is not None
    assert handle.base_file in proof.base_delta_paths
    assert proof.path_overlap == []
    assert proof.branch_patch_changed is False
    assert proof.branch_diff_unchanged is True


def test_already_current_detached_head_emits_preservation_proof(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_detached_current_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert proof is not None
    assert proof.base_delta_paths == []
    assert proof.branch_patch_changed is False
    assert proof.branch_diff_unchanged is True
    assert proof.old_head_oid == proof.new_head_oid


def test_base_rename_surfaces_both_paths_in_base_delta(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_rename_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.old_path in proof.base_delta_paths
    assert handle.new_path in proof.base_delta_paths
