"""Scenario evidence for the instruction-block root managed-block generator."""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.instruction_block import (
    INSTRUCTION_AGENTS,
    INSTRUCTION_CLAUDE,
    LANG_PRIMARY,
    LANG_SECONDARY,
    NEW_SECTION,
    NEW_VERSION,
    OLD_VERSION,
    HARNESS_CLAUDE,
    HARNESS_CODEX,
    ROOT_SHARED_BODY,
    SAMPLE_COMMAND_BODY,
    SAMPLE_COMMAND_BODY_ALT,
    build_template,
    load_instruction_block_module,
    remove_command_slot_fence,
    root_instruction_topology_symlinked,
    harness_line,
    run_generator_write_primary,
    write_both_instruction_files,
    write_spx_tree_with_tests,
    write_template,
)


def test_scaffold_renders_only_enabled_language() -> None:
    module = load_instruction_block_module()
    rendered = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE
    )
    assert f"### {LANG_PRIMARY.capitalize()}" in rendered
    assert f"### {LANG_SECONDARY.capitalize()}" not in rendered


def test_harness_block_renders_only_for_its_harness() -> None:
    module = load_instruction_block_module()
    template = build_template(NEW_VERSION)
    claude = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE)
    codex = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CODEX)

    assert HARNESS_CLAUDE.upper() in claude
    assert HARNESS_CODEX.upper() not in claude
    assert HARNESS_CODEX.upper() in codex
    assert HARNESS_CLAUDE.upper() not in codex


def test_both_blocks_share_body_and_differ_only_in_harness_spans() -> None:
    module = load_instruction_block_module()
    template = build_template(NEW_VERSION)
    claude = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE)
    codex = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CODEX)

    harness_lines = {harness_line(HARNESS_CLAUDE), harness_line(HARNESS_CODEX)}
    claude_shared = [line for line in claude.splitlines() if line not in harness_lines]
    codex_shared = [line for line in codex.splitlines() if line not in harness_lines]
    assert claude_shared == codex_shared
    assert claude != codex


def test_update_propagates_new_section_and_preserves_languages() -> None:
    module = load_instruction_block_module()
    instructions = module.upsert_managed_block(
        ROOT_SHARED_BODY,
        module.render(
            build_template(OLD_VERSION), (LANG_PRIMARY,), OLD_VERSION, HARNESS_CLAUDE
        ),
    )

    new_template = build_template(NEW_VERSION, extra_section=True)
    languages = module.parse_languages(instructions)

    for harness in (HARNESS_CLAUDE, HARNESS_CODEX):
        updated = module.render(new_template, languages, NEW_VERSION, harness)
        assert f"## {NEW_SECTION}" in updated
        assert f"### {LANG_PRIMARY.capitalize()}" in updated
        assert f"### {LANG_SECONDARY.capitalize()}" not in updated


def test_cli_check_ignores_unmanaged_metadata_comments(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    unmanaged_metadata = (
        f"{ROOT_SHARED_BODY}\n"
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {NEW_VERSION} -->\n"
        f"{module.MANAGED_LANGUAGES_PREFIX} {LANG_PRIMARY} -->\n"
    )
    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / instruction_name).write_text(unmanaged_metadata, encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--check",
                "--languages",
                LANG_PRIMARY,
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"


def test_cli_check_treats_markerless_legacy_instructions_as_stale(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    legacy_instructions = (
        f"{module.FRONTMATTER_DELIMITER}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{NEW_VERSION}"\n'
        f"{module.LANGUAGES_KEY}: [{LANG_PRIMARY}]\n"
        f"{module.FRONTMATTER_DELIMITER}\n"
        "\n# Legacy Spec Tree Instructions\n"
    )
    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / instruction_name).write_text(legacy_instructions, encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--check",
                "--languages",
                LANG_PRIMARY,
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"


def test_cli_check_treats_legacy_marker_block_as_stale(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    legacy_start, legacy_end = module.LEGACY_MANAGED_BLOCK_MARKERS[0]
    legacy_block = (
        f"{ROOT_SHARED_BODY}\n"
        f"{legacy_start}\n"
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {NEW_VERSION} -->\n"
        f"{module.MANAGED_TEMPLATE_SOURCE_PREFIX} {module.DEFAULT_TEMPLATE_SOURCE} -->\n"
        f"{module.MANAGED_LANGUAGES_PREFIX} {LANG_PRIMARY} -->\n\n"
        "Legacy body.\n\n"
        f"{legacy_end}\n"
    )
    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / instruction_name).write_text(legacy_block, encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--check",
                "--languages",
                LANG_PRIMARY,
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"


def test_cli_write_migrates_legacy_marker_block_in_place(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    legacy_start, legacy_end = module.LEGACY_MANAGED_BLOCK_MARKERS[0]
    legacy_block = (
        f"{ROOT_SHARED_BODY}\n"
        f"{legacy_start}\n"
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {OLD_VERSION} -->\n"
        f"{module.MANAGED_TEMPLATE_SOURCE_PREFIX} {module.DEFAULT_TEMPLATE_SOURCE} -->\n"
        f"{module.MANAGED_LANGUAGES_PREFIX} {LANG_PRIMARY} -->\n\n"
        "Legacy body.\n\n"
        f"{legacy_end}\n"
    )
    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / instruction_name).write_text(legacy_block, encoding="utf-8")

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

    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / instruction_name).read_text(encoding="utf-8")
        assert content.count(module.ROUTER_BLOCK_END) == 1
        assert module.ROUTER_MARKER_PREFIX in content
        assert legacy_start not in content
        assert "Legacy body." not in content
        assert ROOT_SHARED_BODY.rstrip("\n") in content


def test_cli_write_replaces_markerless_generated_instructions_body(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    legacy_instructions = (
        f"{module.FRONTMATTER_DELIMITER}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{OLD_VERSION}"\n'
        f"{module.TEMPLATE_SOURCE_KEY}: {module.DEFAULT_TEMPLATE_SOURCE}\n"
        f"{module.LANGUAGES_KEY}: [{LANG_PRIMARY}]\n"
        f"{module.FRONTMATTER_DELIMITER}\n\n"
        "# spx/ Directory Guide (Spec Tree)\n\n"
        "Legacy generated guidance.\n"
    )
    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / instruction_name).write_text(legacy_instructions, encoding="utf-8")

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--write",
                "--languages",
                LANG_PRIMARY,
            ]
        )
        == 0
    )

    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / instruction_name).read_text(encoding="utf-8")
        assert content.startswith(module.ROUTER_MARKER_PREFIX)
        assert "Legacy generated guidance." not in content


def test_cli_check_uses_managed_metadata_not_root_prose_comments(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    unmanaged_metadata = (
        f"{ROOT_SHARED_BODY}\n"
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {OLD_VERSION} -->\n"
        f"{module.MANAGED_LANGUAGES_PREFIX} {LANG_SECONDARY} -->\n"
    )
    write_both_instruction_files(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        instruction_path = tmp_path / instruction_name
        instruction_path.write_text(
            f"{unmanaged_metadata}\n{instruction_path.read_text(encoding='utf-8')}",
            encoding="utf-8",
        )

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--check",
                "--languages",
                LANG_PRIMARY,
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "current"


def test_cli_check_uses_managed_metadata_not_root_frontmatter(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    misleading_frontmatter = (
        f"{module.FRONTMATTER_DELIMITER}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{OLD_VERSION}"\n'
        f"{module.LANGUAGES_KEY}: [{LANG_SECONDARY}]\n"
        f"{module.FRONTMATTER_DELIMITER}\n\n"
    )
    write_both_instruction_files(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    for instruction_name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        instruction_path = tmp_path / instruction_name
        instruction_path.write_text(
            f"{misleading_frontmatter}{instruction_path.read_text(encoding='utf-8')}",
            encoding="utf-8",
        )

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--check",
                "--languages",
                LANG_PRIMARY,
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "current"


def test_cli_check_reports_absent_when_one_instruction_file_is_missing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    claude_name = module.AGENT_HARNESS_INSTRUCTION_FILENAMES[HARNESS_CLAUDE]
    block = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE
    )
    (tmp_path / claude_name).write_text(
        module.upsert_managed_block(ROOT_SHARED_BODY, block),
        encoding="utf-8",
    )
    check = [
        "--template",
        str(template),
        "--repo-root",
        str(tmp_path),
        "--check",
        "--languages",
        LANG_PRIMARY,
    ]
    assert module.main(check) == 0
    assert capsys.readouterr().out.strip() == "absent"


def test_cli_write_without_repo_root_exits_2(tmp_path: pathlib.Path) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert module.main(["--template", str(template), "--write"]) == 2


def test_cli_rejects_non_directory_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    repo_root = tmp_path / "not-a-directory"
    repo_root.write_text("not a directory\n", encoding="utf-8")

    exit_code = module.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(repo_root),
            "--check",
        ]
    )

    assert exit_code == 2
    assert "--repo-root is not a directory" in capsys.readouterr().err


def test_cli_rejects_missing_template(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    missing = tmp_path / "nonexistent-template.md"

    exit_code = module.main(
        ["--template", str(missing), "--repo-root", str(tmp_path), "--check"]
    )

    assert exit_code == 2
    assert "--template does not exist" in capsys.readouterr().err


def test_cli_rejects_symlinked_template(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    real_template = write_template(tmp_path, NEW_VERSION)
    linked = tmp_path / "linked-template.md"
    linked.symlink_to(real_template)

    exit_code = module.main(
        ["--template", str(linked), "--repo-root", str(tmp_path), "--check"]
    )

    assert exit_code == 2
    assert "--template is a symlink" in capsys.readouterr().err


def test_cli_rejects_directory_template(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    directory = tmp_path / "template-dir"
    directory.mkdir()

    exit_code = module.main(
        ["--template", str(directory), "--repo-root", str(tmp_path), "--check"]
    )

    assert exit_code == 2
    assert "--template is not a regular file" in capsys.readouterr().err


def test_cli_rejects_root_instruction_symlink_escaping_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-instructions.md"
    outside.write_text(ROOT_SHARED_BODY, encoding="utf-8")
    (tmp_path / INSTRUCTION_CLAUDE).symlink_to(outside)

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

    assert exit_code == 2
    assert "symlink target escapes --repo-root" in capsys.readouterr().err


def test_cli_fill_slot_rejects_root_instruction_symlink_escaping_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-fill.md"
    outside.write_text(ROOT_SHARED_BODY, encoding="utf-8")
    (tmp_path / INSTRUCTION_CLAUDE).symlink_to(outside)
    (tmp_path / INSTRUCTION_AGENTS).write_text(ROOT_SHARED_BODY, encoding="utf-8")

    exit_code = module.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(tmp_path),
            "--fill-slot",
            module.SLOT_MERGE,
            "--from",
            HARNESS_CLAUDE,
        ]
    )

    assert exit_code == 2
    assert "symlink target escapes --repo-root" in capsys.readouterr().err


def test_cli_rejects_spx_symlink_during_language_detection(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-spx"
    outside.mkdir()
    (tmp_path / "spx").symlink_to(outside)

    exit_code = module.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(tmp_path),
            "--write",
        ]
    )

    assert exit_code == 2
    assert "spx directory is a symlink" in capsys.readouterr().err


def test_cli_write_creates_both_root_instruction_files(tmp_path: pathlib.Path) -> None:
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
    for filename in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.values():
        instruction_file = tmp_path / filename
        assert instruction_file.is_file()
        content = instruction_file.read_text(encoding="utf-8")
        assert module.ROUTER_MARKER_PREFIX in content
        assert f"### {LANG_PRIMARY.capitalize()}" in content
        assert content.endswith("\n")


def test_cli_write_preserves_root_content_outside_instruction_block(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    (tmp_path / INSTRUCTION_AGENTS).write_text(ROOT_SHARED_BODY, encoding="utf-8")

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

    for filename in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.values():
        content = (tmp_path / filename).read_text(encoding="utf-8")
        assert ROOT_SHARED_BODY.rstrip("\n") in content
        assert content.count(module.ROUTER_BLOCK_END) == 1


def test_cli_write_replaces_symlinked_root_instruction_with_regular_file(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    topology = root_instruction_topology_symlinked()
    for name, body in topology.files.items():
        (tmp_path / name).write_text(body, encoding="utf-8")
    for name, target in topology.symlinks.items():
        (tmp_path / name).symlink_to(target)

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

    claude_path = tmp_path / INSTRUCTION_CLAUDE
    agents_path = tmp_path / INSTRUCTION_AGENTS
    assert claude_path.is_file()
    assert agents_path.is_file()
    assert not claude_path.is_symlink()
    assert not agents_path.is_symlink()
    assert ROOT_SHARED_BODY.rstrip("\n") in claude_path.read_text(encoding="utf-8")
    assert ROOT_SHARED_BODY.rstrip("\n") in agents_path.read_text(encoding="utf-8")


def test_cli_detects_languages_from_test_extensions(tmp_path: pathlib.Path) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    py_ext = next(
        ext
        for ext, lang in module.LANGUAGE_BY_EXTENSION.items()
        if lang == LANG_PRIMARY
    )
    write_spx_tree_with_tests(tmp_path / "spx", (py_ext,))
    exit_code = module.main(
        ["--template", str(template), "--repo-root", str(tmp_path), "--write"]
    )
    assert exit_code == 0
    content = (tmp_path / INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
    assert f"### {LANG_PRIMARY.capitalize()}" in content
    assert f"### {LANG_SECONDARY.capitalize()}" not in content


def test_is_stale_treats_a_malformed_version_as_stale() -> None:
    module = load_instruction_block_module()
    assert module.is_stale("0.18.0-beta", NEW_VERSION) is True
    assert module.is_stale(OLD_VERSION, "not-a-version") is True


def test_router_marker_records_version_and_langs_inline_without_source() -> None:
    module = load_instruction_block_module()
    block = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE
    )
    lines = block.splitlines()
    assert lines[0] == module.router_marker(NEW_VERSION, (LANG_PRIMARY,))
    assert lines[-1] == module.ROUTER_BLOCK_END
    assert module.MANAGED_TEMPLATE_SOURCE_PREFIX not in block
    assert module.parse_instruction_version(block) == NEW_VERSION
    assert module.parse_instruction_languages(block) == (LANG_PRIMARY,)


def test_write_scaffolds_absent_slot_fences_with_placeholders(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / filename).write_text(ROOT_SHARED_BODY, encoding="utf-8")

    assert run_generator_write_primary(tmp_path, template) == 0

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        for slot in module.FIXED_COMMAND_SLOTS:
            body = module.parse_command_slot(content, slot)
            assert body is not None
            assert not module.is_slot_filled(body)
            assert module.SLOT_PLACEHOLDER_MARK in body


def test_write_fills_an_empty_slot_from_its_filled_sibling(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write_primary(tmp_path, template) == 0

    claude = tmp_path / INSTRUCTION_CLAUDE
    claude.write_text(
        module.set_command_slot(
            claude.read_text(encoding="utf-8"), module.SLOT_MERGE, SAMPLE_COMMAND_BODY
        ),
        encoding="utf-8",
    )

    assert run_generator_write_primary(tmp_path, template) == 0

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        assert (
            module.parse_command_slot(content, module.SLOT_MERGE) == SAMPLE_COMMAND_BODY
        )


def test_write_leaves_a_conflicting_slot_unchanged_and_reports_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write_primary(tmp_path, template) == 0

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

    # A second write leaves both conflicting bodies unchanged rather than choosing one.
    assert run_generator_write_primary(tmp_path, template) == 0
    assert (
        module.parse_command_slot(claude.read_text(encoding="utf-8"), module.SLOT_MERGE)
        == SAMPLE_COMMAND_BODY
    )
    assert (
        module.parse_command_slot(agents.read_text(encoding="utf-8"), module.SLOT_MERGE)
        == SAMPLE_COMMAND_BODY_ALT
    )
    assert module.conflicting_command_slots(tmp_path) == (module.SLOT_MERGE,)

    # The conflict surfaces as drift at the check surface.
    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--check",
                "--languages",
                LANG_PRIMARY,
            ]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"


def test_generation_re_renders_router_while_preserving_slots_and_prose(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    old_template = write_template(tmp_path, OLD_VERSION)
    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (tmp_path / filename).write_text(ROOT_SHARED_BODY, encoding="utf-8")
    assert run_generator_write_primary(tmp_path, old_template) == 0

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        path = tmp_path / filename
        path.write_text(
            module.set_command_slot(
                path.read_text(encoding="utf-8"),
                module.SLOT_VERIFY,
                SAMPLE_COMMAND_BODY,
            ),
            encoding="utf-8",
        )

    new_dir = tmp_path / "newtpl"
    new_dir.mkdir()
    new_template = write_template(new_dir, NEW_VERSION, extra_section=True)
    assert run_generator_write_primary(tmp_path, new_template) == 0

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        # Region 1 — the router block re-renders: the new section and new version arrive.
        assert f"## {NEW_SECTION}" in content
        assert module.router_marker(NEW_VERSION, (LANG_PRIMARY,)) in content
        # Region 2 — the command slot's product body is preserved verbatim.
        assert (
            module.parse_command_slot(content, module.SLOT_VERIFY)
            == SAMPLE_COMMAND_BODY
        )
        # Region 3 — out-of-fence product prose is preserved.
        assert ROOT_SHARED_BODY.rstrip("\n") in content


def test_fill_slot_reconciles_a_conflict_from_the_named_harness(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write_primary(tmp_path, template) == 0

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
    assert module.conflicting_command_slots(tmp_path) == (module.SLOT_MERGE,)

    assert (
        module.main(
            [
                "--template",
                str(template),
                "--repo-root",
                str(tmp_path),
                "--fill-slot",
                module.SLOT_MERGE,
                "--from",
                HARNESS_CLAUDE,
            ]
        )
        == 0
    )

    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        content = (tmp_path / filename).read_text(encoding="utf-8")
        assert (
            module.parse_command_slot(content, module.SLOT_MERGE) == SAMPLE_COMMAND_BODY
        )
    assert module.conflicting_command_slots(tmp_path) == ()


def test_cli_fill_slot_errors_when_a_target_root_file_is_absent(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    # AGENTS.md carries a filled merge slot; CLAUDE.md is absent — reconciling across both
    # files cannot complete, so the run fails loudly rather than filling only one file.
    agents_text = module.set_command_slot(
        module.ensure_slot_fences(ROOT_SHARED_BODY),
        module.SLOT_MERGE,
        SAMPLE_COMMAND_BODY,
    )
    (tmp_path / INSTRUCTION_AGENTS).write_text(agents_text, encoding="utf-8")

    exit_code = module.main(
        [
            "--template",
            str(template),
            "--repo-root",
            str(tmp_path),
            "--fill-slot",
            module.SLOT_MERGE,
            "--from",
            HARNESS_CODEX,
        ]
    )

    assert exit_code == 2
    assert "root instruction file is absent" in capsys.readouterr().err


def test_cli_check_reports_stale_when_a_command_slot_fence_is_missing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write_primary(tmp_path, template) == 0
    check = [
        "--template",
        str(template),
        "--repo-root",
        str(tmp_path),
        "--check",
        "--languages",
        LANG_PRIMARY,
    ]
    assert module.main(check) == 0
    assert capsys.readouterr().out.strip() == "current"

    agents = tmp_path / INSTRUCTION_AGENTS
    agents.write_text(
        remove_command_slot_fence(agents.read_text(encoding="utf-8"), module.SLOT_GATE),
        encoding="utf-8",
    )
    assert (
        module.parse_command_slot(agents.read_text(encoding="utf-8"), module.SLOT_GATE)
        is None
    )

    # The shipped --check verb itself reports the missing fence, without the git-diff gate.
    assert module.main(check) == 0
    assert capsys.readouterr().out.strip() == "stale"


def test_write_repairs_a_malformed_open_only_slot_fence_preserving_its_body(
    tmp_path: pathlib.Path,
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write_primary(tmp_path, template) == 0

    # Fill merge with a real command, then corrupt it into an open marker with no matching
    # close — a truncated write that leaves the product body orphaned.
    agents = tmp_path / INSTRUCTION_AGENTS
    filled = module.set_command_slot(
        agents.read_text(encoding="utf-8"), module.SLOT_MERGE, SAMPLE_COMMAND_BODY
    )
    agents.write_text(
        filled.replace(module.slot_close_marker(module.SLOT_MERGE), ""),
        encoding="utf-8",
    )
    assert (
        module.parse_command_slot(agents.read_text(encoding="utf-8"), module.SLOT_MERGE)
        is None
    )

    # A subsequent --write repairs the fence AND preserves the real command body — the
    # generator never overwrites a product-owned slot body with a placeholder.
    assert run_generator_write_primary(tmp_path, template) == 0
    assert (
        module.parse_command_slot(agents.read_text(encoding="utf-8"), module.SLOT_MERGE)
        == SAMPLE_COMMAND_BODY
    )


def test_cli_check_reports_stale_when_a_slot_is_filled_in_only_one_file(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_instruction_block_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert run_generator_write_primary(tmp_path, template) == 0
    check = [
        "--template",
        str(template),
        "--repo-root",
        str(tmp_path),
        "--check",
        "--languages",
        LANG_PRIMARY,
    ]
    assert module.main(check) == 0
    assert capsys.readouterr().out.strip() == "current"

    # Fill merge in CLAUDE.md only; AGENTS.md keeps the placeholder — the two bodies differ.
    claude = tmp_path / INSTRUCTION_CLAUDE
    claude.write_text(
        module.set_command_slot(
            claude.read_text(encoding="utf-8"), module.SLOT_MERGE, SAMPLE_COMMAND_BODY
        ),
        encoding="utf-8",
    )

    # --check reports stale: sibling-fill on the next --write would change the files.
    assert module.main(check) == 0
    assert capsys.readouterr().out.strip() == "stale"
