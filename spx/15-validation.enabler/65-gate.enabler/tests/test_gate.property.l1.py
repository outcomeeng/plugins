"""Level 1 property tests for the gate orchestrator.

Verifies invariants that must hold across arbitrary step lists:
- Spawn invocation order matches the declared step-list order.
- The elapsed-time value recorded in the timing summary is non-negative
  for any step that completes.
"""

from __future__ import annotations

import re
from typing import Final

from outcomeeng.validation import SUMMARY_KEY_DURATION_SECONDS, Step
from outcomeeng.validation._engine import (
    TIMING_ELAPSED_UNIT,
    TIMING_SUMMARY_HEADER,
    TIMING_SUMMARY_RULE,
)
from outcomeeng_testing.generators.gate import PASS_EXIT_CODE
from outcomeeng_testing.harnesses.gate import (
    gate_step_property,
    pipeline_run_observation,
    summary_steps,
)

TIMING_ROW_PATTERN: Final = re.compile(rf"\s+([0-9]+){re.escape(TIMING_ELAPSED_UNIT)}$")


def _timing_summary_elapsed_values(output: str) -> list[int]:
    summary_text = output.split(f"{TIMING_SUMMARY_HEADER}\n", maxsplit=1)[1]
    rows_text = summary_text.split(f"{TIMING_SUMMARY_RULE}\n", maxsplit=1)[0]
    elapsed_values: list[int] = []
    for line in rows_text.splitlines():
        match = TIMING_ROW_PATTERN.search(line)
        if match is not None:
            elapsed_values.append(int(match.group(1)))
    return elapsed_values


@gate_step_property
def _spawn_order_matches_step_list_order(steps: tuple[Step, ...]) -> None:
    run = pipeline_run_observation(
        steps=steps, exit_codes=[PASS_EXIT_CODE] * len(steps)
    )

    assert run.spawn_calls == tuple(step.argv for step in steps)


def test_spawn_order_matches_step_list_order() -> None:
    """The order in which subprocesses are started equals the step-list order."""
    _spawn_order_matches_step_list_order()


@gate_step_property
def _elapsed_time_is_non_negative_for_completed_steps(
    steps: tuple[Step, ...],
) -> None:
    run = pipeline_run_observation(
        steps=steps, exit_codes=[PASS_EXIT_CODE] * len(steps)
    )

    elapsed_values = _timing_summary_elapsed_values(run.output)
    assert len(elapsed_values) == len(steps)
    for elapsed in elapsed_values:
        assert elapsed >= 0
    assert run.summary is not None
    step_records = summary_steps(run.summary)
    assert step_records, "structured summary must contain step records"
    for step in step_records:
        duration = step[SUMMARY_KEY_DURATION_SECONDS]
        assert isinstance(duration, int)
        assert duration >= 0


def test_elapsed_time_is_non_negative_for_completed_steps() -> None:
    """Every per-step summary record carries a non-negative elapsed value."""
    _elapsed_time_is_non_negative_for_completed_steps()
