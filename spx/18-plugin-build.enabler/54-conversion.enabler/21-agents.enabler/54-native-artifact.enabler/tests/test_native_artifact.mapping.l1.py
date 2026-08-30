"""Mapping evidence for native Codex agent model and skill fields."""

from __future__ import annotations

from outcomeeng.distribution.agents import (
    AGENT_NAME_FIELD,
    AGENT_SKILL_ENABLED_FIELD,
    EFFORT_MAPPINGS,
    INHERIT_MODEL_VALUE,
    MODEL_MAPPINGS,
    MODEL_PREFIX_EXAMPLE_SUFFIX,
    SKILL_ENABLEMENT_LIMITATION,
    convert_agent,
    map_effort,
    map_model,
)
from outcomeeng_testing.harnesses.agent_conversion import (
    EXPECTED_EFFORT_CORRESPONDENCE,
    EXPECTED_MODEL_CORRESPONDENCE,
    converted_instruction_value,
    converted_skill_config,
    source_agent,
    spec_tree_wrapper_agents,
)


def test_source_model_maps_to_codex_model() -> None:
    assert {source for source, _ in EXPECTED_MODEL_CORRESPONDENCE} == {
        source for source, _ in MODEL_MAPPINGS
    }
    for source, expected in EXPECTED_MODEL_CORRESPONDENCE:
        assert map_model(source) == expected
        if source.startswith("claude-"):
            assert map_model(f"{source}{MODEL_PREFIX_EXAMPLE_SUFFIX}") == expected

    assert map_model(INHERIT_MODEL_VALUE) is None


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
        assert all(skill in instructions for skill in source.skills)
        assert SKILL_ENABLEMENT_LIMITATION in instructions


def test_source_effort_maps_to_codex_reasoning_effort() -> None:
    assert {source for source, _ in EXPECTED_EFFORT_CORRESPONDENCE} == set(
        EFFORT_MAPPINGS
    )
    for source, expected in EXPECTED_EFFORT_CORRESPONDENCE:
        assert map_effort(source) == expected


def test_source_effort_reaches_converted_codex_reasoning_effort() -> None:
    for source, expected in EXPECTED_EFFORT_CORRESPONDENCE:
        converted = convert_agent(source_agent(effort=source))
        assert converted.values["model_reasoning_effort"] == expected
