from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_instruction_block_compliance_evidence() -> None:
    run = evidence.compliance_evidence_run()
    assert run.executed == run.declared
