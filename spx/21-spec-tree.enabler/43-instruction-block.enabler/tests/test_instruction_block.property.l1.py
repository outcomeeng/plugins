"""Property evidence for the instruction-block render model."""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_instruction_block_properties() -> None:
    """Generated instruction-block invariants hold across the harness-owned domains."""
    assert harness.instruction_block_properties_hold()
