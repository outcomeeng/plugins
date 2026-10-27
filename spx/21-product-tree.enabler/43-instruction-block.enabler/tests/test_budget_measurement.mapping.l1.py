"""Mapping evidence for the per-file project-doc budget measurement."""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses import instruction_block as harness

MODULE = harness.load_instruction_block_module()


@pytest.mark.parametrize(
    "filename", sorted(MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES.values())
)
@pytest.mark.parametrize("state", list(MODULE.BudgetState))
def test_each_root_file_and_state_maps_to_a_report_with_exact_counts(
    filename: str, state: object
) -> None:
    # The partition representatives derive from the declared ceiling and the decision's
    # boundary law (breach exactly when size exceeds the ceiling): the largest size that
    # fits and the smallest that breaches.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    size = budget if state is MODULE.BudgetState.FIT else budget + 1

    measurement = MODULE.measure_budget(filename, "x" * size)
    line = MODULE.budget_report_line(measurement)

    assert measurement.byte_size == size
    assert measurement.budget == budget
    assert measurement.state is state
    expected_overage = size - budget if state is MODULE.BudgetState.BREACH else 0
    assert measurement.overage == expected_overage
    assert filename in line
    assert f"{size}/{budget}" in line
    assert str(state) in line
    if state is MODULE.BudgetState.BREACH:
        assert f"{expected_overage} over" in line


def test_measurement_counts_utf8_bytes_not_characters() -> None:
    # The ceiling is a byte budget, so a payload whose UTF-8 encoding is wider than its
    # character count separates byte counting from character counting: at a character
    # count equal to the ceiling, character counting would report a fit while byte
    # counting reports a breach. Any multi-byte character carries the law; the byte
    # width comes from the UTF-8 encoding itself.
    budget = MODULE.PROJECT_DOC_BUDGET_BYTES
    unit = "é"
    unit_width = len(unit.encode("utf-8"))
    assert unit_width > 1
    filename = next(iter(MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES.values()))

    measurement = MODULE.measure_budget(filename, unit * budget)

    assert measurement.byte_size == unit_width * budget
    assert measurement.state is MODULE.BudgetState.BREACH
