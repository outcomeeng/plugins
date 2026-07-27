"""Catalog conformance evidence for repository installation."""

from outcomeeng_testing.harnesses.installation import observe_repository_plan


def test_plan_uses_each_catalogs_complete_ordered_plugin_set() -> None:
    observation = observe_repository_plan()

    assert observation.plan.claude_plugins == observation.claude_catalog_names
    assert observation.plan.codex_plugins == observation.codex_catalog_names
