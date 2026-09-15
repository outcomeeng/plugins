"""Git identity and portable payload boundaries for preservation evidence."""

from __future__ import annotations

import pathlib
from dataclasses import fields

from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    fetch_base,
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
    handle = build_behind_base_repo(repository_root(tmp_path))
    fetch_base(handle.repo, handle.base_ref)
    old_head = head_oid(handle.repo)
    old_base = merge_base_oid(handle.repo, handle.remote_ref)
    new_base = resolve_ref(handle.repo, handle.remote_ref)

    result = module.sync_base(handle.repo)
    proof = result.preservation
    assert proof is not None

    # Full OIDs: equal to git's own full rev-parse observations, never abbreviated.
    assert proof.old_head_oid == old_head
    assert proof.old_base_oid == old_base
    assert proof.new_base_oid == new_base
    assert proof.new_head_oid == head_oid(handle.repo)
    payload = result.to_json_dict()["preservation"]
    assert isinstance(payload, dict)
    assert payload[module.SCHEMA_VERSION_KEY] == module.READINESS_SCHEMA_VERSION
    assert set(payload) == {field.name for field in fields(module.Preservation)} | {
        module.SCHEMA_VERSION_KEY
    }
    assert not any("lane" in key or "validation" in key for key in payload)
