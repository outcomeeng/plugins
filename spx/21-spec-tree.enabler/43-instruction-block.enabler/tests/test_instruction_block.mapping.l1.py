from outcomeeng_testing.harnesses import instruction_block_mapping_evidence as evidence


def test_instruction_block_mapping_evidence() -> None:
    run = evidence.mapping_evidence_run()
    assert run.executed == run.declared
