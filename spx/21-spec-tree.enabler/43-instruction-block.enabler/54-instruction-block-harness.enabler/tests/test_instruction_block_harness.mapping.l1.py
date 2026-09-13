"""Mapping evidence for root instruction-file topology seed resolution."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_root_instruction_topology_maps_to_harness_seed_bodies() -> None:
    def preserves_seeds(materialized: dict[str, str], expected: dict[str, str]) -> None:
        assert materialized == expected

    harness.observe_root_instruction_topology_seeds(preserves_seeds)
