"""Network-backed real-agent scenarios for repository installation."""

from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_real_agent_clis_materialize_and_repeat_full_installation() -> None:
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
