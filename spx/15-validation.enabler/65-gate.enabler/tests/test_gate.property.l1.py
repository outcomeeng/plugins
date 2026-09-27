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
    TIMING_DIVIDER,
    TIMING_SUMMARY_BANNER,
    Step,
    run,
)
from outcomeeng_testing.harnesses.gate import RecordingSpawner, gate_property


def _row_elapsed_values(output: str) -> tuple[int, ...]:
    """Read each timing row's elapsed value without the engine's own reader.

    The engine's `timing_row_values` matches a run of digits, so it reports a
    negative elapsed value as its magnitude and the sign never reaches the
    assertion. This reader takes each row's whole trailing token, drops only
    its one-character unit, and parses the rest as a signed integer, so a
    negative value arrives negative. The block's bounds come from the engine's
    published constants, which the reader reads rather than respells; what it
    does not borrow is the engine's parse of a row's value, the step this
    property has to judge for itself.
    """
    _, banner, after_banner = output.partition(f"{TIMING_SUMMARY_BANNER}\n")
    assert banner, "the run writes a timing block"
    block, divider, _ = after_banner.partition(f"{TIMING_DIVIDER}\n")
    assert divider, "the timing block is closed by its divider"
    # The block is split on its own line separator rather than by `splitlines`,
    # which also breaks on a carriage return — a step label may carry one, and a
    # row split through its label leaves a fragment with no value to read.
    return tuple(
        int(line.split()[-1][:-1]) for line in block.split("\n") if line.strip()
    )


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
    elapsed_values = _row_elapsed_values(output)
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
