"""Network-backed real-agent scenarios for repository installation."""

import json

import pytest

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_LOCAL_SCOPE,
    CLAUDE_PROJECT_SCOPE,
    ClaudeInstallRecord,
    FIRST_INSTALL_WARNING,
    ReportField,
    SPEC_TREE_PLUGIN,
)
from outcomeeng_testing.harnesses.installation import (
    observe_codex_subagent_discovery,
    observe_real_first_install,
    observe_real_installation,
    observe_real_record_refresh,
)


def test_real_agent_clis_bootstrap_empty_persistent_state() -> None:
    observation = observe_real_first_install()

    assert observation.initial_state == ()
    assert observation.initial_project_settings is not None
    assert observation.exit_code == 0, observation.stderr
    document = json.loads(observation.stdout)
    assert document[ReportField.CLAUDE_PLUGINS] == [SPEC_TREE_PLUGIN]
    assert document[ReportField.CODEX_PLUGINS] == [SPEC_TREE_PLUGIN]
    assert document[ReportField.WARNINGS] == [
        {
            ReportField.AGENT: agent.value,
            ReportField.MESSAGE: FIRST_INSTALL_WARNING.format(agent=agent.value),
        }
        for agent in Agent
    ]
    assert observation.stderr.splitlines() == [
        f"warning: {FIRST_INSTALL_WARNING.format(agent=agent.value)}" for agent in Agent
    ]
    assert observation.claude_listing_exit_code == 0, observation.claude_listing_stderr
    assert observation.codex_listing_exit_code == 0, observation.codex_listing_stderr
    assert observation.claude_plugins is not None
    assert observation.codex_plugins is not None
    assert observation.claude_plugins.installed == {SPEC_TREE_PLUGIN}
    assert observation.claude_plugins.enabled == {SPEC_TREE_PLUGIN}
    assert observation.codex_plugins.installed == {SPEC_TREE_PLUGIN}
    assert observation.codex_plugins.enabled == {SPEC_TREE_PLUGIN}


def test_real_agent_clis_place_home_agents_and_repeat_full_installation() -> None:
    observation = observe_real_installation()
    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert observation.claude_plugins_second == observation.claude_plugins_first
    assert observation.codex_plugins_second == observation.codex_plugins_first
    assert set(observation.placed_first) == (
        set(observation.placed_initial) | set(observation.shipped_agents)
    )
    assert observation.placed_first == observation.placed_second
    assert observation.unowned_first == observation.unowned_initial
    assert observation.unowned_second == observation.unowned_initial


def test_real_persistent_run_refreshes_a_second_checkout_at_local_scope() -> None:
    observation = observe_real_record_refresh()

    expected = {
        (SPEC_TREE_PLUGIN, CLAUDE_PROJECT_SCOPE, observation.invocation_checkout),
        (SPEC_TREE_PLUGIN, CLAUDE_LOCAL_SCOPE, observation.other_checkout),
    }
    recorded_before = {
        (record.plugin, record.scope, record.project_path)
        for record in observation.records_before
        if isinstance(record, ClaudeInstallRecord)
    }
    assert expected <= recorded_before
    assert observation.exit_code == 0, observation.stderr
    document = json.loads(observation.stdout)
    refreshed = {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            record[ReportField.PROJECT_PATH],
        )
        for record in document[ReportField.CLAUDE_RECORDS]
    }
    assert {(plugin, scope, str(path)) for plugin, scope, path in expected} <= refreshed
    assert observation.records_after == observation.records_before
    assert (
        observation.invocation_activation_after
        == observation.invocation_activation_before
    )
    assert observation.other_activation_after == observation.other_activation_before


@pytest.mark.live_subagent_discovery
def test_fresh_codex_session_discovers_every_placed_canonical_subagent() -> None:
    observation = observe_codex_subagent_discovery()

    assert observation.install_exit_code == 0, observation.install_stderr
    assert observation.login_exit_code == 0, observation.login_stderr
    assert observation.session_exit_code == 0, observation.session_stderr
    assert observation.placed_subagent_names
    assert observation.discovered_subagent_names is not None, (
        observation.session_last_message
    )
    assert observation.placed_subagent_names <= observation.discovered_subagent_names
