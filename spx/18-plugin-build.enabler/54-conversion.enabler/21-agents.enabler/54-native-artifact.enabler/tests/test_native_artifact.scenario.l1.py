"""Scenario evidence for native Codex agent artifact conversion."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from outcomeeng.distribution.agents import (
    AGENT_DESCRIPTION_FIELD,
    AGENT_MCP_SERVERS_FIELD,
    AGENT_NAME_FIELD,
    AGENT_NICKNAME_CANDIDATES_FIELD,
    AGENT_SKILL_ENABLED_FIELD,
    AGENT_SKILLS_FIELD,
    AGENT_TOOLS_FIELD,
    APPROVAL_POLICY_FIELD,
    CODEX_AGENT_ENV_SEPARATOR,
    CODEX_AGENT_ENV_VAR,
    DEVELOPER_INSTRUCTIONS_FIELD,
    READ_ONLY_SANDBOX_MODE,
    SANDBOX_MODE_FIELD,
    SHELL_ENVIRONMENT_POLICY_FIELD,
    SHELL_ENVIRONMENT_SET_FIELD,
    WEB_SEARCH_DISABLED,
    WEB_SEARCH_FIELD,
    convert_agent,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import AGENT_PROFILES, PROFILE_FIELD
from outcomeeng.models import AgentProfile
from outcomeeng.validation.audit_artifacts import IMPLEMENTATION_AUDITOR_STEM
from outcomeeng_testing.harnesses.agent_conversion import (
    YAML_MCP_SERVER_FIXTURES,
    converted_codex_agent_with_yaml_mcp_toml,
    converted_default_codex_source_root_toml,
    converted_empty_tools_toml,
    converted_folded_description_toml,
    converted_source_agent_toml,
    oracle_mapping,
    oracle_string,
    oracle_strings,
    parsed_toml_skill_config,
    spec_tree_wrapper_agents,
    toml_compatible,
    toml_string,
    toml_table,
)


def test_agent_frontmatter_and_body_convert_to_codex_toml(tmp_path: Path) -> None:
    expected, parsed = converted_source_agent_toml(tmp_path)
    expected_name = oracle_string(expected, AGENT_NAME_FIELD)
    expected_skills = oracle_strings(expected, AGENT_SKILLS_FIELD)
    expected_tools = oracle_strings(expected, AGENT_TOOLS_FIELD)
    profile = AgentProfile(oracle_string(expected, PROFILE_FIELD))
    assert parsed[AGENT_NAME_FIELD] == expected_name
    assert parsed[AGENT_DESCRIPTION_FIELD] == oracle_string(
        expected, AGENT_DESCRIPTION_FIELD
    )
    configuration = asdict(AGENT_PROFILES[Target.CODEX][profile])
    assert {key: parsed[key] for key in configuration} == configuration
    assert parsed[WEB_SEARCH_FIELD] == WEB_SEARCH_DISABLED
    assert SANDBOX_MODE_FIELD not in parsed
    assert toml_table(
        toml_table(parsed, SHELL_ENVIRONMENT_POLICY_FIELD),
        SHELL_ENVIRONMENT_SET_FIELD,
    ) == {
        CODEX_AGENT_ENV_VAR: (
            f"{expected.path.parents[1].name}{CODEX_AGENT_ENV_SEPARATOR}"
            f"{expected.path.stem}"
        )
    }
    instructions = toml_string(parsed, DEVELOPER_INSTRUCTIONS_FIELD)
    assert expected.body in instructions
    assert expected_skills
    assert all(skill in instructions for skill in expected_skills)
    assert parsed_toml_skill_config(parsed) == [
        {AGENT_NAME_FIELD: skill, AGENT_SKILL_ENABLED_FIELD: True}
        for skill in expected_skills
    ]
    assert expected_tools
    assert all(tool in instructions for tool in expected_tools)


def test_journal_writing_auditors_inherit_codex_execution_policy() -> None:
    sources = {source.name: source for source in spec_tree_wrapper_agents()}

    # The Change auditor and the implementation auditor are the spec's case.
    for agent_name in ("change-auditor", IMPLEMENTATION_AUDITOR_STEM):
        source = sources[agent_name]
        converted = convert_agent(source)

        assert source.sandbox_mode is None
        assert source.approval_policy is None
        assert SANDBOX_MODE_FIELD not in converted.values
        assert APPROVAL_POLICY_FIELD not in converted.values


def test_folded_yaml_description_converts_to_text(tmp_path: Path) -> None:
    expected, parsed = converted_folded_description_toml(tmp_path)

    assert parsed[AGENT_DESCRIPTION_FIELD] == oracle_string(
        expected, AGENT_DESCRIPTION_FIELD
    )


def test_rendered_codex_agent_tree_converts_to_codex_toml(tmp_path: Path) -> None:
    expected, parsed = converted_default_codex_source_root_toml(tmp_path)
    expected_skills = oracle_strings(expected, AGENT_SKILLS_FIELD)

    assert parsed[AGENT_NAME_FIELD] == oracle_string(expected, AGENT_NAME_FIELD)
    assert parsed[AGENT_DESCRIPTION_FIELD] == oracle_string(
        expected, AGENT_DESCRIPTION_FIELD
    )
    profile = AgentProfile(oracle_string(expected, PROFILE_FIELD))
    configuration = asdict(AGENT_PROFILES[Target.CODEX][profile])
    assert {key: parsed[key] for key in configuration} == configuration
    assert parsed[SANDBOX_MODE_FIELD] == oracle_string(expected, SANDBOX_MODE_FIELD)
    assert parsed[AGENT_NICKNAME_CANDIDATES_FIELD] == list(
        oracle_strings(expected, AGENT_NICKNAME_CANDIDATES_FIELD)
    )
    assert toml_table(parsed, AGENT_MCP_SERVERS_FIELD) == toml_compatible(
        oracle_mapping(expected, AGENT_MCP_SERVERS_FIELD)
    )
    instructions = toml_string(parsed, DEVELOPER_INSTRUCTIONS_FIELD)
    assert expected.body in instructions
    assert expected_skills
    assert all(skill in instructions for skill in expected_skills)
    assert parsed_toml_skill_config(parsed) == [
        {AGENT_NAME_FIELD: skill, AGENT_SKILL_ENABLED_FIELD: True}
        for skill in expected_skills
    ]


def test_yaml_mcp_server_mappings_convert_to_codex_toml(tmp_path: Path) -> None:
    assert YAML_MCP_SERVER_FIXTURES
    for index, fixture in enumerate(YAML_MCP_SERVER_FIXTURES):
        expected, parsed = converted_codex_agent_with_yaml_mcp_toml(
            tmp_path / str(index), fixture
        )

        assert toml_table(parsed, AGENT_MCP_SERVERS_FIELD) == toml_compatible(
            oracle_mapping(expected, AGENT_MCP_SERVERS_FIELD)
        )


def test_explicit_empty_tools_frontmatter_converts_to_restrictive_codex_config(
    tmp_path: Path,
) -> None:
    parsed = converted_empty_tools_toml(tmp_path)

    assert parsed[WEB_SEARCH_FIELD] == WEB_SEARCH_DISABLED
    assert parsed[SANDBOX_MODE_FIELD] == READ_ONLY_SANDBOX_MODE
