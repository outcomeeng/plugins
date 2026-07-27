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
)


def test_each_mode_uses_each_catalogs_complete_ordered_plugin_set() -> None:
    isolated = observe_repository_plan()
    persistent = observe_persistent_execution()
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
    assert persistent.report.plan.claude_plugins == expected_claude
    assert persistent.report.plan.codex_plugins == expected_codex
