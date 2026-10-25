"""Harness that type-checks an inert source fixture under the repository's pyright."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation import PYRIGHT_ARGV, PYTHON_SOURCE_PATHS
from outcomeeng_testing.harnesses.spec_tree import (
    marketplace_root_for_spec_tree_root_test,
)

PYRIGHT_MODE_FIXTURES: Final = (
    Path(__file__).resolve().parents[1] / "fixtures" / "pyright_mode"
)
# The fixture's suffix keeps the package type-checking step from scanning it.
INERT_SOURCE_SUFFIX: Final = ".txt"
PYRIGHT_PROJECT_FLAG: Final = "--project"
PYRIGHT_JSON_FLAG: Final = "--outputjson"


@dataclass(frozen=True)
class PyrightRun:
    """The exit code and the error count pyright reports for one run."""

    returncode: int
    error_count: int


def standard_mode_violation_fixture_path() -> Path:
    """Return the source pyright rejects in standard mode and accepts in basic mode."""

    return PYRIGHT_MODE_FIXTURES / "incompatible_method_override.py.txt"


def run_repository_pyright(test_file: str, fixture: Path) -> PyrightRun:
    """Type-check a copy of ``fixture`` with the gate's pyright and the repository's configuration."""

    product_root = marketplace_root_for_spec_tree_root_test(test_file)
    pyright = tuple(word for word in PYRIGHT_ARGV if word not in PYTHON_SOURCE_PATHS)
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
    return PyrightRun(
        returncode=result.returncode,
        error_count=int(report["summary"]["errorCount"]),
    )
