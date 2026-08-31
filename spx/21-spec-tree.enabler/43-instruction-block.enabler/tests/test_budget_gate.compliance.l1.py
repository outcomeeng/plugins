"""Compliance evidence for the drift gate's budget-regression boundary."""

from __future__ import annotations

from outcomeeng.distribution import instruction_block as gate
from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


def test_gate_fails_only_a_regression_above_the_ceiling() -> None:
    # Every case derives from the declared ceiling and the decision's boundary law:
    # the largest fitting size and the smallest breaching sizes are the partition
    # representatives on each side of the committed/rendered pair.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    fitting = budget
    breaching = budget + 1

    # The violating case: a surface that previously fit regresses above the ceiling.
    assert gate.budget_regression(fitting, breaching, budget) is True
    # A breach the checked change did not introduce is reported, never failed.
    assert gate.budget_regression(breaching, breaching + 1, budget) is False
    # A fitting surface stays clean.
    assert gate.budget_regression(fitting, fitting, budget) is False
    # A file with no committed form cannot regress.
    assert gate.budget_regression(None, breaching, budget) is False
