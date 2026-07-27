"""Catalog conformance evidence for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
)
from outcomeeng_testing.harnesses.installation import observe_repository_plan


def test_plan_uses_each_catalogs_complete_ordered_plugin_set() -> None:
    observation = observe_repository_plan()
    claude_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(observation.claude_catalog)
    )
    codex_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(observation.codex_catalog)
    )

    assert observation.plan.claude_plugins == tuple(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in claude_catalog[CATALOG_PLUGINS_FIELD]
    )
    assert observation.plan.codex_plugins == tuple(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in codex_catalog[CATALOG_PLUGINS_FIELD]
    )
