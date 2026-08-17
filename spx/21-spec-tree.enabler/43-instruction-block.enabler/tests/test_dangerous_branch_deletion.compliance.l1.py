from pathlib import Path

import pytest

from outcomeeng.distribution import instruction_block as source


def test_dangerous_command_guard_policy_rejects_every_missing_rule(
    tmp_path: Path,
) -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    source.validate_authority_hierarchy_policy(documents)

    for (
        requirement_name,
        required_text,
    ) in source.DANGEROUS_COMMAND_GUARD_POLICY_REQUIREMENTS:
        for agent_harness in documents:
            repo_root = tmp_path / requirement_name / agent_harness
            for template_harness, template in templates.items():
                template_path = source.dist_template_path(
                    template_harness, repo_root=repo_root
                )
                template_path.parent.mkdir(parents=True)
                if template_harness == agent_harness:
                    template = template.replace(required_text, "", 1)
                template_path.write_text(template, encoding="utf-8")

            with pytest.raises(source.AuthorityHierarchyPolicyError):
                source.regenerate_instruction_blocks(repo_root=repo_root)

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
