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
    assert (
        evidence.dispatch_reference_policy_evidence_run().executed
        == source.DISPATCH_REFERENCE_POLICY_NAMES
    )


def test_every_harness_router_authorizes_subagent_dispatch() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        source.validate_subagent_dispatch_policy(documents)
        for document in documents.values():
            section = source.subagent_dispatch_policy_section(
                source.managed_router_block(document)
            )
            assert section is not None


def test_each_dispatch_reference_carries_only_its_own_mechanics() -> None:
    references = source.load_dispatch_references()
    source.validate_harness_dispatch_mechanics(references)
    for owning_harness, marker in source.HARNESS_DISPATCH_MECHANICS_MARKERS.items():
        for agent_harness, document in references.items():
            if agent_harness == owning_harness:
                assert marker in document
            else:
                assert marker not in document


def test_router_blocks_carry_no_dispatch_mechanics() -> None:
    # The relocation invariant: the mechanics load with the dispatching skill,
    # so neither harness router carries either harness's mechanics marker.
    documents = evidence.rendered_instruction_blocks()
    for document in documents.values():
        router = source.managed_router_block(document)
        for marker in source.HARNESS_DISPATCH_MECHANICS_MARKERS.values():
            assert marker not in router


def test_leaked_harness_dispatch_mechanics_are_rejected() -> None:
    references = source.load_dispatch_references()
    for agent_harness, document in references.items():
        own_marker = source.HARNESS_DISPATCH_MECHANICS_MARKERS[agent_harness]
        for owning_harness, marker in source.HARNESS_DISPATCH_MECHANICS_MARKERS.items():
            if owning_harness == agent_harness:
                continue
            leaked = document.replace(own_marker, f"{own_marker} {marker}", 1)
            with pytest.raises(source.HarnessDispatchMechanicsError):
                source.validate_harness_dispatch_mechanics({agent_harness: leaked})


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


def test_quoted_dispatch_reference_requirements_are_rejected() -> None:
    references = source.load_dispatch_references()
    for validation in source.DISPATCH_REFERENCE_POLICY_VALIDATIONS:
        for _, required_text in validation.requirements:
            violating_references = {
                agent_harness: document.replace(
                    required_text,
                    f"\n{source.MARKDOWN_BLOCKQUOTE_MARKER} {required_text}\n",
                )
                for agent_harness, document in references.items()
            }
            with pytest.raises(source.InstructionBlockRenderError):
                validation.validator(violating_references)


def test_quoted_policy_requirements_are_rejected() -> None:
    documents = evidence.rendered_instruction_blocks()
    for validation in source.OPERATIVE_POLICY_VALIDATIONS:
        for _, required_text in validation.requirements:
            violating_documents = {
                agent_harness: document.replace(
                    required_text,
                    f"\n{source.MARKDOWN_BLOCKQUOTE_MARKER} {required_text}\n",
                )
                for agent_harness, document in documents.items()
            }
            with pytest.raises(source.InstructionBlockRenderError):
                validation.validator(violating_documents)


def test_fenced_policy_requirements_are_rejected() -> None:
    documents = evidence.rendered_instruction_blocks()
    for validation in source.OPERATIVE_POLICY_VALIDATIONS:
        for _, required_text in validation.requirements:
            violating_documents = {
                agent_harness: document.replace(
                    required_text,
                    "\n".join(
                        (
                            "",
                            source.MARKDOWN_CODE_FENCE_MARKERS[0],
                            required_text,
                            source.MARKDOWN_CODE_FENCE_MARKERS[0],
                            "",
                        )
                    ),
                )
                for agent_harness, document in documents.items()
            }
            with pytest.raises(source.InstructionBlockRenderError):
                validation.validator(violating_documents)
