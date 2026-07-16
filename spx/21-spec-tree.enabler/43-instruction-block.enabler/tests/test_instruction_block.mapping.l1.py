from outcomeeng_testing.harnesses import instruction_block_mapping_evidence as evidence


def test_instruction_block_mapping_evidence() -> None:
    assert (
        evidence.mapping_evidence_run().executed
        == evidence.mapping_evidence_declarations()
    )
