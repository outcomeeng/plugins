"""Compliance tests for Python static-analysis gate membership."""

from __future__ import annotations

import outcomeeng.validation.__main__ as validation_entry
from outcomeeng.validation import (
    MYPY_ARGV,
    PYRIGHT_ARGV,
    RUFF_CHECK_ARGV,
)
from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL, build_full_gate_plan
from outcomeeng_testing.harnesses.l3_collection import (
    full_gate_skipping_recipe_fixture_path,
    justfile_recipe_command,
)
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
    marketplace_top_level_packages,
)
from outcomeeng_testing.harnesses.python_code_quality import (
    run_repository_mypy,
    strict_mode_violation_fixture_path,
)
from outcomeeng_testing.harnesses.real_agent_selection import (
    run_full_check_observation,
)


def _dispatched_recipe(command: tuple[str, ...]) -> tuple[str, ...]:
    """Return the validation recipe words a resolved `check-full` line dispatches."""
    return command[command.index(str(validation_entry.__package__)) + 1 :]


def test_static_analysis_steps_are_named_steps_of_the_full_gate() -> None:
    command = justfile_recipe_command(RECIPE_CHECK_FULL)
    full_gate_steps = {
        selected.step.argv: selected.step.label
        for selected in build_full_gate_plan(()).selected_steps
    }

    assert _dispatched_recipe(command) == (RECIPE_CHECK_FULL,)
    for argv in (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV):
        assert argv in full_gate_steps
        assert full_gate_steps[argv]
    assert len(set(full_gate_steps.values())) == len(full_gate_steps)


def test_the_full_gate_run_spawns_every_static_analysis_step() -> None:
    run = run_full_check_observation()

    assert run.exit_code == 0
    for argv in (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV):
        assert argv in run.spawn_calls


def test_a_check_full_recipe_that_skips_the_full_gate_is_detected() -> None:
    command = justfile_recipe_command(
        RECIPE_CHECK_FULL,
        justfile=full_gate_skipping_recipe_fixture_path(),
    )

    assert _dispatched_recipe(command) != (RECIPE_CHECK_FULL,)


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
