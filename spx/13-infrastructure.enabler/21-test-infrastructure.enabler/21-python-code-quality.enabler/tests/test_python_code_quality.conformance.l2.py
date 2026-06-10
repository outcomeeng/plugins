"""Conformance tests for Python static-analysis commands."""

from __future__ import annotations

import pytest

from outcomeeng.validation import MYPY_ARGV, PYRIGHT_ARGV, RUFF_CHECK_ARGV
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
