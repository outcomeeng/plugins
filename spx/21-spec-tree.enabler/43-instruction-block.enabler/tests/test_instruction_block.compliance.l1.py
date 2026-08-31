"""Compliance evidence for the instruction-block render model.

The ALWAYS/NEVER rules of ``instruction-block.md`` with deterministic test evidence: both root
files are written together, the router is first and carries a read-the-whole-file instruction,
generation reads the ``dist/`` templates, the drift gate reports a missing root path and
overwrites router drift, the refresh workflow regenerates and opens a PR only on drift, no
product-specific string enters the router, a former command-slot fence is ordinary content, a
reconcile never blends bodies, the retired session tokens never render, an unresolved build
macro is rejected, and retired ``spx/`` instruction files are removed.
"""

from __future__ import annotations

import pytest

import pathlib
import re
from typing import cast

from outcomeeng.distribution import instruction_block as dist
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    RUNTIME_TOKEN_SPAWN_AGENT_CAPABILITY,
    RUNTIME_TOKEN_SPAWN_AGENT_NAMES,
    RUNTIME_TOKEN_TOOL_KIND,
    Target,
    format_runtime_token,
)
from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()
WORKFLOW = dist.REFRESH_WORKFLOW


def _distribution_module() -> dist.InstructionBlockModule:
    """Narrow the dynamic script module at distribution-helper boundaries."""
    return cast(dist.InstructionBlockModule, MODULE)


def _template(tmp_path: pathlib.Path) -> pathlib.Path:
    return harness.write_template(tmp_path, harness.NEW_VERSION)


def test_generation_writes_both_root_files(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.run_generator_write_primary(repo, _template(tmp_path))
    assert (repo / harness.INSTRUCTION_CLAUDE).is_file()
    assert (repo / harness.INSTRUCTION_AGENTS).is_file()


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
    expected: dict[str, str] = {}
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        path = dist.dist_template_path(agent_harness)
        assert DIST_DIR_NAME in path.parts
        assert agent_harness in path.parts
        # write a distinct synthetic per-harness dist template, then load it through the production
        # loader the build recipes call — asserting per-harness template content, not just path shape
        template = (
            harness.build_template(harness.NEW_VERSION)
            + f"\nDIST TEMPLATE SOURCE: {agent_harness}\n"
        )
        expected[agent_harness] = template
        dist_path = dist.dist_template_path(agent_harness, repo_root=tmp_path)
        dist_path.parent.mkdir(parents=True, exist_ok=True)
        dist_path.write_text(template, encoding="utf-8")
    loaded = dist.load_harness_templates(_distribution_module(), repo_root=tmp_path)
    assert loaded == expected
    rendered = dist.render_instruction_blocks_from_harness_templates(
        _distribution_module(), loaded, harness.TEMPLATE_LANGUAGES
    )
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        assert f"DIST TEMPLATE SOURCE: {agent_harness}" in rendered[agent_harness]
        assert all(
            f"DIST TEMPLATE SOURCE: {other}" not in rendered[agent_harness]
            for other in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES
            if other != agent_harness
        )


def test_drift_gate_reports_a_missing_root_instruction_file(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    harness.git_commit_at(
        repo, 1000, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )
    (repo / harness.INSTRUCTION_CLAUDE).unlink()

    drift = dist.drifting_instruction_files(
        repo_root=repo, module=_distribution_module()
    )
    assert harness.INSTRUCTION_CLAUDE in drift


def test_drift_gate_marks_untracked_root_file_intent_to_add(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    # both root files written but never committed — a plain git diff would miss them
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    drift = dist.drifting_instruction_files(
        repo_root=repo, module=_distribution_module()
    )
    # --intent-to-add registers each never-committed root file as drift
    assert harness.INSTRUCTION_CLAUDE in drift
    assert harness.INSTRUCTION_AGENTS in drift


def test_drift_gate_skips_missing_obsolete_spx_file(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    harness.init_git_identity(repo)
    harness.write_both_root_files_with_shared_region(
        MODULE, repo, languages=(harness.LANG_PRIMARY,), version=harness.NEW_VERSION
    )
    harness.git_commit_at(
        repo, 1000, harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS
    )
    drift = dist.drifting_instruction_files(
        repo_root=repo, module=_distribution_module()
    )
    # committed root files do not drift, and a never-tracked obsolete spx/ file is not reported
    assert drift == []
    assert "spx/CLAUDE.md" not in drift
    assert "spx/AGENTS.md" not in drift


def test_refresh_workflow_regeneration_drives_pr_decision(
    tmp_path: pathlib.Path,
) -> None:
    gh_log = tmp_path / "gh.log"
    repo = harness.materialize_refresh_repository(tmp_path)

    harness.run_refresh_regeneration_step(repo)
    harness.git_command(
        repo,
        "add",
        harness.INSTRUCTION_CLAUDE,
        harness.INSTRUCTION_AGENTS,
        DIST_DIR_NAME,
    )
    harness.git_command(repo, "commit", "-m", "seed generated workflow output")
    harness.git_command(repo, "push", "origin", WORKFLOW.default_branch)
    harness.run_refresh_regeneration_step(repo)
    output = harness.run_refresh_pr_step(repo, gh_log)
    assert output == "Root instruction blocks are current.\n"
    assert not gh_log.exists()

    spx_dir = repo / "spx"
    for name in harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS:
        (spx_dir / name).write_text(
            (repo / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    harness.git_command(repo, "add", ".")
    harness.git_command(repo, "commit", "-m", "seed obsolete instruction files")
    harness.git_command(repo, "push", "origin", WORKFLOW.default_branch)

    _, advanced_version = harness.advance_authored_template_version(repo)
    harness.run_refresh_regeneration_step(repo)
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        rendered_template = dist.dist_template_path(
            agent_harness, repo_root=repo
        ).read_text(encoding="utf-8")
        assert MODULE.parse_template_version(rendered_template) == advanced_version
    for name in harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS:
        rendered_root = (repo / name).read_text(encoding="utf-8")
        assert MODULE.parse_instruction_version(rendered_root) == advanced_version
    assert not (spx_dir / harness.INSTRUCTION_CLAUDE).exists()
    assert not (spx_dir / harness.INSTRUCTION_AGENTS).exists()
    harness.run_refresh_pr_step(repo, gh_log)

    committed = harness.git_command(
        repo,
        "show",
        "--name-status",
        "--format=%s",
        WORKFLOW.automation_branch,
    ).stdout
    assert WORKFLOW.commit_subject in committed
    assert f"M\t{harness.INSTRUCTION_CLAUDE}" in committed
    assert f"M\t{harness.INSTRUCTION_AGENTS}" in committed
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        rendered_template_path = dist.dist_template_path(
            agent_harness, repo_root=repo
        ).relative_to(repo)
        assert f"M\t{rendered_template_path}" in committed
    assert f"D\tspx/{harness.INSTRUCTION_CLAUDE}" in committed
    assert f"D\tspx/{harness.INSTRUCTION_AGENTS}" in committed
    gh_calls = gh_log.read_text(encoding="utf-8")
    assert "pr list" in gh_calls
    assert "pr create" in gh_calls

    harness.git_command(repo, "switch", WORKFLOW.default_branch)
    _, update_version = harness.advance_authored_template_version(repo)
    harness.run_refresh_regeneration_step(repo)
    update_log = tmp_path / "gh-update.log"
    existing_pr_number = harness.git_command(
        repo, "rev-list", "--count", WORKFLOW.default_branch
    ).stdout.strip()
    update_output = harness.run_refresh_pr_step(
        repo, update_log, existing_pr_number=existing_pr_number
    )
    assert update_output.endswith(
        f"Updated existing pull request #{existing_pr_number}.\n"
    )
    update_calls = update_log.read_text(encoding="utf-8")
    assert "pr list" in update_calls
    assert "pr create" not in update_calls
    updated_agents = harness.git_command(
        repo,
        "show",
        f"{WORKFLOW.automation_branch}:{harness.INSTRUCTION_AGENTS}",
    ).stdout
    assert MODULE.parse_instruction_version(updated_agents) == update_version


def test_regenerate_overwrites_router_drift(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = _template(tmp_path)
    harness.run_generator_write_primary(repo, template)
    claude = repo / harness.INSTRUCTION_CLAUDE
    canonical_body = harness.harness_line(harness.HARNESS_CLAUDE)
    hand_edited_body = f"{canonical_body} {harness.SHARED_REGION_BODY_ALT}"
    claude.write_text(
        claude.read_text(encoding="utf-8")
        .replace(f"v{harness.NEW_VERSION}", f"v{harness.OLD_VERSION}", 1)
        .replace(canonical_body, hand_edited_body, 1),
        encoding="utf-8",
    )
    drifted = claude.read_text(encoding="utf-8")
    assert hand_edited_body in drifted
    harness.run_generator_write_primary(repo, template)
    regenerated = claude.read_text(encoding="utf-8")
    assert MODULE.parse_instruction_version(regenerated) == harness.NEW_VERSION
    assert canonical_body in regenerated
    assert hand_edited_body not in regenerated


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


def test_former_command_slot_fence_is_ordinary_content(
    tmp_path: pathlib.Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    slot_fence = (
        "<!-- SPEC-TREE:author -->\n\nproduct author command\n\n"
        "<!-- /SPEC-TREE:author -->\n"
    )
    for name in (harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS):
        (repo / name).write_text(slot_fence, encoding="utf-8")

    harness.run_generator_write_primary(repo, _template(tmp_path))
    result = (repo / harness.INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    # the former slot text survives as ordinary content, and no slot name is a managed region
    assert "product author command" in result
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


def _render_shipped_instruction_blocks(
    enabled_languages: tuple[str, ...] = harness.TEMPLATE_LANGUAGES,
) -> dict[str, str]:
    """Render shipped harness templates for one source-declared language subset."""
    templates = dist.load_harness_templates(_distribution_module())
    return dist.render_instruction_blocks_from_harness_templates(
        _distribution_module(), templates, enabled_languages
    )


def rendered_instruction_blocks(
    enabled_languages: tuple[str, ...] = harness.TEMPLATE_LANGUAGES,
) -> dict[str, str]:
    """Expose the rendered harness routers keyed by agent harness.

    An observation for a linked test that owns its own predicates; this returns
    rendered content and never judges it.
    """
    return _render_shipped_instruction_blocks(enabled_languages)


CONTEXT_FREE_POLICY_SECTION_HEADINGS = (
    dist.FOUNDATION_POLICY_HEADING,
    dist.NODE_CONTEXT_POLICY_HEADING,
    dist.SUBAGENT_DISPATCH_POLICY_HEADING,
    dist.ROLE_TASK_CONTRACT_POLICY_HEADING,
)


def _markdown_section(document: str, heading: str) -> str:
    """Return one complete Markdown section selected by its fixture heading."""
    level = len(heading) - len(heading.lstrip("#"))
    match = re.search(
        rf"(?ms)^{re.escape(heading)}\n.*?(?=^#{{1,{level}}} |\Z)", document
    )
    if match is None:
        raise ValueError(f"missing fixture section: {heading}")
    return match.group(0)


def _without_markdown_section(document: str, heading: str) -> str:
    """Create a violating fixture by removing one complete policy section."""
    return document.replace(_markdown_section(document, heading), "", 1)


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

    document = _render_shipped_instruction_blocks()[harness.HARNESS_CODEX]
    router = dist.managed_router_block(document)
    assert token not in router
    assert runtime_name in router
    assert (
        "**Spawn each verifier or reviewer with its role task as the initial turn.**"
    ) in router


def test_dist_template_copies_stay_equivalent() -> None:
    """Assert both dist template copies carry the same complete harness spans."""
    templates = dist.load_harness_templates(_distribution_module())
    claude_copy = templates[harness.HARNESS_CLAUDE]
    codex_copy = templates[harness.HARNESS_CODEX]

    assert claude_copy == codex_copy

    for marker in (
        "<!-- harness:codex -->",
        "<!-- harness:claude -->",
        "multi_agent_v1.spawn_agent",
        "**Collect, preserve, then close.**",
        "**Spawn each verifier or reviewer with its role task as the initial turn.**",
        "Use the `Agent` tool for every configured verifier or reviewer.",
    ):
        assert marker in claude_copy
        assert marker in codex_copy


def test_claude_router_uses_native_configured_agent_dispatch() -> None:
    """Assert Claude keeps native configured-agent dispatch."""
    document = _render_shipped_instruction_blocks()[harness.HARNESS_CLAUDE]
    router = dist.managed_router_block(document)

    assert "Use the `Agent` tool for every configured verifier or reviewer." in router
    assert "OUTCOMEENG_CODEX_AGENT_NAME" not in router


def test_wait_for_load_stop_trigger_policy() -> None:
    """Challenge every wait-for-load requirement across all renders."""
    for enabled_languages in harness.template_language_subsets():
        documents = _render_shipped_instruction_blocks(enabled_languages)
        dist.validate_wait_for_load_policy(documents)
        for _, requirement in dist.WAIT_FOR_LOAD_POLICY_REQUIREMENTS:
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(
                    {
                        agent_harness: document.replace(requirement, "", 1)
                        for agent_harness, document in documents.items()
                    }
                )
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(
                    {
                        agent_harness: document.replace(
                            dist.managed_router_block(document),
                            dist.managed_router_block(document)
                            .replace(requirement, "", 1)
                            .replace("\n", f"\n{requirement}\n", 1),
                            1,
                        )
                        for agent_harness, document in documents.items()
                    }
                )
        codex_document = documents[harness.HARNESS_CODEX]
        claude_router = dist.managed_router_block(documents[harness.HARNESS_CLAUDE])
        for _, requirement in dist.WAIT_FOR_LOAD_CODEX_POLICY_REQUIREMENTS:
            assert requirement not in claude_router
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(
                    {
                        **documents,
                        harness.HARNESS_CODEX: codex_document.replace(
                            requirement, "", 1
                        ),
                    }
                )
        for contradiction in dist.WAIT_FOR_LOAD_POLICY_CONTRADICTIONS:
            with pytest.raises(dist.WaitForLoadPolicyError):
                dist.validate_wait_for_load_policy(
                    {
                        agent_harness: document.replace(
                            dist.managed_router_block(document),
                            dist.managed_router_block(document).replace(
                                "\n", f"\n{contradiction.violating_directive}\n", 1
                            ),
                            1,
                        )
                        for agent_harness, document in documents.items()
                    }
                )


def test_authority_hierarchy_policy_is_complete() -> None:
    """Challenge every authority-hierarchy requirement across all renders."""
    for enabled_languages in harness.template_language_subsets():
        documents = _render_shipped_instruction_blocks(enabled_languages)
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
        documents = _render_shipped_instruction_blocks(enabled_languages)
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
        document = _render_shipped_instruction_blocks(enabled_languages)[
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


def test_codex_router_discovers_deferred_agent_tools() -> None:
    """Challenge deferred typed-agent discovery across every language subset."""
    for enabled_languages in harness.template_language_subsets():
        documents = _render_shipped_instruction_blocks(enabled_languages)
        codex_document = documents[harness.HARNESS_CODEX]
        codex_router = dist.managed_router_block(codex_document)
        policy = dist.deferred_agent_discovery_policy_paragraph(codex_router)
        assert policy is not None
        dist.validate_deferred_agent_discovery_policy(
            {dist.CODEX_HARNESS: codex_document}
        )

        claude_router = dist.managed_router_block(documents[harness.HARNESS_CLAUDE])
        assert dist.DEFERRED_AGENT_DISCOVERY_POLICY_ANCHOR not in claude_router

        for _, required_text in dist.DEFERRED_AGENT_DISCOVERY_POLICY_REQUIREMENTS:
            invalid_document = codex_document.replace(
                policy, policy.replace(required_text, "", 1), 1
            )
            with pytest.raises(dist.DeferredAgentDiscoveryPolicyError):
                dist.validate_deferred_agent_discovery_policy(
                    {dist.CODEX_HARNESS: invalid_document}
                )

        for _, required_text in dist.DEFERRED_AGENT_DISCOVERY_LIFECYCLE_REQUIREMENTS:
            invalid_document = codex_document.replace(required_text, "", 1)
            with pytest.raises(dist.DeferredAgentDiscoveryPolicyError):
                dist.validate_deferred_agent_discovery_policy(
                    {dist.CODEX_HARNESS: invalid_document}
                )

        for contradiction in dist.DEFERRED_AGENT_DISCOVERY_POLICY_CONTRADICTIONS:
            invalid_document = codex_document.replace(
                MODULE.ROUTER_BLOCK_END,
                f"{contradiction.violating_directive}\n\n{MODULE.ROUTER_BLOCK_END}",
                1,
            )
            with pytest.raises(dist.DeferredAgentDiscoveryPolicyError):
                dist.validate_deferred_agent_discovery_policy(
                    {dist.CODEX_HARNESS: invalid_document}
                )


def test_rendered_router_omits_forbidden_session_tokens() -> None:
    """Assert forbidden session-result vocabulary stays outside every router."""
    for agent_harness, document in _render_shipped_instruction_blocks().items():
        router = dist.managed_router_block(document)
        for forbidden_text in dist.FORBIDDEN_ROUTER_TOKENS:
            assert forbidden_text not in router
        independent_prose = document + "\n" + "\n".join(dist.FORBIDDEN_ROUTER_TOKENS)
        dist.validate_foundation_access_policy({agent_harness: independent_prose})


def test_foundation_policy_guard_rejects_missing_requirement() -> None:
    """Assert the foundation validator rejects a missing policy section."""
    agent_harness, document = next(iter(_render_shipped_instruction_blocks().items()))
    invalid_document = _without_markdown_section(
        document, CONTEXT_FREE_POLICY_SECTION_HEADINGS[0]
    )
    try:
        dist.validate_foundation_access_policy({agent_harness: invalid_document})
    except dist.FoundationAccessPolicyError:
        pass
    else:
        raise AssertionError("incomplete foundation policy was accepted")


def test_foundation_policy_guard_rejects_forbidden_router_token() -> None:
    """Assert forbidden session-result vocabulary is rejected inside the router."""
    agent_harness, document = next(iter(_render_shipped_instruction_blocks().items()))
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
            _distribution_module(), harness_templates, (harness.LANG_PRIMARY,)
        )
    except dist.UnresolvedInstructionTemplateError:
        pass
    else:
        raise AssertionError("unresolved build macro was accepted")


def test_obsolete_spx_instruction_files_are_removed(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    spx_dir = repo / "spx"
    spx_dir.mkdir()
    for name in harness.INSTRUCTION_CLAUDE, harness.INSTRUCTION_AGENTS:
        (spx_dir / name).write_text("retired spx instruction file\n", encoding="utf-8")

    harness.run_generator_write_primary(repo, _template(tmp_path))
    assert not (spx_dir / harness.INSTRUCTION_CLAUDE).exists()
    assert not (spx_dir / harness.INSTRUCTION_AGENTS).exists()


def test_every_harness_router_authorizes_subagent_dispatch() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = rendered_instruction_blocks(enabled_languages)
        dist.validate_subagent_dispatch_policy(documents)
        for document in documents.values():
            section = dist.subagent_dispatch_policy_section(
                dist.managed_router_block(document)
            )
            assert section is not None


def test_context_free_verification_dispatch_policy_is_rendered() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = rendered_instruction_blocks(enabled_languages)
        dist.validate_context_free_verification_dispatch_policy(documents)
        for heading in CONTEXT_FREE_POLICY_SECTION_HEADINGS:
            for agent_harness, document in documents.items():
                violating_document = _without_markdown_section(document, heading)
                with pytest.raises(dist.ContextFreeVerificationDispatchPolicyError):
                    dist.validate_context_free_verification_dispatch_policy(
                        {agent_harness: violating_document}
                    )


def test_each_harness_block_carries_only_its_own_dispatch_mechanics() -> None:
    documents = rendered_instruction_blocks()
    dist.validate_harness_dispatch_mechanics(documents)
    for owning_harness, marker in dist.HARNESS_DISPATCH_MECHANICS_MARKERS.items():
        for agent_harness, document in documents.items():
            router = dist.managed_router_block(document)
            if agent_harness == owning_harness:
                assert marker in router
            else:
                assert marker not in router


def test_leaked_harness_dispatch_mechanics_are_rejected() -> None:
    documents = rendered_instruction_blocks()
    for agent_harness, document in documents.items():
        own_marker = dist.HARNESS_DISPATCH_MECHANICS_MARKERS[agent_harness]
        for owning_harness, marker in dist.HARNESS_DISPATCH_MECHANICS_MARKERS.items():
            if owning_harness == agent_harness:
                continue
            leaked = document.replace(own_marker, f"{own_marker} {marker}", 1)
            with pytest.raises(dist.HarnessDispatchMechanicsError):
                dist.validate_harness_dispatch_mechanics({agent_harness: leaked})


def test_dropping_the_dispatch_policy_section_is_rejected() -> None:
    for enabled_languages in harness.template_language_subsets():
        documents = rendered_instruction_blocks(enabled_languages)
        for agent_harness, document in documents.items():
            violating_document = _without_markdown_section(
                document, dist.SUBAGENT_DISPATCH_POLICY_HEADING
            )
            with pytest.raises(dist.SubagentDispatchPolicyError):
                dist.validate_subagent_dispatch_policy(
                    {agent_harness: violating_document}
                )


def test_quoted_policy_requirements_are_rejected() -> None:
    documents = rendered_instruction_blocks()
    for heading in CONTEXT_FREE_POLICY_SECTION_HEADINGS:
        for agent_harness, document in documents.items():
            section = _markdown_section(document, heading)
            quoted = "\n".join(f"> {line}" for line in section.splitlines()) + "\n"
            with pytest.raises(dist.InstructionBlockRenderError):
                dist.validate_context_free_verification_dispatch_policy(
                    {agent_harness: document.replace(section, quoted, 1)}
                )


def test_fenced_policy_requirements_are_rejected() -> None:
    documents = rendered_instruction_blocks()
    for agent_harness, document in documents.items():
        violating_document = document
        for heading in CONTEXT_FREE_POLICY_SECTION_HEADINGS:
            section = _markdown_section(document, heading)
            _, body = section.split("\n", 1)
            fenced = f"{heading}\n```text\n{body}```\n"
            violating_document = violating_document.replace(section, fenced, 1)
        with pytest.raises(dist.InstructionBlockRenderError):
            dist.validate_context_free_verification_dispatch_policy(
                {agent_harness: violating_document}
            )
