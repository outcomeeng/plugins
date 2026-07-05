"""Compliance evidence for the instruction-block render model.

The ALWAYS/NEVER rules of ``instruction-block.md`` with deterministic test evidence: both root
files are written together, the router is first and carries a read-the-whole-file instruction,
generation reads the ``dist/`` templates, the writer is bound through the ``just`` recipes and
the lefthook pre-commit hook, the drift gate reports a missing root path and overwrites router
drift, the refresh workflow regenerates and opens a PR only on drift while verifying its pinned
tooling, no product-specific string enters the router, a former command-slot fence is ordinary
content, a reconcile never blends bodies, the retired session tokens never render, an unresolved
build macro is rejected, and retired ``spx/`` instruction files are removed. Real repository
config (``justfile``, ``lefthook.yml``, the workflow) is read through harness helpers.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng.distribution import instruction_block as dist
from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


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
    template = harness.read_canonical_template()
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


def test_generation_reads_dist_templates() -> None:
    for agent_harness in MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        path = dist.dist_template_path(agent_harness)
        assert dist.DIST_DIR_NAME in path.parts
        assert agent_harness in path.parts


def test_justfile_binds_build_and_check_recipes() -> None:
    justfile = dist.REPO_ROOT.joinpath(dist.JUSTFILE_NAME).read_text(encoding="utf-8")
    build_body = harness.justfile_recipe_body(justfile, dist.BUILD_INSTRUCTIONS_RECIPE)
    check_body = harness.justfile_recipe_body(justfile, dist.INSTRUCTIONS_CHECK_RECIPE)
    assert f"outcomeeng.distribution.instruction_block {dist.WRITE_FLAG}" in build_body
    assert "outcomeeng.distribution.instruction_block" in check_body
    assert dist.WRITE_FLAG not in check_body


def test_lefthook_regenerates_through_build_instructions() -> None:
    lefthook = dist.REPO_ROOT.joinpath("lefthook.yml").read_text(encoding="utf-8")
    # the hook's run directive regenerates through the recipe, not a direct generator invocation
    assert "run: just build-instructions" in lefthook


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

    drift = dist.drifting_instruction_files(repo_root=repo, module=MODULE)
    assert harness.INSTRUCTION_CLAUDE in drift


def test_regenerate_overwrites_router_drift(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    template = _template(tmp_path)
    harness.run_generator_write_primary(repo, template)
    claude = repo / harness.INSTRUCTION_CLAUDE
    claude.write_text(
        claude.read_text(encoding="utf-8").replace(f"v{harness.NEW_VERSION}", "v0.0.1"),
        encoding="utf-8",
    )
    harness.run_generator_write_primary(repo, template)
    assert (
        MODULE.parse_instruction_version(claude.read_text(encoding="utf-8"))
        == harness.NEW_VERSION
    )


def test_refresh_workflow_regenerates_and_opens_pr() -> None:
    workflow = dist.REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    regenerate = harness.workflow_run_block("Regenerate instruction blocks")
    assert "just build-instructions" in regenerate
    pr_step = harness.workflow_step_block("Open instruction-block refresh pull request")
    # opens or updates the PR only when git reports drift
    assert "git status --porcelain" in pr_step


def test_refresh_workflow_checks_out_main() -> None:
    checkout = harness.workflow_step_block("Checkout")
    assert "main" in checkout


def test_refresh_workflow_verifies_just_download() -> None:
    install = harness.workflow_run_block("Install just")
    just_sha256 = harness.workflow_env_value("JUST_SHA256")
    # the pinned checksum is declared and the install verifies the download against it
    assert len(just_sha256) == 64
    assert "$JUST_SHA256" in install
    assert "sha256sum" in install.lower()


def test_refresh_workflow_installs_dprint() -> None:
    install = harness.workflow_run_block("Install dprint")
    dprint_version = harness.workflow_env_value("DPRINT_VERSION")
    # the pinned version is declared and the install references it
    assert dprint_version
    assert "${DPRINT_VERSION}" in install


def test_render_passes_brace_token_through_unchanged() -> None:
    rendered = MODULE.render(
        harness.build_template(harness.NEW_VERSION),
        (harness.LANG_PRIMARY,),
        harness.NEW_VERSION,
        harness.HARNESS_CLAUDE,
    )
    assert harness.ILLUSTRATION_TOKEN in rendered


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


def test_rendered_router_omits_retired_session_tokens() -> None:
    template = harness.read_canonical_template()
    version = MODULE.parse_template_version(template)
    for agent_harness in harness.TEMPLATE_HARNESSES:
        rendered = MODULE.render(
            template, harness.TEMPLATE_LANGUAGES, version, agent_harness
        )
        assert harness.SESSION_ARCHIVE_RESULT_INSTRUCTION not in rendered
        assert harness.SESSION_RESULT_FRONTMATTER_FIELD not in rendered


def test_unresolved_build_macro_is_rejected() -> None:
    with pytest.raises(dist.UnresolvedInstructionTemplateError):
        dist.assert_no_unresolved_build_macros(
            harness.render_build_macro(), path="synthetic-template"
        )


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
