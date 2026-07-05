"""Mapping evidence for selected local gate planning."""

from __future__ import annotations

from outcomeeng_testing.harnesses.gate import assert_selected_gate_mapping_contract


def test_selected_gate_mapping_contract() -> None:
    assert_selected_gate_mapping_contract()
