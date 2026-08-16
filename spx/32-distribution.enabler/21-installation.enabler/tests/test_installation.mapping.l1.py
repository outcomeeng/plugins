"""Finite catalog-to-agent mapping evidence for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
)
from outcomeeng_testing.harnesses.installation import (
    observe_persistent_execution,
    observe_repository_plan,
    repository_root,
)
from outcomeeng_testing.generators.installation import generated_agent_subsets
from outcomeeng.distribution.installation import Agent


def test_each_mode_maps_its_selection_to_catalog_order() -> None:
    isolated = observe_repository_plan()
    selected = generated_agent_subsets(
        repository_root(),
        include_spec_tree=True,
    )
    persistent = observe_persistent_execution(selected)
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
    assert persistent.report.plan.claude_plugins == tuple(
        plugin for plugin in expected_claude if plugin in selected[Agent.CLAUDE]
    )
    assert persistent.report.plan.codex_plugins == tuple(
        plugin for plugin in expected_codex if plugin in selected[Agent.CODEX]
    )
