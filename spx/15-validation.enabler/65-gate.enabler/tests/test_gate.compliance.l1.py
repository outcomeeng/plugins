"""Level 1 compliance tests for the gate orchestrator."""

from __future__ import annotations

from outcomeeng_testing.harnesses.gate import assert_gate_compliance_contract


def test_gate_compliance_contract() -> None:
    assert_gate_compliance_contract()
