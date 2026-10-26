"""Level 1 conformance evidence for gate summary JSON shape."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    AD_HOC_SUMMARY_SCHEMA,
    CHECK_SUMMARY_SCHEMA,
    GATE_SUMMARY_SCHEMA,
    PHASE_PREFLIGHT,
    PRIMITIVE_SUMMARY_SCHEMA,
    PURPOSE_CONFORMANCE,
    RECIPE_AD_HOC,
    RECIPE_VALIDATION,
    SUMMARY_KEY_SUMMARY_PATH,
    VERIFICATION_TYPE_VALIDATION,
    Recipe,
    Step,
    assert_json_schema,
)
from outcomeeng_testing.harnesses.gate import (
    check_run_observation,
    pipeline_run_observation,
    recipe_run_observation,
)

PASS = 0
FAIL = 2
FAILING_OUTPUT = "failure detail"


def _recipe() -> Recipe:
    return Recipe(
        name=RECIPE_VALIDATION,
        verification_type=VERIFICATION_TYPE_VALIDATION,
        purpose=PURPOSE_CONFORMANCE,
        preflight_steps=(Step(label="preflight", argv=("preflight",)),),
        steps=(Step(label="validate", argv=("validate",)),),
    )


def test_check_summary_conforms_to_schema_for_primitive_and_wrapper() -> None:
    observation = check_run_observation(recipes=(_recipe(),), exit_codes=[PASS, PASS])

    assert_json_schema(observation.summary, CHECK_SUMMARY_SCHEMA)
    assert observation.exit_code == PASS


def test_failed_primitive_summary_conforms_to_schema() -> None:
    observation = recipe_run_observation(
        recipe=_recipe(),
        exit_codes=[PASS, FAIL],
        outputs=["", FAILING_OUTPUT],
    )

    assert_json_schema(observation.summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert observation.exit_code == FAIL


def test_ad_hoc_run_summary_conforms_to_gate_schema() -> None:
    observation = pipeline_run_observation(
        steps=(Step(label="ad-hoc-step", argv=("ad-hoc-step",)),),
        exit_codes=[PASS],
    )

    summary = observation.summary
    assert_json_schema(summary, AD_HOC_SUMMARY_SCHEMA)
    assert_json_schema(summary, GATE_SUMMARY_SCHEMA)
    assert summary["recipe"] == RECIPE_AD_HOC
    assert observation.exit_code == PASS


def test_primitive_summary_schema_requires_summary_path() -> None:
    observation = recipe_run_observation(recipe=_recipe(), exit_codes=[PASS, PASS])

    summary = dict(observation.summary)
    summary.pop(SUMMARY_KEY_SUMMARY_PATH)
    with pytest.raises(AssertionError, match=SUMMARY_KEY_SUMMARY_PATH):
        assert_json_schema(summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert observation.exit_code == PASS


def test_failed_preflight_primitive_summary_conforms_to_schema() -> None:
    observation = recipe_run_observation(
        recipe=_recipe(), exit_codes=[FAIL], outputs=[FAILING_OUTPUT]
    )

    assert_json_schema(observation.summary, PRIMITIVE_SUMMARY_SCHEMA)
    assert observation.summary["phase"] == PHASE_PREFLIGHT
    assert observation.exit_code == FAIL


def test_failed_preflight_wrapper_summary_conforms_to_schema() -> None:
    observation = check_run_observation(
        recipes=(_recipe(),), exit_codes=[FAIL], outputs=[FAILING_OUTPUT]
    )

    assert_json_schema(observation.summary, CHECK_SUMMARY_SCHEMA)
    assert observation.summary["phase"] == PHASE_PREFLIGHT
    assert observation.exit_code == FAIL
