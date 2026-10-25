"""Conformance tests for Python static-analysis commands."""

from __future__ import annotations

import pytest

from outcomeeng.validation import MYPY_ARGV, PYRIGHT_ARGV, RUFF_CHECK_ARGV
from outcomeeng_testing.harnesses.python_code_quality import (
    run_repository_pyright,
    standard_mode_violation_fixture_path,
)
from outcomeeng_testing.harnesses.spec_tree import (
    run_marketplace_command,
)

QUALITY_ARGVS = (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV)


@pytest.mark.parametrize("argv", QUALITY_ARGVS)
def test_python_quality_command_passes(argv: tuple[str, ...]) -> None:
    result = run_marketplace_command(__file__, argv)

    assert result.returncode == 0, (
        f"{' '.join(argv)} failed with exit code {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_repository_pyright_rejects_a_standard_mode_violation() -> None:
    run = run_repository_pyright(__file__, standard_mode_violation_fixture_path())

    assert run.error_count > 0
    assert run.returncode != 0
