"""Mapping evidence for the explicit command that runs the on-demand suite."""

from __future__ import annotations

import pytest

import outcomeeng.validation.__main__ as validation_entry
from outcomeeng.validation import (
    EXECUTION_LEVELS,
    ON_DEMAND_LEVEL,
    PYTEST_ARGV,
    RECIPE_TEST_ON_DEMAND,
    Step,
    on_demand_recipe,
    test_recipe as direct_test_recipe,
)
from outcomeeng_testing.generators.gate import (
    on_demand_decoy_files,
    on_demand_fixture_files,
)
from outcomeeng_testing.harnesses.on_demand_collection import (
    fixture_collection,
    justfile_recipe_command,
    on_demand_dispatch_spawns,
    pytest_argument_tail,
)

PYTHON_COMMAND = "python3"
PYTHON_MODULE_FLAG = "-m"


@pytest.mark.parametrize("level", EXECUTION_LEVELS)
def test_the_on_demand_recipe_targets_a_file_exactly_when_it_carries_the_on_demand_level(
    level: str,
) -> None:
    files = tuple(
        test_file.path
        for test_file in on_demand_fixture_files()
        if test_file.level == level
    )
    expected = tuple(sorted(files)) if level == ON_DEMAND_LEVEL else ()

    recipe = on_demand_recipe(files)

    assert files
    assert recipe.steps == (
        (Step(label="pytest", argv=(*PYTEST_ARGV, *expected)),) if expected else ()
    )


@pytest.mark.parametrize("level", EXECUTION_LEVELS)
def test_a_direct_target_keeps_every_file_it_names_whatever_its_level(
    level: str,
) -> None:
    named = tuple(
        test_file.path
        for test_file in on_demand_fixture_files()
        if test_file.level == level
    )

    (step,) = direct_test_recipe(named).steps

    assert step.argv[len(PYTEST_ARGV) :] == named


def test_the_dispatch_collects_exactly_the_on_demand_files_of_a_repository() -> None:
    fixture = on_demand_fixture_files()
    expected = frozenset(
        test_file.path for test_file in fixture if test_file.level == ON_DEMAND_LEVEL
    )

    spawns = on_demand_dispatch_spawns((*fixture, *on_demand_decoy_files()))
    (pytest_call,) = (
        call for call in spawns if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )
    collection = fixture_collection(fixture, pytest_argument_tail(pytest_call))

    assert expected
    assert frozenset(pytest_call[len(PYTEST_ARGV) :]) == expected
    assert collection.exit_code == 0, collection.output
    assert collection.collected_files == expected


def test_the_justfile_recipe_runs_the_on_demand_dispatch() -> None:
    assert justfile_recipe_command(RECIPE_TEST_ON_DEMAND) == (
        PYTHON_COMMAND,
        PYTHON_MODULE_FLAG,
        str(validation_entry.__package__),
        RECIPE_TEST_ON_DEMAND,
    )
