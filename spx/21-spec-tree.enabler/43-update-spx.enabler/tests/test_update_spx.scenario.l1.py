"""Scenario evidence for the update-spx root managed-section generator."""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.update_spx import (
    GUIDE_AGENTS,
    GUIDE_CLAUDE,
    LANG_PRIMARY,
    LANG_SECONDARY,
    NEW_SECTION,
    HARNESS_CLAUDE,
    HARNESS_CODEX,
    ROOT_GUIDE_SHARED_BODY,
    build_template,
    load_update_spx_module,
    root_guide_topology_symlinked,
    harness_line,
    write_spx_tree_with_tests,
    write_template,
)

OLD_VERSION = "0.17.0"
NEW_VERSION = "0.18.0"


def _write_both_guides(
    module: object,
    repo_root: pathlib.Path,
    languages: tuple[str, ...],
    version: str,
) -> None:
    """Render and write root CLAUDE.md and AGENTS.md with managed sections."""
    template = build_template(version)
    for harness, filename in module.AGENT_HARNESS_GUIDE_FILENAMES.items():
        section = module.render(template, languages, version, harness)
        (repo_root / filename).write_text(
            module.upsert_managed_section("", section),
            encoding="utf-8",
        )


def test_scaffold_renders_only_enabled_language() -> None:
    module = load_update_spx_module()
    rendered = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE
    )
    assert f"### {LANG_PRIMARY.capitalize()}" in rendered
    assert f"### {LANG_SECONDARY.capitalize()}" not in rendered


def test_harness_block_renders_only_for_its_harness() -> None:
    module = load_update_spx_module()
    template = build_template(NEW_VERSION)
    claude = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE)
    codex = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CODEX)

    assert HARNESS_CLAUDE.upper() in claude
    assert HARNESS_CODEX.upper() not in claude
    assert HARNESS_CODEX.upper() in codex
    assert HARNESS_CLAUDE.upper() not in codex


def test_both_sections_share_body_and_differ_only_in_harness_spans() -> None:
    module = load_update_spx_module()
    template = build_template(NEW_VERSION)
    claude = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE)
    codex = module.render(template, (LANG_PRIMARY,), NEW_VERSION, HARNESS_CODEX)

    harness_lines = {harness_line(HARNESS_CLAUDE), harness_line(HARNESS_CODEX)}
    claude_shared = [line for line in claude.splitlines() if line not in harness_lines]
    codex_shared = [line for line in codex.splitlines() if line not in harness_lines]
    assert claude_shared == codex_shared
    assert claude != codex


def test_update_propagates_new_section_and_preserves_languages() -> None:
    module = load_update_spx_module()
    guide = module.upsert_managed_section(
        ROOT_GUIDE_SHARED_BODY,
        module.render(
            build_template(OLD_VERSION), (LANG_PRIMARY,), OLD_VERSION, HARNESS_CLAUDE
        ),
    )

    new_template = build_template(NEW_VERSION, extra_section=True)
    languages = module.parse_languages(guide)

    for harness in (HARNESS_CLAUDE, HARNESS_CODEX):
        updated = module.render(new_template, languages, NEW_VERSION, harness)
        assert f"## {NEW_SECTION}" in updated
        assert f"### {LANG_PRIMARY.capitalize()}" in updated
        assert f"### {LANG_SECONDARY.capitalize()}" not in updated


def test_cli_check_reports_absent_stale_and_current(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    base = ["--template", str(template), "--repo-root", str(tmp_path), "--check"]
    supplied = [*base, "--languages", LANG_PRIMARY]

    assert module.main(supplied) == 0
    assert capsys.readouterr().out.strip() == "absent"

    _write_both_guides(module, tmp_path, (LANG_PRIMARY,), OLD_VERSION)
    assert module.main(supplied) == 0
    assert capsys.readouterr().out.strip() == "stale"

    _write_both_guides(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    assert module.main(supplied) == 0
    assert capsys.readouterr().out.strip() == "current"


def test_cli_check_reports_language_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    _write_both_guides(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    base = ["--template", str(template), "--repo-root", str(tmp_path), "--check"]

    assert module.main([*base, "--languages", LANG_PRIMARY]) == 0
    assert capsys.readouterr().out.strip() == "current"

    assert module.main([*base, "--languages", f"{LANG_PRIMARY},{LANG_SECONDARY}"]) == 0
    assert capsys.readouterr().out.strip() == "stale"


def test_cli_check_treats_language_order_as_a_set(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    _write_both_guides(module, tmp_path, (LANG_SECONDARY, LANG_PRIMARY), NEW_VERSION)
    base = ["--template", str(template), "--repo-root", str(tmp_path), "--check"]

    assert module.main([*base, "--languages", f"{LANG_PRIMARY},{LANG_SECONDARY}"]) == 0
    assert capsys.readouterr().out.strip() == "current"


def test_cli_check_ignores_unmanaged_metadata_comments(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    unmanaged_metadata = (
        f"{ROOT_GUIDE_SHARED_BODY}\n"
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {NEW_VERSION} -->\n"
        f"{module.MANAGED_LANGUAGES_PREFIX} {LANG_PRIMARY} -->\n"
    )
    for guide_name in (GUIDE_CLAUDE, GUIDE_AGENTS):
        (tmp_path / guide_name).write_text(unmanaged_metadata, encoding="utf-8")

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


def test_cli_check_treats_markerless_legacy_guide_as_stale(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    legacy_guide = (
        f"{module.FRONTMATTER_DELIMITER}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{NEW_VERSION}"\n'
        f"{module.LANGUAGES_KEY}: [{LANG_PRIMARY}]\n"
        f"{module.FRONTMATTER_DELIMITER}\n"
        "\n# Legacy Spec Tree Guide\n"
    )
    for guide_name in (GUIDE_CLAUDE, GUIDE_AGENTS):
        (tmp_path / guide_name).write_text(legacy_guide, encoding="utf-8")

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


def test_cli_write_replaces_markerless_generated_guide_body(
    tmp_path: pathlib.Path,
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    legacy_guide = (
        f"{module.FRONTMATTER_DELIMITER}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{OLD_VERSION}"\n'
        f"{module.TEMPLATE_SOURCE_KEY}: {module.DEFAULT_TEMPLATE_SOURCE}\n"
        f"{module.LANGUAGES_KEY}: [{LANG_PRIMARY}]\n"
        f"{module.FRONTMATTER_DELIMITER}\n\n"
        "# spx/ Directory Guide (Spec Tree)\n\n"
        "Legacy generated guidance.\n"
    )
    for guide_name in (GUIDE_CLAUDE, GUIDE_AGENTS):
        (tmp_path / guide_name).write_text(legacy_guide, encoding="utf-8")

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

    for guide_name in (GUIDE_CLAUDE, GUIDE_AGENTS):
        guide = (tmp_path / guide_name).read_text(encoding="utf-8")
        assert guide.startswith(module.MANAGED_SECTION_START)
        assert "Legacy generated guidance." not in guide


def test_cli_check_uses_managed_metadata_not_root_prose_comments(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    unmanaged_metadata = (
        f"{ROOT_GUIDE_SHARED_BODY}\n"
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {OLD_VERSION} -->\n"
        f"{module.MANAGED_LANGUAGES_PREFIX} {LANG_SECONDARY} -->\n"
    )
    _write_both_guides(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    for guide_name in (GUIDE_CLAUDE, GUIDE_AGENTS):
        guide_path = tmp_path / guide_name
        guide_path.write_text(
            f"{unmanaged_metadata}\n{guide_path.read_text(encoding='utf-8')}",
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
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    misleading_frontmatter = (
        f"{module.FRONTMATTER_DELIMITER}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{OLD_VERSION}"\n'
        f"{module.LANGUAGES_KEY}: [{LANG_SECONDARY}]\n"
        f"{module.FRONTMATTER_DELIMITER}\n\n"
    )
    _write_both_guides(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    for guide_name in (GUIDE_CLAUDE, GUIDE_AGENTS):
        guide_path = tmp_path / guide_name
        guide_path.write_text(
            f"{misleading_frontmatter}{guide_path.read_text(encoding='utf-8')}",
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


def test_cli_check_reports_stale_from_detected_language_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    _write_both_guides(module, tmp_path, (LANG_PRIMARY,), NEW_VERSION)
    extensions = tuple(
        next(ext for ext, lang in module.LANGUAGE_BY_EXTENSION.items() if lang == want)
        for want in (LANG_PRIMARY, LANG_SECONDARY)
    )
    write_spx_tree_with_tests(tmp_path / "spx", extensions)

    assert (
        module.main(
            ["--template", str(template), "--repo-root", str(tmp_path), "--check"]
        )
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"


def test_cli_check_reports_absent_when_one_guide_is_missing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    claude_name = module.AGENT_HARNESS_GUIDE_FILENAMES[HARNESS_CLAUDE]
    section = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, HARNESS_CLAUDE
    )
    (tmp_path / claude_name).write_text(
        module.upsert_managed_section(ROOT_GUIDE_SHARED_BODY, section),
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
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert module.main(["--template", str(template), "--write"]) == 2


def test_cli_rejects_non_directory_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
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


def test_cli_rejects_root_guide_symlink_escaping_repo_root(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-guide.md"
    outside.write_text(ROOT_GUIDE_SHARED_BODY, encoding="utf-8")
    (tmp_path / GUIDE_CLAUDE).symlink_to(outside)

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


def test_cli_rejects_spx_symlink_during_language_detection(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
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


def test_cli_write_creates_both_root_guide_files(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
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
    for filename in module.AGENT_HARNESS_GUIDE_FILENAMES.values():
        guide = tmp_path / filename
        assert guide.is_file()
        content = guide.read_text(encoding="utf-8")
        assert module.MANAGED_SECTION_START in content
        assert f"### {LANG_PRIMARY.capitalize()}" in content
        assert content.endswith("\n")


def test_cli_write_preserves_root_content_outside_managed_section(
    tmp_path: pathlib.Path,
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    (tmp_path / GUIDE_AGENTS).write_text(ROOT_GUIDE_SHARED_BODY, encoding="utf-8")

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

    for filename in module.AGENT_HARNESS_GUIDE_FILENAMES.values():
        content = (tmp_path / filename).read_text(encoding="utf-8")
        assert ROOT_GUIDE_SHARED_BODY.rstrip("\n") in content
        assert content.count(module.MANAGED_SECTION_START) == 1


def test_cli_write_replaces_symlinked_root_guide_with_regular_file(
    tmp_path: pathlib.Path,
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    topology = root_guide_topology_symlinked()
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

    claude_path = tmp_path / GUIDE_CLAUDE
    agents_path = tmp_path / GUIDE_AGENTS
    assert claude_path.is_file()
    assert agents_path.is_file()
    assert not claude_path.is_symlink()
    assert not agents_path.is_symlink()
    assert ROOT_GUIDE_SHARED_BODY.rstrip("\n") in claude_path.read_text(
        encoding="utf-8"
    )
    assert ROOT_GUIDE_SHARED_BODY.rstrip("\n") in agents_path.read_text(
        encoding="utf-8"
    )


def test_cli_detects_languages_from_test_extensions(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
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
    content = (tmp_path / GUIDE_CLAUDE).read_text(encoding="utf-8")
    assert f"### {LANG_PRIMARY.capitalize()}" in content
    assert f"### {LANG_SECONDARY.capitalize()}" not in content


def test_is_stale_treats_a_malformed_version_as_stale() -> None:
    module = load_update_spx_module()
    assert module.is_stale("0.18.0-beta", NEW_VERSION) is True
    assert module.is_stale(OLD_VERSION, "not-a-version") is True
