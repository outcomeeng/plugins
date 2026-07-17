"""Level 1 scenarios for plugin manifest validation."""

from __future__ import annotations

from outcomeeng_testing.harnesses.plugin_manifest import (
    absent_claude_version_is_reported,
    absent_codex_manifest_skips_parity,
    absent_codex_version_is_reported,
    absent_manifest_versions_are_reported,
    absent_validation_targets_are_rejected,
    catalog_entry_without_plugin_is_reported,
    catalog_mismatch_makes_main_fail,
    failed_plugin_validation_is_reported,
    generated_plugins_are_validated,
    invocation_exit_is_not_blocked_by_descendant,
    manifest_version_drift_names_both_versions,
    marketplace_is_validated,
    matching_catalogs_pass,
    matching_manifest_versions_pass,
    parity_drift_makes_main_fail,
    plugin_absent_from_claude_catalog_is_reported,
    plugin_absent_from_codex_catalog_is_reported,
    requires_fork,
    source_plugins_are_validated,
    timeout_terminates_group_and_names_command,
)


def test_marketplace_is_validated() -> None:
    assert marketplace_is_validated()


def test_source_plugins_are_validated() -> None:
    assert source_plugins_are_validated()


def test_generated_plugins_are_validated() -> None:
    assert generated_plugins_are_validated()


def test_failed_plugin_validation_is_reported() -> None:
    assert failed_plugin_validation_is_reported()


def test_absent_validation_targets_are_rejected() -> None:
    assert absent_validation_targets_are_rejected()


def test_plugin_absent_from_claude_catalog_is_reported() -> None:
    assert plugin_absent_from_claude_catalog_is_reported()


def test_plugin_absent_from_codex_catalog_is_reported() -> None:
    assert plugin_absent_from_codex_catalog_is_reported()


def test_matching_catalogs_pass() -> None:
    assert matching_catalogs_pass()


def test_catalog_entry_without_plugin_is_reported() -> None:
    assert catalog_entry_without_plugin_is_reported()


def test_catalog_mismatch_makes_main_fail() -> None:
    assert catalog_mismatch_makes_main_fail()


def test_matching_manifest_versions_pass() -> None:
    assert matching_manifest_versions_pass()


def test_manifest_version_drift_names_both_versions() -> None:
    assert manifest_version_drift_names_both_versions()


def test_absent_codex_manifest_skips_parity() -> None:
    assert absent_codex_manifest_skips_parity()


def test_absent_claude_version_is_reported() -> None:
    assert absent_claude_version_is_reported()


def test_absent_codex_version_is_reported() -> None:
    assert absent_codex_version_is_reported()


def test_absent_manifest_versions_are_reported() -> None:
    assert absent_manifest_versions_are_reported()


def test_parity_drift_makes_main_fail() -> None:
    assert parity_drift_makes_main_fail()


@requires_fork
def test_timeout_terminates_group_and_names_command() -> None:
    assert timeout_terminates_group_and_names_command()


@requires_fork
def test_invocation_exit_is_not_blocked_by_descendant() -> None:
    assert invocation_exit_is_not_blocked_by_descendant()
