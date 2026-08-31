"""Mapping evidence for root instruction-file topology seed resolution."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_root_instruction_topology_maps_to_harness_seed_bodies() -> None:
    observations = harness.observe_root_instruction_topology_seed_mapping()
    topology_cases = harness.harness_seed_topology_cases()
    topology_domain = tuple(harness.HarnessSeedTopology)

    assert (
        tuple(topology_case.kind for topology_case in topology_cases) == topology_domain
    )
    assert tuple(observation.topology_kind for observation in observations) == (
        topology_domain
    )
    for observation, topology_case in zip(observations, topology_cases, strict=True):
        topology = topology_case.factory()
        assert observation.declared_files == tuple(sorted(topology.files.items()))
        assert observation.declared_symlinks == tuple(sorted(topology.symlinks.items()))

        placed = dict(topology.files)
        for link, target in topology.symlinks.items():
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
        assert observation.observed == expected, observation.topology_kind
