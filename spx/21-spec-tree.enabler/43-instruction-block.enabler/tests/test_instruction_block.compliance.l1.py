from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_instruction_block_compliance_evidence() -> None:
    assert (
        evidence.compliance_evidence_run().executed
        == evidence.compliance_evidence_declarations()
    )
