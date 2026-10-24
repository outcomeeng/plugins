"""Observations for on-demand test selection in the selected and full gates.

The full-gate runs drive the production entry point through the gate harness's
recording spawner and scripted git runner, and the direct-execution run drives
the `test` recipe the direct entry point composes through the same recording
spawner. Exception case: Stage 5, Interaction protocols — the claim is which
argvs the gate and the direct recipe spawn, and the recording spawner exposes
them without launching validators or the on-demand tests themselves.

Pytest collection runs for real: the observation is the set of test node ids a
pytest argument tail collects, which is what the gate's exclusion decides.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation import (
    PREFLIGHT_STEPS,
    TEST_STEPS,
    VALIDATION_STEPS,
    test_recipe as direct_test_recipe,
)
from outcomeeng.validation._steps import PYTEST_NODE_ID_SEPARATOR
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
    FIRST_PARENT_BASE_REF,
    run_full_check as production_run_full_check,
)
from outcomeeng_testing.harnesses.changeset_scope import build_repo_without_origin
from outcomeeng_testing.harnesses.gate import (
    RecipeRunObservation,
    RecordingSpawner,
    RunObservation,
    recipe_run_observation,
    selected_gate_runner_for_paths,
)

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]
PYTEST_COLLECTION_TIMEOUT_SECONDS: Final = 120
PYTEST_COLLECTION_ARGV: Final = (
    sys.executable,
    "-m",
    "pytest",
    "--collect-only",
    "-qq",
    "-p",
    "no:cacheprovider",
)
_SPAWN_BUDGET: Final = (
    2 * len(PREFLIGHT_STEPS) + len(VALIDATION_STEPS) + len(TEST_STEPS)
)


def repository_relative_path(module_file: str) -> str:
    """Return ``module_file`` relative to this checkout, in posix form."""

    return Path(module_file).resolve().relative_to(REPOSITORY_ROOT).as_posix()


@dataclass(frozen=True)
class PytestCollectionObservation:
    """The test node ids one real pytest collection reports for an argument tail."""

    arguments: tuple[str, ...]
    exit_code: int
    collected: frozenset[str]
    output: str


def pytest_collection_observation(
    arguments: Sequence[str],
) -> PytestCollectionObservation:
    """Collect ``arguments`` with the checkout's pytest and report the node ids."""

    completed = subprocess.run(
        (*PYTEST_COLLECTION_ARGV, *arguments),
        cwd=REPOSITORY_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=PYTEST_COLLECTION_TIMEOUT_SECONDS,
        check=False,
    )
    return PytestCollectionObservation(
        arguments=tuple(arguments),
        exit_code=completed.returncode,
        collected=frozenset(
            line.strip()
            for line in completed.stdout.splitlines()
            if PYTEST_NODE_ID_SEPARATOR in line
        ),
        output=completed.stdout + completed.stderr,
    )


def run_full_check_observation(*, branch_path: str = "") -> RunObservation:
    """Run the explicit full gate against scripted git state and record the run."""

    runner = selected_gate_runner_for_paths(branch_path=branch_path)
    spawner = RecordingSpawner(exit_codes=[os.EX_OK] * _SPAWN_BUDGET)
    sink = io.StringIO()
    with TemporaryDirectory() as tmp:
        exit_code = production_run_full_check(
            spawner=spawner,
            sink=sink,
            repo=Path(tmp),
            base_ref=DEFAULT_BASE_REF,
            runner=runner,
        )
    return RunObservation(
        exit_code=exit_code,
        output=sink.getvalue(),
        spawn_calls=tuple(spawner.spawn_calls),
        runner_calls=tuple(runner.calls),
    )


def first_parent_full_check_observation(*, branch_path: str) -> RunObservation:
    """Run the explicit full gate where no remote default branch is configured.

    The repository is a real git checkout without ``refs/remotes/origin/HEAD``,
    as CI's merge-commit checkout is, and the gate resolves its base itself;
    the scripted git runner answers branch discovery only against the first
    parent, so any other base fails the run.
    """

    runner = selected_gate_runner_for_paths(
        base_ref=FIRST_PARENT_BASE_REF,
        branch_path=branch_path,
    )
    spawner = RecordingSpawner(exit_codes=[os.EX_OK] * _SPAWN_BUDGET)
    sink = io.StringIO()
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        build_repo_without_origin(repo)
        exit_code = production_run_full_check(
            spawner=spawner,
            sink=sink,
            repo=repo,
            runner=runner,
        )
    return RunObservation(
        exit_code=exit_code,
        output=sink.getvalue(),
        spawn_calls=tuple(spawner.spawn_calls),
        runner_calls=tuple(runner.calls),
    )


def direct_test_observation(pytest_arguments: Sequence[str]) -> RecipeRunObservation:
    """Run the direct `test` recipe for ``pytest_arguments`` and record the run.

    The direct entry point composes this recipe from the caller's pytest
    arguments alone; every scripted child exits successfully, so the recorded
    argvs are the complete set the direct recipe spawns.
    """

    recipe = direct_test_recipe(pytest_arguments)
    return recipe_run_observation(
        recipe=recipe,
        exit_codes=[os.EX_OK] * (len(recipe.preflight_steps) + len(recipe.steps)),
    )
