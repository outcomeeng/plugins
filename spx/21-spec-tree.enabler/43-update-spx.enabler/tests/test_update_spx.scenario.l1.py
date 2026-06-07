"""Scenario evidence for the update-spx render helper.

Covers the existential scenarios in ``update-spx.md``: a scaffold renders the
template with the product name substituted and only the enabled language's block,
and an update re-renders a newer template with the guide's existing config so a
newly introduced section propagates while the product name and language selection
persist.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng_testing.harnesses.update_spx import (
    LANG_PRIMARY,
    LANG_SECONDARY,
    NEW_SECTION,
    PRODUCT_NAME,
    build_template,
    load_update_spx_module,
    write_pre_schema_guide,
    write_template,
)

OLD_VERSION = "0.17.0"
NEW_VERSION = "0.18.0"


def test_scaffold_renders_name_and_only_enabled_language() -> None:
    module = load_update_spx_module()
    template = build_template(NEW_VERSION)
    config = module.GuideConfig(product_name=PRODUCT_NAME, languages=(LANG_PRIMARY,))
    rendered = module.render(template, config, NEW_VERSION)
    assert PRODUCT_NAME in rendered
    assert module.PRODUCT_NAME_PLACEHOLDER not in rendered
    assert f"### {LANG_PRIMARY.capitalize()}" in rendered
    assert f"### {LANG_SECONDARY.capitalize()}" not in rendered


def test_update_propagates_new_section_and_preserves_config() -> None:
    module = load_update_spx_module()
    config = module.GuideConfig(product_name=PRODUCT_NAME, languages=(LANG_PRIMARY,))
    guide = module.render(build_template(OLD_VERSION), config, OLD_VERSION)

    new_template = build_template(NEW_VERSION, extra_section=True)
    updated = module.render(new_template, module.parse_config(guide), NEW_VERSION)

    assert f"## {NEW_SECTION}" in updated
    assert PRODUCT_NAME in updated
    assert f"### {LANG_PRIMARY.capitalize()}" in updated
    assert f"### {LANG_SECONDARY.capitalize()}" not in updated


def test_cli_check_reports_absent_stale_and_current(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    config = module.GuideConfig(product_name=PRODUCT_NAME, languages=(LANG_PRIMARY,))

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
        module.render(build_template(NEW_VERSION), config, OLD_VERSION),
        encoding="utf-8",
    )
    assert (
        module.main(["--template", str(template), "--product", str(guide), "--check"])
        == 0
    )
    assert capsys.readouterr().out.strip() == "stale"

    guide.write_text(
        module.render(build_template(NEW_VERSION), config, NEW_VERSION),
        encoding="utf-8",
    )
    assert (
        module.main(["--template", str(template), "--product", str(guide), "--check"])
        == 0
    )
    assert capsys.readouterr().out.strip() == "current"


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
            "--name",
            PRODUCT_NAME,
            "--languages",
            LANG_PRIMARY,
            "--write",
        ]
    )
    assert exit_code == 0
    assert guide.is_file()
    content = guide.read_text(encoding="utf-8")
    assert PRODUCT_NAME in content
    assert content.endswith("\n")


def test_cli_update_of_pre_schema_guide_requires_name(tmp_path: pathlib.Path) -> None:
    module = load_update_spx_module()
    template = write_template(tmp_path, NEW_VERSION)
    guide = write_pre_schema_guide(tmp_path, OLD_VERSION, PRODUCT_NAME)

    # A guide predating the config schema holds the name in its body; updating without
    # a supplied name must refuse rather than silently discard it.
    assert (
        module.main(["--template", str(template), "--product", str(guide), "--write"])
        == 2
    )

    # With a supplied name and languages, the update migrates the guide.
    exit_code = module.main(
        [
            "--template",
            str(template),
            "--product",
            str(guide),
            "--name",
            PRODUCT_NAME,
            "--languages",
            LANG_PRIMARY,
            "--write",
        ]
    )
    assert exit_code == 0
    content = guide.read_text(encoding="utf-8")
    assert PRODUCT_NAME in content
    assert f"### {LANG_PRIMARY.capitalize()}" in content


def test_is_stale_treats_a_malformed_version_as_stale() -> None:
    module = load_update_spx_module()
    # A non-numeric version segment must not crash the comparison.
    assert module.is_stale("0.18.0-beta", NEW_VERSION) is True
    assert module.is_stale(OLD_VERSION, "not-a-version") is True
