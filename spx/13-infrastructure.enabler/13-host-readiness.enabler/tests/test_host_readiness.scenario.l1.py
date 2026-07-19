"""Scenario evidence for bounded host-readiness waiter invocations."""

from outcomeeng_testing.harnesses.host_readiness import (
    run_deadline_not_ready,
    run_error_reading_load,
    run_immediate_ready,
    run_interrupted_during_wait,
    run_ready_before_deadline,
    run_unsupported_platform,
)


def test_initial_ready_observation_returns_without_sleeping() -> None:
    run = run_immediate_ready()

    assert run.result.status is run.module.Status.READY
    assert run.result.ready is True
    assert int(run.result.exit_code) == 0
    assert not run.clock.sleeps


def test_load_becoming_ready_returns_from_the_same_invocation() -> None:
    run = run_ready_before_deadline()

    assert run.result.status is run.module.Status.READY
    assert run.clock.sleeps
    assert run.result.wait_cycles == len(run.clock.sleeps)
    assert run.result.waited_seconds < run.module.MAXIMUM_WAIT_SECONDS


def test_load_remaining_high_returns_not_ready_at_the_deadline() -> None:
    run = run_deadline_not_ready()

    assert run.result.status is run.module.Status.NOT_READY
    assert run.result.ready is False
    assert int(run.result.exit_code) == 3
    assert run.result.final is not None
    assert run.result.waited_seconds == run.module.MAXIMUM_WAIT_SECONDS
    assert sum(run.clock.sleeps) == run.module.MAXIMUM_WAIT_SECONDS


def test_host_without_a_positive_cpu_count_returns_unsupported() -> None:
    run = run_unsupported_platform()

    assert run.result.status is run.module.Status.UNSUPPORTED
    assert run.result.ready is False
    assert int(run.result.exit_code) == 2


def test_interrupt_during_a_wait_interval_returns_interrupted() -> None:
    run = run_interrupted_during_wait()

    assert run.result.status is run.module.Status.INTERRUPTED
    assert run.result.ready is False
    assert int(run.result.exit_code) == 130


def test_failing_load_reader_returns_error() -> None:
    run = run_error_reading_load()

    assert run.result.status is run.module.Status.ERROR
    assert run.result.ready is False
    assert int(run.result.exit_code) == 1
