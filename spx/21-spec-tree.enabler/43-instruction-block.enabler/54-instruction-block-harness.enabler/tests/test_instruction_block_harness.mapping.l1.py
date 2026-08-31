"""Mapping evidence for root instruction-file topology seed resolution."""

from outcomeeng_testing.generators.instruction_block import (
    HarnessSeedTopology,
    harness_seed_topology_contract,
)
from outcomeeng_testing.harnesses import instruction_block as harness


def test_root_instruction_topology_maps_to_harness_seed_bodies() -> None:
    observations = harness.observe_root_instruction_topology_seed_mapping()
    topology_cases = harness.harness_seed_topology_cases()
    topology_domain = tuple(HarnessSeedTopology)
    cases = harness.generated_cases()

    assert (
        tuple(topology_case.kind for topology_case in topology_cases) == topology_domain
    )
    assert tuple(observation.topology_kind for observation in observations) == (
        topology_domain
    )
    for observation in observations:
        contract = harness_seed_topology_contract(observation.topology_kind, cases)
        assert tuple(sorted(name for name, _ in observation.declared_files)) == tuple(
            sorted(contract.declared_files)
        )
        assert observation.declared_symlinks == tuple(
            sorted(contract.declared_symlinks)
        )

        expected = tuple(
            sorted(
                {
                    cases.instruction_claude: harness.instruction_block_fixture_text(
                        contract.claude_seed_fixture
                    ),
                    cases.instruction_agents: harness.instruction_block_fixture_text(
                        contract.agents_seed_fixture
                    ),
                }.items()
            )
        )
        assert observation.observed == expected, observation.topology_kind
