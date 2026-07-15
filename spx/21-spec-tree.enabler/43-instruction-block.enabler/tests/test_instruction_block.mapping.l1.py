from outcomeeng_testing.harnesses import instruction_block as harness


def test_instruction_block_mapping_evidence() -> None:
    assert harness.mapping_evidence_is_valid()
