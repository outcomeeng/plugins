"""Real Git scenario evidence for the stack record and restack contract."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    build_alternate_base_repo,
    build_conflicting_repo,
    build_stacked_repo_behind_base,
    build_stacked_repo_merged_predecessor,
    build_stacked_repo_open_predecessor_advanced,
    build_stacked_repo_rewritten_published_predecessor,
    build_stacked_repo_unpublished_predecessor,
    build_stacked_repo_without_record,
    build_three_level_stack_behind_base,
    commit_subjects_above,
    load_sync_base_module,
    repository_root,
    resolve_ref,
)


def test_rebased_predecessor_writes_the_record_on_its_dependent(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_behind_base(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.branch == handle.predecessor_branch
    # The stacked branch contained the predecessor's pre-rebase tip, so it now
    # names the predecessor and that tip.
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.predecessor_branch, tip=handle.predecessor_tip
    )


def test_rebased_predecessor_leaves_a_farther_dependent_recording_its_nearer_one(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_three_level_stack_behind_base(repository_root(tmp_path))
    assert handle.third_branch is not None
    assert handle.stacked_tip is not None

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    # The middle branch sat on the rebased tip and records it; the top branch
    # already names the middle branch as its nearer predecessor and keeps it.
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.predecessor_branch, tip=handle.predecessor_tip
    )
    assert module.read_stack_record(
        handle.repo, handle.third_branch
    ) == module.StackRecord(predecessor=handle.stacked_branch, tip=handle.stacked_tip)


def test_explicit_base_sync_writes_the_record_on_the_synced_branch(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_alternate_base_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo, base_ref=handle.alternate_ref)

    assert result.status is module.SyncStatus.REBASED
    assert module.read_stack_record(
        handle.repo, handle.feature_branch
    ) == module.StackRecord(
        predecessor=handle.alternate_ref,
        tip=resolve_ref(handle.repo, handle.alternate_remote_ref),
    )


def test_recorded_branch_syncs_onto_its_open_predecessor_without_base(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_open_predecessor_advanced(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.predecessor_remote_ref
    assert handle.predecessor_advance_file is not None
    assert (handle.repo / handle.predecessor_advance_file).exists()
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.predecessor_branch,
        tip=resolve_ref(handle.repo, handle.predecessor_remote_ref),
    )


def test_recorded_branch_follows_an_unpublished_rewritten_predecessor(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_unpublished_predecessor(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    # Only the stacked branch's own commit sits above the local predecessor, and
    # the predecessor's rewritten content is what the working tree carries.
    assert commit_subjects_above(handle.repo, handle.predecessor_branch) == [
        handle.stacked_message
    ]
    assert (handle.repo / handle.predecessor_file).read_text(
        encoding="utf-8"
    ) == handle.predecessor_rewrite_content
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.predecessor_branch,
        tip=resolve_ref(handle.repo, handle.predecessor_branch),
    )


def test_recorded_branch_follows_a_rewritten_published_predecessor(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_rewritten_published_predecessor(
        repository_root(tmp_path)
    )

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.predecessor_remote_ref
    # Only the stacked branch's own commit was replayed above the rewritten
    # predecessor on origin; the stale predecessor commit left its history.
    assert commit_subjects_above(handle.repo, handle.predecessor_remote_ref) == [
        handle.stacked_message
    ]
    assert (handle.repo / handle.predecessor_file).read_text(
        encoding="utf-8"
    ) == handle.predecessor_rewrite_content
    assert result.preservation is not None
    assert result.preservation.old_base_oid == handle.predecessor_tip
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.predecessor_branch,
        tip=resolve_ref(handle.repo, handle.predecessor_remote_ref),
    )


def test_recorded_branch_restacks_onto_the_default_after_predecessor_merged(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_merged_predecessor(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.remote_ref
    # Only the stacked branch's own commit was replayed; the stale predecessor
    # commit was not, and the merged rewrite is what the tree now carries.
    assert commit_subjects_above(handle.repo, handle.remote_ref) == [
        handle.stacked_message
    ]
    assert (handle.repo / handle.predecessor_file).read_text(
        encoding="utf-8"
    ) == handle.predecessor_rewrite_content
    assert result.preservation is not None
    assert result.preservation.old_base_oid == handle.predecessor_tip
    assert result.preservation.new_base_oid == resolve_ref(
        handle.repo, handle.remote_ref
    )
    assert result.preservation.stack_predecessor == handle.predecessor_branch
    assert result.preservation.stack_tip_before == handle.predecessor_tip
    assert result.preservation.stack_tip_after is None
    assert module.read_stack_record(handle.repo, handle.stacked_branch) is None


def test_unrecorded_stack_derives_and_records_its_predecessor(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_without_record(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    # The stacked branch already sits on the predecessor's pushed tip, so the
    # derived predecessor is the base and nothing is behind.
    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert result.remote_ref == handle.predecessor_remote_ref
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.predecessor_branch, tip=handle.predecessor_tip
    )


def test_conflict_report_lists_the_restack_recovery(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_conflicting_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.CONFLICT
    assert result.conflict is not None
    # The restack form is a spec-declared value the source owns; its agreement
    # with the spec is audit evidence, and this test exercises the behavior of
    # listing it for the conflicted base.
    assert (
        module.restack_operator_option(handle.remote_ref)
        in result.conflict.operator_options
    )
