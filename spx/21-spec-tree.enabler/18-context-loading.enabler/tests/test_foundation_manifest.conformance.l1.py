"""Conformance evidence: every generated tree ships a foundation-resource manifest
matching the declared contract.

The oracle is the contract the validation module declares — supported schema
version, single core document path, and catalog shape — applied to the real
manifest each generated tree ships. The generated-tree domain comes from the
source-owned ``Target`` enum, never a hand-picked directory list.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.validation.foundation_manifest import (
    CORE_DOCUMENT_RELATIVE_PATH,
    MANIFEST_RELATIVE_PATH,
    SPEC_TREE_PLUGIN_NAME,
    SUPPORTED_SCHEMA_VERSION,
    manifest_violations,
    parse_foundation_manifest,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)


def _shipped_plugin_root(target: Target) -> Path:
    reader = DistTreeReader(root=marketplace_root_for_spec_tree_root_test(__file__))
    return reader.target_root(target) / SPEC_TREE_PLUGIN_NAME


@pytest.mark.parametrize("target", sorted(Target))
def test_shipped_manifest_declares_the_supported_schema_version(
    target: Target,
) -> None:
    manifest_path = _shipped_plugin_root(target) / MANIFEST_RELATIVE_PATH
    manifest = parse_foundation_manifest(manifest_path.read_text(encoding="utf-8"))
    assert manifest.schema_version == SUPPORTED_SCHEMA_VERSION


@pytest.mark.parametrize("target", sorted(Target))
def test_shipped_manifest_names_the_single_core_foundation_document(
    target: Target,
) -> None:
    manifest_path = _shipped_plugin_root(target) / MANIFEST_RELATIVE_PATH
    manifest = parse_foundation_manifest(manifest_path.read_text(encoding="utf-8"))
    assert manifest.core == CORE_DOCUMENT_RELATIVE_PATH


@pytest.mark.parametrize("target", sorted(Target))
def test_shipped_manifest_catalogs_carry_package_relative_paths(
    target: Target,
) -> None:
    manifest_path = _shipped_plugin_root(target) / MANIFEST_RELATIVE_PATH
    manifest = parse_foundation_manifest(manifest_path.read_text(encoding="utf-8"))
    declared = (*manifest.references, *manifest.templates, *manifest.examples)
    assert declared, "the shipped catalogs must declare the extended resources"
    assert all(not Path(path).is_absolute() for path in declared)


@pytest.mark.parametrize("target", sorted(Target))
def test_shipped_manifest_passes_the_package_checks(target: Target) -> None:
    assert manifest_violations(_shipped_plugin_root(target)) == []
