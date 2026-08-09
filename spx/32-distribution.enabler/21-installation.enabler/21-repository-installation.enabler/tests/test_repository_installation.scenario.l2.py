"""Real-agent end-to-end evidence for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    SourceAction,
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
    claude_plugins = frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in claude_catalog[CATALOG_PLUGINS_FIELD]
    )
    codex_plugins = frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in codex_catalog[CATALOG_PLUGINS_FIELD]
    )

    persistent_report = cast(
        dict[str, list[str]], json.loads(observation.persistent_stdout)
    )
    pending = frozenset(persistent_report["pending_publication"])

    assert observation.persistent_exit_code == 0, observation.persistent_stderr
    assert pending <= claude_plugins | codex_plugins
    assert observation.persistent_claude_plugins.installed == claude_plugins - pending
    assert (
        observation.persistent_claude_plugins.enabled
        == observation.persistent_selection - pending
    )
    assert observation.persistent_selection < claude_plugins
    assert (
        observation.persistent_settings_after == observation.persistent_settings_before
    )
    assert observation.persistent_codex_plugins.installed == codex_plugins - pending
    assert observation.persistent_claude_source_action is SourceAction.REFRESH
    assert observation.persistent_codex_source_action is SourceAction.REFRESH
    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert (
        observation.claude_registration_target == observation.codex_registration_target
    )
    assert observation.claude_registration_target == str(
        observation.invocation_checkout
    )
    state_root = observation.state_roots[0].parent
    assert all(root.is_relative_to(state_root) for root in observation.state_roots)
    assert observation.claude_plugins_first.installed == claude_plugins
    assert observation.claude_plugins_first.enabled == claude_plugins
    assert observation.claude_plugins_second == observation.claude_plugins_first
    assert observation.codex_plugins_first.installed == codex_plugins
    assert observation.codex_plugins_first.enabled == codex_plugins
    assert observation.codex_plugins_second == observation.codex_plugins_first
    assert set(observation.placed_first) == (
        set(observation.placed_initial) | set(observation.shipped_agents)
    )
    assert observation.placed_first == observation.placed_second
    assert observation.unowned_first == observation.unowned_initial
    assert observation.unowned_second == observation.unowned_initial
