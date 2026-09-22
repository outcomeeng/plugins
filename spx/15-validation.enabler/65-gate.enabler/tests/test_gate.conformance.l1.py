"""Level 1 conformance evidence for gate summary JSON shape."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from outcomeeng.validation import (
    AD_HOC_SUMMARY_SCHEMA,
    CHECK_SUMMARY_SCHEMA,
    GATE_SUMMARY_SCHEMA,
    PHASE_PREFLIGHT,
    PRIMITIVE_SUMMARY_SCHEMA,
    RECIPE_AD_HOC,
    RECIPE_VALIDATION,
    SUMMARY_KEY_PHASE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_SKIPPED,
    SUMMARY_KEY_STEPS,
    SUMMARY_KEY_SUMMARY_PATH,
    SUCCESS_EXIT_CODE,
    SUMMARY_PATH_LABEL,
    TEST_RECIPE,
    Step,
    assert_json_schema,
    run,
    run_check,
    run_recipe,
)
from outcomeeng.validation.agent_disable import AGENT_SWITCHES
from outcomeeng_testing.harnesses.gate import (
    FAIL_EXIT_CODE,
    FAILING_CHILD_OUTPUT_PREFIX,
    UNDECLARED_SWITCH,
    RecordingSpawner,
    read_summary,
    single_step_recipe,
    skip_report_observation,
    summary_steps,
)


def test_check_summary_conforms_to_schema_for_primitive_and_wrapper(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "summary.json"
    recipe = single_step_recipe(RECIPE_VALIDATION)
    spawner = RecordingSpawner(exit_codes=[SUCCESS_EXIT_CODE, SUCCESS_EXIT_CODE])
    sink = io.StringIO()

    exit_code = run_check(
        spawner=spawner,
        sink=sink,
        recipes=(recipe,),
        summary_path=summary_path,
    )

    summary = read_summary(summary_path)
    assert_json_schema(summary, CHECK_SUMMARY_SCHEMA)
    assert exit_code == SUCCESS_EXIT_CODE


def test_failed_primitive_summary_conforms_to_schema(tmp_path: Path) -> None:
    summary_path = tmp_path / "failure-summary.json"
    recipe = single_step_recipe(RECIPE_VALIDATION)
    spawner = RecordingSpawner(
        exit_codes=[SUCCESS_EXIT_CODE, FAIL_EXIT_CODE],
        outputs=["", FAILING_CHILD_OUTPUT_PREFIX],
    )
    sink = io.StringIO()

    exit_code = run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=recipe,
        summary_path=summary_path,
    )

    summary = read_summary(summary_path)
    assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert exit_code == FAIL_EXIT_CODE


def test_ad_hoc_run_summary_conforms_to_gate_schema(tmp_path: Path) -> None:
    spawner = RecordingSpawner(exit_codes=[SUCCESS_EXIT_CODE])
    sink = io.StringIO()

    exit_code = run(
        spawner=spawner,
        sink=sink,
        steps=(Step(label="ad-hoc-step", argv=("ad-hoc-step",)),),
    )

    summary_path = Path(sink.getvalue().split(f"{SUMMARY_PATH_LABEL} ")[1].strip())
    summary = read_summary(summary_path)
    assert_json_schema(summary, AD_HOC_SUMMARY_SCHEMA)
    assert_json_schema(summary, GATE_SUMMARY_SCHEMA)
    assert summary[SUMMARY_KEY_RECIPE] == RECIPE_AD_HOC
    assert exit_code == SUCCESS_EXIT_CODE


def test_primitive_summary_schema_requires_summary_path(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary-path-required.json"
    recipe = single_step_recipe(RECIPE_VALIDATION)
    spawner = RecordingSpawner(exit_codes=[SUCCESS_EXIT_CODE, SUCCESS_EXIT_CODE])
    sink = io.StringIO()

    exit_code = run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=recipe,
        summary_path=summary_path,
    )

    summary = read_summary(summary_path)
    summary.pop(SUMMARY_KEY_SUMMARY_PATH)
    with pytest.raises(AssertionError, match=SUMMARY_KEY_SUMMARY_PATH):
        assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert exit_code == SUCCESS_EXIT_CODE


def test_failed_preflight_primitive_summary_conforms_to_schema(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "preflight-failure-summary.json"
    recipe = single_step_recipe(RECIPE_VALIDATION)
    spawner = RecordingSpawner(
        exit_codes=[FAIL_EXIT_CODE],
        outputs=[FAILING_CHILD_OUTPUT_PREFIX],
    )
    sink = io.StringIO()

    exit_code = run_recipe(
        spawner=spawner,
        sink=sink,
        recipe=recipe,
        summary_path=summary_path,
    )

    summary = read_summary(summary_path)
    assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert summary[SUMMARY_KEY_PHASE] == PHASE_PREFLIGHT
    assert exit_code == FAIL_EXIT_CODE


def test_failed_preflight_wrapper_summary_conforms_to_schema(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "preflight-wrapper-summary.json"
    recipe = single_step_recipe(RECIPE_VALIDATION)
    spawner = RecordingSpawner(
        exit_codes=[FAIL_EXIT_CODE],
        outputs=[FAILING_CHILD_OUTPUT_PREFIX],
    )
    sink = io.StringIO()

    exit_code = run_check(
        spawner=spawner,
        sink=sink,
        recipes=(recipe,),
        summary_path=summary_path,
    )

    summary = read_summary(summary_path)
    assert_json_schema(summary, CHECK_SUMMARY_SCHEMA)
    assert summary[SUMMARY_KEY_PHASE] == PHASE_PREFLIGHT
    assert exit_code == FAIL_EXIT_CODE


def test_summary_with_declared_skips_conforms_to_schema() -> None:
    observation = skip_report_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE]
        * (len(TEST_RECIPE.preflight_steps) + len(TEST_RECIPE.steps)),
        switches=AGENT_SWITCHES,
    )
    steps = observation.summary[SUMMARY_KEY_STEPS]
    assert isinstance(steps, list)

    assert_json_schema(observation.summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert any(SUMMARY_KEY_SKIPPED in step for step in steps)
    assert observation.exit_code == SUCCESS_EXIT_CODE


def test_a_report_line_outside_the_declared_switches_leaves_the_summary_conforming() -> (
    None
):
    observation = skip_report_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE]
        * (len(TEST_RECIPE.preflight_steps) + len(TEST_RECIPE.steps)),
        switches=(*AGENT_SWITCHES, UNDECLARED_SWITCH),
    )

    assert UNDECLARED_SWITCH not in AGENT_SWITCHES
    assert_json_schema(observation.summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert observation.exit_code == SUCCESS_EXIT_CODE


def test_a_step_carrying_the_skip_key_and_no_row_fails_the_schema() -> None:
    observation = skip_report_observation(
        recipe=TEST_RECIPE,
        exit_codes=[SUCCESS_EXIT_CODE]
        * (len(TEST_RECIPE.preflight_steps) + len(TEST_RECIPE.steps)),
        switches=AGENT_SWITCHES,
    )
    emptied = 0
    for step in summary_steps(observation.summary):
        if SUMMARY_KEY_SKIPPED in step:
            step[SUMMARY_KEY_SKIPPED] = []
            emptied += 1

    with pytest.raises(AssertionError, match=SUMMARY_KEY_SKIPPED):
        assert_json_schema(observation.summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert emptied > 0
    assert observation.exit_code == SUCCESS_EXIT_CODE
