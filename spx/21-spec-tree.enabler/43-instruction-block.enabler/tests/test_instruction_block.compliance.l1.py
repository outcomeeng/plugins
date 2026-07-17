from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_instruction_block_compliance_evidence() -> None:
    assert (
        evidence.compliance_evidence_run().executed
        == evidence.compliance_evidence_declarations()
    )
    assert (
        evidence.codex_router_policy_evidence_run().executed
        == source.CODEX_ROUTER_POLICY_NAMES
    )
