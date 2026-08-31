"""Conformance evidence for the sync-base readiness-preservation proof."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    head_oid,
    load_sync_base_module,
    merge_base_oid,
    resolve_ref,
)


def test_proof_conforms_to_versioned_portable_schema(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / "pool"
    root.mkdir()
    module = load_sync_base_module()
    handle = build_behind_base_repo(root)
    old_head_oid = head_oid(handle.repo)
    old_base_oid = merge_base_oid(handle.repo, old_head_oid, handle.remote_ref)

    payload = module.sync_base(handle.repo).to_json_dict()
    proof = payload["preservation"]
    expected_oids = (
        old_base_oid,
        resolve_ref(handle.repo, handle.remote_ref),
        old_head_oid,
        head_oid(handle.repo),
    )

    assert proof["schema_version"] == module.READINESS_SCHEMA_VERSION
    for key, expected_oid in zip(
        module.READINESS_PROOF_FIELDS[1:5], expected_oids, strict=True
    ):
        assert proof[key] == expected_oid
    assert tuple(proof) == module.READINESS_PROOF_FIELDS
