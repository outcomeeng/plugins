"""Native scheduling preserves occupied labels and stops disposable jobs."""

from outcomeeng_testing.harnesses.consumption_control import (
    native_installation_observation,
    workspace,
)


def test_native_install_status_stop_and_restart() -> None:
    with workspace() as work:
        observed = native_installation_observation(work)
        assert observed.status == observed.expected_status
        assert len(observed.installed_loaded) == observed.expected_job_count
        assert len(observed.stopped_loaded) == observed.expected_job_count
        assert len(observed.restarted_loaded) == observed.expected_job_count
        assert len(observed.cleanup_loaded) == observed.expected_job_count
        assert all(observed.installed_loaded)
        assert all(loaded is False for loaded in observed.stopped_loaded)
        assert all(observed.restarted_loaded)
        assert all(loaded is False for loaded in observed.cleanup_loaded)
