"""Compliance tests for Python static-analysis gate membership."""

from __future__ import annotations

from outcomeeng.validation import (
    MYPY_ARGV,
    PYRIGHT_ARGV,
    PYTHON_SOURCE_PATHS,
    RUFF_CHECK_ARGV,
    STEPS,
)


def test_static_analysis_steps_are_declared_in_gate() -> None:
    step_argvs = {step.argv for step in STEPS}

    assert RUFF_CHECK_ARGV in step_argvs
    assert MYPY_ARGV in step_argvs
    assert PYRIGHT_ARGV in step_argvs


def test_mypy_gate_step_runs_strict_mode() -> None:
    assert "--strict" in MYPY_ARGV


def test_type_checking_steps_target_product_packages() -> None:
    for package_path in PYTHON_SOURCE_PATHS:
        assert package_path in MYPY_ARGV
        assert package_path in PYRIGHT_ARGV
