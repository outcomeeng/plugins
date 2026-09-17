"""Mapping evidence for native Codex agent model and skill fields."""

from __future__ import annotations

from outcomeeng.distribution.agents import (
    AGENT_NAME_FIELD,
    AGENT_SKILL_ENABLED_FIELD,
    AGENT_SKILL_INCLUDE_INSTRUCTIONS_FIELD,
    SKILL_ENABLEMENT_LIMITATION,
    convert_agent,
)
from dataclasses import asdict
from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import AGENT_PROFILES, AgentProfile
from outcomeeng_testing.harnesses.agent_conversion import (
    converted_instruction_value,
    converted_skill_config,
    source_agent,
    spec_tree_wrapper_agents,
)


def test_complete_native_profile_reaches_converted_agent() -> None:
    for profile in (*AgentProfile, None):
        converted = convert_agent(source_agent(profile=profile))
        expected = asdict(
            AGENT_PROFILES[Target.CODEX][profile or AgentProfile.STANDARD]
        )
        assert {key: converted.values[key] for key in expected} == expected


def test_skills_are_preserved_as_codex_config_and_guidance() -> None:
    wrappers = spec_tree_wrapper_agents()

    assert wrappers
    for source in wrappers:
        assert source.skills, f"{source.source_path}: skills are required"
        converted = convert_agent(source)
        instructions = converted_instruction_value(converted)
        assert converted_skill_config(converted) == tuple(
            {AGENT_NAME_FIELD: skill, AGENT_SKILL_ENABLED_FIELD: True}
            for skill in source.skills
        )
        skills = converted.values["skills"]
        assert isinstance(skills, dict)
        assert skills[AGENT_SKILL_INCLUDE_INSTRUCTIONS_FIELD] is True
        assert all(skill in instructions for skill in source.skills)
        assert SKILL_ENABLEMENT_LIMITATION in instructions
