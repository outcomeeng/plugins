"""Harnesses that type-check an inert source fixture under the gate's type checkers."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation import MYPY_ARGV, PYRIGHT_ARGV, PYTHON_SOURCE_PATHS
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)

_FIXTURES: Final = Path(__file__).resolve().parents[1] / "fixtures"
PYRIGHT_MODE_FIXTURES: Final = _FIXTURES / "pyright_mode"
MYPY_MODE_FIXTURES: Final = _FIXTURES / "mypy_mode"
# The fixture's suffix keeps the package type-checking step from scanning it.
INERT_SOURCE_SUFFIX: Final = ".txt"
PYRIGHT_PROJECT_FLAG: Final = "--project"
PYRIGHT_JSON_FLAG: Final = "--outputjson"
MYPY_ERROR_MARKER: Final = ": error:"


@dataclass(frozen=True)
class TypeCheckRun:
    """The exit code and the error count a type checker reports for one run."""

    returncode: int
    error_count: int


def standard_mode_violation_fixture_path() -> Path:
    """Return the source pyright rejects in standard mode and accepts in basic mode."""

    return PYRIGHT_MODE_FIXTURES / "incompatible_method_override.py.txt"


def strict_mode_violation_fixture_path() -> Path:
    """Return the source mypy accepts by default and rejects under strict mode."""

    return MYPY_MODE_FIXTURES / "unannotated_function.py.txt"


def _gate_command(argv: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(word for word in argv if word not in PYTHON_SOURCE_PATHS)


def run_repository_pyright(test_file: str, fixture: Path) -> TypeCheckRun:
    """Type-check a copy of ``fixture`` with the gate's pyright and the repository's configuration."""

    product_root = marketplace_root_for_spec_tree_root_test(test_file)
    pyright = _gate_command(PYRIGHT_ARGV)
    with TemporaryDirectory() as directory:
        source = Path(directory) / fixture.name.removesuffix(INERT_SOURCE_SUFFIX)
        shutil.copyfile(fixture, source)
        result = subprocess.run(  # noqa: S603 — argv is a source-owned command contract.
            [
                *pyright,
                PYRIGHT_JSON_FLAG,
                PYRIGHT_PROJECT_FLAG,
                str(product_root),
                str(source),
            ],
            cwd=product_root,
            capture_output=True,
            text=True,
            check=False,
        )
    report = json.loads(result.stdout)
    return TypeCheckRun(
        returncode=result.returncode,
        error_count=int(report["summary"]["errorCount"]),
    )


def run_repository_mypy(test_file: str, fixture: Path) -> TypeCheckRun:
    """Type-check a copy of ``fixture`` with the gate's mypy and the repository's configuration."""

    product_root = marketplace_root_for_spec_tree_root_test(test_file)
    with TemporaryDirectory() as directory:
        source = Path(directory) / fixture.name.removesuffix(INERT_SOURCE_SUFFIX)
        shutil.copyfile(fixture, source)
        result = subprocess.run(  # noqa: S603 — argv is a source-owned command contract.
            [*_gate_command(MYPY_ARGV), str(source)],
            cwd=product_root,
            capture_output=True,
            text=True,
            check=False,
        )
    return TypeCheckRun(
        returncode=result.returncode,
        error_count=sum(
            MYPY_ERROR_MARKER in line for line in result.stdout.splitlines()
        ),
    )
