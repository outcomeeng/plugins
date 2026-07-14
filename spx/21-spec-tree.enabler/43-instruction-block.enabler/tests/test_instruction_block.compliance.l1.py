"""Compliance evidence for the instruction-block render model."""

from outcomeeng_testing.harnesses import instruction_block_compliance as harness


def test_instruction_block_compliance() -> None:
    """Instruction-block output obeys every harness-owned compliance check."""
    assert harness.instruction_block_compliance_holds()
