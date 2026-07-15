from outcomeeng_testing.harnesses import instruction_block_property_evidence as evidence


def test_instruction_block_property_evidence() -> None:
    assert (
        evidence.property_evidence_run().executed
        == evidence.property_evidence_declarations()
    )
