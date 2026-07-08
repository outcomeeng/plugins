"""Property evidence for selected gate determinism."""

from __future__ import annotations

from outcomeeng_testing.harnesses.gate import (
    assert_selected_gate_selection_is_deterministic,
)


def test_selection_is_deterministic_for_path_order_and_duplicates() -> None:
    assert_selected_gate_selection_is_deterministic()
