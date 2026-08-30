"""Scenario evidence for native Codex agent artifact conversion."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from outcomeeng.distribution.agents import (
    AGENT_NAME_FIELD,
    AGENT_SKILL_ENABLED_FIELD,
    CODEX_AGENT_ENV_SEPARATOR,
    CODEX_AGENT_ENV_VAR,
    MODEL_MAPPINGS,
    READ_ONLY_SANDBOX_MODE,
    WEB_SEARCH_DISABLED,
)
from outcomeeng_testing.harnesses.agent_conversion import (
    CODEX_BLOCK_MCP_AGENT_FIXTURE,
    CODEX_FLOW_MCP_AGENT_FIXTURE,
    PLUGIN_NAME,
    agent_conversion_fixture,
    converted_codex_agent_with_yaml_mcp_toml,
    converted_default_codex_source_root_toml,
    converted_empty_tools_toml,
    converted_folded_description_toml,
    converted_source_agent_toml,
    oracle_mapping,
    oracle_optional_string,
    oracle_string,
    oracle_strings,
    parsed_toml_skill_config,
    toml_compatible,
    toml_string,
    toml_table,
)


def test_agent_frontmatter_and_body_convert_to_codex_toml(tmp_path: Path) -> None:
    expected, parsed = converted_source_agent_toml(tmp_path)
    expected_name = oracle_string(expected, "name")
    expected_skills = oracle_strings(expected, "skills")
    expected_tools = oracle_strings(expected, "tools")
    source_model = oracle_optional_string(expected, "model")

    assert source_model is not None
    assert parsed["name"] == expected_name
    assert parsed["description"] == oracle_string(expected, "description")
    assert parsed["model"] == dict(MODEL_MAPPINGS)[source_model]
    assert parsed["web_search"] == WEB_SEARCH_DISABLED
    assert "sandbox_mode" not in parsed
    assert toml_table(toml_table(parsed, "shell_environment_policy"), "set") == {
        CODEX_AGENT_ENV_VAR: f"{PLUGIN_NAME}{CODEX_AGENT_ENV_SEPARATOR}{expected_name}"
    }
    instructions = toml_string(parsed, "developer_instructions")
    assert expected.body in instructions
    assert all(skill in instructions for skill in expected_skills)
    assert parsed_toml_skill_config(parsed) == [
        {AGENT_NAME_FIELD: skill, AGENT_SKILL_ENABLED_FIELD: True}
        for skill in expected_skills
    ]
    assert all(tool in instructions for tool in expected_tools)


def test_folded_yaml_description_converts_to_text(tmp_path: Path) -> None:
    expected, parsed = converted_folded_description_toml(tmp_path)

    assert parsed["description"] == oracle_string(expected, "description")


def test_rendered_codex_agent_tree_converts_to_codex_toml(tmp_path: Path) -> None:
    expected, parsed = converted_default_codex_source_root_toml(tmp_path)
    expected_skills = oracle_strings(expected, "skills")

    assert parsed["name"] == oracle_string(expected, "name")
    assert parsed["description"] == oracle_string(expected, "description")
    assert parsed["model"] == oracle_string(expected, "model")
    assert parsed["model_reasoning_effort"] == oracle_string(
        expected, "model_reasoning_effort"
    )
    assert parsed["sandbox_mode"] == oracle_string(expected, "sandbox_mode")
    assert parsed["nickname_candidates"] == list(
        oracle_strings(expected, "nickname_candidates")
    )
    source_docs_server = oracle_mapping(expected, "mcp_servers")["docs"]
    assert isinstance(source_docs_server, Mapping)
    parsed_docs_server = toml_table(toml_table(parsed, "mcp_servers"), "docs")
    assert parsed_docs_server["command"] == source_docs_server["command"]
    source_args = source_docs_server["args"]
    assert isinstance(source_args, list)
    assert parsed_docs_server["args"] == source_args
    instructions = toml_string(parsed, "developer_instructions")
    assert expected.body in instructions
    assert all(skill in instructions for skill in expected_skills)
    assert parsed_toml_skill_config(parsed) == [
        {AGENT_NAME_FIELD: skill, AGENT_SKILL_ENABLED_FIELD: True}
        for skill in expected_skills
    ]


def test_yaml_mcp_server_mappings_convert_to_codex_toml(tmp_path: Path) -> None:
    observations = (
        converted_codex_agent_with_yaml_mcp_toml(
            tmp_path,
            agent_conversion_fixture(CODEX_BLOCK_MCP_AGENT_FIXTURE),
        ),
        converted_codex_agent_with_yaml_mcp_toml(
            tmp_path,
            agent_conversion_fixture(CODEX_FLOW_MCP_AGENT_FIXTURE),
        ),
    )

    for expected, parsed in observations:
        assert toml_table(parsed, "mcp_servers") == toml_compatible(
            oracle_mapping(expected, "mcp_servers")
        )


def test_explicit_empty_tools_frontmatter_converts_to_restrictive_codex_config(
    tmp_path: Path,
) -> None:
    parsed = converted_empty_tools_toml(tmp_path)

    assert parsed["web_search"] == WEB_SEARCH_DISABLED
    assert parsed["sandbox_mode"] == READ_ONLY_SANDBOX_MODE
