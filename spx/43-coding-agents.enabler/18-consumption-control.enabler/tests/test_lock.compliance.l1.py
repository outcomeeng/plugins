"""A real advisory lock excludes overlapping finite workers."""

from outcomeeng_testing.harnesses.consumption_control import lock_observation, workspace


def test_busy_worker_returns_without_collecting() -> None:
    with workspace() as work:
        observed = lock_observation(work)
        assert observed.status == observed.expected_status
        assert observed.exitcode == observed.expected_exitcode
        assert not observed.state_exists
