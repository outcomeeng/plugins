"""Compliance evidence for the router's positions section."""

import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_every_harness_router_carries_the_complete_positions_section() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        assert set(documents) == {source.CLAUDE_HARNESS, source.CODEX_HARNESS}
        source.validate_positions_policy(documents)


@pytest.mark.parametrize("agent_harness", [source.CLAUDE_HARNESS, source.CODEX_HARNESS])
def test_each_positions_requirement_is_enforced(agent_harness: str) -> None:
    document = evidence.rendered_instruction_blocks()[agent_harness]
    router = source.managed_router_block(document)

    for _, required_text in source.POSITIONS_POLICY_REQUIREMENTS:
        violating_document = document.replace(
            router, router.replace(required_text, "", 1), 1
        )
        assert violating_document != document
        with pytest.raises(source.PositionsPolicyError):
            source.validate_positions_policy({agent_harness: violating_document})


def test_generation_runs_the_positions_validation() -> None:
    validators = [
        validation.validator for validation in source.OPERATIVE_POLICY_VALIDATIONS
    ]
    assert source.validate_positions_policy in validators
