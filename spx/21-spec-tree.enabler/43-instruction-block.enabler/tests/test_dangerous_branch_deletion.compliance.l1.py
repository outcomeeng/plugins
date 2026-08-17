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
    required_text = source.DANGEROUS_COMMAND_GUARD_STOP_TRIGGER_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_retry_prohibition() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_COMMAND_GUARD_RETRY_PROHIBITION_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_dynamic_branch_prohibition() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_BRANCH_DYNAMIC_PROHIBITION_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_dynamic_branch_forms() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_BRANCH_DYNAMIC_FORMS_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_quoted_form_denial() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_BRANCH_QUOTED_FORM_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_literal_name_requirement() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_BRANCH_LITERAL_NAME_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_multi_branch_permission() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_BRANCH_MULTI_NAME_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_sanctioned_path() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_COMMAND_GUARD_SANCTIONED_PATH_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_terminal_report() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_COMMAND_GUARD_TERMINAL_REPORT_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_terminal_purpose() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_COMMAND_GUARD_TERMINAL_PURPOSE_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
            )


def test_dcg_policy_rejects_missing_terminal_reason() -> None:
    module = source.load_instruction_block_module()
    templates = source.load_harness_templates(module)
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.template_languages(next(iter(templates.values()))),
    )
    required_text = source.DANGEROUS_COMMAND_GUARD_TERMINAL_REASON_REQUIREMENT

    for agent_harness, document in documents.items():
        assert required_text in document
        with pytest.raises(source.AuthorityHierarchyPolicyError):
            source.validate_authority_hierarchy_policy(
                {agent_harness: document.replace(required_text, "", 1)}
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
