import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_instruction_block_compliance_evidence() -> None:
    assert (
        evidence.compliance_evidence_run().executed
        == evidence.compliance_evidence_declarations()
    )
    assert evidence.router_policy_evidence_run().executed == source.ROUTER_POLICY_NAMES


def test_every_harness_router_authorizes_subagent_dispatch() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        source.validate_subagent_dispatch_policy(documents)
        for document in documents.values():
            section = source.subagent_dispatch_policy_section(
                source.managed_router_block(document)
            )
            assert section is not None


def test_dropping_a_required_dispatch_literal_is_rejected() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        for agent_harness, document in documents.items():
            section = source.subagent_dispatch_policy_section(
                source.managed_router_block(document)
            )
            assert section is not None
            for _, required_text in source.SUBAGENT_DISPATCH_POLICY_REQUIREMENTS:
                violating_document = document.replace(
                    section, section.replace(required_text, "", 1), 1
                )
                with pytest.raises(source.SubagentDispatchPolicyError):
                    source.validate_subagent_dispatch_policy(
                        {agent_harness: violating_document}
                    )
