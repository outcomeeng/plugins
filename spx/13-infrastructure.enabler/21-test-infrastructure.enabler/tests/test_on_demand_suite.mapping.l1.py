"""Mapping evidence for the explicit command that runs the on-demand suite."""

from __future__ import annotations

from outcomeeng.validation import (
    ON_DEMAND_LEVEL,
    PYTEST_ARGV,
    Step,
    on_demand_recipe,
    test_recipe as direct_test_recipe,
)
from outcomeeng_testing.generators.gate import GeneratedTestFile
from outcomeeng_testing.harnesses.gate import on_demand_suite_property


@on_demand_suite_property
def _the_on_demand_recipe_targets_exactly_the_on_demand_files(
    test_files: list[GeneratedTestFile],
) -> None:
    expected = sorted(
        test_file.path for test_file in test_files if test_file.level == ON_DEMAND_LEVEL
    )

    recipe = on_demand_recipe([test_file.path for test_file in test_files])

    assert recipe.steps == (
        (Step(label="pytest", argv=(*PYTEST_ARGV, *expected)),) if expected else ()
    )


@on_demand_suite_property
def _a_direct_target_naming_an_on_demand_file_keeps_it(
    test_files: list[GeneratedTestFile],
) -> None:
    named = [
        test_file.path for test_file in test_files if test_file.level == ON_DEMAND_LEVEL
    ]

    recipe = direct_test_recipe(named)

    assert recipe.steps[0].argv[len(PYTEST_ARGV) :] == tuple(named)


def test_the_on_demand_recipe_targets_exactly_the_on_demand_files() -> None:
    _the_on_demand_recipe_targets_exactly_the_on_demand_files()


def test_a_direct_target_naming_an_on_demand_file_keeps_it() -> None:
    _a_direct_target_naming_an_on_demand_file_keeps_it()
