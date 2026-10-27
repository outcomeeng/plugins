"""Mapping evidence for explicit Product Tree wrapper-agent models."""

from outcomeeng.distribution.agents import (
    AGENT_NAME_FIELD,
    AGENT_SKILL_ENABLED_FIELD,
    SKILL_ENABLEMENT_LIMITATION,
    convert_agent,
)
from outcomeeng_testing.harnesses.agent_conversion import (
    converted_instruction_value,
    converted_skill_config,
    product_tree_wrapper_agents,
)


def test_product_tree_wrapper_agents_use_explicit_models() -> None:
    wrappers = product_tree_wrapper_agents()

    assert wrappers
    for agent in wrappers:
        assert agent.skills, f"{agent.source_path}: skills are required"
        converted = convert_agent(agent)
        assert "model" in converted.values
        assert converted_skill_config(converted) == tuple(
            {AGENT_NAME_FIELD: skill, AGENT_SKILL_ENABLED_FIELD: True}
            for skill in agent.skills
        )
        instructions = converted_instruction_value(converted)
        assert all(skill in instructions for skill in agent.skills)
        assert SKILL_ENABLEMENT_LIMITATION in instructions
