"""Level 1 scenario tests for the gate orchestrator."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    FAILURE_EXCERPT_LINE_LIMIT,
    FORWARDED_SIGNALS,
    FULL_LOG_LABEL,
    PHASE_COMPLETE,
    PHASE_PREFLIGHT,
    PHASE_RECIPE,
    PURPOSE_CONFORMANCE,
    PURPOSE_CORRECTNESS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    RUN_FAIL_STATUS,
    RUN_PASS_STATUS,
    SPAWN_FAILURE_EXIT_CODE,
    STEP_FAIL_STATUS,
    STEP_PASS_STATUS,
    SUMMARY_KEY_ARGV,
    SUMMARY_KEY_EXCERPT,
    SUMMARY_KEY_EXIT_CODE,
    SUMMARY_KEY_LOG_PATH,
    SUMMARY_KEY_PHASE,
    SUMMARY_KEY_PURPOSE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
    SUMMARY_KEY_SUMMARY_PATH,
    SUMMARY_KEY_VERIFICATION_TYPE,
    TEST_RECIPE,
    TEST_STEPS,
    VALIDATION_RECIPE,
    VALIDATION_STEPS,
    VERIFICATION_TYPE_TESTING,
    VERIFICATION_TYPE_VALIDATION,
)
from outcomeeng_testing.harnesses.gate import (
    FAIL_EXIT_CODE,
    FAILING_CHILD_OUTPUT_PREFIX,
    PASS_EXIT_CODE,
    PASSING_CHILD_OUTPUT,
    SPAWN_FAILURE_MESSAGE,
    check_run_observation,
    pipeline_run_observation,
    recipe_run_observation,
    signal_interrupt_observation,
    single_step_recipe,
    spawn_failure_observation,
    summary_recipes,
    summary_steps,
    three_no_op_steps,
)


def test_the_validation_recipe_runs_preflight_first_and_reports_conformance() -> None:
    run = recipe_run_observation(
        recipe=VALIDATION_RECIPE,
        exit_codes=[PASS_EXIT_CODE]
        * (len(VALIDATION_RECIPE.preflight_steps) + len(VALIDATION_RECIPE.steps)),
    )

    assert run.exit_code == PASS_EXIT_CODE
    assert run.spawn_calls[0] == VALIDATION_RECIPE.preflight_steps[0].argv
    assert PYTEST_ARGV not in run.spawn_calls
    assert run.summary[SUMMARY_KEY_RECIPE] == RECIPE_VALIDATION
    assert run.summary[SUMMARY_KEY_VERIFICATION_TYPE] == VERIFICATION_TYPE_VALIDATION
    assert run.summary[SUMMARY_KEY_PURPOSE] == PURPOSE_CONFORMANCE
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
    assert run.summary[SUMMARY_KEY_PHASE] == PHASE_COMPLETE
    assert run.summary[SUMMARY_KEY_SUMMARY_PATH] == run.summary_path
    for step in summary_steps(run.summary):
        assert SUMMARY_KEY_LOG_PATH not in step
        assert step[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
        assert isinstance(step[SUMMARY_KEY_EXIT_CODE], int)


def test_the_test_recipe_runs_pytest_after_preflight() -> None:
    run = recipe_run_observation(
        recipe=TEST_RECIPE,
        exit_codes=[PASS_EXIT_CODE]
        * (len(TEST_RECIPE.preflight_steps) + len(TEST_RECIPE.steps)),
    )

    assert run.exit_code == PASS_EXIT_CODE
    assert run.spawn_calls == (
        TEST_RECIPE.preflight_steps[0].argv,
        TEST_RECIPE.steps[0].argv,
    )
    assert run.summary[SUMMARY_KEY_RECIPE] == RECIPE_TEST
    assert run.summary[SUMMARY_KEY_VERIFICATION_TYPE] == VERIFICATION_TYPE_TESTING
    assert run.summary[SUMMARY_KEY_PURPOSE] == PURPOSE_CORRECTNESS
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
    for step in summary_steps(run.summary):
        assert SUMMARY_KEY_LOG_PATH not in step
        assert step[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS
        assert isinstance(step[SUMMARY_KEY_EXIT_CODE], int)


def test_a_passing_pipeline_prints_headers_in_order_and_removes_logs() -> None:
    steps = three_no_op_steps()

    run = pipeline_run_observation(
        steps=steps,
        exit_codes=[PASS_EXIT_CODE] * len(steps),
        outputs=[PASSING_CHILD_OUTPUT] * len(steps),
    )

    assert run.exit_code == PASS_EXIT_CODE
    assert "━━━ Timing Summary ━━━" in run.output
    summary = run.output[run.output.index("━━━ Timing Summary ━━━") :]
    assert "TOTAL" in summary
    assert PASSING_CHILD_OUTPUT not in run.output
    assert run.written_outputs == (PASSING_CHILD_OUTPUT,) * len(steps)
    header_positions = [run.output.index(f"━━━ {step.label} ━━━") for step in steps]
    assert header_positions == sorted(header_positions)
    for step in steps:
        assert step.label in summary
        assert f"{STEP_PASS_STATUS}  {step.label}" in run.output
    assert run.retained_logs == (None,) * len(steps)


def test_a_failing_step_stops_the_pipeline_and_retains_its_log() -> None:
    steps = three_no_op_steps()
    failing_output = "\n".join(
        f"{FAILING_CHILD_OUTPUT_PREFIX} {index}"
        for index in range(FAILURE_EXCERPT_LINE_LIMIT + 2)
    )

    run = pipeline_run_observation(
        steps=steps,
        exit_codes=[PASS_EXIT_CODE, FAIL_EXIT_CODE, PASS_EXIT_CODE],
        outputs=[PASSING_CHILD_OUTPUT, failing_output, PASSING_CHILD_OUTPUT],
    )

    summary = run.output[run.output.index("━━━ Timing Summary ━━━") :]
    assert run.exit_code == FAIL_EXIT_CODE
    assert len(run.spawn_calls) == 2
    assert steps[0].label in summary
    assert steps[1].label in summary
    assert steps[2].label not in summary
    assert "FAILED" in summary
    assert steps[1].label in summary[summary.index("FAILED") :]
    assert f"{STEP_FAIL_STATUS}  {steps[1].label}" in run.output
    assert FULL_LOG_LABEL in run.output
    assert run.log_paths[1] in run.output
    assert f"{FAILING_CHILD_OUTPUT_PREFIX} 0" not in run.output
    assert (
        f"{FAILING_CHILD_OUTPUT_PREFIX} {FAILURE_EXCERPT_LINE_LIMIT + 1}" in run.output
    )
    assert run.retained_logs[0] is None
    assert run.retained_logs[1] == failing_output


def test_a_failing_recipe_step_records_excerpt_and_log_path() -> None:
    failing_output = f"{FAILING_CHILD_OUTPUT_PREFIX} retained"
    recipe = single_step_recipe(RECIPE_VALIDATION)

    run = recipe_run_observation(
        recipe=recipe,
        exit_codes=[PASS_EXIT_CODE, FAIL_EXIT_CODE],
        outputs=[PASSING_CHILD_OUTPUT, failing_output],
    )

    steps = summary_steps(run.summary)
    assert run.exit_code == FAIL_EXIT_CODE
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert run.summary[SUMMARY_KEY_PHASE] == PHASE_RECIPE
    assert run.summary[SUMMARY_KEY_EXIT_CODE] == FAIL_EXIT_CODE
    assert steps[1][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert steps[1][SUMMARY_KEY_ARGV] == list(recipe.steps[0].argv)
    assert steps[1][SUMMARY_KEY_EXCERPT] == failing_output
    assert run.retained_logs[1] == failing_output
    assert steps[1][SUMMARY_KEY_LOG_PATH] == run.log_paths[1]
    assert run.summary_path in run.output


def test_a_spawn_failure_is_recorded_with_its_message() -> None:
    recipe = single_step_recipe(RECIPE_VALIDATION)

    run = spawn_failure_observation(recipe=recipe)

    steps = summary_steps(run.summary)
    assert run.exit_code == SPAWN_FAILURE_EXIT_CODE
    assert f"{STEP_FAIL_STATUS}  {recipe.preflight_steps[0].label}" in run.output
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert run.summary[SUMMARY_KEY_PHASE] == PHASE_PREFLIGHT
    assert run.summary[SUMMARY_KEY_EXIT_CODE] == SPAWN_FAILURE_EXIT_CODE
    assert steps[0][SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert steps[0][SUMMARY_KEY_LOG_PATH] == run.log_paths[0]
    assert SPAWN_FAILURE_MESSAGE in str(steps[0][SUMMARY_KEY_EXCERPT])
    assert run.retained_logs[0] is not None
    assert SPAWN_FAILURE_MESSAGE in run.retained_logs[0]


def test_the_check_wrapper_stops_at_the_first_failing_recipe() -> None:
    validation = single_step_recipe(RECIPE_VALIDATION)
    test = single_step_recipe(RECIPE_TEST)

    run = check_run_observation(
        recipes=(validation, test),
        exit_codes=[PASS_EXIT_CODE, FAIL_EXIT_CODE, PASS_EXIT_CODE, PASS_EXIT_CODE],
    )

    recipes = summary_recipes(run.summary)
    assert run.exit_code == FAIL_EXIT_CODE
    assert len(run.spawn_calls) == len(validation.preflight_steps) + len(
        validation.steps
    )
    assert run.summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
    assert run.summary[SUMMARY_KEY_VERIFICATION_TYPE] is None
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert len(recipes) == 1
    assert recipes[0][SUMMARY_KEY_RECIPE] == RECIPE_VALIDATION


def test_the_check_wrapper_runs_both_recipes_when_validation_passes() -> None:
    validation = single_step_recipe(RECIPE_VALIDATION)
    test = single_step_recipe(RECIPE_TEST)

    run = check_run_observation(
        recipes=(validation, test),
        exit_codes=[PASS_EXIT_CODE] * 4,
    )

    recipes = summary_recipes(run.summary)
    assert run.exit_code == PASS_EXIT_CODE
    assert run.spawn_calls == (
        validation.preflight_steps[0].argv,
        validation.steps[0].argv,
        test.preflight_steps[0].argv,
        test.steps[0].argv,
    )
    assert [recipe[SUMMARY_KEY_RECIPE] for recipe in recipes] == [
        RECIPE_VALIDATION,
        RECIPE_TEST,
    ]
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS


@pytest.mark.parametrize("signum", FORWARDED_SIGNALS)
def test_a_signal_before_a_child_handle_writes_a_failed_summary(signum: int) -> None:
    run = signal_interrupt_observation(signum)

    assert run.exit_code == 128 + signum
    assert run.summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
    assert run.summary[SUMMARY_KEY_PHASE] == PHASE_RECIPE
    assert run.summary[SUMMARY_KEY_STATUS] == RUN_FAIL_STATUS
    assert run.summary[SUMMARY_KEY_EXIT_CODE] == 128 + signum
    assert run.summary[SUMMARY_KEY_STEPS] == []


def test_the_production_step_lists_run_end_to_end() -> None:
    steps = (*VALIDATION_STEPS, *TEST_STEPS)

    run = pipeline_run_observation(
        steps=steps,
        exit_codes=[PASS_EXIT_CODE] * len(steps),
    )

    assert run.exit_code == PASS_EXIT_CODE
    assert len(run.spawn_calls) == len(steps)
