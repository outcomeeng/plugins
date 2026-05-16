"""Level 1 scenario tests for the gate orchestrator.

Verifies the orchestrator's externally observable behavior — header lines,
timing summary content, exit codes — under a passing pipeline and a
pipeline that fails at a specific step.

Subprocess invocation is replaced by a recording spawner (Stage 5 exception:
Interaction protocols). Output is captured via an injected StringIO sink.
"""

from __future__ import annotations

import io
from typing import Final

from outcomeeng.validation import STEPS, Step, run
from outcomeeng_testing.harnesses.gate import RecordingSpawner

PASS: Final = 0
FAIL: Final = 2


def _three_no_op_steps() -> tuple[Step, ...]:
    return (
        Step(label="alpha", argv=("noop-alpha",)),
        Step(label="beta", argv=("noop-beta",)),
        Step(label="gamma", argv=("noop-gamma",)),
    )


class TestPassingPipeline:
    """All steps exit 0; expect headers, full timing summary, exit 0."""

    def test_exits_zero(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS])
        sink = io.StringIO()

        exit_code = run(spawner=spawner, sink=sink, steps=_three_no_op_steps())

        assert exit_code == PASS

    def test_header_printed_before_each_step(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS])
        sink = io.StringIO()

        run(spawner=spawner, sink=sink, steps=_three_no_op_steps())

        output = sink.getvalue()
        for step in _three_no_op_steps():
            header = f"━━━ {step.label} ━━━"
            assert header in output

    def test_header_precedes_spawn_for_each_step(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS])
        sink = io.StringIO()
        steps = _three_no_op_steps()

        run(spawner=spawner, sink=sink, steps=steps)

        output = sink.getvalue()
        header_positions = [output.index(f"━━━ {step.label} ━━━") for step in steps]
        assert header_positions == sorted(header_positions)

    def test_timing_summary_block_present(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS])
        sink = io.StringIO()

        run(spawner=spawner, sink=sink, steps=_three_no_op_steps())

        assert "━━━ Timing Summary ━━━" in sink.getvalue()

    def test_timing_summary_includes_total_row(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS])
        sink = io.StringIO()

        run(spawner=spawner, sink=sink, steps=_three_no_op_steps())

        output = sink.getvalue()
        summary_start = output.index("━━━ Timing Summary ━━━")
        assert "TOTAL" in output[summary_start:]

    def test_timing_summary_includes_row_per_step(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS])
        sink = io.StringIO()
        steps = _three_no_op_steps()

        run(spawner=spawner, sink=sink, steps=steps)

        output = sink.getvalue()
        summary_start = output.index("━━━ Timing Summary ━━━")
        summary = output[summary_start:]
        for step in steps:
            assert step.label in summary


class TestFailingStep:
    """A step at position k exits non-zero; expect partial summary, exit k's status."""

    def test_exits_with_failing_step_status(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, FAIL, PASS])
        sink = io.StringIO()

        exit_code = run(spawner=spawner, sink=sink, steps=_three_no_op_steps())

        assert exit_code == FAIL

    def test_subsequent_steps_not_started(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, FAIL, PASS])
        sink = io.StringIO()

        run(spawner=spawner, sink=sink, steps=_three_no_op_steps())

        # Only the first two steps should have been spawned; the third must not run.
        assert len(spawner.spawn_calls) == 2

    def test_timing_summary_lists_completed_steps_only(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, FAIL, PASS])
        sink = io.StringIO()
        steps = _three_no_op_steps()

        run(spawner=spawner, sink=sink, steps=steps)

        output = sink.getvalue()
        summary_start = output.index("━━━ Timing Summary ━━━")
        summary = output[summary_start:]
        assert steps[0].label in summary
        assert steps[1].label in summary
        assert steps[2].label not in summary

    def test_failed_row_names_failing_step(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, FAIL, PASS])
        sink = io.StringIO()
        steps = _three_no_op_steps()

        run(spawner=spawner, sink=sink, steps=steps)

        output = sink.getvalue()
        summary_start = output.index("━━━ Timing Summary ━━━")
        summary = output[summary_start:]
        assert "FAILED" in summary
        # The FAILED row appears at or after the failing step's label.
        failed_idx = summary.index("FAILED")
        assert steps[1].label in summary[failed_idx:]


class TestProductionStepListSmoke:
    """The production STEPS constant runs through the orchestrator end-to-end.

    Uses the same recording spawner — proves STEPS is shape-compatible with
    `run(...)` without launching real validators.
    """

    def test_run_with_production_steps_succeeds_when_all_pass(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS] * len(STEPS))
        sink = io.StringIO()

        exit_code = run(spawner=spawner, sink=sink, steps=STEPS)

        assert exit_code == PASS
        assert len(spawner.spawn_calls) == len(STEPS)
