"""Compliance evidence for the Codex canonical-agent registry policy."""

import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_codex_router_carries_the_complete_canonical_agent_registry_policy() -> None:
    documents = evidence.rendered_instruction_blocks()
    source.validate_codex_agent_registry_policy(documents)


def test_each_canonical_agent_registry_requirement_is_enforced() -> None:
    documents = evidence.rendered_instruction_blocks()
    codex_document = documents[Target.CODEX]

    for _, required_text in source.CODEX_AGENT_REGISTRY_POLICY_REQUIREMENTS:
        violating_document = codex_document.replace(required_text, "", 1)
        with pytest.raises(source.CodexAgentRegistryPolicyError):
            source.validate_codex_agent_registry_policy(
                {
                    Target.CODEX: violating_document,
                    Target.CLAUDE: documents[Target.CLAUDE],
                }
            )


def test_codex_agent_registry_policy_is_codex_only() -> None:
    documents = evidence.rendered_instruction_blocks()
    router_end = source.load_instruction_block_module().ROUTER_BLOCK_END
    leaked_claude_document = documents[Target.CLAUDE].replace(
        router_end,
        f"{source.CODEX_AGENT_REGISTRY_POLICY_HEADING}\n\n{router_end}",
        1,
    )

    with pytest.raises(source.CodexAgentRegistryPolicyError):
        source.validate_codex_agent_registry_policy(
            {
                Target.CODEX: documents[Target.CODEX],
                Target.CLAUDE: leaked_claude_document,
            }
        )
