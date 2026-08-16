"""Network-backed real-agent mappings for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    Agent,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    SourceAction,
)
from outcomeeng_testing.harnesses.installation import (
    canonical_catalog_plugin_names,
    observe_real_installation,
)


def test_real_agent_clis_map_full_and_generated_subsets() -> None:
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
        dict[str, list[dict[str, str]]], json.loads(observation.persistent_stdout)
    )
    pending_entries = persistent_report["pending_publication"]
    claude_pending = frozenset(
        entry["plugin"]
        for entry in pending_entries
        if entry["agent"] == Agent.CLAUDE.value
    )
    codex_pending = frozenset(
        entry["plugin"]
        for entry in pending_entries
        if entry["agent"] == Agent.CODEX.value
    )
    published = canonical_catalog_plugin_names()
    subset_claude_catalog = cast(
        dict[str, list[dict[str, object]]],
        json.loads(observation.subset_claude_catalog),
    )
    subset_codex_catalog = cast(
        dict[str, list[dict[str, object]]],
        json.loads(observation.subset_codex_catalog),
    )
    subset_claude_plugins = frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in subset_claude_catalog[CATALOG_PLUGINS_FIELD]
    )
    subset_codex_plugins = frozenset(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in subset_codex_catalog[CATALOG_PLUGINS_FIELD]
    )

    assert observation.persistent_exit_code == 0, observation.persistent_stderr
    assert (
        claude_pending | codex_pending
        == (
            observation.persistent_claude_selected
            | observation.persistent_codex_selected
        )
        - published
    )
    assert observation.persistent_claude_plugins.installed == (
        observation.persistent_claude_selected - claude_pending
    )
    assert (
        observation.persistent_claude_plugins.enabled
        == (observation.persistent_selection & observation.persistent_claude_selected)
        - claude_pending
    )
    assert observation.persistent_codex_plugins.installed == (
        observation.persistent_codex_selected - codex_pending
    )
    assert not observation.persistent_claude_plugins.installed & (
        claude_plugins - observation.persistent_claude_selected
    )
    assert not observation.persistent_codex_plugins.installed & (
        codex_plugins - observation.persistent_codex_selected
    )
    assert (
        observation.persistent_settings_after == observation.persistent_settings_before
    )
    assert observation.persistent_claude_source_action is SourceAction.REFRESH
    assert observation.persistent_codex_source_action is SourceAction.REFRESH
    assert observation.claude_plugins_first.installed == claude_plugins
    assert observation.claude_plugins_first.enabled == claude_plugins
    assert observation.codex_plugins_first.installed == codex_plugins
    assert observation.codex_plugins_first.enabled == codex_plugins
    assert observation.claude_registration_target == str(
        observation.invocation_checkout
    )
    assert observation.codex_registration_target == str(observation.invocation_checkout)
    assert observation.subset_exit_code == 0, observation.subset_stderr
    assert observation.subset_claude_plugins.installed == subset_claude_plugins
    assert observation.subset_claude_plugins.enabled == subset_claude_plugins
    assert observation.subset_codex_plugins.installed == subset_codex_plugins
    assert observation.subset_codex_plugins.enabled == subset_codex_plugins
    assert observation.subset_claude_registration_target == str(
        observation.subset_invocation_checkout
    )
    assert observation.subset_codex_registration_target == str(
        observation.subset_invocation_checkout
    )
    assert all(
        root.is_relative_to(observation.invocation_checkout.parent)
        for root in observation.state_roots
    )
