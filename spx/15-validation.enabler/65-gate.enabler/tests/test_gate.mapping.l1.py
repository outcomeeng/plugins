"""Level 1 mapping evidence for the gate recipe contracts."""

from __future__ import annotations

from outcomeeng.validation import (
    CHECK_RECIPES,
    FMT_CHECK_ARGV,
    HOOK_SAFETY_ARGV,
    MYPY_ARGV,
    PURPOSE_CONFORMANCE,
    PURPOSE_CORRECTNESS,
    PYTEST_ARGV,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SPX_MARKDOWN_ARGV,
    Step,
    TEST_STEPS,
    VALIDATION_STEPS,
    VERIFICATION_TYPE_TESTING,
    VERIFICATION_TYPE_VALIDATION,
    test_recipe,
)
from outcomeeng_testing.harnesses.gate import (
    PYTEST_TARGET_ARG,
    STATIC_ANALYSIS_ARGVS,
)


def test_primitive_recipe_maps_to_its_command_surface() -> None:
    recipes = {recipe.name: recipe for recipe in CHECK_RECIPES}

    assert len(recipes) == len(CHECK_RECIPES) == 2
    validation = recipes[RECIPE_VALIDATION]
    test = recipes[RECIPE_TEST]
    validation_argvs = {step.argv for step in validation.steps}

    assert validation.steps == VALIDATION_STEPS
    assert FMT_CHECK_ARGV in validation_argvs
    assert RUFF_FORMAT_ARGV in validation_argvs
    assert RUFF_CHECK_ARGV in validation_argvs
    assert set(STATIC_ANALYSIS_ARGVS).issubset(validation_argvs)
    assert "--strict" in MYPY_ARGV
    assert SPX_MARKDOWN_ARGV in validation_argvs
    assert HOOK_SAFETY_ARGV in validation_argvs
    assert PYTEST_ARGV not in validation_argvs
    assert test.steps == TEST_STEPS == (Step(label="pytest", argv=PYTEST_ARGV),)


def test_primitive_recipe_maps_to_its_verification_contract() -> None:
    recipes = {recipe.name: recipe for recipe in CHECK_RECIPES}
    validation = recipes[RECIPE_VALIDATION]
    test = recipes[RECIPE_TEST]

    assert validation.verification_type == VERIFICATION_TYPE_VALIDATION
    assert validation.purpose == PURPOSE_CONFORMANCE
    assert test.verification_type == VERIFICATION_TYPE_TESTING
    assert test.purpose == PURPOSE_CORRECTNESS

    targeted = test_recipe((PYTEST_TARGET_ARG,))
    assert targeted.name == test.name
    assert targeted.verification_type == test.verification_type
    assert targeted.purpose == test.purpose
    assert targeted.preflight_steps == test.preflight_steps
    assert targeted.steps == (
        Step(label="pytest", argv=(*PYTEST_ARGV, PYTEST_TARGET_ARG)),
    )
