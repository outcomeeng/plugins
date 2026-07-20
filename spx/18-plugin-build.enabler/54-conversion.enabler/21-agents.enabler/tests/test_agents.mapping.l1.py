"""Mapping evidence for agent model, effort, and permission conversion."""

from __future__ import annotations

from outcomeeng_testing.harnesses.agent_conversion import (
    assert_all_tools_sentinel_leaves_sandbox_to_runtime_default,
    assert_all_tools_sentinel_leaves_web_search_to_runtime_default,
    assert_explicit_empty_tool_allowlist_disables_web_search,
    assert_explicit_empty_tool_allowlist_infers_read_only_sandbox,
    assert_explicit_unmapped_permission_mode_blocks_read_only_inference,
    assert_identity_preflight_precedes_source_role_instructions,
    assert_missing_tool_allowlist_leaves_sandbox_to_runtime_default,
    assert_missing_tool_allowlist_leaves_web_search_to_runtime_default,
    assert_opus_model_maps_to_distinct_top_tier_codex_model,
    assert_permission_modes_map_to_codex_sandbox_or_manual_review,
    assert_read_only_tool_allowlist_infers_read_only_sandbox,
    assert_read_only_web_tool_allowlist_infers_read_only_sandbox,
    assert_script_capable_tool_allowlist_leaves_sandbox_to_runtime_default,
    assert_source_effort_maps_to_codex_reasoning_effort,
    assert_source_effort_reaches_converted_codex_reasoning_effort,
    assert_source_model_maps_to_codex_model,
    assert_skills_are_preserved_as_codex_config_and_guidance,
    assert_supported_permission_mode_reaches_converted_codex_sandbox_mode,
    assert_tool_allowlist_with_web_tool_leaves_web_search_to_runtime_default,
    assert_tool_allowlist_without_web_tool_disables_web_search,
    assert_unmapped_permission_mode_converts_to_manual_review_guidance,
    assert_web_capable_only_tool_allowlist_infers_read_only_sandbox,
    assert_write_capable_tool_allowlist_converts_to_manual_review_guidance,
    assert_write_capable_tool_allowlist_leaves_sandbox_to_runtime_default,
)


def test_source_model_maps_to_codex_model() -> None:
    assert_source_model_maps_to_codex_model()


def test_skills_are_preserved_as_codex_config_and_guidance() -> None:
    assert_skills_are_preserved_as_codex_config_and_guidance()


def test_identity_preflight_precedes_source_role_instructions() -> None:
    assert_identity_preflight_precedes_source_role_instructions()


def test_opus_model_maps_to_distinct_top_tier_codex_model() -> None:
    assert_opus_model_maps_to_distinct_top_tier_codex_model()


def test_source_effort_maps_to_codex_reasoning_effort() -> None:
    assert_source_effort_maps_to_codex_reasoning_effort()


def test_source_effort_reaches_converted_codex_reasoning_effort() -> None:
    assert_source_effort_reaches_converted_codex_reasoning_effort()


def test_permission_modes_map_to_codex_sandbox_or_manual_review() -> None:
    assert_permission_modes_map_to_codex_sandbox_or_manual_review()


def test_supported_permission_mode_reaches_converted_codex_sandbox_mode() -> None:
    assert_supported_permission_mode_reaches_converted_codex_sandbox_mode()


def test_tool_allowlist_without_web_tool_disables_web_search() -> None:
    assert_tool_allowlist_without_web_tool_disables_web_search()


def test_explicit_empty_tool_allowlist_disables_web_search() -> None:
    assert_explicit_empty_tool_allowlist_disables_web_search()


def test_missing_tool_allowlist_leaves_web_search_to_runtime_default() -> None:
    assert_missing_tool_allowlist_leaves_web_search_to_runtime_default()


def test_tool_allowlist_with_web_tool_leaves_web_search_to_runtime_default() -> None:
    assert_tool_allowlist_with_web_tool_leaves_web_search_to_runtime_default()


def test_all_tools_sentinel_leaves_web_search_to_runtime_default() -> None:
    assert_all_tools_sentinel_leaves_web_search_to_runtime_default()


def test_read_only_tool_allowlist_infers_read_only_sandbox() -> None:
    assert_read_only_tool_allowlist_infers_read_only_sandbox()


def test_read_only_web_tool_allowlist_infers_read_only_sandbox() -> None:
    assert_read_only_web_tool_allowlist_infers_read_only_sandbox()


def test_web_capable_only_tool_allowlist_infers_read_only_sandbox() -> None:
    assert_web_capable_only_tool_allowlist_infers_read_only_sandbox()


def test_all_tools_sentinel_leaves_sandbox_to_runtime_default() -> None:
    assert_all_tools_sentinel_leaves_sandbox_to_runtime_default()


def test_explicit_empty_tool_allowlist_infers_read_only_sandbox() -> None:
    assert_explicit_empty_tool_allowlist_infers_read_only_sandbox()


def test_missing_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert_missing_tool_allowlist_leaves_sandbox_to_runtime_default()


def test_write_capable_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert_write_capable_tool_allowlist_leaves_sandbox_to_runtime_default()


def test_script_capable_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    assert_script_capable_tool_allowlist_leaves_sandbox_to_runtime_default()


def test_explicit_unmapped_permission_mode_blocks_read_only_inference() -> None:
    assert_explicit_unmapped_permission_mode_blocks_read_only_inference()


def test_unmapped_permission_mode_converts_to_manual_review_guidance() -> None:
    assert_unmapped_permission_mode_converts_to_manual_review_guidance()


def test_write_capable_tool_allowlist_converts_to_manual_review_guidance() -> None:
    assert_write_capable_tool_allowlist_converts_to_manual_review_guidance()
