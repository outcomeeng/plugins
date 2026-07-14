"""Conformance evidence for the shipped diagnose manifest.

The diagnostics node declares that the manifest passed to ``spx diagnose``
carries the product's source-of-truth spx-version floor, the methodology
marketplace identity, the owning plugin identity, and the selected check set.
These tests verify the authored source and the committed dist tree.
"""

from __future__ import annotations

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.diagnose_manifest import (
    authored_diagnose_manifest_contract,
    shipped_diagnose_manifest_contract,
)
from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION
from outcomeeng_testing.harnesses.diagnostics import (
    authored_diagnose_manifest,
    authored_diagnose_plugin_name,
    read_shipped_diagnose_manifest,
    rendered_diagnose_manifests_match_their_owners,
)


def test_authored_manifest_sources_the_floor_through_the_build_token() -> None:
    """The authored manifest carries only source-owned build tokens and values."""
    assert authored_diagnose_manifest() == authored_diagnose_manifest_contract()


def test_each_shipped_target_renders_the_manifest_contract() -> None:
    """Every shipped target carries the rendered diagnose manifest contract."""
    for target in Target:
        assert read_shipped_diagnose_manifest(
            target
        ) == shipped_diagnose_manifest_contract(
            plugin_name=authored_diagnose_plugin_name(),
            spx_floor=REQUIRED_SPX_VERSION,
        )


def test_each_manifest_requires_only_its_owning_plugin() -> None:
    assert rendered_diagnose_manifests_match_their_owners()
