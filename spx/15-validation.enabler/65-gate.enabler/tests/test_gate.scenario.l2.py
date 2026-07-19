"""Level 2 scenarios for real gate process-group signal behavior."""

from __future__ import annotations

from outcomeeng_testing.harnesses.gate_signal import (
    assert_production_spawner_captures_child_output,
    assert_production_spawner_signal_terminates_child,
    assert_signals_terminate_process_groups_within_grace,
    assert_spawn_window_signals_reach_child_groups,
)


def test_signal_terminates_process_group_within_grace() -> None:
    assert_signals_terminate_process_groups_within_grace()


def test_signal_during_production_spawn_reaches_child_group() -> None:
    assert_spawn_window_signals_reach_child_groups()


def test_production_spawner_captures_child_output() -> None:
    assert_production_spawner_captures_child_output()


def test_production_spawner_signal_to_group_terminates_child() -> None:
    assert_production_spawner_signal_terminates_child()
