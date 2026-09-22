"""Level 1 property tests for the gate orchestrator.

Verifies invariants that must hold across arbitrary step lists:
- Spawn invocation order matches the declared step-list order.
- The elapsed-time value recorded in the timing summary is non-negative
  for any step that completes.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from outcomeeng.validation import (
    SUCCESS_EXIT_CODE,
    SUMMARY_KEY_DURATION_SECONDS,
    SUMMARY_KEY_STEPS,
    SUMMARY_PATH_LABEL,
    Step,
    run,
)
from outcomeeng.validation._engine import timing_row_values
from outcomeeng_testing.harnesses.gate import RecordingSpawner, gate_property


@gate_property
def test_spawn_order_matches_step_list_order(steps: tuple[Step, ...]) -> None:
    """The order in which subprocesses are started equals the step-list order."""
    spawner = RecordingSpawner(exit_codes=[SUCCESS_EXIT_CODE] * len(steps))
    sink = io.StringIO()

    run(spawner=spawner, sink=sink, steps=steps)

    invoked_argvs = spawner.spawn_calls
    expected_argvs = [step.argv for step in steps]
    assert invoked_argvs == expected_argvs


@gate_property
def test_elapsed_time_is_non_negative_for_completed_steps(
    steps: tuple[Step, ...],
) -> None:
    """Every per-step summary record carries a non-negative elapsed value."""
    spawner = RecordingSpawner(exit_codes=[SUCCESS_EXIT_CODE] * len(steps))
    sink = io.StringIO()

    run(spawner=spawner, sink=sink, steps=steps)

    output = sink.getvalue()
    # Every line of the run reaches one sink, and a step's status line ends in
    # the same elapsed seconds as its timing row, so a reader that took the
    # run's lines rather than its timing block would return one value per step
    # twice over.
    elapsed_values = timing_row_values(output)
    assert len(elapsed_values) == len(steps)
    for elapsed in elapsed_values:
        assert elapsed >= 0

    summary_path = next(
        Path(line.removeprefix(SUMMARY_PATH_LABEL).strip())
        for line in output.splitlines()
        if line.startswith(SUMMARY_PATH_LABEL)
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary[SUMMARY_KEY_STEPS], "structured summary must contain step records"
    for step in summary[SUMMARY_KEY_STEPS]:
        assert isinstance(step[SUMMARY_KEY_DURATION_SECONDS], int)
        assert step[SUMMARY_KEY_DURATION_SECONDS] >= 0
