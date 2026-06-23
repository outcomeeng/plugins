"""Scenario evidence for the update-spx two-file guide generator.

Covers the existential scenarios in ``update-spx.md``: a scaffold renders only the
enabled language's block and only its own runtime's blocks; the two output files share
their body and differ only in the runtime spans; an update re-renders a newer template so
a new section propagates while the language selection persists; the CLI edge writes both
guide files, detects languages from ``spx/**/tests/`` extensions, and reports staleness;
and a malformed version is treated as stale rather than crashing.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.update_spx import (
    LANG_PRIMARY,
    LANG_SECONDARY,
    NEW_SECTION,
    RUNTIME_CLAUDE,
    RUNTIME_CODEX,
    build_template,
    load_update_spx_module,
    write_spx_tree_with_tests,
    write_template,
)

OLD_VERSION = "0.17.0"
NEW_VERSION = "0.18.0"


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


def test_both_files_share_body_and_differ_only_in_runtime_spans() -> None:
    module = load_update_spx_module()
    template = build_template(NEW_VERSION)
    claude = module.render(template, (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CLAUDE)
    codex = module.render(template, (LANG_PRIMARY,), NEW_VERSION, RUNTIME_CODEX)

    # The shared body — every line that is not a runtime-only span — is identical.
    runtime_lines = {f"{RUNTIME_CLAUDE.upper()} runs the audit as a subagent."}
    runtime_lines.add(f"{RUNTIME_CODEX.upper()} runs the audit as a subagent.")
    claude_shared = [line for line in claude.splitlines() if line not in runtime_lines]
    codex_shared = [line for line in codex.splitlines() if line not in runtime_lines]
    assert claude_shared == codex_shared
    assert claude != codex


def test_update_propagates_new_section_and_preserves_languages() -> None:
    module = load_update_spx_module()
    guide = module.render(
        build_template(OLD_VERSION), (LANG_PRIMARY,), OLD_VERSION, RUNTIME_CLAUDE
    )

    new_template = build_template(NEW_VERSION, extra_section=True)
    updated = module.render(
        new_template, module.parse_languages(guide), NEW_VERSION, RUNTIME_CLAUDE
    )

    assert f"## {NEW_SECTION}" in updated
    assert f"### {LANG_PRIMARY.capitalize()}" in updated
    assert f"### {LANG_SECONDARY.capitalize()}" not in updated


def _write_both_guides(
    module: object, spx_dir: pathlib.Path, languages: tuple[str, ...], version: str
) -> None:
    """Render and write CLAUDE.md and AGENTS.md at ``version`` for the given languages."""
    for runtime, filename in module.RUNTIME_GUIDE_FILENAMES.items():
        (spx_dir / filename).write_text(
            module.render(build_template(version), languages, version, runtime),
            encoding="utf-8",
        )


def test_cli_check_reports_absent_stale_and_current(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    base = ["--template", str(template), "--spx-dir", str(tmp_path), "--check"]
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
    base = ["--template", str(template), "--spx-dir", str(tmp_path), "--check"]

    assert module.main([*base, "--languages", LANG_PRIMARY]) == 0
    assert capsys.readouterr().out.strip() == "current"

    assert module.main([*base, "--languages", f"{LANG_PRIMARY},{LANG_SECONDARY}"]) == 0
    assert capsys.readouterr().out.strip() == "stale"


def test_cli_write_without_spx_dir_exits_2(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert module.main(["--template", str(template), "--write"]) == 2


def test_cli_write_creates_both_guide_files(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    exit_code = module.main(
        [
            "--template",
            str(template),
            "--spx-dir",
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
        assert f"### {LANG_PRIMARY.capitalize()}" in content
        assert content.endswith("\n")


def test_cli_detects_languages_from_test_extensions(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    # The product's only test files are Python, so detection enables python alone.
    # The extension is source-derived from the module's extension->language mapping.
    py_ext = next(
        ext for ext, lang in module.LANGUAGE_BY_EXTENSION.items() if lang == LANG_PRIMARY
    )
    write_spx_tree_with_tests(tmp_path, (py_ext,))
    exit_code = module.main(
        ["--template", str(template), "--spx-dir", str(tmp_path), "--write"]
    )
    assert exit_code == 0
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert f"### {LANG_PRIMARY.capitalize()}" in content
    assert f"### {LANG_SECONDARY.capitalize()}" not in content


def test_is_stale_treats_a_malformed_version_as_stale() -> None:
    module = load_update_spx_module()
    assert module.is_stale("0.18.0-beta", NEW_VERSION) is True
    assert module.is_stale(OLD_VERSION, "not-a-version") is True
