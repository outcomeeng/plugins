"""Level 1 compliance tests for the gate orchestrator."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import math
import signal

import pytest

from outcomeeng.validation._spawner import _restore_child_signal_mask
from outcomeeng.validation.polling_enforcement import (
    SLEEP_ATTRIBUTE,
    SLEEP_MODULE,
    WATCH_INVOCATION,
    unbounded_polling_sites,
)
from outcomeeng.validation import (
    CHECK_RECIPES,
    EVAL_LINKS_ARGV,
    FMT_CHECK_ARGV,
    FORWARDED_SIGNALS,
    HOOK_SAFETY_ARGV,
    MYPY_ARGV,
    ORCHESTRATOR_MODULE_NAMES,
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
    STEP_PASS_STATUS,
    STEP_SKIP_STATUS,
    STEP_STATUS_PREFIX_FORM,
    SUCCESS_EXIT_CODE,
    SUMMARY_KEY_PURPOSE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_SKIPPED,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
    SUMMARY_KEY_VERIFICATION_TYPE,
    Step,
    TEST_RECIPE,
    TEST_STEPS,
    TIMING_DIVIDER,
    TIMING_SUMMARY_BANNER,
    TimingBlockNotBounded,
    VALIDATION_RECIPE,
    VALIDATION_STEPS,
    VERIFICATION_TYPE_TESTING,
    VERIFICATION_TYPE_VALIDATION,
    test_recipe as build_test_recipe,
    timing_row_values,
)
from outcomeeng.validation.agent_disable import AGENT_SWITCHES
from outcomeeng.validation.skip_report import (
    SKIP_REPORT_SWITCH_FIELD,
    SKIP_REPORT_TEST_FIELD,
)
from outcomeeng_testing.harnesses.gate import (
    CHILD_OUTPUT_LINE,
    HIGH_VOLUME_CHILD_LINES,
    HIGH_VOLUME_CHILD_OUTPUT,
    LOW_VOLUME_CHILD_OUTPUT,
    UNDECLARED_SWITCH,
    OrchestratorModuleAbsent,
    SleepBudgetExhausted,
    UnconfinedDisposableState,
    confined_to,
    declared_skip_recording,
    timing_block_observation,
    skip_report_observation,
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
        exit_codes=[SUCCESS_EXIT_CODE]
        * (len(VALIDATION_RECIPE.preflight_steps) + len(VALIDATION_RECIPE.steps)),
    )

    assert run.exit_code == SUCCESS_EXIT_CODE
    assert run.summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
    assert run.summary[SUMMARY_KEY_VERIFICATION_TYPE] is None
    assert run.summary[SUMMARY_KEY_PURPOSE] is None


def test_child_output_is_captured_never_streamed() -> None:
    run = recipe_run_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE, SUCCESS_EXIT_CODE],
        outputs=[HIGH_VOLUME_CHILD_OUTPUT, HIGH_VOLUME_CHILD_OUTPUT],
    )

    assert run.exit_code == SUCCESS_EXIT_CODE
    assert HIGH_VOLUME_CHILD_OUTPUT not in run.output
    assert len(run.output.splitlines()) < len(HIGH_VOLUME_CHILD_OUTPUT.splitlines())


def test_live_output_grows_with_step_count_not_child_output_volume() -> None:
    quiet = recipe_run_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE, SUCCESS_EXIT_CODE],
        outputs=[LOW_VOLUME_CHILD_OUTPUT, LOW_VOLUME_CHILD_OUTPUT],
    )
    loud = recipe_run_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE, SUCCESS_EXIT_CODE],
        outputs=[HIGH_VOLUME_CHILD_OUTPUT, HIGH_VOLUME_CHILD_OUTPUT],
    )

    assert CHILD_OUTPUT_LINE not in loud.output, (
        "no child output line reaches the live sink, capped prefix included"
    )
    quiet_lines = len(quiet.output.splitlines())
    loud_lines = len(loud.output.splitlines())
    assert quiet_lines == loud_lines, (
        f"{HIGH_VOLUME_CHILD_LINES}x the child output changed the live output "
        f"from {quiet_lines} lines to {loud_lines}"
    )
    steps = len(TEST_RECIPE.preflight_steps) + len(TEST_RECIPE.steps)
    assert (
        sum(line.startswith(STEP_PASS_STATUS) for line in quiet.output.splitlines())
        == steps
    )


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
    for forwarded in FORWARDED_SIGNALS:
        assert f"signal.{forwarded.name}" in source


def test_no_gate_module_polls_without_bound() -> None:
    assert unbounded_polling_sites(validation_package_modules()) == ()


def test_an_absent_enumerated_orchestrator_module_is_refused(tmp_path: Path) -> None:
    with pytest.raises(OrchestratorModuleAbsent) as raised:
        validation_package_modules(package_dir=tmp_path)

    assert raised.value.path.parent == tmp_path
    assert raised.value.path.name in ORCHESTRATOR_MODULE_NAMES


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


def test_a_while_true_name_bound_sleep_is_reported(tmp_path: Path) -> None:
    offender = tmp_path / "name_poller.py"
    offender.write_text(
        f"from {SLEEP_MODULE} import {SLEEP_ATTRIBUTE}\n\n\ndef run() -> None:\n"
        f"    while True:\n        {SLEEP_ATTRIBUTE}(1)\n",
        encoding="utf-8",
    )

    reported = unbounded_polling_sites((offender,))

    assert len(reported) == 1
    assert str(offender) in reported[0]


def test_a_loop_calling_its_own_same_named_function_is_not_reported(
    tmp_path: Path,
) -> None:
    conforming = tmp_path / "own_sleep.py"
    conforming.write_text(
        f"def {SLEEP_ATTRIBUTE}(count: int) -> int:\n    return count - 1\n\n\n"
        f"def run(count: int) -> None:\n"
        f"    while True:\n        count = {SLEEP_ATTRIBUTE}(count)\n"
        f"        if count == 0:\n            return None\n",
        encoding="utf-8",
    )

    assert unbounded_polling_sites((conforming,)) == ()


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


def test_a_shutdown_past_its_sleep_budget_is_refused_by_name() -> None:
    short_budget = bounded_shutdown_observation().sleep_budget - 1

    with pytest.raises(SleepBudgetExhausted) as raised:
        bounded_shutdown_observation(sleep_budget=short_budget)

    assert raised.value.budget == short_budget
    assert raised.value.sleep_calls == short_budget


def test_declared_skips_are_named_in_the_summary_and_after_the_status_line() -> None:
    observation = skip_report_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE] * (len(TEST_RECIPE.preflight_steps) + 1),
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
        STEP_STATUS_PREFIX_FORM.format(status=STEP_PASS_STATUS, label=PYTEST_STEP_LABEL)
    )
    for record in observation.written_records:
        line = SKIP_LINE_FORM.format(
            status=STEP_SKIP_STATUS,
            test=record[SKIP_REPORT_TEST_FIELD],
            switch=record[SKIP_REPORT_SWITCH_FIELD],
        )
        assert line in observation.output
        assert observation.output.index(line) > status_at


def test_a_report_line_naming_an_undeclared_switch_reaches_no_summary_row() -> None:
    observation = skip_report_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE] * (len(TEST_RECIPE.preflight_steps) + 1),
        switches=(*AGENT_SWITCHES, UNDECLARED_SWITCH),
    )
    declared = [
        record
        for record in observation.written_records
        if record[SKIP_REPORT_SWITCH_FIELD] in AGENT_SWITCHES
    ]
    refused = [
        record
        for record in observation.written_records
        if record[SKIP_REPORT_SWITCH_FIELD] not in AGENT_SWITCHES
    ]
    steps = observation.summary[SUMMARY_KEY_STEPS]
    assert isinstance(steps, list)
    recorded = [step for step in steps if SUMMARY_KEY_SKIPPED in step]

    assert declared
    assert refused
    assert observation.recording_steps == 1
    assert len(recorded) == observation.recording_steps
    assert [step[SUMMARY_KEY_SKIPPED] for step in recorded] == [declared] * len(
        recorded
    )
    for record in refused:
        assert record[SKIP_REPORT_TEST_FIELD] not in json.dumps(observation.summary)
        assert record[SKIP_REPORT_TEST_FIELD] not in observation.output
    for record in declared:
        assert (
            SKIP_LINE_FORM.format(
                status=STEP_SKIP_STATUS,
                test=record[SKIP_REPORT_TEST_FIELD],
                switch=record[SKIP_REPORT_SWITCH_FIELD],
            )
            in observation.output
        )


def test_the_row_reader_reads_every_step_row_of_a_complete_block() -> None:
    observation = timing_block_observation()

    values = timing_row_values(observation.output)

    assert len(values) == observation.step_count
    assert all(value >= 0 for value in values)


def test_the_row_reader_refuses_a_block_missing_either_bound() -> None:
    observation = timing_block_observation()

    for text, missing in (
        (observation.without_banner, TIMING_SUMMARY_BANNER),
        (observation.without_divider, TIMING_DIVIDER),
    ):
        with pytest.raises(TimingBlockNotBounded) as raised:
            timing_row_values(text)

        assert raised.value.missing == missing


def test_a_real_child_records_each_declared_skip_with_its_own_switch() -> None:
    with declared_skip_recording() as recording:
        records = [json.loads(line) for line in recording.recorded_lines]

        assert recording.exit_code == SUCCESS_EXIT_CODE, recording.output
        assert [sorted(record) for record in records] == [
            sorted((SKIP_REPORT_TEST_FIELD, SKIP_REPORT_SWITCH_FIELD))
        ] * len(recording.switch_rows)
        assert {
            (record[SKIP_REPORT_TEST_FIELD], record[SKIP_REPORT_SWITCH_FIELD])
            for record in records
        } == set(recording.switch_rows)
        assert not [
            record
            for record in records
            if record[SKIP_REPORT_TEST_FIELD] in recording.other_rows
        ]


def test_a_real_child_records_a_marker_bearing_row_with_its_own_switch() -> None:
    with declared_skip_recording(through_markers=True) as recording:
        records = [json.loads(line) for line in recording.recorded_lines]

        assert recording.exit_code == SUCCESS_EXIT_CODE, recording.output
        assert {
            (record[SKIP_REPORT_TEST_FIELD], record[SKIP_REPORT_SWITCH_FIELD])
            for record in records
        } == set(recording.switch_rows)
        assert not [
            record
            for record in records
            if record[SKIP_REPORT_TEST_FIELD] in recording.other_rows
        ]


def test_a_real_child_records_nothing_when_no_destination_is_named() -> None:
    with declared_skip_recording(name_destination=False) as recording:
        assert recording.exit_code == SUCCESS_EXIT_CODE, recording.output
        assert recording.recorded_lines == ()
        assert not recording.destination.exists()


def test_a_confined_recording_run_proceeds_inside_its_own_disposable_root() -> None:
    with declared_skip_recording() as recording:
        assert recording.exit_code == SUCCESS_EXIT_CODE, recording.output
        assert recording.child_reported_directory == recording.state_root.resolve()
        assert recording.child_reported_directory in recording.confinement_checked
        assert recording.destination.resolve() in recording.confinement_checked

    assert not recording.state_root.exists()


def test_an_unconfined_target_is_refused_by_name(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"

    with pytest.raises(UnconfinedDisposableState) as raised:
        confined_to(root, outside)

    assert raised.value.path == outside.resolve()
    assert raised.value.root == root.resolve()


def test_a_run_without_declared_skips_carries_no_skipped_entry() -> None:
    observation = recipe_run_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE] * (len(TEST_RECIPE.preflight_steps) + 1),
    )
    steps = observation.summary[SUMMARY_KEY_STEPS]
    assert isinstance(steps, list)

    assert all(SUMMARY_KEY_SKIPPED not in step for step in steps)
    assert STEP_SKIP_STATUS not in observation.output
