"""Mapping evidence for root instruction-file topology seed resolution."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_root_instruction_topology_maps_to_harness_seed_bodies() -> None:
    observations = harness.observe_root_instruction_topology_seed_mapping()
    expected = {
        "only-claude": (
            (harness.INSTRUCTION_AGENTS, harness.ROOT_CLAUDE_BODY),
            (harness.INSTRUCTION_CLAUDE, harness.ROOT_CLAUDE_BODY),
        ),
        "only-agents": (
            (harness.INSTRUCTION_AGENTS, harness.ROOT_AGENTS_BODY),
            (harness.INSTRUCTION_CLAUDE, harness.ROOT_AGENTS_BODY),
        ),
        "separate": (
            (harness.INSTRUCTION_AGENTS, harness.ROOT_AGENTS_BODY),
            (harness.INSTRUCTION_CLAUDE, harness.ROOT_CLAUDE_BODY),
        ),
        "symlinked": (
            (harness.INSTRUCTION_AGENTS, harness.ROOT_SHARED_BODY),
            (harness.INSTRUCTION_CLAUDE, harness.ROOT_SHARED_BODY),
        ),
    }

    assert len(observations) == 4
    for observation in observations:
        assert observation.topology_name in expected
        assert observation.observed == expected[observation.topology_name]
