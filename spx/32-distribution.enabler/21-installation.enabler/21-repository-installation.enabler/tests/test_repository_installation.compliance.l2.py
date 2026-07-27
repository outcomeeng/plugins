"""Real isolated-state boundary evidence for repository installation."""

from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_isolated_installation_preserves_persistent_agent_state() -> None:
    observation = observe_real_installation()

    assert observation.persistent_initial == observation.persistent_first
    assert observation.persistent_initial == observation.persistent_second
