"""Readiness-preservation tests for the sync-base module.

Covers the readiness-preservation Scenario and Compliance assertions in
``../sync-base.md``:

- A clean rebase whose base advance does not overlap the branch reports no path
  overlap and an unchanged branch patch identity (the reuse signal).
- A clean rebase whose base advance overlaps the branch's file reports the
  overlap, so a caller does not reuse a prior local review.
- An already-current branch reports an empty base delta and an unchanged branch
  patch identity.
- A clean detached HEAD advanced to the base tip emits a proof reporting the base
  advance and an unchanged branch patch identity.
- A clean detached HEAD already at the base tip emits a proof reporting an empty
  base delta and an unchanged branch patch identity.
- The proof carries a schema version, full unabbreviated OIDs, and no
  only portable Git-fact fields.

These are ``l1`` — direct in-process calls into ``sync_base`` against real git
repositories seeded under ``tmp_path``.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    build_current_repo,
    build_detached_behind_base_repo,
    build_detached_current_repo,
    build_overlapping_base_repo,
    build_rename_base_repo,
    fetch_base,
    load_sync_base_module,
)

_FULL_OID_LEN = 40


def _root(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "pool"
    root.mkdir()
    return root


def test_non_overlapping_rebase_preserves_local_review(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    # The base advanced over base_file; the branch changed feature_file — disjoint.
    assert handle.base_file in proof.base_delta_paths
    assert handle.feature_file in proof.branch_paths_after
    assert proof.path_overlap == []
    assert proof.branch_patch_changed is False
    # The reuse signal a caller reads before considering its governance check.
    assert proof.branch_diff_unchanged is True


def test_overlapping_rebase_does_not_preserve_local_review(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_overlapping_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)
    proof = result.preservation

    # Base and branch both touched the same file; the rebase auto-merged.
    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.overlap_file in proof.path_overlap
    # Any overlap forbids reuse, regardless of patch identity.
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
    # No base movement the branch is behind: empty delta, unchanged branch patch.
    assert proof.base_delta_paths == []
    assert proof.branch_patch_changed is False
    assert proof.branch_diff_unchanged is True
    # HEAD is untouched by an already-current sync.
    assert proof.old_head_oid == proof.new_head_oid


def test_base_delta_accurate_when_caller_prefetched(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))
    # The caller already fetched the base before invoking sync-base, so the
    # remote-tracking ref already points at the advanced base.
    fetch_base(handle.repo)

    result = module.sync_base(handle.repo)
    proof = result.preservation

    # Anchoring the base delta at the branch's fork point keeps it accurate: the
    # base advance is reported even though a pre-fetch remote ref equals the new
    # base and would have reported an empty delta.
    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.base_file in proof.base_delta_paths
    assert proof.path_overlap == []
    assert proof.branch_diff_unchanged is True


def test_advanced_detached_head_emits_preservation_proof(
    tmp_path: pathlib.Path,
) -> None:
    # A clean detached worktree advanced to the base tip emits the same proof a
    # branch rebase does: the base advance is reported, and the parked worktree
    # carries no branch work of its own, so the patch identity is unchanged and
    # all prior readiness is preserved.
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
    # A detached worktree already at the base tip emits a proof with an empty
    # base delta and an unchanged branch patch identity — no advance happened and
    # nothing the caller's readiness depends on moved.
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

    # A base rename reports both the old and new path (--no-renames), so a base
    # rename of a path the branch also touched cannot hide behind the new name.
    assert result.status is module.SyncStatus.REBASED
    assert proof is not None
    assert handle.old_path in proof.base_delta_paths
    assert handle.new_path in proof.base_delta_paths


def test_proof_carries_schema_version_full_oids_and_portable_fields(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))

    payload = module.sync_base(handle.repo).to_json_dict()
    proof = payload["preservation"]

    assert proof["schema_version"] == module.READINESS_SCHEMA_VERSION
    for key in ("old_base_oid", "new_base_oid", "old_head_oid", "new_head_oid"):
        assert len(proof[key]) == _FULL_OID_LEN
        assert proof[key] == proof[key].lower()
    assert set(proof) == {
        "schema_version",
        "old_base_oid",
        "new_base_oid",
        "old_head_oid",
        "new_head_oid",
        "base_delta_paths",
        "branch_paths_before",
        "branch_paths_after",
        "path_overlap",
        "branch_patch_changed",
        "branch_diff_unchanged",
    }
