"""Compliance tests for Python static-analysis gate membership."""

from __future__ import annotations

import pytest

from outcomeeng.validation import (
    MYPY_ARGV,
    PYRIGHT_ARGV,
    RUFF_CHECK_ARGV,
    VALIDATION_ENTRY_COMMAND,
)
from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL, build_full_gate_plan
from outcomeeng_testing.harnesses.l3_collection import (
    full_gate_skipping_recipe_fixture_path,
    justfile_recipe_dispatch,
)
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
    marketplace_top_level_packages,
)
from outcomeeng_testing.harnesses.python_code_quality import (
    run_check_full_dispatch,
    run_repository_mypy,
    strict_mode_violation_fixture_path,
)


def test_static_analysis_steps_are_named_steps_of_the_full_gate() -> None:
    dispatch = justfile_recipe_dispatch(RECIPE_CHECK_FULL)
    full_gate_steps = {
        selected.step.argv: selected.step.label
        for selected in build_full_gate_plan(()).selected_steps
    }

    assert dispatch.entry == VALIDATION_ENTRY_COMMAND
    assert dispatch.recipe_words == (RECIPE_CHECK_FULL,)
    for argv in (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV):
        assert argv in full_gate_steps
        assert full_gate_steps[argv]
    assert len(set(full_gate_steps.values())) == len(full_gate_steps)


def test_check_full_dispatch_spawns_every_static_analysis_step() -> None:
    run = run_check_full_dispatch()

    assert run.exit_code == 0
    for argv in (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV):
        assert argv in run.spawn_calls


@pytest.mark.parametrize(
    "checker",
    (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV),
    ids=lambda argv: " ".join(argv),
)
def test_a_failing_static_analysis_step_fails_check_full(
    checker: tuple[str, ...],
) -> None:
    run = run_check_full_dispatch(failing_argv=checker)

    assert checker in run.spawn_calls
    assert run.exit_code != 0


def test_a_check_full_recipe_that_skips_the_full_gate_is_detected() -> None:
    dispatch = justfile_recipe_dispatch(
        RECIPE_CHECK_FULL,
        justfile=full_gate_skipping_recipe_fixture_path(),
    )

    assert dispatch.entry == VALIDATION_ENTRY_COMMAND
    assert dispatch.recipe_words != (RECIPE_CHECK_FULL,)


def test_mypy_gate_step_rejects_a_strict_mode_violation() -> None:
    run = run_repository_mypy(__file__, strict_mode_violation_fixture_path())

    assert run.error_count > 0
    assert run.returncode != 0


def test_type_checking_steps_target_product_packages() -> None:
    packages = marketplace_top_level_packages(
        marketplace_root_for_spec_tree_root_test(__file__)
    )

    assert packages
    for package_path in packages:
        assert package_path in MYPY_ARGV
        assert package_path in PYRIGHT_ARGV
