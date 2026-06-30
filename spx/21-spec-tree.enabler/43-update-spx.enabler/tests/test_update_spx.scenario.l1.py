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
    RUNTIME_CLAUDE,
    RUNTIME_CODEX,
    ROOT_GUIDE_SHARED_BODY,
    build_template,
    load_update_spx_module,
    root_guide_topology_symlinked,
    runtime_line,
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
    for runtime, filename in module.RUNTIME_GUIDE_FILENAMES.items():
        section = module.render(template, languages, version, runtime)
        (repo_root / filename).write_text(
            module.upsert_managed_section("", section),
            encoding="utf-8",
        )


def test_scaffold_renders_only_enabled_language() -> None:
    module = load_update_spx_module()
    rendered = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CLAUDE
    )
    assert f"### {LANG_PRIMARY.capitalize()}" in rendered
    assert f"### {LANG_SECONDARY.capitalize()}" not in rendered


def test_runtime_block_renders_only_for_its_runtime() -> None:
    module = load_update_spx_module()
    template = build_template(NEW_VERSION)
    claude = module.render(template, (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CLAUDE)
    codex = module.render(template, (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CODEX)

    assert RUNTIME_CLAUDE.upper() in claude
    assert RUNTIME_CODEX.upper() not in claude
    assert RUNTIME_CODEX.upper() in codex
    assert RUNTIME_CLAUDE.upper() not in codex


def test_both_sections_share_body_and_differ_only_in_runtime_spans() -> None:
    module = load_update_spx_module()
    template = build_template(NEW_VERSION)
    claude = module.render(template, (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CLAUDE)
    codex = module.render(template, (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CODEX)

    runtime_lines = {runtime_line(RUNTIME_CLAUDE), runtime_line(RUNTIME_CODEX)}
    claude_shared = [line for line in claude.splitlines() if line not in runtime_lines]
    codex_shared = [line for line in codex.splitlines() if line not in runtime_lines]
    assert claude_shared == codex_shared
    assert claude != codex


def test_update_propagates_new_section_and_preserves_languages() -> None:
    module = load_update_spx_module()
    guide = module.upsert_managed_section(
        ROOT_GUIDE_SHARED_BODY,
        module.render(
            build_template(OLD_VERSION), (LANG_PRIMARY,), OLD_VERSION, RUNTIME_CLAUDE
        ),
    )

    new_template = build_template(NEW_VERSION, extra_section=True)
    languages = module.parse_languages(guide)

    for runtime in (RUNTIME_CLAUDE, RUNTIME_CODEX):
        updated = module.render(new_template, languages, NEW_VERSION, runtime)
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
    claude_name = module.RUNTIME_GUIDE_FILENAMES[RUNTIME_CLAUDE]
    section = module.render(
        build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CLAUDE
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
    for filename in module.RUNTIME_GUIDE_FILENAMES.values():
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

    for filename in module.RUNTIME_GUIDE_FILENAMES.values():
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


def test_cli_write_removes_obsolete_spx_guides(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    spx_dir = tmp_path / "spx"
    spx_dir.mkdir()
    (spx_dir / GUIDE_CLAUDE).write_text("old claude guide\n", encoding="utf-8")
    (spx_dir / GUIDE_AGENTS).write_text("old agents guide\n", encoding="utf-8")

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

    assert not (spx_dir / GUIDE_CLAUDE).exists()
    assert not (spx_dir / GUIDE_AGENTS).exists()


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
