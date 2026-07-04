"""Property evidence for selected gate determinism."""

from __future__ import annotations

from hypothesis import given

from outcomeeng.validation.selected_gate import build_selected_gate_plan
from outcomeeng_testing.generators.gate import selected_gate_changed_paths


@given(selected_gate_changed_paths())
def test_selection_is_deterministic_for_path_order_and_duplicates(
    paths: list[str],
) -> None:
    forward = build_selected_gate_plan(tuple(paths))
    reverse = build_selected_gate_plan(tuple(reversed(paths * 2)))

    assert forward.changed_paths == reverse.changed_paths
    assert forward.full_gate == reverse.full_gate
    assert tuple(item.step.argv for item in forward.selected_steps) == tuple(
        item.step.argv for item in reverse.selected_steps
    )
