"""Compliance evidence for the root managed instruction-block generator.

Rules in ``instruction-block.md`` with deterministic test evidence:

- NEVER: the render substitutes a product-specific string — a brace-delimited illustration
  token in the template passes through to the instruction block unchanged.
- NEVER: an update keeps an unmodeled hand-prose edit inside the instruction block — a
  tampered block re-renders to the same output as a clean render from the same languages.
- ALWAYS: generation writes instruction blocks into both root instruction files.
- ALWAYS: instruction blocks render from harness-specific templates under ``dist/``.
- NEVER: instruction-block generation writes output from a template with unresolved build macros.
- NEVER: obsolete ``spx/`` instruction files remain after instruction-block generation.
- ALWAYS: the drift gate requires each fixed command slot's fence in each root file.
- ALWAYS: the router block references a command slot by name.
- NEVER: the generator authors, edits, or overwrites a command slot's product-owned body.
"""

import pathlib

import pytest

from outcomeeng.distribution import instruction_block
from outcomeeng.distribution.contracts import DIST_DIR_NAME
from outcomeeng_testing.harnesses.instruction_block import (
    INSTRUCTION_AGENTS,
    INSTRUCTION_CLAUDE,
    ILLUSTRATION_TOKEN,
    LANG_PRIMARY,
    NEW_VERSION,
    HARNESS_CLAUDE,
    HARNESS_CODEX,
    ROOT_SHARED_BODY,
    SAMPLE_COMMAND_BODY,
    SAMPLE_COMMAND_BODY_ALT,
    SESSION_ARCHIVE_RESULT_INSTRUCTION,
    SESSION_MANAGEMENT_HEADING,
    SESSION_RESULT_FRONTMATTER_FIELD,
    build_template,
    extract_markdown_section,
    git_command,
    init_git_identity,
    justfile_recipe_body,
    load_instruction_block_module,
    read_canonical_template,
    remove_command_slot_fence,
    render_build_macro,
    run_generator_write,
    run_refresh_pr_step,
    workflow_env_value,
    workflow_run_block,
    workflow_step_block,
    write_template,
)

JUNK_EDIT = "HAND-EDITED JUNK THAT MUST NOT SURVIVE A RE-RENDER"


def test_render_passes_brace_token_through_unchanged() -> None:
    module = load_instruction_block_module()
    rendered = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE
    )
    assert ILLUSTRATION_TOKEN in rendered


def test_re_render_ignores_unmodeled_instruction_block_edits() -> None:
    module = load_instruction_block_module()
    template = build_template(NEW_VERSION)
    clean_block = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE)
    existing_document = f"{ROOT_SHARED_BODY}\n\n{clean_block}"

    tampered = existing_document.replace(
        module.ROUTER_BLOCK_END,
        f"\n## Hand Section\n\n{JUNK_EDIT}\n{module.ROUTER_BLOCK_END}",
    )
    updated = module.upsert_managed_block(tampered, clean_block)

    assert JUNK_EDIT not in updated
    assert ROOT_SHARED_BODY.rstrip("\n") in updated
    assert clean_block in updated


def test_generation_writes_both_root_instruction_files(tmp_path: pathlib.Path) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)

    exit_code = module.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(tmp_path),
            "--languages",
            LANG_PRIMARY,
            "--write",
        ]
    )
    assert exit_code == 0

    written = {
        name
        for name in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.values()
        if (tmp_path / name).is_file()
    }
    assert written == set(module.AGENT_HARNESS_INSTRUCTION_FILENAMES.values())


def test_root_content_outside_instruction_block_is_preserved(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / filename).write_text(ROOT_SHARED_BODY, encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--languages",
                LANG_PRIMARY,
                "--write",
            ]
        )
        == 0
    )

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        assert ROOT_SHARED_BODY.rstrip("\n") in content
        assert content.count(module.ROUTER_MARKER_PREFIX) == 1
        assert content.count(module.ROUTER_BLOCK_END) == 1


def test_instruction_templates_are_loaded_from_harness_specific_dist_outputs(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    expected: dict[str, str] = {}
    for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        path = instruction_block.dist_template_path(harness)
        assert (
            path
            == instruction_block.REPO_ROOT
            / DIST_DIR_NAME
            / harness
            / instruction_block.DIST_TEMPLATE_RELATIVE_PATH
        )
        template = build_template(f"{NEW_VERSION}.{harness}")
        expected[harness] = template
        dist_path = instruction_block.dist_template_path(harness, repo_root=tmp_path)
        dist_path.parent.mkdir(parents=True, exist_ok=True)
        dist_path.write_text(template, encoding="utf-8")

    assert (
        instruction_block.load_harness_templates(module, repo_root=tmp_path) == expected
    )


def test_instruction_render_rejects_unresolved_build_macro() -> None:
    module = load_instruction_block_module()
    harness_templates = {
        harness: build_template(NEW_VERSION)
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    harness_templates[HARNESS_CODEX] += render_build_macro()

    with pytest.raises(instruction_block.UnresolvedInstructionTemplateError):
        instruction_block.render_instruction_blocks_from_harness_templates(
            module, harness_templates, (LANG_PRIMARY,)
        )


def test_justfile_exposes_instruction_writer_and_gate() -> None:
    justfile = instruction_block.REPO_ROOT.joinpath(
        instruction_block.JUSTFILE_NAME
    ).read_text(encoding="utf-8")

    build_body = justfile_recipe_body(
        justfile, instruction_block.BUILD_INSTRUCTIONS_RECIPE
    )
    check_body = justfile_recipe_body(
        justfile, instruction_block.INSTRUCTIONS_CHECK_RECIPE
    )
    # The writer recipe invokes the module with --write; the gate recipe invokes it bare.
    # Scoping each invocation to its own recipe body makes a body swap fail this test.
    assert (
        f"outcomeeng.distribution.instruction_block {instruction_block.WRITE_FLAG}"
        in build_body
    )
    assert instruction_block.WRITE_FLAG not in check_body
    assert "outcomeeng.distribution.instruction_block" in check_body


def test_lefthook_instruction_refresh_uses_rendered_dist_templates() -> None:
    lefthook = instruction_block.REPO_ROOT.joinpath("lefthook.yml").read_text(
        encoding="utf-8"
    )

    assert "run: just build-instructions" in lefthook
    assert (
        "--template src/plugins/spec-tree/skills/understand/templates/instruction-block.md"
        not in lefthook
    )
    assert "--repo-root ." not in lefthook


def test_instruction_drift_probe_marks_untracked_root_files_intent_to_add(
    tmp_path: pathlib.Path,
) -> None:
    init_git_identity(tmp_path)
    (tmp_path / ".gitignore").write_text("\n", encoding="utf-8")
    git_command(tmp_path, "add", ".gitignore")
    git_command(tmp_path, "commit", "-m", "seed repository")
    (tmp_path / INSTRUCTION_CLAUDE).write_text("generated claude\n", encoding="utf-8")
    (tmp_path / INSTRUCTION_AGENTS).write_text("generated agents\n", encoding="utf-8")

    assert instruction_block.drifting_instruction_files(repo_root=tmp_path) == [
        INSTRUCTION_AGENTS,
        INSTRUCTION_CLAUDE,
    ]


def test_instruction_drift_probe_reports_missing_root_files(
    tmp_path: pathlib.Path,
) -> None:
    init_git_identity(tmp_path)
    (tmp_path / ".gitignore").write_text("\n", encoding="utf-8")
    git_command(tmp_path, "add", ".gitignore")
    git_command(tmp_path, "commit", "-m", "seed repository")

    assert instruction_block.drifting_instruction_files(repo_root=tmp_path) == [
        INSTRUCTION_AGENTS,
        INSTRUCTION_CLAUDE,
    ]


def test_instruction_drift_probe_skips_missing_obsolete_spx_files(
    tmp_path: pathlib.Path,
) -> None:
    spx_dir = tmp_path / "spx"
    spx_dir.mkdir()
    for path in (
        tmp_path / INSTRUCTION_CLAUDE,
        tmp_path / INSTRUCTION_AGENTS,
        spx_dir / INSTRUCTION_CLAUDE,
        spx_dir / INSTRUCTION_AGENTS,
    ):
        path.write_text(f"{path.name}\n", encoding="utf-8")

    init_git_identity(tmp_path)
    git_command(tmp_path, "add", ".")
    git_command(tmp_path, "commit", "-m", "seed instruction files")

    (spx_dir / INSTRUCTION_CLAUDE).unlink()
    (spx_dir / INSTRUCTION_AGENTS).unlink()

    assert instruction_block.drifting_instruction_files(repo_root=tmp_path) == [
        f"spx/{INSTRUCTION_AGENTS}",
        f"spx/{INSTRUCTION_CLAUDE}",
    ]


def test_root_instruction_refresh_workflow_regenerates_and_opens_pr() -> None:
    workflow = instruction_block.REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "schedule:" in workflow
    assert "\npermissions:" not in workflow
    assert (
        "    permissions:\n      contents: write\n      pull-requests: write"
        in workflow
    )
    regenerate_commands = workflow_run_block(
        "Regenerate instruction blocks"
    ).splitlines()
    build_skills = regenerate_commands.index("just build-skills")
    build_instructions = regenerate_commands.index("just build-instructions")
    assert build_skills < build_instructions
    assert "just instructions-check" not in regenerate_commands


def test_root_instruction_refresh_workflow_checks_out_main() -> None:
    checkout_step = workflow_step_block("Checkout")

    assert "          ref: main\n" in checkout_step


def test_root_instruction_refresh_workflow_verifies_just_download() -> None:
    install_commands = workflow_run_block("Install just")
    just_sha256 = workflow_env_value("JUST_SHA256")

    assert just_sha256
    assert 'tmp="$(mktemp -d)"' in install_commands
    assert "trap 'rm -rf \"$tmp\"' EXIT" in install_commands
    assert '-o "$tmp/just.tar.gz"' in install_commands
    assert 'printf \'%s  %s\\n\' "$JUST_SHA256" "$tmp/just.tar.gz"' in install_commands
    assert "sha256sum -c -" in install_commands
    assert 'sudo install -m 0755 "$tmp/just" /usr/local/bin/just' in install_commands
    assert "-o just.tar.gz" not in install_commands
    assert "tar -xzf just.tar.gz" not in install_commands
    # The assertion is "before installing it": the checksum verification must precede the
    # install, so a reorder that installs the unverified download fails this test.
    assert install_commands.index("sha256sum -c -") < install_commands.index(
        'sudo install -m 0755 "$tmp/just" /usr/local/bin/just'
    )
    # "fails the run rather than executing": halt-on-error is what turns a `sha256sum -c -`
    # mismatch (non-zero exit through the pipe) into a failed step. Without it the mismatch
    # would print an error and continue into the install, so deleting the directive while
    # keeping the checksum command fails this test.
    assert "set -euo pipefail" in install_commands


def test_root_instruction_refresh_workflow_installs_dprint() -> None:
    # `just build-skills` formats generated dist output with dprint, so the refresh
    # workflow must provision dprint before regenerating — otherwise the build fails
    # with "dprint is required to format generated dist output".
    install_commands = workflow_run_block("Install dprint")
    dprint_version = workflow_env_value("DPRINT_VERSION")

    assert dprint_version
    assert 'bun add -g "dprint@${DPRINT_VERSION}"' in install_commands
    assert "dprint --version" in install_commands
    # The assertion is "before regenerating skill output": the Install dprint step must precede
    # the Regenerate step that runs `just build-skills`, so moving it after fails this test.
    workflow = instruction_block.REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
    assert workflow.index("      - name: Install dprint") < workflow.index(
        "      - name: Regenerate instruction blocks"
    )


def test_root_instruction_refresh_pr_step_exits_cleanly_without_drift(
    tmp_path: pathlib.Path,
) -> None:
    gh_log = tmp_path / "gh.log"
    init_git_identity(tmp_path)
    (tmp_path / INSTRUCTION_CLAUDE).write_text("current\n", encoding="utf-8")
    (tmp_path / INSTRUCTION_AGENTS).write_text("current\n", encoding="utf-8")
    git_command(tmp_path, "add", ".")
    git_command(tmp_path, "commit", "-m", "seed instruction files")

    output = run_refresh_pr_step(tmp_path, gh_log)

    assert output == "Root instruction blocks are current.\n"
    assert not gh_log.exists()


def test_root_instruction_refresh_pr_step_stages_obsolete_deletions(
    tmp_path: pathlib.Path,
) -> None:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    gh_log = tmp_path / "gh.log"
    git_command(tmp_path, "init", "--bare", str(remote))
    git_command(tmp_path, "clone", str(remote), str(repo))
    git_command(repo, "config", "user.name", "Test User")
    git_command(repo, "config", "user.email", "test@example.com")
    spx_dir = repo / "spx"
    spx_dir.mkdir()
    for path in (
        repo / INSTRUCTION_CLAUDE,
        repo / INSTRUCTION_AGENTS,
        spx_dir / INSTRUCTION_CLAUDE,
        spx_dir / INSTRUCTION_AGENTS,
    ):
        path.write_text(f"{path.name}\n", encoding="utf-8")
    git_command(repo, "add", ".")
    git_command(repo, "commit", "-m", "seed instruction files")
    git_command(repo, "branch", "-M", "main")
    git_command(repo, "push", "-u", "origin", "main")

    (repo / INSTRUCTION_CLAUDE).write_text("updated\n", encoding="utf-8")
    (repo / INSTRUCTION_AGENTS).write_text("updated\n", encoding="utf-8")
    (spx_dir / INSTRUCTION_CLAUDE).unlink()
    (spx_dir / INSTRUCTION_AGENTS).unlink()

    run_refresh_pr_step(repo, gh_log)

    committed = git_command(
        repo,
        "show",
        "--name-status",
        "--format=%s",
        "automation/refresh-instruction-blocks",
    ).stdout
    assert "Refresh root instruction blocks" in committed
    assert f"M\t{INSTRUCTION_CLAUDE}" in committed
    assert f"M\t{INSTRUCTION_AGENTS}" in committed
    assert f"D\tspx/{INSTRUCTION_CLAUDE}" in committed
    assert f"D\tspx/{INSTRUCTION_AGENTS}" in committed
    gh_calls = gh_log.read_text(encoding="utf-8")
    assert "pr list" in gh_calls
    assert "pr create" in gh_calls


def test_write_regenerates_a_drifted_instruction_block(tmp_path: pathlib.Path) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    args = [
        "--template",
        str(template),
        "--repo-root",
        str(tmp_path),
        "--languages",
        LANG_PRIMARY,
    ]
    assert module.main([*args, "--write"]) == 0

    # Drift both instruction blocks by hand, then regenerate. Product-owned root content
    # outside the block markers remains; drift inside the instruction block is removed.
    instruction_files = [
        tmp_path / name for name in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.values()
    ]
    for instruction_file in instruction_files:
        instruction_file.write_text(
            instruction_file.read_text().replace(
                module.ROUTER_BLOCK_END,
                f"\nHAND DRIFT\n{module.ROUTER_BLOCK_END}",
            ),
            encoding="utf-8",
        )
    assert module.main([*args, "--write"]) == 0
    for instruction_file in instruction_files:
        assert "HAND DRIFT" not in instruction_file.read_text(encoding="utf-8")


def test_no_rendered_instruction_block_teaches_result_session_frontmatter() -> None:
    module = load_instruction_block_module()
    template = read_canonical_template()
    # Render the canonical template through the generator for each agent harness and assert the
    # rendered Session Management section carries no session-result instruction — a deterministic
    # regression guard on render()'s output that fails if a template edit reintroduces the token.
    for harness in (HARNESS_CLAUDE, HARNESS_CODEX):
        rendered = module.render(template, (LANG_PRIMARY,), NEW_VERSION, harness)
        section = extract_markdown_section(rendered, SESSION_MANAGEMENT_HEADING)
        assert SESSION_ARCHIVE_RESULT_INSTRUCTION not in section
        assert SESSION_RESULT_FRONTMATTER_FIELD not in section


def test_write_removes_obsolete_spx_instruction_files(tmp_path: pathlib.Path) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    spx_dir = tmp_path / "spx"
    spx_dir.mkdir()
    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (spx_dir / filename).write_text("obsolete\n", encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--languages",
                LANG_PRIMARY,
                "--write",
            ]
        )
        == 0
    )

    assert not (spx_dir / INSTRUCTION_CLAUDE).exists()
    assert not (spx_dir / INSTRUCTION_AGENTS).exists()


def test_generation_requires_every_fixed_command_slot_fence(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / filename).write_text(ROOT_SHARED_BODY, encoding="utf-8")

    assert run_generator_write(module, tmp_path, template, languages=LANG_PRIMARY) == 0

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        for slot in module.FIXED_COMMAND_SLOTS:
            assert module.parse_command_slot(content, slot) is not None


def test_rendered_router_references_each_command_slot_by_name() -> None:
    module = load_instruction_block_module()
    template = read_canonical_template()
    # Render the canonical template through the generator for each harness and assert every
    # slot name survives into the rendered router block — exercising render()'s pass-through of
    # non-conditional body text, not the raw authored template prose.
    for harness in (HARNESS_CLAUDE, HARNESS_CODEX):
        rendered = module.render(template, (LANG_PRIMARY,), NEW_VERSION, harness)
        for slot in module.FIXED_COMMAND_SLOTS:
            assert module.slot_reference(slot) in rendered


def test_drift_gate_reports_a_missing_command_slot_fence(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write(module, tmp_path, template, languages=LANG_PRIMARY) == 0
    init_git_identity(tmp_path)
    git_command(tmp_path, "add", ".")
    git_command(tmp_path, "commit", "-m", "seed instruction files")

    # A committed root file loses one slot fence; the gate regenerates (restoring it) and its
    # drift probe reports the file as drifted.
    agents = tmp_path / INSTRUCTION_AGENTS
    agents.write_text(
        remove_command_slot_fence(agents.read_text(encoding="utf-8"), module.SLOT_GATE),
        encoding="utf-8",
    )
    assert (
        module.parse_command_slot(agents.read_text(encoding="utf-8"), module.SLOT_GATE)
        is None
    )
    git_command(tmp_path, "commit", "-am", "drop gate fence")

    assert run_generator_write(module, tmp_path, template, languages=LANG_PRIMARY) == 0
    assert (
        module.parse_command_slot(agents.read_text(encoding="utf-8"), module.SLOT_GATE)
        is not None
    )
    assert INSTRUCTION_AGENTS in instruction_block.drifting_instruction_files(
        repo_root=tmp_path
    )


def test_regenerate_preserves_a_filled_command_slot_body(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write(module, tmp_path, template, languages=LANG_PRIMARY) == 0

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        path = tmp_path / filename
        path.write_text(
            module.set_command_slot(
                path.read_text(encoding="utf-8"), module.SLOT_MERGE, SAMPLE_COMMAND_BODY
            ),
            encoding="utf-8",
        )

    assert run_generator_write(module, tmp_path, template, languages=LANG_PRIMARY) == 0

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        assert (
            module.parse_command_slot(content, module.SLOT_MERGE) == SAMPLE_COMMAND_BODY
        )


def test_drift_gate_reports_a_cross_file_command_slot_conflict(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write(module, tmp_path, template, languages=LANG_PRIMARY) == 0

    claude = tmp_path / INSTRUCTION_CLAUDE
    agents = tmp_path / INSTRUCTION_AGENTS
    claude.write_text(
        module.set_command_slot(
            claude.read_text(encoding="utf-8"), module.SLOT_MERGE, SAMPLE_COMMAND_BODY
        ),
        encoding="utf-8",
    )
    agents.write_text(
        module.set_command_slot(
            agents.read_text(encoding="utf-8"),
            module.SLOT_MERGE,
            SAMPLE_COMMAND_BODY_ALT,
        ),
        encoding="utf-8",
    )

    assert instruction_block.conflicting_command_slots(repo_root=tmp_path) == (
        module.SLOT_MERGE,
    )
    report = instruction_block.render_report([], (module.SLOT_MERGE,))
    assert instruction_block.SLOT_CONFLICT_HEADER in report
    assert module.slot_reference(module.SLOT_MERGE) in report
