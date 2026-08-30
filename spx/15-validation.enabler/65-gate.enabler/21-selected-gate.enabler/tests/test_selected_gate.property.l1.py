"""Property evidence for selected gate determinism."""

from __future__ import annotations

from outcomeeng.validation.selected_gate import build_selected_gate_plan
from outcomeeng_testing.harnesses.gate import (
    SELECTED_GATE_PROPERTY_REPLAY_PATH,
    SELECTED_GATE_PROPERTY_SEED,
    captured_property_failure_notes,
    selected_gate_property,
)


@selected_gate_property
def _selection_is_order_and_duplication_insensitive(paths: list[str]) -> None:
    forward = build_selected_gate_plan(tuple(paths))
    reverse = build_selected_gate_plan(tuple(reversed(paths * 2)))

    assert forward.changed_paths == reverse.changed_paths
    assert forward.full_gate == reverse.full_gate
    assert tuple(item.step.argv for item in forward.selected_steps) == tuple(
        item.step.argv for item in reverse.selected_steps
    )


def test_selection_is_deterministic_for_path_order_and_duplicates() -> None:
    _selection_is_order_and_duplication_insensitive()


def test_property_failure_reports_seed_and_replay_path() -> None:
    @selected_gate_property
    def always_fails(paths: list[str]) -> None:
        assert not paths

    notes = captured_property_failure_notes(always_fails)

    assert f"Hypothesis seed: {SELECTED_GATE_PROPERTY_SEED}" in notes
    assert f"Replay path: {SELECTED_GATE_PROPERTY_REPLAY_PATH}" in notes
