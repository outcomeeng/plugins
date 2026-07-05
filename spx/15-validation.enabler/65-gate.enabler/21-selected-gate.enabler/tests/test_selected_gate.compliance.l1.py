"""Compliance evidence for selected gate execution."""

from __future__ import annotations

from outcomeeng_testing.harnesses.gate import assert_selected_gate_compliance_contract


def test_selected_gate_compliance_contract() -> None:
    assert_selected_gate_compliance_contract()
