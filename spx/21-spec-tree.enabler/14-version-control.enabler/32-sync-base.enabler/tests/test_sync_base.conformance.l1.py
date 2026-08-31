"""Conformance evidence for the sync-base readiness-preservation proof."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    build_behind_base_repo,
    load_sync_base_module,
)

_FULL_OID_LEN = 40


def test_proof_conforms_to_versioned_portable_schema(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / "pool"
    root.mkdir()
    module = load_sync_base_module()
    handle = build_behind_base_repo(root)

    payload = module.sync_base(handle.repo).to_json_dict()
    proof = payload["preservation"]

    assert proof["schema_version"] == module.READINESS_SCHEMA_VERSION
    for key in ("old_base_oid", "new_base_oid", "old_head_oid", "new_head_oid"):
        assert len(proof[key]) == _FULL_OID_LEN
        assert proof[key] == proof[key].lower()
    assert tuple(proof) == module.READINESS_PROOF_FIELDS
