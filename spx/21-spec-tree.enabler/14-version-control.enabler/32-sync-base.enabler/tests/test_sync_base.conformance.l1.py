"""Conformance evidence: the synchronizer's derivation entry points are the canonical objects."""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import load_changeset_scope_module
from outcomeeng_testing.harnesses.sync_base import load_sync_base_module


def test_base_derivation_entry_points_are_the_canonical_changeset_scope_objects() -> (
    None
):
    # The separately owned changeset-scope module is the oracle: each derivation
    # name the synchronizer exposes is that module's object, not a copy of it.
    canonical = load_changeset_scope_module()
    sync = load_sync_base_module()
    assert sync.detect_base_ref is canonical.detect_base_ref
    assert sync.remote_tracking_ref is canonical.remote_tracking_ref
    assert sync.detect_current_branch is canonical.detect_current_branch
