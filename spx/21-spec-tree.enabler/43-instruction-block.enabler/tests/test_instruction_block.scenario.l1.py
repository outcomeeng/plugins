"""Scenario evidence for the instruction-block render model."""

from outcomeeng_testing.harnesses import instruction_block_scenarios as harness


def test_instruction_block_scenarios() -> None:
    """Every declared instruction-block interaction passes its harness scenario."""
    assert harness.instruction_block_scenarios_hold()
