import pytest

from outcomeeng.distribution import instruction_block as source


def test_dangerous_branch_deletion_policy_rejects_every_missing_rule() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    source.validate_authority_hierarchy_policy(documents)

    for _, required_text in source.DANGEROUS_BRANCH_DELETION_POLICY_REQUIREMENTS:
        for agent_harness, document in documents.items():
            violating_document = document.replace(required_text, "", 1)
            with pytest.raises(source.AuthorityHierarchyPolicyError):
                source.validate_authority_hierarchy_policy(
                    {agent_harness: violating_document}
                )

    for agent_harness, document in documents.items():
        guard_section = source._markdown_section(
            document, source.DANGEROUS_COMMAND_GUARD_POLICY_HEADING
        )
        quoted_guard = "\n".join(
            f"> {line}" if line else ">" for line in guard_section.splitlines()
        )
        violating_document = document.replace(guard_section, quoted_guard, 1)
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: violating_document}
            )
