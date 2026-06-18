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
from typing import Final

from hypothesis import given, settings

from outcomeeng.validation import SUMMARY_PATH_LABEL, Step, run
from outcomeeng_testing.generators.gate import step_lists
from outcomeeng_testing.harnesses.gate import RecordingSpawner

MAX_EXAMPLES: Final = 50
PASS: Final = 0


@given(steps=step_lists())
@settings(max_examples=MAX_EXAMPLES)
def test_spawn_order_matches_step_list_order(steps: tuple[Step, ...]) -> None:
    """The order in which subprocesses are started equals the step-list order."""
    spawner = RecordingSpawner(exit_codes=[PASS] * len(steps))
    sink = io.StringIO()

    run(spawner=spawner, sink=sink, steps=steps)

    invoked_argvs = spawner.spawn_calls
    expected_argvs = [step.argv for step in steps]
    assert invoked_argvs == expected_argvs


@given(steps=step_lists())
@settings(max_examples=MAX_EXAMPLES)
def test_elapsed_time_is_non_negative_for_completed_steps(
    steps: tuple[Step, ...],
) -> None:
    """Every per-step summary record carries a non-negative elapsed value."""
    spawner = RecordingSpawner(exit_codes=[PASS] * len(steps))
    sink = io.StringIO()

    run(spawner=spawner, sink=sink, steps=steps)

    output = sink.getvalue()
    summary_path = next(
        Path(line.removeprefix(SUMMARY_PATH_LABEL).strip())
        for line in output.splitlines()
        if line.startswith(SUMMARY_PATH_LABEL)
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["steps"], "structured summary must contain step records"
    for step in summary["steps"]:
        assert step["duration_seconds"] >= 0
