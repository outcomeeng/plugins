"""Compliance evidence for converted Codex agent boundaries."""

from __future__ import annotations

from outcomeeng_testing.harnesses.agent_conversion import (
    assert_default_source_root_uses_rendered_codex_agents,
    assert_duplicate_generated_agent_filename_fails_before_install_writes,
    assert_environment_marker_is_namespaced_by_source_plugin,
    assert_environment_marker_without_source_plugin_uses_agent_name,
    assert_generated_toml_stays_outside_codex_plugin_manifest_content,
    assert_install_overwrites_generated_owned_agent_from_manifest,
    assert_install_refuses_to_claim_untracked_identical_agent,
    assert_invalid_generated_manifest_uses_converter_error,
    assert_manual_guidance_preserves_source_only_fields,
)


def test_manual_guidance_preserves_source_only_fields() -> None:
    assert_manual_guidance_preserves_source_only_fields()


def test_default_source_root_uses_rendered_codex_agents() -> None:
    assert_default_source_root_uses_rendered_codex_agents()


def test_generated_toml_stays_outside_codex_plugin_manifest_content() -> None:
    assert_generated_toml_stays_outside_codex_plugin_manifest_content()


def test_environment_marker_is_namespaced_by_source_plugin() -> None:
    assert_environment_marker_is_namespaced_by_source_plugin()


def test_environment_marker_without_source_plugin_uses_agent_name() -> None:
    assert_environment_marker_without_source_plugin_uses_agent_name()


def test_invalid_generated_manifest_uses_converter_error() -> None:
    assert_invalid_generated_manifest_uses_converter_error()


def test_install_refuses_to_claim_untracked_identical_agent() -> None:
    assert_install_refuses_to_claim_untracked_identical_agent()


def test_install_overwrites_generated_owned_agent_from_manifest() -> None:
    assert_install_overwrites_generated_owned_agent_from_manifest()


def test_duplicate_generated_agent_filename_fails_before_install_writes() -> None:
    assert_duplicate_generated_agent_filename_fails_before_install_writes()
