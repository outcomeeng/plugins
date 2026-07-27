"""Real-agent end-to-end evidence for repository installation."""

from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_real_agent_clis_install_every_catalog_plugin_idempotently() -> None:
    observation = observe_real_installation()

    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert observation.claude_plugins_first == observation.catalog_claude_plugins
    assert observation.claude_plugins_second == observation.catalog_claude_plugins
    assert observation.codex_plugins_first == observation.catalog_codex_plugins
    assert observation.codex_plugins_second == observation.catalog_codex_plugins
    assert observation.placed_first == observation.placed_second
    assert observation.unowned_first == observation.unowned_initial
    assert observation.unowned_second == observation.unowned_initial
