"""Mapping evidence for the explicit command that runs the L3 tests."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    EXECUTION_LEVELS,
    L3_LEVEL,
    PYTEST_ARGV,
    RECIPE_TEST,
    RECIPE_TEST_L3,
    VALIDATION_ENTRY_COMMAND,
    l3_recipe,
    test_recipe as direct_test_recipe,
)
from outcomeeng_testing.generators.gate import (
    l3_decoy_files,
    l3_fixture_files,
)
from outcomeeng_testing.harnesses.l3_collection import (
    fixture_collection,
    justfile_recipe_dispatch,
    pytest_argument_tail,
    recipe_dispatch_spawns,
)

L3_FIXTURE_PATHS = tuple(
    test_file.path for test_file in l3_fixture_files() if test_file.level == L3_LEVEL
)


@pytest.mark.parametrize("level", EXECUTION_LEVELS)
def test_the_l3_recipe_targets_a_file_exactly_when_it_carries_the_l3_level(
    level: str,
) -> None:
    files = tuple(
        test_file.path for test_file in l3_fixture_files() if test_file.level == level
    )

    recipe = l3_recipe(files)

    assert files
    if level == L3_LEVEL:
        (step,) = recipe.steps
        assert frozenset(step.argv[len(PYTEST_ARGV) :]) == frozenset(files)
    else:
        assert recipe.steps == ()


@pytest.mark.parametrize("level", EXECUTION_LEVELS)
def test_a_direct_target_keeps_every_file_it_names_whatever_its_level(
    level: str,
) -> None:
    named = tuple(
        test_file.path for test_file in l3_fixture_files() if test_file.level == level
    )

    (step,) = direct_test_recipe(named).steps

    assert frozenset(step.argv[len(PYTEST_ARGV) :]) == frozenset(named)


def test_the_dispatch_collects_exactly_the_l3_files_of_a_repository() -> None:
    fixture = l3_fixture_files()
    expected = frozenset(
        test_file.path for test_file in fixture if test_file.level == L3_LEVEL
    )

    spawns = recipe_dispatch_spawns((RECIPE_TEST_L3,), (*fixture, *l3_decoy_files()))
    (pytest_call,) = (
        call for call in spawns if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )
    collection = fixture_collection(fixture, pytest_argument_tail(pytest_call))

    assert expected
    assert frozenset(pytest_call[len(PYTEST_ARGV) :]) == expected
    assert collection.exit_code == 0, collection.output
    assert collection.collected_files == expected


def test_the_justfile_recipe_runs_the_l3_dispatch() -> None:
    dispatch = justfile_recipe_dispatch(RECIPE_TEST_L3)

    assert dispatch.entry == VALIDATION_ENTRY_COMMAND
    assert dispatch.recipe_words == (RECIPE_TEST_L3,)


@pytest.mark.parametrize("named", L3_FIXTURE_PATHS)
def test_the_justfile_test_recipe_forwards_a_named_file_to_the_test_dispatch(
    named: str,
) -> None:
    fixture = l3_fixture_files()
    dispatch = justfile_recipe_dispatch(RECIPE_TEST, named)

    assert dispatch.entry == VALIDATION_ENTRY_COMMAND
    spawns = recipe_dispatch_spawns(dispatch.recipe_words, fixture)
    (pytest_call,) = (
        call for call in spawns if call[: len(PYTEST_ARGV)] == PYTEST_ARGV
    )
    collection = fixture_collection(fixture, pytest_argument_tail(pytest_call))

    assert collection.exit_code == 0, collection.output
    assert collection.collected_files == frozenset((named,))
