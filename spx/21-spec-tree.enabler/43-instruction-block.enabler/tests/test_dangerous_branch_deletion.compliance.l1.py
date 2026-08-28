import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)


def test_rendered_dcg_policy_satisfies_the_production_validator() -> None:
    documents = evidence.rendered_instruction_blocks()

    source.validate_authority_hierarchy_policy(documents)
    for agent_harness, document in documents.items():
        router = source.managed_router_block(document)
        guard_section = source.dangerous_command_guard_policy_section(router)
        source.validate_dangerous_command_guard_policy({agent_harness: guard_section})


def test_dcg_policy_rejects_each_missing_operative_requirement() -> None:
    documents = evidence.rendered_instruction_blocks()

    for agent_harness, document in documents.items():
        router = source.managed_router_block(document)
        guard_section = source.dangerous_command_guard_policy_section(router)
        for (
            requirement_name,
            required_text,
        ) in source.DANGEROUS_COMMAND_GUARD_POLICY_REQUIREMENTS:
            assert required_text in guard_section
            violating_section = guard_section.replace(required_text, "", 1)

            with pytest.raises(source.AuthorityHierarchyPolicyError) as raised:
                source.validate_dangerous_command_guard_policy(
                    {agent_harness: violating_section}
                )
            assert requirement_name in str(raised.value)


def test_dcg_policy_rejects_quoted_guard_section() -> None:
    documents = evidence.rendered_instruction_blocks()

    for agent_harness, document in documents.items():
        router = source.managed_router_block(document)
        guard_section = source.dangerous_command_guard_policy_section(router)
        heading, *policy_lines = guard_section.splitlines()
        quoted_section = "\n".join((heading, *(f"> {line}" for line in policy_lines)))

        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_dangerous_command_guard_policy(
                {agent_harness: quoted_section}
            )
