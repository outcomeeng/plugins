"""Direct compliance predicates for the root instruction-block renderer."""

from __future__ import annotations

import pathlib
import re

import pytest

from outcomeeng.distribution import instruction_block as dist
from outcomeeng.distribution import instruction_block as source
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    RUNTIME_TOKEN_SPAWN_AGENT_CAPABILITY,
    RUNTIME_TOKEN_SPAWN_AGENT_NAMES,
    RUNTIME_TOKEN_TOOL_KIND,
    Target,
    format_runtime_token,
)
from outcomeeng_testing.harnesses import instruction_block as harness
from outcomeeng_testing.harnesses import (
    instruction_block_compliance_evidence as evidence,
)

MODULE = evidence.MODULE
WORKFLOW = evidence.WORKFLOW


def test_generation_writes_both_root_files(tmp_path: pathlib.Path) -> None:
    paths = evidence.generated_root_paths(tmp_path)
    assert len(paths) == len(MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES)
    for path in paths:
        assert path.is_file()


@pytest.mark.parametrize("agent_harness", harness.TEMPLATE_HARNESSES)
def test_router_is_first_and_carries_read_whole_file_instruction(
    agent_harness: str,
) -> None:
    template = harness.read_canonical_template(agent_harness)
    rendered = MODULE.render(
        template,
        harness.TEMPLATE_LANGUAGES,
        MODULE.parse_template_version(template),
        agent_harness,
    )
    document = MODULE.prepend_router_block(rendered, harness.ROOT_SHARED_BODY)
    assert document.startswith(MODULE.ROUTER_MARKER_PREFIX)
    router_block = document[: document.index(MODULE.ROUTER_BLOCK_END)]
    assert harness.READ_ENTIRE_FILE_INSTRUCTION in router_block


def test_generation_reads_dist_templates(tmp_path: pathlib.Path) -> None:
    observation = evidence.dist_template_load(tmp_path)
    assert observation.loaded == observation.expected
    for agent_harness, path in observation.paths.items():
        assert DIST_DIR_NAME in path.parts
        assert agent_harness in path.parts
        assert observation.markers[agent_harness] in observation.rendered[agent_harness]
        for other, marker in observation.markers.items():
            if other != agent_harness:
                assert marker not in observation.rendered[agent_harness]


def test_justfile_binds_build_and_check_recipes() -> None:
    justfile = dist.REPO_ROOT.joinpath(dist.JUSTFILE_NAME).read_text(encoding="utf-8")
    build_body = harness.justfile_recipe_body(justfile, dist.BUILD_INSTRUCTIONS_RECIPE)
    check_body = harness.justfile_recipe_body(justfile, dist.INSTRUCTIONS_CHECK_RECIPE)
    assert f"outcomeeng.distribution.instruction_block {dist.WRITE_FLAG}" in build_body
    assert "outcomeeng.distribution.instruction_block" in check_body
    assert dist.WRITE_FLAG not in check_body


def test_lefthook_regenerates_through_build_instructions() -> None:
    lefthook = dist.REPO_ROOT.joinpath("lefthook.yml").read_text(encoding="utf-8")
    # the hook's run directive regenerates through the recipe
    assert f"run: just {dist.BUILD_INSTRUCTIONS_RECIPE}" in lefthook
    # NEVER a direct generator invocation against the authored src template
    assert "--template src/plugins" not in lefthook
    assert "--repo-root ." not in lefthook


def test_drift_gate_reports_a_missing_root_instruction_file(
    tmp_path: pathlib.Path,
) -> None:
    assert harness.INSTRUCTION_CLAUDE in evidence.missing_root_drift(tmp_path)


def test_drift_gate_marks_untracked_root_file_intent_to_add(
    tmp_path: pathlib.Path,
) -> None:
    drift = evidence.untracked_root_drift(tmp_path)
    assert harness.INSTRUCTION_CLAUDE in drift
    assert harness.INSTRUCTION_AGENTS in drift


def test_drift_gate_skips_missing_obsolete_spx_file(tmp_path: pathlib.Path) -> None:
    assert evidence.absent_obsolete_drift(tmp_path) == []


def test_refresh_workflow_regeneration_drives_pr_decision(
    tmp_path: pathlib.Path,
) -> None:
    observation = evidence.refresh_workflow_observation(tmp_path)
    assert not observation.initial_gh_log_exists
    for version in (*observation.template_versions, *observation.root_versions):
        assert version == observation.advanced_version
    assert not any(observation.obsolete_present)
    assert WORKFLOW.commit_subject in observation.committed
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        assert f"M\t{name}" in observation.committed
        assert f"D\tspx/{name}" in observation.committed
    for path in observation.template_paths:
        assert f"M\t{path}" in observation.committed
    assert "pr list" in observation.gh_calls
    assert "pr create" in observation.gh_calls
    assert observation.update_output.endswith(
        f"Updated existing pull request #{observation.existing_pr_number}.\n"
    )
    assert "pr list" in observation.update_calls
    assert "pr create" not in observation.update_calls
    assert (
        MODULE.parse_instruction_version(observation.updated_agents)
        == observation.update_version
    )


def test_regenerate_overwrites_router_drift(tmp_path: pathlib.Path) -> None:
    observation = evidence.overwritten_router_drift(tmp_path)
    assert observation.hand_edited_body in observation.drifted
    assert (
        MODULE.parse_instruction_version(observation.regenerated) == harness.NEW_VERSION
    )
    assert observation.canonical_body in observation.regenerated
    assert observation.hand_edited_body not in observation.regenerated


def test_refresh_workflow_regenerates_and_opens_pr() -> None:
    workflow = WORKFLOW.path().read_text(encoding="utf-8")
    assert WORKFLOW.dispatch_key in workflow
    regenerate = harness.workflow_run_block(WORKFLOW.regenerate_step)
    for command in WORKFLOW.build_commands:
        assert command in regenerate
    assert regenerate.index(WORKFLOW.build_commands[0]) < regenerate.index(
        WORKFLOW.build_commands[1]
    )
    pr_step = harness.workflow_step_block(WORKFLOW.open_pr_step)
    # opens or updates the PR only when git reports drift
    assert WORKFLOW.drift_probe in pr_step
    assert workflow.index(f"      - name: {WORKFLOW.regenerate_step}") < workflow.index(
        f"      - name: {WORKFLOW.open_pr_step}"
    )


def test_refresh_workflow_checks_out_main() -> None:
    checkout = harness.workflow_step_block(WORKFLOW.checkout_step)
    assert WORKFLOW.default_branch in checkout


def test_refresh_workflow_verifies_just_download() -> None:
    install = harness.workflow_run_block(WORKFLOW.install_just_step)
    just_sha256 = harness.workflow_env_value(WORKFLOW.just_checksum_env)
    # the pinned checksum is declared
    assert len(just_sha256) == 64
    assert f"${WORKFLOW.just_checksum_env}" in install
    # the download lands in a temp dir with a cleanup trap
    assert "mktemp -d" in install
    assert "trap " in install
    assert "rm -rf" in install
    # the checksum is verified against the download BEFORE the binary is installed
    assert install.index("sha256sum -c") < install.index("install -m 0755")
    # NEVER the insecure pattern: a fixed cwd download file extracted without the temp path
    assert "-o just.tar.gz" not in install
    assert "tar -xzf just.tar.gz" not in install


def test_refresh_workflow_installs_dprint() -> None:
    install = harness.workflow_run_block(WORKFLOW.install_dprint_step)
    dprint_version = harness.workflow_env_value(WORKFLOW.dprint_version_env)
    assert dprint_version
    # the pinned version is installed via bun and then verified
    assert f'bun add -g "dprint@${{{WORKFLOW.dprint_version_env}}}"' in install
    assert "dprint --version" in install
    workflow = WORKFLOW.path().read_text(encoding="utf-8")
    assert workflow.index(
        f"      - name: {WORKFLOW.install_dprint_step}"
    ) < workflow.index(f"      - name: {WORKFLOW.regenerate_step}")


def test_render_passes_brace_token_through_unchanged() -> None:
    templates = tuple(
        harness.read_canonical_template(agent_harness)
        for agent_harness in harness.TEMPLATE_HARNESSES
    )
    brace_tokens = tuple(
        dict.fromkeys(
            token
            for template in templates
            for token in re.findall(r"\{[^{}\n]+\}", template)
        )
    )
    assert brace_tokens
    rendered = tuple(
        MODULE.render(
            template,
            harness.TEMPLATE_LANGUAGES,
            MODULE.parse_template_version(template),
            agent_harness,
        )
        for agent_harness, template in zip(
            harness.TEMPLATE_HARNESSES, templates, strict=True
        )
    )
    missing = tuple(
        token for token in brace_tokens if not any(token in body for body in rendered)
    )
    assert not missing, f"rendering changed or removed brace tokens: {missing!r}"


def test_former_command_slot_fence_is_ordinary_content(tmp_path: pathlib.Path) -> None:
    result, original = evidence.former_command_slot_render(tmp_path)
    assert original in result
    assert set(MODULE.parse_shared_regions(result)) == {harness.SHARED_REGION_NAME}


def test_reconcile_replaces_the_losing_region_whole() -> None:
    open_marker = MODULE.shared_open_marker(harness.SHARED_REGION_NAME)
    close_marker = MODULE.shared_close_marker(harness.SHARED_REGION_NAME)
    doc_a = f"{open_marker}\n\n{harness.SHARED_REGION_BODY}\n\n{close_marker}\n"
    doc_b = f"{open_marker}\n\n{harness.SHARED_REGION_BODY_ALT}\n\n{close_marker}\n"
    _, new_b = MODULE.reconcile_shared_regions(doc_a, doc_b, "a")
    reconciled = MODULE.parse_shared_regions(new_b)[harness.SHARED_REGION_NAME]
    assert reconciled == harness.SHARED_REGION_BODY
    assert harness.SHARED_REGION_BODY_ALT not in reconciled


def test_codex_role_input_uses_runtime_capability() -> None:
    """Assert role-task submission renders through a discoverable runtime token."""
    authored = dist.AUTHORED_TEMPLATE_PATH.read_text(encoding="utf-8")
    token = format_runtime_token(
        RUNTIME_TOKEN_TOOL_KIND,
        RUNTIME_TOKEN_SPAWN_AGENT_CAPABILITY,
        Target.CODEX.value,
    )
    runtime_name = RUNTIME_TOKEN_SPAWN_AGENT_NAMES[Target.CODEX.value]

    assert token in authored
    assert runtime_name not in authored

    document = evidence.rendered_instruction_blocks()[harness.HARNESS_CODEX]
    router = dist.managed_router_block(document)
    assert token not in router
    assert runtime_name in router
    assert source.HARNESS_DISPATCH_MECHANICS_MARKERS[source.CODEX_HARNESS] in router


def test_dist_template_copies_stay_equivalent() -> None:
    """Assert both dist template copies carry the same complete harness spans."""
    templates = dist.load_harness_templates(evidence._distribution_module())
    claude_copy = templates[harness.HARNESS_CLAUDE]
    codex_copy = templates[harness.HARNESS_CODEX]

    assert claude_copy == codex_copy

    for marker in (
        "<!-- harness:codex -->",
        "<!-- harness:claude -->",
        *source.HARNESS_DISPATCH_MECHANICS_MARKERS.values(),
    ):
        assert marker in claude_copy
        assert marker in codex_copy


def test_claude_router_uses_native_configured_agent_dispatch() -> None:
    """Assert Claude keeps native configured-agent dispatch."""
    document = evidence.rendered_instruction_blocks()[harness.HARNESS_CLAUDE]
    router = dist.managed_router_block(document)

    assert source.HARNESS_DISPATCH_MECHANICS_MARKERS[source.CLAUDE_HARNESS] in router
    assert "OUTCOMEENG_CODEX_AGENT_NAME" not in router


def test_wait_for_load_stop_trigger_policy() -> None:
    """Challenge every wait-for-load requirement across all renders."""
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        dist.validate_wait_for_load_policy(documents)
        for _, requirement in dist.WAIT_FOR_LOAD_POLICY_REQUIREMENTS:
            removed = {
                agent_harness: document.replace(requirement, "", 1)
                for agent_harness, document in documents.items()
            }
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(removed)
            relocated = {
                agent_harness: document.replace(
                    dist.managed_router_block(document),
                    dist.managed_router_block(document)
                    .replace(requirement, "", 1)
                    .replace("\n", f"\n{requirement}\n", 1),
                    1,
                )
                for agent_harness, document in documents.items()
            }
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(relocated)
        codex_document = documents[harness.HARNESS_CODEX]
        claude_router = dist.managed_router_block(documents[harness.HARNESS_CLAUDE])
        for _, requirement in dist.WAIT_FOR_LOAD_CODEX_POLICY_REQUIREMENTS:
            assert requirement not in claude_router
            removed = {
                **documents,
                harness.HARNESS_CODEX: codex_document.replace(requirement, "", 1),
            }
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(removed)
        for contradiction in dist.WAIT_FOR_LOAD_POLICY_CONTRADICTIONS:
            contradicted = {
                agent_harness: document.replace(
                    dist.managed_router_block(document),
                    dist.managed_router_block(document).replace(
                        "\n", f"\n{contradiction.violating_directive}\n", 1
                    ),
                    1,
                )
                for agent_harness, document in documents.items()
            }
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(contradicted)


def test_authority_hierarchy_policy_is_complete() -> None:
    """Challenge every authority-hierarchy requirement across all renders."""
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        dist.validate_authority_hierarchy_policy(documents)
        for _, requirement in dist.AUTHORITY_HIERARCHY_POLICY_REQUIREMENTS:
            for agent_harness, document in documents.items():
                invalid_document = document.replace(requirement, "", 1)
                try:
                    dist.validate_authority_hierarchy_policy(
                        {agent_harness: invalid_document}
                    )
                except dist.AuthorityHierarchyPolicyError:
                    pass
                else:
                    raise AssertionError(
                        f"incomplete authority hierarchy was accepted: {requirement}"
                    )


def test_all_routers_enforce_operator_question_interrupt() -> None:
    """Challenge question policy across every declared language subset."""
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        dist.validate_operator_question_policy(documents)
        for agent_harness, document in documents.items():
            router = dist.managed_router_block(document)
            policy = dist.operator_question_policy_block(router)
            assert policy is not None

            for _, required_text in dist.OPERATOR_QUESTION_REQUIREMENTS:
                invalid_document = document.replace(
                    policy, policy.replace(required_text, "", 1), 1
                )
                try:
                    dist.validate_operator_question_policy(
                        {agent_harness: invalid_document}
                    )
                except dist.OperatorQuestionPolicyError:
                    pass
                else:
                    raise AssertionError(
                        "incomplete operator-question policy was accepted: "
                        f"{required_text}"
                    )

            for (
                contradiction_name,
                contradiction_text,
            ) in dist.OPERATOR_QUESTION_CONTRADICTIONS:
                invalid_policy = policy.replace(
                    dist.OPERATOR_QUESTION_POLICY_CLOSE,
                    f"{contradiction_text}\n\n{dist.OPERATOR_QUESTION_POLICY_CLOSE}",
                    1,
                )
                invalid_document = document.replace(policy, invalid_policy, 1)
                try:
                    dist.validate_operator_question_policy(
                        {agent_harness: invalid_document}
                    )
                except dist.OperatorQuestionPolicyError:
                    pass
                else:
                    raise AssertionError(
                        "contradictory operator-question policy was accepted: "
                        f"{contradiction_name}"
                    )


def test_codex_router_bounds_dispatched_verifiers() -> None:
    """Challenge verifier policy across every declared language subset."""
    for enabled_languages in harness.template_language_subsets():
        document = evidence.rendered_instruction_blocks(enabled_languages)[
            harness.HARNESS_CODEX
        ]
        router = dist.managed_router_block(document)
        policy = dist.verifier_dispatch_policy_paragraph(router)
        assert policy is not None
        dist.validate_verifier_dispatch_policy({dist.CODEX_HARNESS: document})

        for _, required_text in dist.CODEX_VERIFIER_DISPATCH_REQUIREMENTS:
            invalid_document = document.replace(
                policy, policy.replace(required_text, "", 1), 1
            )
            try:
                dist.validate_verifier_dispatch_policy(
                    {dist.CODEX_HARNESS: invalid_document}
                )
            except dist.VerifierDispatchPolicyError:
                pass
            else:
                raise AssertionError(
                    f"incomplete verifier dispatch policy was accepted: {required_text}"
                )

        for contradiction in dist.CODEX_VERIFIER_DISPATCH_CONTRADICTIONS:
            invalid_document = document.replace(
                MODULE.ROUTER_BLOCK_END,
                f"{contradiction.violating_directive}\n\n{MODULE.ROUTER_BLOCK_END}",
                1,
            )
            try:
                dist.validate_verifier_dispatch_policy(
                    {dist.CODEX_HARNESS: invalid_document}
                )
            except dist.VerifierDispatchPolicyError:
                pass
            else:
                raise AssertionError(
                    f"contradictory verifier directive was accepted: {contradiction.name}"
                )


def test_rendered_router_omits_forbidden_session_tokens() -> None:
    """Assert forbidden session-result vocabulary stays outside every router."""
    for agent_harness, document in evidence.rendered_instruction_blocks().items():
        router = dist.managed_router_block(document)
        for forbidden_text in dist.FORBIDDEN_ROUTER_TOKENS:
            assert forbidden_text not in router
        independent_prose = document + "\n" + "\n".join(dist.FORBIDDEN_ROUTER_TOKENS)
        dist.validate_foundation_access_policy({agent_harness: independent_prose})


def test_foundation_policy_guard_rejects_missing_requirement() -> None:
    """Assert every required foundation-policy phrase is enforced in the router."""
    agent_harness, document = next(iter(evidence.rendered_instruction_blocks().items()))
    required_text = dist.FOUNDATION_POLICY_REQUIREMENTS[0][1]
    router = dist.managed_router_block(document)
    invalid_document = document.replace(router, router.replace(required_text, "", 1), 1)
    try:
        dist.validate_foundation_access_policy({agent_harness: invalid_document})
    except dist.FoundationAccessPolicyError:
        pass
    else:
        raise AssertionError("incomplete foundation policy was accepted")


def test_foundation_policy_guard_rejects_forbidden_router_token() -> None:
    """Assert forbidden session-result vocabulary is rejected inside the router."""
    agent_harness, document = next(iter(evidence.rendered_instruction_blocks().items()))
    module = harness.load_instruction_block_module()
    invalid_document = document.replace(
        module.ROUTER_BLOCK_END,
        f"{dist.FORBIDDEN_ROUTER_TOKENS[0]}\n\n{module.ROUTER_BLOCK_END}",
        1,
    )
    try:
        dist.validate_foundation_access_policy({agent_harness: invalid_document})
    except dist.FoundationAccessPolicyError:
        pass
    else:
        raise AssertionError("forbidden router token was accepted")


def test_unresolved_build_macro_is_rejected() -> None:
    # exercise the production pipeline function the build recipes call, not just the primitive: one
    # harness's dist template still carries an unresolved build macro, and the guard must propagate
    # through render_instruction_blocks_from_harness_templates
    harness_templates = {
        agent_harness: harness.build_template(harness.NEW_VERSION)
        for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    harness_templates[harness.HARNESS_CODEX] += harness.render_build_macro()
    try:
        dist.render_instruction_blocks_from_harness_templates(
            evidence._distribution_module(), harness_templates, (harness.LANG_PRIMARY,)
        )
    except dist.UnresolvedInstructionTemplateError:
        pass
    else:
        raise AssertionError("unresolved build macro was accepted")


def test_obsolete_spx_instruction_files_are_removed(tmp_path: pathlib.Path) -> None:
    for path in evidence.removed_obsolete_paths(tmp_path):
        assert not path.exists()


def test_every_harness_router_authorizes_subagent_dispatch() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        source.validate_subagent_dispatch_policy(documents)
        for document in documents.values():
            section = source.subagent_dispatch_policy_section(
                source.managed_router_block(document)
            )
            assert section is not None


def test_each_harness_block_carries_only_its_own_dispatch_mechanics() -> None:
    documents = evidence.rendered_instruction_blocks()
    source.validate_harness_dispatch_mechanics(documents)
    for owning_harness, marker in source.HARNESS_DISPATCH_MECHANICS_MARKERS.items():
        for agent_harness, document in documents.items():
            router = source.managed_router_block(document)
            if agent_harness == owning_harness:
                assert marker in router
            else:
                assert marker not in router


def test_leaked_harness_dispatch_mechanics_are_rejected() -> None:
    documents = evidence.rendered_instruction_blocks()
    for agent_harness, document in documents.items():
        own_marker = source.HARNESS_DISPATCH_MECHANICS_MARKERS[agent_harness]
        for owning_harness, marker in source.HARNESS_DISPATCH_MECHANICS_MARKERS.items():
            if owning_harness == agent_harness:
                continue
            leaked = document.replace(own_marker, f"{own_marker} {marker}", 1)
            with pytest.raises(source.HarnessDispatchMechanicsError):
                source.validate_harness_dispatch_mechanics({agent_harness: leaked})


def test_dropping_a_required_dispatch_literal_is_rejected() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = evidence.rendered_instruction_blocks(enabled_languages)
        for agent_harness, document in documents.items():
            section = source.subagent_dispatch_policy_section(
                source.managed_router_block(document)
            )
            assert section is not None
            for _, required_text in source.SUBAGENT_DISPATCH_POLICY_REQUIREMENTS:
                violating_document = document.replace(
                    section, section.replace(required_text, "", 1), 1
                )
                with pytest.raises(source.SubagentDispatchPolicyError):
                    source.validate_subagent_dispatch_policy(
                        {agent_harness: violating_document}
                    )


def test_quoted_policy_requirements_are_rejected() -> None:
    documents = evidence.rendered_instruction_blocks()
    for validation in source.OPERATIVE_POLICY_VALIDATIONS:
        for _, required_text in validation.requirements:
            violating_documents = {
                agent_harness: document.replace(
                    required_text,
                    f"\n{source.MARKDOWN_BLOCKQUOTE_MARKER} {required_text}\n",
                )
                for agent_harness, document in documents.items()
            }
            with pytest.raises(source.InstructionBlockRenderError):
                validation.validator(violating_documents)


def test_fenced_policy_requirements_are_rejected() -> None:
    documents = evidence.rendered_instruction_blocks()
    for validation in source.OPERATIVE_POLICY_VALIDATIONS:
        for _, required_text in validation.requirements:
            violating_documents = {
                agent_harness: document.replace(
                    required_text,
                    "\n".join(
                        (
                            "",
                            source.MARKDOWN_CODE_FENCE_MARKERS[0],
                            required_text,
                            source.MARKDOWN_CODE_FENCE_MARKERS[0],
                            "",
                        )
                    ),
                )
                for agent_harness, document in documents.items()
            }
            with pytest.raises(source.InstructionBlockRenderError):
                validation.validator(violating_documents)
