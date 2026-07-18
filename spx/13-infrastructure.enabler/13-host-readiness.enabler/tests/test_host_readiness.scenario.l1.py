"""Scenario evidence for bounded host-readiness waiter invocations."""

from outcomeeng_testing.harnesses.host_readiness import (
    run_deadline_not_ready,
    run_immediate_ready,
    run_ready_before_deadline,
)


def test_initial_ready_observation_returns_without_sleeping() -> None:
    assert (
        run_immediate_ready().result.status is run_immediate_ready().module.Status.READY
    )
    assert run_immediate_ready().result.ready is True
    assert (
        run_immediate_ready().result.exit_code
        is run_immediate_ready().module.ExitCode.READY
    )
    assert not run_immediate_ready().clock.sleeps


def test_load_becoming_ready_returns_from_the_same_invocation() -> None:
    assert (
        run_ready_before_deadline().result.status
        is run_ready_before_deadline().module.Status.READY
    )
    assert run_ready_before_deadline().result.ready is True
    assert (
        run_ready_before_deadline().result.exit_code
        is run_ready_before_deadline().module.ExitCode.READY
    )
    assert run_ready_before_deadline().result.wait_cycles == len(
        run_ready_before_deadline().clock.sleeps
    )
    assert (
        run_ready_before_deadline().result.waited_seconds
        < run_ready_before_deadline().module.MAXIMUM_WAIT_SECONDS
    )


def test_load_remaining_high_returns_not_ready_at_the_deadline() -> None:
    assert (
        run_deadline_not_ready().result.status
        is run_deadline_not_ready().module.Status.NOT_READY
    )
    assert run_deadline_not_ready().result.ready is False
    assert (
        run_deadline_not_ready().result.exit_code
        is run_deadline_not_ready().module.ExitCode.NOT_READY
    )
    assert run_deadline_not_ready().result.final is not None
    assert (
        run_deadline_not_ready().result.waited_seconds
        == run_deadline_not_ready().module.MAXIMUM_WAIT_SECONDS
    )
    assert sum(run_deadline_not_ready().clock.sleeps) == (
        run_deadline_not_ready().module.MAXIMUM_WAIT_SECONDS
    )
