"""Compliance evidence for the router's methodology-declaration instruction."""

import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_both_routers_carry_the_complete_methodology_declaration_instruction() -> None:
    documents = evidence.rendered_instruction_blocks()
    source.validate_methodology_declaration_policy(documents)


@pytest.mark.parametrize("harness", [source.CLAUDE_HARNESS, source.CODEX_HARNESS])
def test_each_methodology_declaration_requirement_is_enforced(harness: str) -> None:
    documents = evidence.rendered_instruction_blocks()
    document = documents[harness]

    for _, required_text in source.METHODOLOGY_DECLARATION_POLICY_REQUIREMENTS:
        violating_document = document.replace(required_text, "", 1)
        assert violating_document != document
        with pytest.raises(source.MethodologyDeclarationPolicyError):
            source.validate_methodology_declaration_policy(
                {harness: violating_document}
            )
