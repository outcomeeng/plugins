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

    payload = module.sync_base(handle.repo).to_json_dict()
    proof = payload["preservation"]

    assert proof["schema_version"] == module.READINESS_SCHEMA_VERSION
    assert proof["old_head_oid"] == old_head
    assert proof["old_base_oid"] == old_base
    assert proof["new_base_oid"] == new_base
    assert proof["new_head_oid"] == head_oid(handle.repo)
    assert set(proof) == {field.name for field in fields(module.Preservation)} | {
        "schema_version"
    }
    assert not any("lane" in key or "validation" in key for key in proof)
