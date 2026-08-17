import pytest

from outcomeeng.distribution import instruction_block as source


def test_dcg_policy_rejects_missing_stop_trigger() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "a dangerous-command guard (DCG) block terminates the "
                        "attempted command family",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_retry_prohibition() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "retry it by reformulating, splitting, rewriting, removing "
                        "the flagged clause, or substituting an equivalent command "
                        "to evade the guard",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_dynamic_branch_prohibition() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "pass dynamic branch names to `git branch -d` or "
                        "`git branch -D`",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_dynamic_branch_forms() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "variables, command substitutions, arrays, and globs are "
                        "denied",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_quoted_form_denial() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "including when quoted or placed after `--`",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_literal_name_requirement() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "Type every branch name literally",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_multi_branch_permission() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "delete several literal names in one command",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_sanctioned_path() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "follow the active skills, repository instructions, and "
                        "declared overlays to find a sanctioned operation",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_missing_terminal_report() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )

    for agent_harness, document in documents.items():
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {
                    agent_harness: document.replace(
                        "report the blocked command with secrets redacted",
                        "",
                        1,
                    )
                }
            )


def test_dcg_policy_rejects_quoted_guard_section() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    source.validate_authority_hierarchy_policy(documents)

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
