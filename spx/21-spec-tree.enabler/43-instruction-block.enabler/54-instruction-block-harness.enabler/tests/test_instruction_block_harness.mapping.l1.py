"""Mapping evidence for root instruction-file topology seed resolution."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_root_instruction_topology_maps_to_harness_seed_bodies() -> None:
    observations = harness.observe_root_instruction_topology_seed_mapping()

    assert len(observations) == 4
    for observation in observations:
        placed = dict(observation.declared_files)
        for link, target in observation.declared_symlinks:
            placed[link] = placed[target]

        claude_seed = placed.get(harness.INSTRUCTION_CLAUDE)
        agents_seed = placed.get(harness.INSTRUCTION_AGENTS, claude_seed)
        if claude_seed is None:
            claude_seed = agents_seed
        if claude_seed is None or agents_seed is None:
            claude_seed = agents_seed = ""

        expected = tuple(
            sorted(
                {
                    harness.INSTRUCTION_CLAUDE: claude_seed,
                    harness.INSTRUCTION_AGENTS: agents_seed,
                }.items()
            )
        )
        assert observation.observed == expected, observation.topology_name
