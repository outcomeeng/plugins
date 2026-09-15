"""Network-backed real isolated-state boundary evidence."""

from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_isolated_installation_preserves_persistent_agent_state() -> None:
    observation = observe_real_installation()

    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert observation.persistent_mode_first & 0o777 == 0
    assert observation.persistent_mode_second & 0o777 == 0
    assert observation.persistent_initial == observation.persistent_first
    assert observation.persistent_initial == observation.persistent_second
