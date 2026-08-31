"""Level 1 compliance tests for the gate orchestrator."""

from __future__ import annotations

import ast
import math
import signal
from typing import cast

from outcomeeng.validation import (
    CHECK_RECIPES,
    FMT_CHECK_ARGV,
    HOOK_SAFETY_ARGV,
    MYPY_ARGV,
    POST_KILL_REAP_ATTEMPTS,
    PURPOSE_CONFORMANCE,
    PURPOSE_CORRECTNESS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SIGNAL_GRACE_SECONDS,
    SIGNAL_POLL_INTERVAL_SECONDS,
    SPX_MARKDOWN_ARGV,
    SUMMARY_KEY_PURPOSE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_VERIFICATION_TYPE,
    Step,
    TEST_RECIPE,
    TEST_STEPS,
    VALIDATION_RECIPE,
    VALIDATION_STEPS,
    VERIFICATION_TYPE_TESTING,
    VERIFICATION_TYPE_VALIDATION,
    test_recipe as build_test_recipe,
)
from outcomeeng_testing.harnesses.gate import (
    HIGH_VOLUME_CHILD_OUTPUT,
    PASS_EXIT_CODE,
    PYTEST_TARGET_ARG,
    STATIC_ANALYSIS_ARGVS,
    bounded_shutdown_observation,
    call_keyword_map,
    check_run_observation,
    while_loops_in_gate_modules,
    popen_calls_from,
    recipe_run_observation,
    validation_package_source_text,
    validation_subprocess_importers,
)


def test_the_full_gate_carries_every_required_step() -> None:
    step_argvs = {step.argv for step in VALIDATION_STEPS}

    assert isinstance(VALIDATION_STEPS, tuple)
    assert isinstance(TEST_STEPS, tuple)
    assert len(VALIDATION_STEPS) >= 1
    assert len(TEST_STEPS) >= 1
    assert all(isinstance(step, Step) for step in (*VALIDATION_STEPS, *TEST_STEPS))
    assert FMT_CHECK_ARGV in step_argvs
    assert RUFF_FORMAT_ARGV in step_argvs
    assert RUFF_CHECK_ARGV in step_argvs
    assert set(STATIC_ANALYSIS_ARGVS).issubset(step_argvs)
    assert "--strict" in MYPY_ARGV
    assert SPX_MARKDOWN_ARGV in step_argvs
    assert HOOK_SAFETY_ARGV in step_argvs
    assert PYTEST_ARGV not in step_argvs
    assert TEST_STEPS == (Step(label="pytest", argv=PYTEST_ARGV),)


def test_recipe_types_and_purposes_match_the_verification_taxonomy() -> None:
    assert VALIDATION_RECIPE.name == RECIPE_VALIDATION
    assert VALIDATION_RECIPE.verification_type == VERIFICATION_TYPE_VALIDATION
    assert VALIDATION_RECIPE.purpose == PURPOSE_CONFORMANCE
    assert TEST_RECIPE.name == RECIPE_TEST
    assert TEST_RECIPE.verification_type == VERIFICATION_TYPE_TESTING
    assert TEST_RECIPE.purpose == PURPOSE_CORRECTNESS
    assert [recipe.name for recipe in CHECK_RECIPES] == [
        RECIPE_VALIDATION,
        RECIPE_TEST,
    ]
    assert RECIPE_CHECK not in {
        VALIDATION_RECIPE.verification_type,
        TEST_RECIPE.verification_type,
    }

    assert build_test_recipe() == TEST_RECIPE
    targeted = build_test_recipe((PYTEST_TARGET_ARG,))
    assert targeted.name == TEST_RECIPE.name
    assert targeted.verification_type == TEST_RECIPE.verification_type
    assert targeted.purpose == TEST_RECIPE.purpose
    assert targeted.preflight_steps == TEST_RECIPE.preflight_steps
    assert targeted.steps == (
        Step(label="pytest", argv=(*PYTEST_ARGV, PYTEST_TARGET_ARG)),
    )


def test_the_check_wrapper_reports_no_verification_type() -> None:
    run = check_run_observation(
        recipes=(VALIDATION_RECIPE,),
        exit_codes=[PASS_EXIT_CODE]
        * (len(VALIDATION_RECIPE.preflight_steps) + len(VALIDATION_RECIPE.steps)),
    )

    assert run.exit_code == PASS_EXIT_CODE
    assert isinstance(run.summary, dict)
    summary = cast(dict[str, object], run.summary)
    assert summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
    assert summary[SUMMARY_KEY_VERIFICATION_TYPE] is None
    assert summary[SUMMARY_KEY_PURPOSE] is None


def test_child_output_is_captured_never_streamed() -> None:
    run = recipe_run_observation(
        recipe=TEST_RECIPE,
        exit_codes=[PASS_EXIT_CODE, PASS_EXIT_CODE],
        outputs=[HIGH_VOLUME_CHILD_OUTPUT, HIGH_VOLUME_CHILD_OUTPUT],
    )

    assert run.exit_code == PASS_EXIT_CODE
    assert HIGH_VOLUME_CHILD_OUTPUT not in run.output
    assert len(run.output.splitlines()) < len(HIGH_VOLUME_CHILD_OUTPUT.splitlines())


def test_subprocess_lives_only_in_the_production_spawner() -> None:
    importers = validation_subprocess_importers()

    assert len(importers) == 1, (
        f"`subprocess` must be imported by exactly one module "
        f"(the production adapter); found: {importers}"
    )
    spawner_path = importers[0]
    source = spawner_path.read_text(encoding="utf-8")
    popen_calls = popen_calls_from(spawner_path)
    assert popen_calls, "production spawner must call subprocess.Popen"
    for call in popen_calls:
        kwargs = call_keyword_map(call)
        assert "start_new_session" in kwargs, "Popen call must pass start_new_session"
        value = kwargs["start_new_session"]
        assert isinstance(value, ast.Constant) and value.value is True, (
            "start_new_session must be the literal True"
        )
        assert "preexec_fn" in kwargs, "Popen call must pass preexec_fn"
        preexec_fn = kwargs["preexec_fn"]
        assert isinstance(preexec_fn, ast.Name)
        assert preexec_fn.id == "_restore_child_signal_mask"
    assert "signal.pthread_sigmask(signal.SIG_UNBLOCK" in source
    for signal_name in ("SIGTERM", "SIGINT", "SIGHUP"):
        assert f"signal.{signal_name}" in source


def test_no_gate_module_polls_with_while_true_sleep() -> None:
    for module_name, loop in while_loops_in_gate_modules():
        is_while_true = isinstance(loop.test, ast.Constant) and loop.test.value is True
        has_sleep_call = any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "sleep"
            for child in ast.walk(loop)
        )
        assert not (is_while_true and has_sleep_call), module_name
    assert "gh run watch" not in validation_package_source_text()


def test_signal_shutdown_waits_are_bounded() -> None:
    shutdown = bounded_shutdown_observation()

    grace_sleep_calls = math.ceil(SIGNAL_GRACE_SECONDS / SIGNAL_POLL_INTERVAL_SECONDS)
    assert not shutdown.sleep_budget_exceeded
    assert shutdown.sleep_budget == grace_sleep_calls + POST_KILL_REAP_ATTEMPTS
    assert shutdown.received_signals == (signal.SIGTERM, signal.SIGKILL)
    assert shutdown.sleep_call_count == shutdown.sleep_budget
    assert shutdown.monotonic_calls == grace_sleep_calls + 2
    assert shutdown.poll_calls == grace_sleep_calls + POST_KILL_REAP_ATTEMPTS
