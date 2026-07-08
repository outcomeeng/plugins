"""Level 1 scenario tests for the gate orchestrator."""

from __future__ import annotations

from outcomeeng_testing.harnesses.gate import assert_gate_scenario_contract


def test_gate_scenario_contract() -> None:
    assert_gate_scenario_contract()
