"""Scenario evidence for the update-spx render helper.

Covers the existential scenarios in ``update-spx.md``: a scaffold renders only the
enabled language's block; an update re-renders a newer template with the guide's
recorded languages so a new section propagates while the language selection persists;
the CLI edge reports staleness and writes the guide; and a malformed version is treated
as stale rather than crashing.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.update_spx import (
    LANG_PRIMARY,
    LANG_SECONDARY,
    NEW_SECTION,
    build_template,
    load_update_spx_module,
    write_guide_without_languages,
    write_template,
)

OLD_VERSION = "0.17.0"
NEW_VERSION = "0.18.0"


def test_scaffold_renders_only_enabled_language() -> None:
    module = load_update_spx_module()
    rendered = module.render(build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION)
    assert f"### {LANG_PRIMARY.capitalize()}" in rendered
    assert f"### {LANG_SECONDARY.capitalize()}" not in rendered


def test_update_propagates_new_section_and_preserves_languages() -> None:
    module = load_update_spx_module()
    guide = module.render(build_template(OLD_VERSION), (LANG_PRIMARY,), OLD_VERSION)

    new_template = build_template(NEW_VERSION, extra_section=True)
    updated = module.render(new_template, module.parse_languages(guide), NEW_VERSION)

    assert f"## {NEW_SECTION}" in updated
    assert f"### {LANG_PRIMARY.capitalize()}" in updated
    assert f"### {LANG_SECONDARY.capitalize()}" not in updated


def test_cli_check_reports_absent_stale_and_current(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)

    absent = [
        "--template",
        str(template),
        "--product",
        str(tmp_path / "absent.md"),
        "--check",
    ]
    assert module.main(absent) == 0
    assert capsys.readouterr().out.strip() == "absent"

    guide = tmp_path / "CLAUDE.md"
    guide.write_text(
        module.render(build_template(NEW_VERSION), (LANG_PRIMARY,), OLD_VERSION),
        encoding="utf-8",
    )
    assert (
        module.main(["--template", str(template), "--product", str(guide), "--check"])
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"

    guide.write_text(
        module.render(build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION),
        encoding="utf-8",
    )
    assert (
        module.main(["--template", str(template), "--product", str(guide), "--check"])
        == 0
    )
    assert capsys.readouterr().out.strip() == "current"


def test_cli_check_reports_language_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    guide = tmp_path / "CLAUDE.md"
    guide.write_text(
        module.render(build_template(NEW_VERSION), (LANG_PRIMARY,), NEW_VERSION),
        encoding="utf-8",
    )
    base = ["--template", str(template), "--product", str(guide), "--check"]

    # Supplied languages match the recorded set on a version-current guide -> current.
    assert module.main([*base, "--languages", LANG_PRIMARY]) == 0
    assert capsys.readouterr().out.strip() == "current"

    # Supplied languages differ from the recorded set -> stale, despite the version match.
    assert module.main([*base, "--languages", f"{LANG_PRIMARY},{LANG_SECONDARY}"]) == 0
    assert capsys.readouterr().out.strip() == "stale"


def test_cli_write_without_product_exits_2(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    assert module.main(["--template", str(template), "--write"]) == 2


def test_cli_write_creates_guide(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    guide = tmp_path / "CLAUDE.md"
    exit_code = module.main(
        [
            "--template",
            str(template),
            "--product",
            str(guide),
            "--languages",
            LANG_PRIMARY,
            "--write",
        ]
    )
    assert exit_code == 0
    assert guide.is_file()
    content = guide.read_text(encoding="utf-8")
    assert f"### {LANG_PRIMARY.capitalize()}" in content
    assert content.endswith("\n")


def test_cli_update_without_recorded_languages_requires_languages(
    tmp_path: pathlib.Path,
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    guide = write_guide_without_languages(tmp_path, OLD_VERSION)

    # A guide with no `languages` key must refuse rather than silently render empty.
    assert (
        module.main(["--template", str(template), "--product", str(guide), "--write"])
        == 2
    )

    # With a supplied language set, the update renders the enabled language.
    exit_code = module.main(
        [
            "--template",
            str(template),
            "--product",
            str(guide),
            "--languages",
            LANG_PRIMARY,
            "--write",
        ]
    )
    assert exit_code == 0
    assert f"### {LANG_PRIMARY.capitalize()}" in guide.read_text(encoding="utf-8")


def test_is_stale_treats_a_malformed_version_as_stale() -> None:
    module = load_update_spx_module()
    # A non-numeric version segment must not crash the comparison.
    assert module.is_stale("0.18.0-beta", NEW_VERSION) is True
    assert module.is_stale(OLD_VERSION, "not-a-version") is True
