"""Scenario evidence for rendered agent to Codex custom-agent conversion."""

from __future__ import annotations

from outcomeeng_testing.harnesses.agent_conversion import (
    assert_agent_frontmatter_and_body_convert_to_codex_toml,
    assert_explicit_empty_tools_frontmatter_converts_to_restrictive_codex_config,
    assert_folded_yaml_description_converts_to_text,
    assert_rendered_codex_agent_tree_converts_to_codex_toml,
    assert_skills_are_preserved_as_developer_instruction_guidance,
)


def test_agent_frontmatter_and_body_convert_to_codex_toml() -> None:
    assert_agent_frontmatter_and_body_convert_to_codex_toml()


def test_folded_yaml_description_converts_to_text() -> None:
    assert_folded_yaml_description_converts_to_text()


def test_skills_are_preserved_as_developer_instruction_guidance() -> None:
    assert_skills_are_preserved_as_developer_instruction_guidance()


def test_rendered_codex_agent_tree_converts_to_codex_toml() -> None:
    assert_rendered_codex_agent_tree_converts_to_codex_toml()


def test_explicit_empty_tools_frontmatter_converts_to_restrictive_codex_config() -> (
    None
):
    assert_explicit_empty_tools_frontmatter_converts_to_restrictive_codex_config()
