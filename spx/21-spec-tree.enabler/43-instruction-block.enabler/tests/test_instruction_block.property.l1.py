from outcomeeng_testing.harnesses import instruction_block_property_evidence as evidence


def test_instruction_block_property_evidence() -> None:
    run = evidence.property_evidence_run()
    assert run.executed == run.declared
