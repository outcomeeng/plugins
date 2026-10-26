"""Level 1 conformance evidence for gate summary JSON shape."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    AD_HOC_SUMMARY_SCHEMA,
    CHECK_SUMMARY_SCHEMA,
    GATE_SUMMARY_SCHEMA,
    PHASE_PREFLIGHT,
    PRIMITIVE_SUMMARY_SCHEMA,
    RECIPE_AD_HOC,
    SPAWN_FAILURE_EXIT_CODE,
    SUMMARY_KEY_PHASE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_SUMMARY_PATH,
    VALIDATION_RECIPE,
    assert_json_schema,
)
from outcomeeng_testing.harnesses.gate import (
    PASS_EXIT_CODE,
    check_run_observation,
    pipeline_run_observation,
    recipe_run_observation,
)

FAIL = SPAWN_FAILURE_EXIT_CODE
RECIPE_STEP_COUNT = len(VALIDATION_RECIPE.preflight_steps) + len(
    VALIDATION_RECIPE.steps
)


def test_check_summary_conforms_to_schema_for_primitive_and_wrapper() -> None:
    observation = check_run_observation(
        recipes=(VALIDATION_RECIPE,), exit_codes=[PASS_EXIT_CODE] * RECIPE_STEP_COUNT
    )

    assert_json_schema(observation.summary, CHECK_SUMMARY_SCHEMA)
    assert observation.exit_code == PASS_EXIT_CODE


def test_failed_primitive_summary_conforms_to_schema() -> None:
    observation = recipe_run_observation(
        recipe=VALIDATION_RECIPE,
        exit_codes=[PASS_EXIT_CODE] * len(VALIDATION_RECIPE.preflight_steps) + [FAIL],
    )

    assert_json_schema(observation.summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert observation.exit_code == FAIL


def test_ad_hoc_run_summary_conforms_to_gate_schema() -> None:
    steps = VALIDATION_RECIPE.steps
    observation = pipeline_run_observation(
        steps=steps, exit_codes=[PASS_EXIT_CODE] * len(steps)
    )

    summary = observation.summary
    assert_json_schema(summary, AD_HOC_SUMMARY_SCHEMA)
    assert_json_schema(summary, GATE_SUMMARY_SCHEMA)
    assert summary[SUMMARY_KEY_RECIPE] == RECIPE_AD_HOC
    assert observation.exit_code == PASS_EXIT_CODE


def test_primitive_summary_schema_requires_summary_path() -> None:
    observation = recipe_run_observation(
        recipe=VALIDATION_RECIPE, exit_codes=[PASS_EXIT_CODE] * RECIPE_STEP_COUNT
    )

    summary = dict(observation.summary)
    summary.pop(SUMMARY_KEY_SUMMARY_PATH)
    with pytest.raises(AssertionError, match=SUMMARY_KEY_SUMMARY_PATH):
        assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert observation.exit_code == PASS_EXIT_CODE


def test_failed_preflight_primitive_summary_conforms_to_schema() -> None:
    observation = recipe_run_observation(recipe=VALIDATION_RECIPE, exit_codes=[FAIL])

    assert_json_schema(observation.summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert observation.summary[SUMMARY_KEY_PHASE] == PHASE_PREFLIGHT
    assert observation.exit_code == FAIL


def test_failed_preflight_wrapper_summary_conforms_to_schema() -> None:
    observation = check_run_observation(recipes=(VALIDATION_RECIPE,), exit_codes=[FAIL])

    assert_json_schema(observation.summary, CHECK_SUMMARY_SCHEMA)
    assert observation.summary[SUMMARY_KEY_PHASE] == PHASE_PREFLIGHT
    assert observation.exit_code == FAIL
