"""Level 1 property tests for the gate orchestrator.

Verifies invariants that must hold across arbitrary step lists:
- Spawn invocation order matches the declared step-list order.
- The elapsed-time value recorded in the timing summary is non-negative
  for any step that completes.
"""

from __future__ import annotations

import re
from typing import Final

from outcomeeng.validation import (
    SUMMARY_KEY_DURATION_SECONDS,
    Step,
)
from outcomeeng_testing.harnesses.gate import (
    PASS_EXIT_CODE,
    ScriptedMonotonicClock,
    pipeline_run_observation,
    step_list_property,
    summary_steps,
    timed_step_list_property,
)

TIMING_ROW_PATTERN: Final = re.compile(r"\s+([0-9]+)s$")


def _timing_summary_elapsed_values(output: str) -> list[int]:
    summary_text = output.split("━━━ Timing Summary ━━━\n", maxsplit=1)[1]
    rows_text = summary_text.split("  ────────────────────────\n", maxsplit=1)[0]
    elapsed_values: list[int] = []
    for line in rows_text.splitlines():
        match = TIMING_ROW_PATTERN.search(line)
        if match is not None:
            elapsed_values.append(int(match.group(1)))
    return elapsed_values


@step_list_property
def _spawn_order_matches_step_list_order(steps: tuple[Step, ...]) -> None:
    observation = pipeline_run_observation(
        steps=steps, exit_codes=[PASS_EXIT_CODE] * len(steps)
    )

    invoked_argvs = list(observation.spawn_calls)
    expected_argvs = [step.argv for step in steps]
    assert invoked_argvs == expected_argvs


def test_spawn_order_matches_step_list_order() -> None:
    """The order in which subprocesses are started equals the step-list order."""
    _spawn_order_matches_step_list_order()


# Assertion design record: elapsed-time property
# - Assertion: for any step that exits 0, the elapsed-time value recorded in
#   the timing summary is a non-negative integer (universal, open domain).
# - Production subject: the gate engine's per-step elapsed read, observed
#   through the timing-summary rows and the structured summary durations.
# - Case provenance: step lists from the gate generator; per-read clock
#   advances from the gate generator, each at least one second so every step
#   interval is positive and nonzero after rounding.
# - Oracle owner: the spec's non-negative-integer relationship; the controlled
#   clock only supplies readings, the predicate stays in this test.
# - Rejected mutation: `round(step_start - monotonic())` at the step elapsed
#   read in the engine.
# - Failure observation: that mutation records a value of at most -1, which the
#   timing-row pattern does not match (len(elapsed_values) != len(steps)) and
#   which fails `duration >= 0` in the structured summary.


@timed_step_list_property
def _elapsed_time_is_non_negative_for_completed_steps(
    steps: tuple[Step, ...],
    increments: tuple[float, ...],
) -> None:
    observation = pipeline_run_observation(
        steps=steps,
        exit_codes=[PASS_EXIT_CODE] * len(steps),
        monotonic=ScriptedMonotonicClock(increments=increments),
    )

    elapsed_values = _timing_summary_elapsed_values(observation.output)
    assert len(elapsed_values) == len(steps)
    for elapsed in elapsed_values:
        assert elapsed >= 0

    summary = observation.summary
    step_records = summary_steps(summary)
    assert step_records, "structured summary must contain step records"
    for step in step_records:
        duration = step[SUMMARY_KEY_DURATION_SECONDS]
        assert isinstance(duration, int)
        assert duration >= 0


def test_elapsed_time_is_non_negative_for_completed_steps() -> None:
    """Every per-step summary record carries a non-negative elapsed value."""
    _elapsed_time_is_non_negative_for_completed_steps()
