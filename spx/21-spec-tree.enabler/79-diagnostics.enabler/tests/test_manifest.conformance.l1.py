"""Conformance evidence for the shipped diagnose manifest.

The diagnostics node declares that the manifest passed to ``spx diagnose``
carries the product's source-of-truth spx-version floor, the methodology
marketplace identity, the offered plugin set, and the selected check set. These
tests verify the authored source and the committed dist tree.
"""

from __future__ import annotations

from outcomeeng.distribution.contracts import Target
from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION
from outcomeeng_testing.harnesses.diagnostics import (
    EXPECTED_DIAGNOSE_CHECKS,
    EXPECTED_MARKETPLACE,
    SPX_FLOOR_TOKEN,
    authored_diagnose_manifest,
    expected_plugin_names,
    read_shipped_diagnose_manifest,
)


def test_authored_manifest_sources_the_floor_through_the_build_token() -> None:
    """The authored manifest carries the floor token, not a copied value."""
    assert authored_diagnose_manifest()["spx_floor"] == SPX_FLOOR_TOKEN


def test_each_shipped_target_renders_the_manifest_contract() -> None:
    """Every shipped target carries the rendered diagnose manifest contract."""
    expected = {
        "spx_floor": REQUIRED_SPX_VERSION,
        "marketplace": EXPECTED_MARKETPLACE,
        "expected_plugins": list(expected_plugin_names()),
        "checks": list(EXPECTED_DIAGNOSE_CHECKS),
    }

    for target in Target:
        manifest = read_shipped_diagnose_manifest(target)
        assert manifest == expected
