"""Level 1 compliance tests for the gate orchestrator."""

from __future__ import annotations

import ast
from pathlib import Path
import math
import signal

from outcomeeng.validation._spawner import _restore_child_signal_mask
from outcomeeng.validation.polling_enforcement import (
    SLEEP_ATTRIBUTE,
    WATCH_INVOCATION,
    unbounded_polling_sites,
)
from outcomeeng.validation import (
    CHECK_RECIPES,
    EVAL_LINKS_ARGV,
    FMT_CHECK_ARGV,
    HOOK_SAFETY_ARGV,
    MYPY_ARGV,
    POST_KILL_REAP_ATTEMPTS,
    PURPOSE_CONFORMANCE,
    PYRIGHT_ARGV,
    PYTEST_STEP_LABEL,
    PURPOSE_CORRECTNESS,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    RUN_PASS_STATUS,
    SIGNAL_GRACE_SECONDS,
    SIGNAL_POLL_INTERVAL_SECONDS,
    SKIP_LINE_FORM,
    SPX_MARKDOWN_ARGV,
    STEP_SKIP_STATUS,
    STEP_STATUS_PREFIX_FORM,
    SUMMARY_KEY_PURPOSE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_SKIPPED,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
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
from outcomeeng.validation.agent_disable import (
    AGENT_SWITCHES,
    SKIP_REPORT_SWITCH_FIELD,
    SKIP_REPORT_TEST_FIELD,
)
from outcomeeng_testing.harnesses.gate import (
    HIGH_VOLUME_CHILD_OUTPUT,
    skip_report_observation,
    PASS_EXIT_CODE,
    PYTEST_TARGET_ARG,
    bounded_shutdown_observation,
    call_keyword_map,
    check_run_observation,
    validation_package_modules,
    popen_calls_from,
    recipe_run_observation,
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
    assert MYPY_ARGV in step_argvs
    assert PYRIGHT_ARGV in step_argvs
    assert SPX_MARKDOWN_ARGV in step_argvs
    assert EVAL_LINKS_ARGV in step_argvs
    assert HOOK_SAFETY_ARGV in step_argvs
    assert PYTEST_ARGV not in step_argvs
    assert TEST_STEPS == (Step(label=PYTEST_STEP_LABEL, argv=PYTEST_ARGV),)


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
        Step(label=PYTEST_STEP_LABEL, argv=(*PYTEST_ARGV, PYTEST_TARGET_ARG)),
    )


def test_the_check_wrapper_reports_no_verification_type() -> None:
    run = check_run_observation(
        recipes=(VALIDATION_RECIPE,),
        exit_codes=[PASS_EXIT_CODE]
        * (len(VALIDATION_RECIPE.preflight_steps) + len(VALIDATION_RECIPE.steps)),
    )

    assert run.exit_code == PASS_EXIT_CODE
    assert run.summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
    assert run.summary[SUMMARY_KEY_VERIFICATION_TYPE] is None
    assert run.summary[SUMMARY_KEY_PURPOSE] is None


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
        assert preexec_fn.id == _restore_child_signal_mask.__name__
    assert f"signal.{signal.pthread_sigmask.__name__}(signal.SIG_UNBLOCK" in source
    for signal_name in ("SIGTERM", "SIGINT", "SIGHUP"):
        assert f"signal.{signal_name}" in source


def test_no_gate_module_polls_without_bound() -> None:
    assert unbounded_polling_sites(validation_package_modules()) == ()


def test_a_while_true_sleep_is_reported(tmp_path: Path) -> None:
    offender = tmp_path / "poller.py"
    offender.write_text(
        f"import time\n\n\ndef run() -> None:\n"
        f"    while True:\n        time.{SLEEP_ATTRIBUTE}(1)\n",
        encoding="utf-8",
    )

    reported = unbounded_polling_sites((offender,))

    assert len(reported) == 1
    assert str(offender) in reported[0]


def test_a_watch_invocation_is_reported(tmp_path: Path) -> None:
    offender = tmp_path / "watcher.py"
    offender.write_text(f'COMMAND = "{WATCH_INVOCATION}"\n', encoding="utf-8")

    assert unbounded_polling_sites((offender,)) == (f"{offender}::{WATCH_INVOCATION}",)


def test_a_bounded_loop_is_not_reported(tmp_path: Path) -> None:
    conforming = tmp_path / "bounded.py"
    conforming.write_text(
        f"import time\n\n\ndef run(deadline: float) -> None:\n"
        f"    while deadline > 0:\n        time.{SLEEP_ATTRIBUTE}(1)\n"
        f"        deadline -= 1\n",
        encoding="utf-8",
    )

    assert unbounded_polling_sites((conforming,)) == ()


def test_signal_shutdown_waits_are_bounded() -> None:
    shutdown = bounded_shutdown_observation()

    grace_sleep_calls = math.ceil(SIGNAL_GRACE_SECONDS / SIGNAL_POLL_INTERVAL_SECONDS)
    assert shutdown.sleep_budget == grace_sleep_calls + POST_KILL_REAP_ATTEMPTS
    assert shutdown.received_signals == (signal.SIGTERM, signal.SIGKILL)
    assert shutdown.sleep_call_count == shutdown.sleep_budget
    assert shutdown.monotonic_calls == grace_sleep_calls + 2
    assert shutdown.poll_calls == grace_sleep_calls + POST_KILL_REAP_ATTEMPTS


def test_declared_skips_are_named_in_the_summary_and_after_the_status_line() -> None:
    observation = skip_report_observation(
        recipe=TEST_RECIPE,
        exit_codes=[PASS_EXIT_CODE] * (len(TEST_RECIPE.preflight_steps) + 1),
        switches=AGENT_SWITCHES,
    )
    steps = observation.summary[SUMMARY_KEY_STEPS]
    assert isinstance(steps, list)
    recorded = [step for step in steps if SUMMARY_KEY_SKIPPED in step]

    assert observation.written_records
    assert observation.recording_steps == 1
    assert len(recorded) == observation.recording_steps
    assert [step[SUMMARY_KEY_SKIPPED] for step in recorded] == [
        list(observation.written_records)
    ] * observation.recording_steps
    assert all(step[SUMMARY_KEY_STATUS] == RUN_PASS_STATUS for step in recorded)
    status_at = observation.output.index(
        STEP_STATUS_PREFIX_FORM.format(
            status=RUN_PASS_STATUS.upper(), label=PYTEST_STEP_LABEL
        )
    )
    for record in observation.written_records:
        line = SKIP_LINE_FORM.format(
            status=STEP_SKIP_STATUS,
            test=record[SKIP_REPORT_TEST_FIELD],
            switch=record[SKIP_REPORT_SWITCH_FIELD],
        )
        assert line in observation.output
        assert observation.output.index(line) > status_at


def test_a_run_without_declared_skips_carries_no_skipped_entry() -> None:
    observation = recipe_run_observation(
        recipe=TEST_RECIPE,
        exit_codes=[PASS_EXIT_CODE] * (len(TEST_RECIPE.preflight_steps) + 1),
    )
    steps = observation.summary[SUMMARY_KEY_STEPS]
    assert isinstance(steps, list)

    assert all(SUMMARY_KEY_SKIPPED not in step for step in steps)
    assert STEP_SKIP_STATUS not in observation.output
