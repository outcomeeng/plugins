"""Harnesses that type-check an inert source fixture under the gate's type checkers."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

import outcomeeng.validation.__main__ as validation_entry
from outcomeeng.validation import MYPY_ARGV, PYRIGHT_ARGV, PYTHON_SOURCE_PATHS
from outcomeeng.validation._model import ProcessHandle
from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL
from outcomeeng_testing.harnesses.changeset_scope import (
    build_repo_without_origin,
    commit_file,
)
from outcomeeng_testing.harnesses.gate import RecordingHandle
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
CHECKER_FAILURE_EXIT_CODE: Final = 1
_FIRST_PID: Final = 10_000
# The full gate diffs the head against its first parent, so the scratch
# checkout carries a second commit on top of the builder's initial one.
_SECOND_COMMIT_FILE: Final = "changed.txt"


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


@dataclass
class CheckerFailingSpawner:
    """A ProcessSpawner whose child exits nonzero for one argv and zero for every other."""

    failing_argv: tuple[str, ...] | None = None
    spawn_calls: list[tuple[str, ...]] = field(default_factory=list)

    def spawn(self, argv: Sequence[str], output_path: Path) -> ProcessHandle:
        recorded = tuple(argv)
        self.spawn_calls.append(recorded)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("", encoding="utf-8")
        return RecordingHandle(
            pid=_FIRST_PID + len(self.spawn_calls),
            exit_code=(
                CHECKER_FAILURE_EXIT_CODE if recorded == self.failing_argv else os.EX_OK
            ),
        )


@dataclass(frozen=True)
class FullDispatchRun:
    """The exit code and the spawned argvs of one `check-full` dispatch."""

    exit_code: int
    spawn_calls: tuple[tuple[str, ...], ...]


def run_check_full_dispatch(
    failing_argv: tuple[str, ...] | None = None,
) -> FullDispatchRun:
    """Dispatch `check-full` through the validation entry point against a scratch checkout.

    Every child the dispatch spawns is recorded and exits zero, except the one
    whose argv equals ``failing_argv``, which exits nonzero.
    """

    spawner = CheckerFailingSpawner(failing_argv=failing_argv)
    with TemporaryDirectory() as directory:
        repo = Path(directory)
        build_repo_without_origin(repo)
        commit_file(repo, _SECOND_COMMIT_FILE, _SECOND_COMMIT_FILE, _SECOND_COMMIT_FILE)
        exit_code = validation_entry.main(
            [RECIPE_CHECK_FULL],
            spawner=spawner,
            sink=io.StringIO(),
            repo=repo,
        )
    return FullDispatchRun(exit_code=exit_code, spawn_calls=tuple(spawner.spawn_calls))
