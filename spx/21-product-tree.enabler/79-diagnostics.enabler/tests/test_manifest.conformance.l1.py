"""Conformance evidence for the shipped diagnose manifest.

The diagnostics node declares that the manifest passed to ``spx diagnose``
carries the product's source-of-truth spx-version floor, the methodology
marketplace identity, the owning plugin identity, and the selected check set.
These tests verify the authored source and the committed dist tree.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.diagnostics import (
    authored_diagnose_manifests_match_contract,
    canonical_shipped_diagnose_manifests_match_contract,
    rendered_diagnose_manifests_match_their_owners,
)


def test_authored_manifest_sources_the_floor_through_the_build_token() -> None:
    """Authored manifests carry only source-owned build tokens and values."""
    assert authored_diagnose_manifests_match_contract()


def test_each_shipped_target_renders_the_manifest_contract() -> None:
    """Every shipped target carries the rendered diagnose manifest contract."""
    assert canonical_shipped_diagnose_manifests_match_contract()


def test_each_manifest_requires_only_its_owning_plugin() -> None:
    assert rendered_diagnose_manifests_match_their_owners()
