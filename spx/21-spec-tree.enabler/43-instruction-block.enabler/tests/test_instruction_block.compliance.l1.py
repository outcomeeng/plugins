import pytest

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


def test_wait_for_load_stop_trigger_policy() -> None:
    for documents in evidence.rendered_wait_for_load_policy_document_sets():
        source.validate_wait_for_load_policy(documents)
        for _, requirement in source.WAIT_FOR_LOAD_POLICY_REQUIREMENTS:
            with pytest.raises(source.WaitForLoadPolicyError):
                source.validate_wait_for_load_policy(
                    {
                        agent_harness: document.replace(requirement, "", 1)
                        for agent_harness, document in documents.items()
                    }
                )
            with pytest.raises(source.WaitForLoadPolicyError):
                source.validate_wait_for_load_policy(
                    {
                        agent_harness: document.replace(
                            source.managed_router_block(document),
                            source.managed_router_block(document)
                            .replace(requirement, "", 1)
                            .replace("\n", f"\n{requirement}\n", 1),
                            1,
                        )
                        for agent_harness, document in documents.items()
                    }
                )
        for contradiction in source.WAIT_FOR_LOAD_POLICY_CONTRADICTIONS:
            with pytest.raises(source.WaitForLoadPolicyError):
                source.validate_wait_for_load_policy(
                    {
                        agent_harness: document.replace(
                            source.managed_router_block(document),
                            source.managed_router_block(document).replace(
                                "\n", f"\n{contradiction.violating_directive}\n", 1
                            ),
                            1,
                        )
                        for agent_harness, document in documents.items()
                    }
                )
