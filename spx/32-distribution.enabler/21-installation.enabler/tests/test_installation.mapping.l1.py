"""Finite catalog-to-agent mapping evidence for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    Agent,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    SPEC_TREE_PLUGIN,
)
from outcomeeng_testing.generators.installation import (
    generated_persistent_catalog_selections,
)
from outcomeeng_testing.harnesses.installation import (
    observe_persistent_catalog_subset_plans,
    observe_repository_plan,
)


def test_each_mode_maps_its_selection_to_catalog_order() -> None:
    isolated = observe_repository_plan()
    claude_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(isolated.claude_catalog)
    )
    codex_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(isolated.codex_catalog)
    )
    expected_claude = tuple(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in claude_catalog[CATALOG_PLUGINS_FIELD]
    )
    expected_codex = tuple(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in codex_catalog[CATALOG_PLUGINS_FIELD]
    )

    assert isolated.plan.claude_plugins == expected_claude
    assert isolated.plan.codex_plugins == expected_codex
    observations = observe_persistent_catalog_subset_plans()
    assert tuple(observation.agent for observation in observations) == tuple(Agent)
    for observation in observations:
        assert tuple(mapping.selected for mapping in observation.mappings) == (
            generated_persistent_catalog_selections(observation.catalog)
        )
        for mapping in observation.mappings:
            assert mapping.planned == (
                (SPEC_TREE_PLUGIN,)
                if not mapping.selected
                else tuple(
                    plugin
                    for plugin in observation.catalog
                    if plugin in mapping.selected
                )
            )
            assert mapping.installs == mapping.planned
            assert mapping.enables == (
                mapping.planned if observation.agent is Agent.CLAUDE else ()
            )
