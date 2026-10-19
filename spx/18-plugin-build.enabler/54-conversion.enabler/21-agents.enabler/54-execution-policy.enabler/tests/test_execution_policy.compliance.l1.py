"""Compliance evidence for converted Codex execution-policy guidance."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from outcomeeng.distribution.agents import (
    DISALLOWED_TOOLS_LIMITATION,
    MANUAL_REVIEW_GUIDANCE_TAG,
    READ_ONLY_TOOLS,
    SCRIPT_CAPABLE_TOOLS,
    WEB_CAPABLE_TOOLS,
    WRITE_CAPABLE_TOOLS,
    convert_agent,
    render_agent_toml,
    MANUAL_REVIEW_GUIDANCE_CLOSE,
    MANUAL_REVIEW_GUIDANCE_OPEN,
    PERMISSION_MODE_LIMITATION,
    SKILL_ENABLEMENT_LIMITATION,
    SUPPORTED_FRONTMATTER_FIELDS,
    TOOLS_GUIDANCE_LIMITATION,
    UNSUPPORTED_FIELDS_LIMITATION,
)
from outcomeeng.distribution.contracts import (
    REQUIRE_SKILL_GUIDANCE_TEMPLATE,
    RUNTIME_TOKEN_USE_SKILL_NAMES,
    Target,
)
from outcomeeng.distribution.profiles import AGENT_PROFILES, AgentProfile
from outcomeeng_testing.harnesses.agent_conversion import (
    build_repository_agents,
    converted_instruction_value,
    parsed_toml_skill_config,
    installed_guarded_writer_toml,
    oracle_string,
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


SKILL_TOOL_NAME = RUNTIME_TOKEN_USE_SKILL_NAMES[Target.CLAUDE.value]
CAPABILITY_VOCABULARY = (
    READ_ONLY_TOOLS | SCRIPT_CAPABLE_TOOLS | WEB_CAPABLE_TOOLS | WRITE_CAPABLE_TOOLS
)
GUIDANCE_BLOCK = re.compile(
    rf"<{MANUAL_REVIEW_GUIDANCE_TAG}>(.*?)</{MANUAL_REVIEW_GUIDANCE_TAG}>", re.DOTALL
)
SOURCE_TOOLS_WITHOUT_SKILL = ("Read", "Grep")
SOURCE_SKILLS = ("alpha:first", "beta:second")


def _named_capabilities(text: str) -> frozenset[str]:
    return frozenset(
        name for name in CAPABILITY_VOCABULARY if re.search(rf"\b{name}\b", text)
    )


def test_guidance_names_only_capabilities_of_the_rendered_tool_set() -> None:
    agent = source_agent(
        skills=SOURCE_SKILLS,
        tools=SOURCE_TOOLS_WITHOUT_SKILL,
        tools_declared=True,
    )

    instructions = converted_instruction_value(convert_agent(agent))

    (guidance,) = GUIDANCE_BLOCK.findall(instructions)
    assert _named_capabilities(guidance) == frozenset(SOURCE_TOOLS_WITHOUT_SKILL)


def test_every_composing_agent_loads_skills_through_the_use_skill_instruction(
    tmp_path: Path,
) -> None:
    built = build_repository_agents(tmp_path)
    generated = tuple(
        tomllib.loads(path.read_text(encoding="utf-8"))
        for path in sorted((built.dist_root / Target.CODEX.value).rglob("*.toml"))
        if "agents" in path.parts
    )
    composing = [parsed for parsed in generated if "skills" in parsed]
    synthetic = convert_agent(
        source_agent(
            skills=SOURCE_SKILLS,
            tools=(*SOURCE_TOOLS_WITHOUT_SKILL, SKILL_TOOL_NAME),
            tools_declared=True,
        )
    )
    composing.append(tomllib.loads(render_agent_toml(synthetic)))

    assert len(composing) > 1
    for parsed in composing:
        instructions = toml_string(parsed, "developer_instructions")
        for entry in parsed_toml_skill_config(parsed):
            skill = toml_string(entry, "name")
            assert (
                REQUIRE_SKILL_GUIDANCE_TEMPLATE.format(skill_ref=skill) in instructions
            )
        assert SKILL_TOOL_NAME not in _named_capabilities(instructions)
