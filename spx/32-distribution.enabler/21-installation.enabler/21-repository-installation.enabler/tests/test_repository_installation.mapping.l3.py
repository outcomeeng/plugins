"""Network-backed real-agent mappings for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    PLUGIN_OPERATIONS,
    ReportField,
)
from outcomeeng_testing.generators.installation import (
    catalog_plugin_names_from_bytes,
)
from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_real_agent_clis_map_full_and_generated_subsets() -> None:
    observation = observe_real_installation()
    claude_plugins = frozenset(
        catalog_plugin_names_from_bytes(observation.claude_catalog)
    )
    codex_plugins = frozenset(
        catalog_plugin_names_from_bytes(observation.codex_catalog)
    )
    persistent_report = cast(
        dict[str, object], json.loads(observation.persistent_stdout)
    )
    pending_entries = cast(
        list[dict[str, str]], persistent_report[ReportField.PENDING_PUBLICATION]
    )
    subset_claude_plugins = frozenset(
        catalog_plugin_names_from_bytes(observation.subset_claude_catalog)
    )
    subset_codex_plugins = frozenset(
        catalog_plugin_names_from_bytes(observation.subset_codex_catalog)
    )

    commands = cast(list[dict[str, str]], persistent_report[ReportField.COMMANDS])
    selected_by_agent = {
        Target.CLAUDE: observation.persistent_claude_selected,
        Target.CODEX: observation.persistent_codex_selected,
    }

    assert observation.persistent_exit_code == 0, observation.persistent_stderr
    for agent, selected in selected_by_agent.items():
        refreshed = frozenset(
            command[ReportField.PLUGIN]
            for command in commands
            if command[ReportField.AGENT] == agent.value
            and command[ReportField.OPERATION]
            in {operation.value for operation in PLUGIN_OPERATIONS}
        )
        assert refreshed == selected, agent
    assert persistent_report[ReportField.COMPLETED_OPERATIONS] >= len(commands)
    assert pending_entries == [], pending_entries
    assert (
        observation.persistent_claude_plugins.installed
        == observation.persistent_claude_selected
    )
    assert observation.persistent_claude_plugins.enabled == (
        observation.persistent_selection & observation.persistent_claude_selected
    )
    assert (
        observation.persistent_codex_plugins.installed
        == observation.persistent_codex_selected
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
    assert observation.persistent_claude_registered
    assert observation.persistent_codex_registered
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
    assert observation.state_roots
    assert all(
        root.is_relative_to(observation.invocation_checkout.parent)
        for root in observation.state_roots
    )
