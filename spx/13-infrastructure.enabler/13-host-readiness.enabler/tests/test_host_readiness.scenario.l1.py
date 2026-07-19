"""Scenario evidence for bounded host-readiness waiter invocations."""

from outcomeeng_testing.harnesses.host_readiness import (
    run_deadline_not_ready,
    run_immediate_ready,
    run_ready_before_deadline,
)


def test_initial_ready_observation_returns_without_sleeping() -> None:
    run = run_immediate_ready()

    assert run.result.status is run.module.Status.READY
    assert run.result.ready is True
    assert run.result.exit_code is run.module.ExitCode.READY
    assert not run.clock.sleeps


def test_load_becoming_ready_returns_from_the_same_invocation() -> None:
    run = run_ready_before_deadline()

    assert run.result.status is run.module.Status.READY
    assert run.result.ready is True
    assert run.result.exit_code is run.module.ExitCode.READY
    assert run.result.wait_cycles == len(run.clock.sleeps)
    assert run.result.waited_seconds < run.module.MAXIMUM_WAIT_SECONDS


def test_load_remaining_high_returns_not_ready_at_the_deadline() -> None:
    run = run_deadline_not_ready()

    assert run.result.status is run.module.Status.NOT_READY
    assert run.result.ready is False
    assert run.result.exit_code is run.module.ExitCode.NOT_READY
    assert run.result.final is not None
    assert run.result.waited_seconds == run.module.MAXIMUM_WAIT_SECONDS
    assert sum(run.clock.sleeps) == run.module.MAXIMUM_WAIT_SECONDS
