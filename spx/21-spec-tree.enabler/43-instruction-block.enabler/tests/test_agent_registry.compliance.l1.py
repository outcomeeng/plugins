"""Compliance evidence for the Codex canonical-agent registry policy."""

import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_codex_router_carries_the_complete_canonical_agent_registry_policy() -> None:
    documents = evidence.rendered_instruction_blocks()
    source.validate_codex_agent_registry_policy(documents)


def test_each_canonical_agent_registry_requirement_is_enforced() -> None:
    documents = evidence.rendered_instruction_blocks()
    codex_document = documents[source.CODEX_HARNESS]

    for _, required_text in source.CODEX_AGENT_REGISTRY_POLICY_REQUIREMENTS:
        violating_document = codex_document.replace(required_text, "", 1)
        with pytest.raises(source.CodexAgentRegistryPolicyError):
            source.validate_codex_agent_registry_policy(
                {
                    source.CODEX_HARNESS: violating_document,
                    source.CLAUDE_HARNESS: documents[source.CLAUDE_HARNESS],
                }
            )


def test_codex_agent_registry_policy_is_codex_only() -> None:
    documents = evidence.rendered_instruction_blocks()
    leaked_claude_document = documents[source.CLAUDE_HARNESS].replace(
        "# Spec Tree Instructions",
        f"# Spec Tree Instructions\n\n{source.CODEX_AGENT_REGISTRY_POLICY_HEADING}",
        1,
    )

    with pytest.raises(source.CodexAgentRegistryPolicyError):
        source.validate_codex_agent_registry_policy(
            {
                source.CODEX_HARNESS: documents[source.CODEX_HARNESS],
                source.CLAUDE_HARNESS: leaked_claude_document,
            }
        )
