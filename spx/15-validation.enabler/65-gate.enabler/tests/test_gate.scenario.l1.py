"""Level 1 scenario tests for the gate orchestrator.

Verifies the orchestrator's externally observable behavior — header lines,
timing summary content, exit codes — under a passing pipeline and a
pipeline that fails at a specific step.

Subprocess invocation is replaced by a recording spawner (Stage 5 exception:
Interaction protocols). Output is captured via an injected StringIO sink.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Final, cast

from outcomeeng.validation import (
    CHECK_RECIPES,
    FAILURE_EXCERPT_LINE_LIMIT,
    FULL_LOG_LABEL,
    PHASE_COMPLETE,
    PHASE_RECIPE,
    PURPOSE_CONFORMANCE,
    PURPOSE_CORRECTNESS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    RUN_FAIL_STATUS,
    RUN_PASS_STATUS,
    STEPS,
    SUMMARY_KEY_EXIT_CODE,
    SUMMARY_KEY_EXCERPT,
    SUMMARY_KEY_LOG_PATH,
    SUMMARY_KEY_PHASE,
    SUMMARY_KEY_PURPOSE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_RECIPES,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
    SUMMARY_KEY_SUMMARY_PATH,
    SUMMARY_KEY_VERIFICATION_TYPE,
    STEP_FAIL_STATUS,
    STEP_PASS_STATUS,
    TEST_RECIPE,
    VALIDATION_RECIPE,
    VERIFICATION_TYPE_TESTING,
    VERIFICATION_TYPE_VALIDATION,
    Recipe,
    Step,
    run,
    run_check,
    run_recipe,
)
from outcomeeng_testing.harnesses.gate import RecordingSpawner

PASS: Final = 0
FAIL: Final = 2
PASSING_OUTPUT: Final = "passing validator output"
FAILING_OUTPUT_PREFIX: Final = "failing validator output line"


def _three_no_op_steps() -> tuple[Step, ...]:
    return (
        Step(label="alpha", argv=("noop-alpha",)),
        Step(label="beta", argv=("noop-beta",)),
        Step(label="gamma", argv=("noop-gamma",)),
    )


def _single_step_recipe(name: str) -> Recipe:
    return Recipe(
        name=name,
        verification_type=VERIFICATION_TYPE_VALIDATION,
        purpose=PURPOSE_CONFORMANCE,
        preflight_steps=(Step(label=f"{name}-preflight", argv=(f"{name}-preflight",)),),
        steps=(Step(label=f"{name}-step", argv=(f"{name}-step",)),),
    )


def _read_summary(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast("dict[str, object]", data)


def _summary_steps(summary: dict[str, object]) -> list[dict[str, object]]:
    steps = summary[SUMMARY_KEY_STEPS]
    assert isinstance(steps, list)
    for step in steps:
        assert isinstance(step, dict)
    return cast("list[dict[str, object]]", steps)


def _summary_recipes(summary: dict[str, object]) -> list[dict[str, object]]:
    recipes = summary[SUMMARY_KEY_RECIPES]
    assert isinstance(recipes, list)
    for recipe in recipes:
        assert isinstance(recipe, dict)
    return cast("list[dict[str, object]]", recipes)


class TestPrimitiveRecipes:
    """Primitive recipes report verification vocabulary and run preflight inside."""

    def test_validation_recipe_runs_preflight_and_reports_validation_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        summary_path = tmp_path / "validation-summary.json"
        spawner = RecordingSpawner(
            exit_codes=[PASS]
            * (len(VALIDATION_RECIPE.preflight_steps) + len(VALIDATION_RECIPE.steps))
        )
        sink = io.StringIO()

        exit_code = run_recipe(
            spawner=spawner,
            sink=sink,
            recipe=VALIDATION_RECIPE,
            summary_path=summary_path,
        )

        summary = _read_summary(summary_path)
        assert exit_code == PASS
        assert spawner.spawn_calls[0] == VALIDATION_RECIPE.preflight_steps[0].argv
        assert PYTEST_ARGV not in spawner.spawn_calls
        assert summary[SUMMARY_KEY_RECIPE] == RECIPE_VALIDATION
        assert summary[SUMMARY_KEY_VERIFICATION_TYPE] == VERIFICATION_TYPE_VALIDATION
        assert summary[SUMMARY_KEY_PURPOSE] == PURPOSE_CONFORMANCE
        assert summary[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
        assert summary[SUMMARY_KEY_PHASE] == PHASE_COMPLETE
        assert summary[SUMMARY_KEY_SUMMARY_PATH] == str(summary_path)
        for step in _summary_steps(summary):
            assert SUMMARY_KEY_LOG_PATH not in step
            assert step[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
            assert isinstance(step[SUMMARY_KEY_EXIT_CODE], int)

    def test_test_recipe_runs_preflight_and_reports_testing_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        summary_path = tmp_path / "test-summary.json"
        spawner = RecordingSpawner(
            exit_codes=[PASS]
            * (len(TEST_RECIPE.preflight_steps) + len(TEST_RECIPE.steps))
        )
        sink = io.StringIO()

        exit_code = run_recipe(
            spawner=spawner,
            sink=sink,
            recipe=TEST_RECIPE,
            summary_path=summary_path,
        )

        summary = _read_summary(summary_path)
        assert exit_code == PASS
        assert spawner.spawn_calls == [
            TEST_RECIPE.preflight_steps[0].argv,
            TEST_RECIPE.steps[0].argv,
        ]
        assert summary[SUMMARY_KEY_RECIPE] == RECIPE_TEST
        assert summary[SUMMARY_KEY_VERIFICATION_TYPE] == VERIFICATION_TYPE_TESTING
        assert summary[SUMMARY_KEY_PURPOSE] == PURPOSE_CORRECTNESS
        assert summary[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
        for step in _summary_steps(summary):
            assert SUMMARY_KEY_LOG_PATH not in step
            assert step[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
            assert isinstance(step[SUMMARY_KEY_EXIT_CODE], int)


class TestPassingPipeline:
    """All steps exit 0; expect quiet live output and removed logs."""

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

    def test_pass_status_printed_per_step(self) -> None:
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS])
        sink = io.StringIO()
        steps = _three_no_op_steps()

        run(spawner=spawner, sink=sink, steps=steps)

        output = sink.getvalue()
        for step in steps:
            assert f"{STEP_PASS_STATUS}  {step.label}" in output

    def test_passing_step_output_goes_to_log_not_live_sink(self) -> None:
        spawner = RecordingSpawner(
            exit_codes=[PASS, PASS, PASS],
            outputs=[PASSING_OUTPUT, PASSING_OUTPUT, PASSING_OUTPUT],
        )
        sink = io.StringIO()

        run(spawner=spawner, sink=sink, steps=_three_no_op_steps())

        assert PASSING_OUTPUT not in sink.getvalue()
        assert spawner.written_outputs == [
            PASSING_OUTPUT,
            PASSING_OUTPUT,
            PASSING_OUTPUT,
        ]
        for output_path in spawner.output_paths:
            assert not output_path.exists()


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

    def test_failing_step_prints_status_excerpt_and_log_path(self) -> None:
        failing_output = "\n".join(
            f"{FAILING_OUTPUT_PREFIX} {index}"
            for index in range(FAILURE_EXCERPT_LINE_LIMIT + 2)
        )
        spawner = RecordingSpawner(
            exit_codes=[PASS, FAIL, PASS],
            outputs=[PASSING_OUTPUT, failing_output, PASSING_OUTPUT],
        )
        sink = io.StringIO()
        steps = _three_no_op_steps()

        run(spawner=spawner, sink=sink, steps=steps)

        output = sink.getvalue()
        failing_log_path = spawner.output_paths[1]
        assert f"{STEP_FAIL_STATUS}  {steps[1].label}" in output
        assert FULL_LOG_LABEL in output
        assert str(failing_log_path) in output
        assert f"{FAILING_OUTPUT_PREFIX} 0" not in output
        assert f"{FAILING_OUTPUT_PREFIX} {FAILURE_EXCERPT_LINE_LIMIT + 1}" in output
        assert not spawner.output_paths[0].exists()
        assert failing_log_path.read_text(encoding="utf-8") == failing_output

    def test_failing_primitive_retains_log_and_records_summary(
        self,
        tmp_path: Path,
    ) -> None:
        failing_output = f"{FAILING_OUTPUT_PREFIX} retained"
        summary_path = tmp_path / "failure-summary.json"
        recipe = _single_step_recipe(RECIPE_VALIDATION)
        spawner = RecordingSpawner(
            exit_codes=[PASS, FAIL],
            outputs=[PASSING_OUTPUT, failing_output],
        )
        sink = io.StringIO()

        exit_code = run_recipe(
            spawner=spawner,
            sink=sink,
            recipe=recipe,
            summary_path=summary_path,
        )

        summary = _read_summary(summary_path)
        steps = _summary_steps(summary)
        failing_log_path = spawner.output_paths[1]
        assert exit_code == FAIL
        assert summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert summary[SUMMARY_KEY_PHASE] == PHASE_RECIPE
        assert summary[SUMMARY_KEY_EXIT_CODE] == FAIL
        assert steps[1][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert steps[1][SUMMARY_KEY_EXCERPT] == failing_output
        assert steps[1][SUMMARY_KEY_LOG_PATH] == str(failing_log_path)
        assert failing_log_path.read_text(encoding="utf-8") == failing_output


class TestCheckWrapper:
    """The check wrapper composes primitive summaries without its own type."""

    def test_check_stops_when_validation_fails(self, tmp_path: Path) -> None:
        summary_path = tmp_path / "check-summary.json"
        validation = _single_step_recipe(RECIPE_VALIDATION)
        test = _single_step_recipe(RECIPE_TEST)
        spawner = RecordingSpawner(exit_codes=[PASS, FAIL, PASS, PASS])
        sink = io.StringIO()

        exit_code = run_check(
            spawner=spawner,
            sink=sink,
            recipes=(validation, test),
            summary_path=summary_path,
        )

        summary = _read_summary(summary_path)
        recipes = _summary_recipes(summary)
        assert exit_code == FAIL
        assert len(spawner.spawn_calls) == len(validation.preflight_steps) + len(
            validation.steps
        )
        assert summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
        assert summary[SUMMARY_KEY_VERIFICATION_TYPE] is None
        assert summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
        assert len(recipes) == 1
        assert recipes[0][SUMMARY_KEY_RECIPE] == RECIPE_VALIDATION

    def test_check_runs_validation_then_test_when_validation_passes(
        self,
        tmp_path: Path,
    ) -> None:
        summary_path = tmp_path / "check-pass-summary.json"
        validation = _single_step_recipe(RECIPE_VALIDATION)
        test = _single_step_recipe(RECIPE_TEST)
        spawner = RecordingSpawner(exit_codes=[PASS, PASS, PASS, PASS])
        sink = io.StringIO()

        exit_code = run_check(
            spawner=spawner,
            sink=sink,
            recipes=(validation, test),
            summary_path=summary_path,
        )

        summary = _read_summary(summary_path)
        recipes = _summary_recipes(summary)
        assert exit_code == PASS
        assert spawner.spawn_calls == [
            validation.preflight_steps[0].argv,
            validation.steps[0].argv,
            test.preflight_steps[0].argv,
            test.steps[0].argv,
        ]
        assert [recipe[SUMMARY_KEY_RECIPE] for recipe in recipes] == [
            RECIPE_VALIDATION,
            RECIPE_TEST,
        ]
        assert summary[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS

    def test_production_check_recipe_order_is_validation_then_test(self) -> None:
        assert [recipe.name for recipe in CHECK_RECIPES] == [
            RECIPE_VALIDATION,
            RECIPE_TEST,
        ]


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
