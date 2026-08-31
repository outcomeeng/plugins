"""Mapping evidence for root instruction-file topology seed resolution."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_root_instruction_topology_maps_to_harness_seed_bodies() -> None:
    observations = harness.observe_root_instruction_topology_seed_mapping()

    assert len(observations) == 4
    for observation in observations:
        assert observation.observed == observation.expected
