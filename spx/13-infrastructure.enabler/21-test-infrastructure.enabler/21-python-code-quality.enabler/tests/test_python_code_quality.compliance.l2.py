"""Compliance tests for Python static-analysis gate membership."""

from __future__ import annotations

from pathlib import PurePosixPath

import outcomeeng.validation.__main__ as validation_entry
from outcomeeng.validation import (
    MYPY_ARGV,
    PYRIGHT_ARGV,
    RUFF_CHECK_ARGV,
)
from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL, build_full_gate_plan
from outcomeeng_testing.harnesses.l3_collection import justfile_recipe_command
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
    marketplace_tracked_files,
)


def test_static_analysis_steps_are_named_steps_of_the_full_gate() -> None:
    command = justfile_recipe_command(RECIPE_CHECK_FULL)
    full_gate_steps = {
        selected.step.argv: selected.step.label
        for selected in build_full_gate_plan(()).selected_steps
    }

    assert command[command.index(str(validation_entry.__package__)) + 1 :] == (
        RECIPE_CHECK_FULL,
    )
    for argv in (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV):
        assert argv in full_gate_steps
        assert full_gate_steps[argv]
    assert len(set(full_gate_steps.values())) == len(full_gate_steps)


def test_mypy_gate_step_runs_strict_mode() -> None:
    assert "--strict" in MYPY_ARGV


def test_type_checking_steps_target_product_packages() -> None:
    root = marketplace_root_for_spec_tree_root_test(__file__)
    packages = {
        PurePosixPath(path).parts[0]
        for path in marketplace_tracked_files(root)
        if len(PurePosixPath(path).parts) == 2
        and PurePosixPath(path).name == "__init__.py"
    }

    assert packages
    for package_path in packages:
        assert package_path in MYPY_ARGV
        assert package_path in PYRIGHT_ARGV
