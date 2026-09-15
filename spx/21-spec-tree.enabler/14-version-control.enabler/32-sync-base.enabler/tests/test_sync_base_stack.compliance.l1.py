"""Real Git compliance evidence for the stack record and restack contract."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    branch_config_entries,
    build_alternate_base_repo,
    build_behind_base_repo,
    build_current_repo,
    build_stacked_repo_merged_predecessor,
    build_stacked_repo_open_predecessor_advanced,
    commit_subjects_above,
    is_ancestor,
    load_sync_base_module,
    repository_root,
    resolve_ref,
)


def test_restack_replays_only_the_branch_commits_and_never_resets(
    tmp_path: pathlib.Path,
) -> None:
    # A plain rebase of this stack replays the stale predecessor commit against
    # its rewritten form and conflicts; a reset would drop the branch's own
    # commit. The restack does neither: the branch's commit survives above the
    # base tip and the stale predecessor commit is gone from its history.
    module = load_sync_base_module()
    handle = build_stacked_repo_merged_predecessor(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.conflict is None
    assert is_ancestor(handle.repo, resolve_ref(handle.repo, handle.remote_ref), "HEAD")
    assert not is_ancestor(handle.repo, handle.predecessor_tip, "HEAD")
    assert commit_subjects_above(handle.repo, handle.remote_ref) == [
        handle.stacked_message
    ]


def test_plain_rebase_with_no_dependent_writes_no_record(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    entries = branch_config_entries(handle.repo, handle.feature_branch)
    assert (
        module.stack_config_key(handle.feature_branch, module.STACK_PREDECESSOR_KEY)
        not in entries
    )
    assert (
        module.stack_config_key(handle.feature_branch, module.STACK_TIP_KEY)
        not in entries
    )
    assert module.read_stack_record(handle.repo, handle.feature_branch) is None


def test_explicit_default_base_writes_no_record(
    tmp_path: pathlib.Path,
) -> None:
    # --base naming the default branch is not a stack: nothing is recorded.
    module = load_sync_base_module()
    handle = build_current_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo, base_ref=handle.base_ref)

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert module.read_stack_record(handle.repo, handle.feature_branch) is None


def test_restack_onto_the_default_removes_both_record_keys(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_merged_predecessor(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    entries = branch_config_entries(handle.repo, handle.stacked_branch)
    assert (
        module.stack_config_key(handle.stacked_branch, module.STACK_PREDECESSOR_KEY)
        not in entries
    )
    assert (
        module.stack_config_key(handle.stacked_branch, module.STACK_TIP_KEY)
        not in entries
    )


def test_proof_carries_stack_facts_as_full_oids_under_the_schema_version(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_stacked_repo_merged_predecessor(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    payload = result.to_json_dict()["preservation"]
    assert isinstance(payload, dict)
    assert payload["schema_version"] == module.READINESS_SCHEMA_VERSION
    assert payload["stack_predecessor"] == handle.predecessor_branch
    # Full OIDs: equal to git's own full rev-parse observations, never abbreviated.
    assert payload["stack_tip_before"] == handle.predecessor_tip
    assert payload["old_base_oid"] == handle.predecessor_tip
    assert payload["new_base_oid"] == resolve_ref(handle.repo, handle.remote_ref)
    assert payload["stack_tip_after"] is None


def test_proof_reports_the_surviving_record_tip_after_a_stacked_sync(
    tmp_path: pathlib.Path,
) -> None:
    # A stacked sync onto an open predecessor keeps the record, so the proof's
    # stack_tip_after is the predecessor's full tip OID rather than null.
    module = load_sync_base_module()
    handle = build_stacked_repo_open_predecessor_advanced(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    payload = result.to_json_dict()["preservation"]
    assert isinstance(payload, dict)
    assert payload["stack_predecessor"] == handle.predecessor_branch
    assert payload["stack_tip_before"] == handle.predecessor_tip
    assert payload["stack_tip_after"] == resolve_ref(
        handle.repo, handle.predecessor_remote_ref
    )


def test_proof_reports_a_null_tip_before_when_the_record_is_new(
    tmp_path: pathlib.Path,
) -> None:
    # An explicit non-default --base creates the record, so nothing precedes it
    # and stack_tip_after is the base's full tip OID.
    module = load_sync_base_module()
    handle = build_alternate_base_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo, base_ref=handle.alternate_ref)

    payload = result.to_json_dict()["preservation"]
    assert isinstance(payload, dict)
    assert payload["stack_predecessor"] == handle.alternate_ref
    assert payload["stack_tip_before"] is None
    assert payload["stack_tip_after"] == resolve_ref(
        handle.repo, handle.alternate_remote_ref
    )
