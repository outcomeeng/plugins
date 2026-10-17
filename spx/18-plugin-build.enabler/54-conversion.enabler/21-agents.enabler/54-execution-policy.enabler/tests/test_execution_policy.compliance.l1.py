"""Compliance evidence for converted Codex execution-policy guidance."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution.agents import (
    DISALLOWED_TOOLS_LIMITATION,
    MANUAL_REVIEW_GUIDANCE_CLOSE,
    MANUAL_REVIEW_GUIDANCE_OPEN,
    PERMISSION_MODE_LIMITATION,
    READ_ONLY_TOOLS,
    SCRIPT_CAPABLE_TOOLS,
    SKILL_ENABLEMENT_LIMITATION,
    SUPPORTED_FRONTMATTER_FIELDS,
    TOOLS_GUIDANCE_LIMITATION,
    UNSUPPORTED_FIELDS_LIMITATION,
    WEB_CAPABLE_TOOLS,
    WRITE_CAPABLE_TOOLS,
    convert_agent,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import AGENT_PROFILES, AgentProfile
from outcomeeng_testing.harnesses.agent_conversion import (
    installed_guarded_writer_toml,
    oracle_string,
    converted_instruction_value,
    oracle_strings,
    source_agent,
    toml_string,
)


def test_manual_guidance_preserves_source_only_fields(tmp_path: Path) -> None:
    expected, parsed = installed_guarded_writer_toml(tmp_path)
    expected_skills = oracle_strings(expected, "skills")
    expected_tools = oracle_strings(expected, "tools")
    expected_disallowed_tools = oracle_strings(expected, "disallowedTools")
    expected_unsupported_fields = tuple(
        sorted(
            field
            for field in expected.frontmatter
            if field not in SUPPORTED_FRONTMATTER_FIELDS
        )
    )

    instructions = toml_string(parsed, "developer_instructions")
    profile = AgentProfile(oracle_string(expected, "profile"))
    assert parsed["model"] == AGENT_PROFILES[Target.CODEX][profile].model
    assert all(skill in instructions for skill in expected_skills)
    assert all(tool in instructions for tool in expected_tools)
    assert all(tool in instructions for tool in expected_disallowed_tools)
    assert all(field in instructions for field in expected_unsupported_fields)
    assert oracle_string(expected, "permissionMode") in instructions
    assert SKILL_ENABLEMENT_LIMITATION in instructions
    assert TOOLS_GUIDANCE_LIMITATION in instructions
    assert DISALLOWED_TOOLS_LIMITATION in instructions
    assert PERMISSION_MODE_LIMITATION in instructions
    assert UNSUPPORTED_FIELDS_LIMITATION in instructions
    assert MANUAL_REVIEW_GUIDANCE_OPEN in instructions
    assert MANUAL_REVIEW_GUIDANCE_CLOSE in instructions
    assert "##" not in instructions
    assert "sandbox_mode" not in parsed


def test_manual_guidance_never_names_a_capability_absent_from_the_source_tool_set() -> None:
    universe = tuple(
        sorted(
            READ_ONLY_TOOLS
            | SCRIPT_CAPABLE_TOOLS
            | WEB_CAPABLE_TOOLS
            | WRITE_CAPABLE_TOOLS
        )
    )
    for absent in universe:
        declared = tuple(tool for tool in universe if tool != absent)
        converted = convert_agent(source_agent(tools=declared, tools_declared=True))
        instructions = converted_instruction_value(converted)
        guidance = instructions.split(MANUAL_REVIEW_GUIDANCE_OPEN, 1)[1]

        assert f"`{absent}`" not in guidance, absent
        assert all(f"`{tool}`" in guidance for tool in declared), absent
