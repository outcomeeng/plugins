"""Real-agent end-to-end evidence for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
)
from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_real_agent_clis_install_every_catalog_plugin_idempotently() -> None:
    observation = observe_real_installation()
    claude_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(observation.claude_catalog)
    )
    codex_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(observation.codex_catalog)
    )

    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert (
        observation.claude_registration_target == observation.codex_registration_target
    )
    assert observation.claude_registration_target.endswith("/checkout")
    state_root = observation.state_roots[0].parent
    assert all(root.is_relative_to(state_root) for root in observation.state_roots)
    assert observation.claude_plugins_first == frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in claude_catalog[CATALOG_PLUGINS_FIELD]
    )
    assert observation.claude_plugins_second == frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in claude_catalog[CATALOG_PLUGINS_FIELD]
    )
    assert observation.codex_plugins_first == frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in codex_catalog[CATALOG_PLUGINS_FIELD]
    )
    assert observation.codex_plugins_second == frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in codex_catalog[CATALOG_PLUGINS_FIELD]
    )
    assert observation.placed_first != observation.placed_initial
    changed_names = {
        name for name, _content in observation.placed_first
    } - {name for name, _content in observation.placed_initial}
    assert changed_names
    assert all(
        any(name.startswith(prefix) for prefix in observation.ownership_prefixes)
        for name in changed_names
    )
    assert observation.placed_first == observation.placed_second
    assert observation.unowned_first == observation.unowned_initial
    assert observation.unowned_second == observation.unowned_initial
