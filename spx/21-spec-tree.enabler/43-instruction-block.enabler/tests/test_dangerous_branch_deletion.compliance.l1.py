from typing import cast

import pytest

from outcomeeng.distribution import instruction_block as source
from outcomeeng_testing.harnesses import instruction_block as harness


def test_dangerous_branch_deletion_policy_rejects_every_missing_rule() -> None:
    module = cast(
        source.InstructionBlockModule, harness.load_instruction_block_module()
    )
    documents = source.render_instruction_blocks_from_harness_templates(
        module,
        source.load_harness_templates(module),
        harness.TEMPLATE_LANGUAGES,
    )
    source.validate_authority_hierarchy_policy(documents)

    for _, required_text in source.DANGEROUS_BRANCH_DELETION_POLICY_REQUIREMENTS:
        for agent_harness, document in documents.items():
            violating_document = document.replace(required_text, "", 1)
            with pytest.raises(source.AuthorityHierarchyPolicyError):
                source.validate_authority_hierarchy_policy(
                    {agent_harness: violating_document}
                )
