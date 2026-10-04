"""Git identity and portable payload boundaries for preservation evidence."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    build_prefetched_behind_base_repo,
    head_oid,
    load_sync_base_module,
    merge_base_oid,
    repository_root,
    resolve_ref,
)


def test_proof_carries_schema_version_and_full_oids_no_lane_name(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_prefetched_behind_base_repo(repository_root(tmp_path))
    old_head = head_oid(handle.repo)
    old_base = merge_base_oid(handle.repo, handle.remote_ref)
    new_base = resolve_ref(handle.repo, handle.remote_ref)

    payload = module.sync_base(handle.repo).to_json_dict()
    proof = payload[module.RESULT_PRESERVATION_KEY]

    assert (
        proof[module.PRESERVATION_SCHEMA_VERSION_KEY] == module.READINESS_SCHEMA_VERSION
    )
    assert proof[module.OLD_HEAD_OID_KEY] == old_head
    assert proof[module.OLD_BASE_OID_KEY] == old_base
    assert proof[module.NEW_BASE_OID_KEY] == new_base
    assert proof[module.NEW_HEAD_OID_KEY] == head_oid(handle.repo)
    # The proof carries exactly its schema version and git facts, so no
    # validation-lane field stands beside them.
    assert set(proof) == {
        module.PRESERVATION_SCHEMA_VERSION_KEY,
        module.OLD_BASE_OID_KEY,
        module.NEW_BASE_OID_KEY,
        module.OLD_HEAD_OID_KEY,
        module.NEW_HEAD_OID_KEY,
        module.BASE_DELTA_PATHS_KEY,
        module.BRANCH_PATHS_BEFORE_KEY,
        module.BRANCH_PATHS_AFTER_KEY,
        module.PATH_OVERLAP_KEY,
        module.BRANCH_PATCH_CHANGED_KEY,
        module.BRANCH_DIFF_UNCHANGED_KEY,
    }
