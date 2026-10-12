"""Managed assets and job failures cross the recording command boundary."""

from outcomeeng_testing.harnesses.consumption_control import (
    installation_observation,
    workspace,
)


def test_versioned_assets_restart_and_unknown_job_state() -> None:
    with workspace() as work:
        observed = installation_observation(work)
        assert not observed.inactive_assets_exist
        assert not observed.inactive_calls
        assert observed.owned_assets == observed.expected_assets
        assert all(
            observed.stable_root in arguments for arguments in observed.stable_arguments
        )
        assert all(
            observed.source_root not in argument
            for arguments in observed.stable_arguments
            for argument in arguments
        )
        assert not any(observed.stopped_loaded)
        assert all(observed.restarted_loaded)
        assert observed.failed_status == observed.expected_failed_status
        assert all(loaded is None for loaded in observed.unknown_loaded)
        assert observed.calls
