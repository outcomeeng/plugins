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
    SUPPORTED_SCHEMA_VERSION,
    authored_plugin_root,
    manifest_violations,
    parse_foundation_manifest,
    shipped_plugin_root,
)
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)


def _shipped_plugin_root(target: Target) -> Path:
    return shipped_plugin_root(
        marketplace_root_for_spec_tree_root_test(__file__), target
    )


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


@pytest.mark.parametrize("target", sorted(Target))
def test_shipped_manifest_is_byte_identical_to_the_authored_manifest(
    target: Target,
) -> None:
    repo_root = marketplace_root_for_spec_tree_root_test(__file__)
    authored = authored_plugin_root(repo_root) / MANIFEST_RELATIVE_PATH
    shipped = _shipped_plugin_root(target) / MANIFEST_RELATIVE_PATH
    assert shipped.read_bytes() == authored.read_bytes()
