"""Compliance evidence for converted Codex execution-policy guidance."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from outcomeeng.distribution.agents import (
    AGENT_SKILLS_FIELD,
    AGENT_TOOLS_FIELD,
    DEVELOPER_INSTRUCTIONS_FIELD,
    DISALLOWED_TOOLS_LIMITATION,
    MANUAL_REVIEW_GUIDANCE_CLOSE,
    MANUAL_REVIEW_GUIDANCE_OPEN,
    PERMISSION_MODE_LIMITATION,
    SANDBOX_MODE_FIELD,
    SKILL_ENABLEMENT_LIMITATION,
    SOURCE_DISALLOWED_TOOLS_FIELD,
    SOURCE_PERMISSION_MODE_FIELD,
    SUPPORTED_FRONTMATTER_FIELDS,
    TOOLS_GUIDANCE_LIMITATION,
    UNSUPPORTED_FIELDS_LIMITATION,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import AGENT_PROFILES, PROFILE_FIELD
from outcomeeng.models import AgentProfile
from outcomeeng_testing.harnesses.agent_conversion import (
    installed_guarded_writer_toml,
    oracle_string,
    oracle_strings,
    toml_string,
)


def test_manual_guidance_preserves_source_only_fields(tmp_path: Path) -> None:
    expected, parsed = installed_guarded_writer_toml(tmp_path)
    expected_skills = oracle_strings(expected, AGENT_SKILLS_FIELD)
    expected_tools = oracle_strings(expected, AGENT_TOOLS_FIELD)
    expected_disallowed_tools = oracle_strings(expected, SOURCE_DISALLOWED_TOOLS_FIELD)
    expected_unsupported_fields = tuple(
        sorted(
            field
            for field in expected.frontmatter
            if field not in SUPPORTED_FRONTMATTER_FIELDS
        )
    )
    profile = AgentProfile(oracle_string(expected, PROFILE_FIELD))
    configuration = asdict(AGENT_PROFILES[Target.CODEX][profile])

    instructions = toml_string(parsed, DEVELOPER_INSTRUCTIONS_FIELD)
    before, opened, rest = instructions.partition(MANUAL_REVIEW_GUIDANCE_OPEN)
    guidance, closed, _after = rest.partition(MANUAL_REVIEW_GUIDANCE_CLOSE)

    assert expected_skills
    assert expected_tools
    assert expected_disallowed_tools
    assert expected_unsupported_fields
    assert {key: parsed[key] for key in configuration} == configuration
    assert opened
    assert closed
    assert expected.body in before
    assert all(skill in guidance for skill in expected_skills)
    assert all(tool in guidance for tool in expected_tools)
    assert all(tool in guidance for tool in expected_disallowed_tools)
    assert all(field in guidance for field in expected_unsupported_fields)
    assert oracle_string(expected, SOURCE_PERMISSION_MODE_FIELD) in guidance
    assert SKILL_ENABLEMENT_LIMITATION in guidance
    assert TOOLS_GUIDANCE_LIMITATION in guidance
    assert DISALLOWED_TOOLS_LIMITATION in guidance
    assert PERMISSION_MODE_LIMITATION in guidance
    assert UNSUPPORTED_FIELDS_LIMITATION in guidance
    assert SANDBOX_MODE_FIELD not in parsed
