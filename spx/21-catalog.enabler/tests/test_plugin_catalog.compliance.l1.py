"""Compliance evidence for plugin catalog generation."""

from __future__ import annotations

from outcomeeng.catalog.plugin_catalog import (
    BEGIN_SENTINEL,
    CATALOG_AGENT_KIND,
    CATALOG_DRIFT_EXIT_CODE,
    CATALOG_SUCCESS_EXIT_CODE,
    CATALOG_SKILL_KIND,
    LIFECYCLE_SKILL_DESCRIPTION_PREFIX,
    END_SENTINEL,
    PLUGIN_LIFECYCLE_SKILL_NAME_PATTERN,
)
from outcomeeng_testing.harnesses.plugin_catalog import (
    observe_catalog_frontmatter_include_purpose,
    observe_catalog_splice_with_non_sentinel_markers,
    observe_check_mode_with_drift,
    observe_generated_catalog,
    observe_generated_catalog_sentinels,
    observe_purpose_shortening_with_em_dash,
    observe_repository_catalog_inventory,
    observe_runtime_divergent_skill_purpose,
)


def test_generated_catalog_is_deterministic() -> None:
    observation = observe_generated_catalog()

    assert observation.first_render == observation.second_render
    assert observation.entry_kinds == {CATALOG_SKILL_KIND, CATALOG_AGENT_KIND}


def test_generated_catalog_uses_declared_sentinels() -> None:
    observation = observe_generated_catalog_sentinels()

    assert observation.catalog.startswith(f"{BEGIN_SENTINEL}\n\n")
    assert observation.catalog.endswith(f"{END_SENTINEL}\n")


def test_catalog_splice_ignores_non_sentinel_markers() -> None:
    observation = observe_catalog_splice_with_non_sentinel_markers()

    assert observation.spliced_readme.startswith(observation.ignored_prefix)
    assert observation.stale_catalog_body not in observation.spliced_readme
    assert observation.catalog in observation.spliced_readme


def test_check_mode_fails_when_readme_catalog_drifts() -> None:
    observation = observe_check_mode_with_drift()

    assert observation.exit_code != CATALOG_SUCCESS_EXIT_CODE
    assert observation.exit_code == CATALOG_DRIFT_EXIT_CODE


def test_every_marketplace_plugin_catalogs_its_lifecycle_skill() -> None:
    observation = observe_repository_catalog_inventory()

    assert observation.skill_entries_by_plugin
    assert all(
        f"`/{PLUGIN_LIFECYCLE_SKILL_NAME_PATTERN.format(plugin_name=plugin_name)}`"
        in {entry_name for entry_name, _ in skill_entries}
        for plugin_name, skill_entries in observation.skill_entries_by_plugin
    )
    assert all(
        not purpose.startswith(LIFECYCLE_SKILL_DESCRIPTION_PREFIX)
        for plugin_name, skill_entries in observation.skill_entries_by_plugin
        for entry_name, purpose in skill_entries
        if entry_name
        == f"`/{PLUGIN_LIFECYCLE_SKILL_NAME_PATTERN.format(plugin_name=plugin_name)}`"
    )


def test_runtime_divergent_skill_descriptions_name_each_target() -> None:
    observation = observe_runtime_divergent_skill_purpose()

    assert all(
        f"{target_label}: {purpose}" in observation.actual
        for target_label, purpose in observation.target_purposes
    )


def test_catalog_frontmatter_includes_use_shared_root() -> None:
    observation = observe_catalog_frontmatter_include_purpose()

    assert all(
        f"{target_label}: {purpose}" in observation.actual
        for target_label, purpose in observation.target_purposes
    )


def test_purpose_shortening_preserves_untrimmed_em_dash() -> None:
    observation = observe_purpose_shortening_with_em_dash()

    assert observation.shortened == observation.source
