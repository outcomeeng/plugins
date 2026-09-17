"""Compliance evidence for converted Codex execution-policy guidance."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution.agents import (
    DISALLOWED_TOOLS_LIMITATION,
    MANUAL_REVIEW_GUIDANCE_CLOSE,
    MANUAL_REVIEW_GUIDANCE_OPEN,
    PERMISSION_MODE_LIMITATION,
    SKILL_ENABLEMENT_LIMITATION,
    SUPPORTED_FRONTMATTER_FIELDS,
    TOOLS_GUIDANCE_LIMITATION,
    UNSUPPORTED_FIELDS_LIMITATION,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.contracts import (
    RUNTIME_TOKEN_TOOL_KIND,
    RUNTIME_TOKEN_USE_SKILL_CAPABILITY,
    RUNTIME_TOKEN_USE_SKILL_NAMES,
    format_runtime_token,
)
from outcomeeng.distribution.profiles import AGENT_PROFILES, AgentProfile
from outcomeeng_testing.harnesses.agent_conversion import (
    installed_guarded_writer_toml,
    built_repository_agent_toml,
    oracle_string,
    oracle_strings,
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


def test_manual_guidance_uses_only_the_rendered_source_tool_set(
    tmp_path: Path,
) -> None:
    source, parsed = built_repository_agent_toml(
        tmp_path,
        agent_name="implementation-auditor",
    )
    source_tools = oracle_strings(source, "tools")
    token = format_runtime_token(
        RUNTIME_TOKEN_TOOL_KIND,
        RUNTIME_TOKEN_USE_SKILL_CAPABILITY,
    )
    instructions = toml_string(parsed, "developer_instructions")
    rendered_tools = tuple(tool for tool in source_tools if tool != token)
    manual_guidance = instructions.split(MANUAL_REVIEW_GUIDANCE_OPEN, 1)[1].split(
        MANUAL_REVIEW_GUIDANCE_CLOSE,
        1,
    )[0]

    assert token in source_tools
    assert "Use skill `spec-tree:audit-implementation`." in instructions
    assert all(tool in instructions for tool in rendered_tools)
    assert token not in instructions
    assert RUNTIME_TOKEN_USE_SKILL_NAMES[Target.CLAUDE.value] not in manual_guidance
