from outcomeeng_testing.harnesses import instruction_block as harness


def test_instruction_block_compliance_evidence() -> None:
    assert harness.compliance_evidence_is_valid()
