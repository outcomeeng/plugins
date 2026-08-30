"""Network-backed real-agent scenarios for repository installation."""

import json

from outcomeeng.distribution.installation import (
    Agent,
    FIRST_INSTALL_WARNING,
    ReportField,
    SPEC_TREE_PLUGIN,
)
from outcomeeng_testing.harnesses.installation import (
    observe_codex_role_discovery,
    observe_real_first_install,
    observe_real_installation,
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


def test_fresh_codex_session_discovers_every_placed_canonical_role() -> None:
    observation = observe_codex_role_discovery()

    assert observation.install_exit_code == 0, observation.install_stderr
    assert observation.login_exit_code == 0, observation.login_stderr
    assert observation.session_exit_code == 0, observation.session_stderr
    assert observation.placed_roles
    assert observation.discovered_roles is not None, observation.session_last_message
    assert observation.placed_roles <= observation.discovered_roles
