"""Native scheduling preserves occupied labels and stops disposable jobs."""

from outcomeeng_testing.harnesses.consumption_control import (
    native_installation_observation,
    workspace,
)


def test_native_install_status_stop_and_restart() -> None:
    with workspace() as work:
        observed = native_installation_observation(work)
        assert observed.status == observed.expected_status
        assert all(observed.installed_loaded)
        assert not any(observed.stopped_loaded)
        assert all(observed.restarted_loaded)
        assert not any(observed.cleanup_loaded)
