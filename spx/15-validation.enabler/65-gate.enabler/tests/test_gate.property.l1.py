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
import re
from typing import Final

from hypothesis import given

from outcomeeng.validation import (
    SUMMARY_KEY_DURATION_SECONDS,
    SUMMARY_KEY_STEPS,
    SUMMARY_PATH_LABEL,
    Step,
    run,
)
from outcomeeng_testing.generators.gate import step_lists
from outcomeeng_testing.harnesses.gate import RecordingSpawner, run_gate_property

PASS: Final = 0
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


def test_spawn_order_matches_step_list_order() -> None:
    """The order in which subprocesses are started equals the step-list order."""

    @given(steps=step_lists())
    def property_case(steps: tuple[Step, ...]) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS] * len(steps))
        sink = io.StringIO()

        run(spawner=spawner, sink=sink, steps=steps)

        invoked_argvs = spawner.spawn_calls
        expected_argvs = [step.argv for step in steps]
        assert invoked_argvs == expected_argvs

    run_gate_property(property_case)


def test_elapsed_time_is_non_negative_for_completed_steps() -> None:
    """Every per-step summary record carries a non-negative elapsed value."""

    @given(steps=step_lists())
    def property_case(steps: tuple[Step, ...]) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS] * len(steps))
        sink = io.StringIO()

        run(spawner=spawner, sink=sink, steps=steps)

        output = sink.getvalue()
        elapsed_values = _timing_summary_elapsed_values(output)
        assert len(elapsed_values) == len(steps)
        for elapsed in elapsed_values:
            assert elapsed >= 0

        summary_path = next(
            Path(line.removeprefix(SUMMARY_PATH_LABEL).strip())
            for line in output.splitlines()
            if line.startswith(SUMMARY_PATH_LABEL)
        )
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary[SUMMARY_KEY_STEPS], (
            "structured summary must contain step records"
        )
        for step in summary[SUMMARY_KEY_STEPS]:
            assert isinstance(step[SUMMARY_KEY_DURATION_SECONDS], int)
            assert step[SUMMARY_KEY_DURATION_SECONDS] >= 0

    run_gate_property(property_case)
