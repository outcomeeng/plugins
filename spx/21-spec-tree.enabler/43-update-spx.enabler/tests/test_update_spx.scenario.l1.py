"""Scenario evidence for the update-spx render helper.

Covers the existential scenarios in ``update-spx.md``: a scaffold renders the
template with the product name substituted and only the enabled language's block,
and an update re-renders a newer template with the guide's existing config so a
newly introduced section propagates while the product name and language selection
persist.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.update_spx import (
    LANG_PRIMARY,
    LANG_SECONDARY,
    NEW_SECTION,
    PRODUCT_NAME,
    build_template,
    load_update_spx_module,
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
