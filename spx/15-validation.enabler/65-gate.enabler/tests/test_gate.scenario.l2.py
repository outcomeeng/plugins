"""Level 2 scenarios for real gate process-group signal behavior."""

from __future__ import annotations

import signal
from typing import cast

from outcomeeng.validation import (
    FORWARDED_SIGNALS,
    ProductionSpawner,
    RUN_FAIL_STATUS,
    SUMMARY_KEY_EXIT_CODE,
    SUMMARY_KEY_LOG_PATH,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
)
from outcomeeng_testing.harnesses.gate_signal import (
    SignalGroupObservation,
    observe_production_spawner_captures_child_output,
    observe_production_spawner_signal_terminates_child,
    observe_signals_terminate_process_groups_within_grace,
    observe_spawn_window_signals_reach_child_groups,
)


def _assert_failed_signal_observations(
    observations: tuple[SignalGroupObservation, ...],
) -> None:
    assert tuple(item.delivered_signal for item in observations) == FORWARDED_SIGNALS
    for observation in observations:
        expected_exit_code = 128 + int(observation.delivered_signal)
        assert observation.child_alive_before
        assert observation.grandchild_alive_before
        assert observation.received_group_signal == int(signal.SIGTERM)
        assert not observation.child_alive_after
        assert observation.orchestrator_exit_code == expected_exit_code
        assert observation.summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert observation.summary[SUMMARY_KEY_EXIT_CODE] == expected_exit_code
        steps = cast(list[dict[str, object]], observation.summary[SUMMARY_KEY_STEPS])
        assert len(steps) == 1
        assert steps[0][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert steps[0][SUMMARY_KEY_EXIT_CODE] == expected_exit_code
        assert SUMMARY_KEY_LOG_PATH in steps[0]


def test_signal_terminates_process_group_within_grace() -> None:
    _assert_failed_signal_observations(
        observe_signals_terminate_process_groups_within_grace()
    )


def test_signal_during_production_spawn_reaches_child_group() -> None:
    _assert_failed_signal_observations(
        observe_spawn_window_signals_reach_child_groups()
    )


def test_production_spawner_captures_child_output() -> None:
    observation = observe_production_spawner_captures_child_output()

    assert observation.exit_code == 0
    assert observation.output == f"{ProductionSpawner.__name__}\n"


def test_production_spawner_signal_to_group_terminates_child() -> None:
    observation = observe_production_spawner_signal_terminates_child()

    assert observation.alive_before
    assert observation.exit_code != 0
