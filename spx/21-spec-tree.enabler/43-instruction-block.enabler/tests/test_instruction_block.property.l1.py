from outcomeeng_testing.harnesses import instruction_block as harness


def test_instruction_block_property_evidence() -> None:
    assert harness.property_evidence_is_valid()
