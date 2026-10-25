"""Level 2 scenarios for real gate process-group signal behavior."""

from __future__ import annotations

import signal
from typing import cast

import pytest

from outcomeeng.validation import (
    FORWARDED_SIGNALS,
    RUN_FAIL_STATUS,
    SIGNAL_GRACE_SECONDS,
    SUMMARY_KEY_EXIT_CODE,
    SUMMARY_KEY_LOG_PATH,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
)
from outcomeeng_testing.harnesses.gate_signal import (
    observe_direct_child_reap,
    observe_in_flight_signal_run,
    observe_production_spawner_group_signal,
    observe_production_spawner_output,
    observe_spawn_window_signal_run,
)


@pytest.mark.parametrize("delivered_signal", FORWARDED_SIGNALS, ids=str)
def test_signal_terminates_process_group_within_grace(
    delivered_signal: signal.Signals,
) -> None:
    run = observe_in_flight_signal_run(delivered_signal)
    steps = cast(list[dict[str, object]], run.summary[SUMMARY_KEY_STEPS])

    assert run.child_alive_before_signal
    assert run.grandchild_alive_before_signal
    assert run.grandchild_received_signal == int(signal.SIGTERM)
    assert not run.child_alive_after_exit
    assert run.orchestrator_exit_code == 128 + int(delivered_signal)
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert run.summary[SUMMARY_KEY_EXIT_CODE] == 128 + int(delivered_signal)
    assert steps[0][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert steps[0][SUMMARY_KEY_EXIT_CODE] == 128 + int(delivered_signal)
    assert SUMMARY_KEY_LOG_PATH in steps[0]


@pytest.mark.parametrize("delivered_signal", FORWARDED_SIGNALS, ids=str)
def test_signal_during_production_spawn_reaches_child_group(
    delivered_signal: signal.Signals,
) -> None:
    run = observe_spawn_window_signal_run(delivered_signal)
    steps = cast(list[dict[str, object]], run.summary[SUMMARY_KEY_STEPS])

    assert run.child_alive_before_signal
    assert run.grandchild_alive_before_signal
    assert run.grandchild_received_signal == int(signal.SIGTERM)
    assert not run.child_alive_after_exit
    assert run.orchestrator_exit_code == 128 + int(delivered_signal)
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert run.summary[SUMMARY_KEY_EXIT_CODE] == 128 + int(delivered_signal)
    assert steps[0][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert steps[0][SUMMARY_KEY_EXIT_CODE] == 128 + int(delivered_signal)
    assert SUMMARY_KEY_LOG_PATH in steps[0]


@pytest.mark.parametrize("delivered_signal", FORWARDED_SIGNALS, ids=str)
def test_grace_wait_ends_when_a_direct_child_exits_on_sigterm(
    delivered_signal: signal.Signals,
) -> None:
    reap = observe_direct_child_reap(delivered_signal, child_exits_on_sigterm=True)

    assert reap.run_exit_code == 128 + int(delivered_signal)
    assert reap.child_reaped_before_orchestrator_exit
    assert reap.seconds_from_signal_to_return < SIGNAL_GRACE_SECONDS


@pytest.mark.parametrize("delivered_signal", FORWARDED_SIGNALS, ids=str)
def test_orchestrator_reaps_a_direct_child_it_killed_after_the_grace_wait(
    delivered_signal: signal.Signals,
) -> None:
    reap = observe_direct_child_reap(delivered_signal, child_exits_on_sigterm=False)

    assert reap.run_exit_code == 128 + int(delivered_signal)
    assert reap.child_reaped_before_orchestrator_exit
    assert reap.seconds_from_signal_to_return >= SIGNAL_GRACE_SECONDS


def test_production_spawner_captures_child_output() -> None:
    output = observe_production_spawner_output()

    assert output.exit_code == 0
    assert output.captured == f"{output.printed}\n"


def test_production_spawner_signal_to_group_terminates_child() -> None:
    group_signal = observe_production_spawner_group_signal()

    assert group_signal.poll_before_signal is None
    assert group_signal.exit_code_after_signal != 0
