"""Real Git compliance evidence for the stack record and restack contract."""

from __future__ import annotations

import dataclasses
import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    ConfigWriteRefusingRunner,
    branch_config_entries,
    build_alternate_base_repo,
    build_behind_base_repo,
    build_current_repo,
    build_stacked_repo_merged_predecessor,
    build_stacked_repo_nearest_of_two,
    build_stacked_repo_open_predecessor_advanced,
    build_stacked_repo_unordered_candidates,
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

    proof = result.preservation
    assert proof is not None
    assert proof.stack_predecessor == handle.predecessor_branch
    # Full OIDs: equal to git's own full rev-parse observations, never abbreviated.
    assert proof.stack_tip_before == handle.predecessor_tip
    assert proof.old_base_oid == handle.predecessor_tip
    assert proof.new_base_oid == resolve_ref(handle.repo, handle.remote_ref)
    assert proof.stack_tip_after is None
    # The serialized proof carries every field under the field's own name; the
    # names' agreement with the decision is audit evidence.
    payload = result.to_json_dict()["preservation"]
    assert isinstance(payload, dict)
    for field in dataclasses.fields(proof):
        assert payload[field.name] == getattr(proof, field.name)


def test_proof_reports_the_surviving_record_tip_after_a_stacked_sync(
    tmp_path: pathlib.Path,
) -> None:
    # A stacked sync onto an open predecessor keeps the record, so the proof's
    # stack_tip_after is the predecessor's full tip OID rather than null.
    module = load_sync_base_module()
    handle = build_stacked_repo_open_predecessor_advanced(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    proof = result.preservation
    assert proof is not None
    assert proof.stack_predecessor == handle.predecessor_branch
    assert proof.stack_tip_before == handle.predecessor_tip
    assert proof.stack_tip_after == resolve_ref(
        handle.repo, handle.predecessor_remote_ref
    )
    payload = result.to_json_dict()["preservation"]
    assert isinstance(payload, dict)
    for field in dataclasses.fields(proof):
        assert payload[field.name] == getattr(proof, field.name)


def test_proof_reports_a_null_tip_before_when_the_record_is_new(
    tmp_path: pathlib.Path,
) -> None:
    # An explicit non-default --base creates the record, so nothing precedes it
    # and stack_tip_after is the base's full tip OID.
    module = load_sync_base_module()
    handle = build_alternate_base_repo(repository_root(tmp_path))

    result = module.sync_base(handle.repo, base_ref=handle.alternate_ref)

    proof = result.preservation
    assert proof is not None
    assert proof.stack_predecessor == handle.alternate_ref
    assert proof.stack_tip_before is None
    assert proof.stack_tip_after == resolve_ref(
        handle.repo, handle.alternate_remote_ref
    )
    payload = result.to_json_dict()["preservation"]
    assert isinstance(payload, dict)
    for field in dataclasses.fields(proof):
        assert payload[field.name] == getattr(proof, field.name)


def test_derivation_records_the_nearest_of_two_ordered_candidates(
    tmp_path: pathlib.Path,
) -> None:
    # Two local branches forked from the default before this branch forked from
    # them; the nearer fork wins, and a rule that picked the farther one would
    # record the first predecessor instead.
    module = load_sync_base_module()
    handle = build_stacked_repo_nearest_of_two(repository_root(tmp_path))
    assert handle.second_candidate_branch is not None
    assert handle.second_candidate_tip is not None

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert result.remote_ref == module.remote_tracking_ref(
        handle.second_candidate_branch
    )
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.second_candidate_branch, tip=handle.second_candidate_tip
    )


def test_derivation_with_unordered_candidates_writes_no_record(
    tmp_path: pathlib.Path,
) -> None:
    # Two candidates whose forks neither descend from the other name no
    # predecessor: the sync lands on the default base and both keys stay absent.
    module = load_sync_base_module()
    handle = build_stacked_repo_unordered_candidates(repository_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert result.remote_ref == handle.remote_ref
    assert module.read_stack_record(handle.repo, handle.stacked_branch) is None
    entries = branch_config_entries(handle.repo, handle.stacked_branch)
    assert (
        module.stack_config_key(handle.stacked_branch, module.STACK_PREDECESSOR_KEY)
        not in entries
    )
    assert (
        module.stack_config_key(handle.stacked_branch, module.STACK_TIP_KEY)
        not in entries
    )


def test_failed_record_write_is_never_reported_as_a_clean_sync(
    tmp_path: pathlib.Path,
) -> None:
    # Stage 5 exception 1 (failure simulation): the injected runner refuses
    # every git config write while the rebase itself runs for real, so the
    # sync must report the refused record rather than a clean outcome.
    module = load_sync_base_module()
    handle = build_alternate_base_repo(repository_root(tmp_path))
    runner = ConfigWriteRefusingRunner()

    result = module.sync_base(handle.repo, base_ref=handle.alternate_ref, runner=runner)

    assert result.status is module.SyncStatus.GIT_FAILURE
    # The result names the sync that was in flight: the synchronized branch and
    # the base it targeted, with the refused key in the detail.
    assert result.branch == handle.feature_branch
    assert result.remote_ref == handle.alternate_remote_ref
    assert (
        module.stack_config_key(handle.feature_branch, module.STACK_PREDECESSOR_KEY)
        in result.detail
    )
    assert runner.refused
    assert module.read_stack_record(handle.repo, handle.feature_branch) is None


def test_failed_record_removal_is_never_reported_as_a_clean_sync(
    tmp_path: pathlib.Path,
) -> None:
    # Stage 5 exception 1 (failure simulation): the injected runner refuses the
    # git config unset that clears the record after a merged-predecessor
    # restack, so the sync reports the refused key and the record survives.
    module = load_sync_base_module()
    handle = build_stacked_repo_merged_predecessor(repository_root(tmp_path))
    runner = ConfigWriteRefusingRunner()

    result = module.sync_base(handle.repo, runner=runner)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert result.branch == handle.stacked_branch
    assert result.remote_ref == handle.remote_ref
    assert (
        module.stack_config_key(handle.stacked_branch, module.STACK_PREDECESSOR_KEY)
        in result.detail
    )
    assert runner.refused
    assert module.read_stack_record(
        handle.repo, handle.stacked_branch
    ) == module.StackRecord(
        predecessor=handle.predecessor_branch, tip=handle.predecessor_tip
    )


def test_absent_record_key_on_removal_is_not_a_failure(
    tmp_path: pathlib.Path,
) -> None:
    # Stage 5 exception 1 (failure simulation): git reports the key already
    # absent on unset; an absent key is not a failed removal, so the restack
    # stays a clean outcome whose proof shows the record cleared.
    module = load_sync_base_module()
    handle = build_stacked_repo_merged_predecessor(repository_root(tmp_path))
    runner = ConfigWriteRefusingRunner(returncode=module.CONFIG_KEY_ABSENT_EXIT)

    result = module.sync_base(handle.repo, runner=runner)

    assert result.status is module.SyncStatus.REBASED
    assert result.preservation is not None
    assert result.preservation.stack_tip_after is None
