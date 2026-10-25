"""Observations of the L3 tests through real pytest collection.

The harness writes a violating whole-payload fixture, test files at every
execution level, into a temporary repository and reports which files real
pytest collects for the argument tail of a pytest argv the production recipes
compose. It also reports the argvs a recipe dispatch spawns against that repository and the
command the `justfile` recipe body resolves to for the words a caller passes, and
projects a selected-gate plan onto the pytest arguments its steps carry. The
linked tests own every predicate over those observations.

Exception case: Stage 5, Interaction protocols — the dispatch observation runs
the production entry point through the gate harness's recording spawner, which
exposes the spawned argvs without launching the L3 tests themselves.
"""

from __future__ import annotations

import io
import os
import shlex
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.validation import L3_LEVEL, PREFLIGHT_STEPS, PYTEST_ARGV, TEST_STEPS
from outcomeeng.validation.__main__ import main as validation_main
from outcomeeng.validation._steps import PYTEST_NODE_ID_SEPARATOR
from outcomeeng.validation.selected_gate import SelectedGatePlan
from outcomeeng_testing.generators.gate import GeneratedTestFile, l3_fixture_files
from outcomeeng_testing.harnesses.gate import RecordingSpawner
from outcomeeng_testing.harnesses.real_agent_selection import REPOSITORY_ROOT

PYTEST_MODULE_TOKEN: Final = "pytest"
# The collection runs outside the repository, so the repository root is put on the
# import path for the exclusion plugin the argument tail names.
PYTHONPATH_VARIABLE: Final = "PYTHONPATH"
COLLECTION_TIMEOUT_SECONDS: Final = 120
JUST_TIMEOUT_SECONDS: Final = 30
FIXTURE_TEST_SOURCE: Final = "def test_case() -> None:\n    pass\n"
FIXTURE_PYTEST_CONFIG_NAME: Final = "pytest.ini"
FIXTURE_PYTEST_CONFIG: Final = "[pytest]\n"
COLLECTION_ARGV: Final = (
    sys.executable,
    "-m",
    PYTEST_MODULE_TOKEN,
    "--collect-only",
    "-q",
    "-p",
    "no:cacheprovider",
    "--import-mode=importlib",
    "-c",
    FIXTURE_PYTEST_CONFIG_NAME,
)
JUST_DRY_RUN_ARGV: Final = ("just", "--dry-run", "--justfile")
# `just --dry-run` prints each command line of the recipe to stderr.
SPAWN_BUDGET: Final = len(PREFLIGHT_STEPS) + len(TEST_STEPS)


def pytest_argument_tail(argv: Sequence[str]) -> tuple[str, ...]:
    """Return the arguments that follow the pytest module in a spawned argv."""

    return tuple(argv[argv.index(PYTEST_MODULE_TOKEN) + 1 :])


def pytest_argvs(argvs: Iterable[Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    """Return the argvs that spawn pytest, in the order given."""

    return tuple(
        tuple(argv) for argv in argvs if tuple(argv[: len(PYTEST_ARGV)]) == PYTEST_ARGV
    )


def plan_pytest_arguments(plan: SelectedGatePlan) -> tuple[tuple[str, ...], ...]:
    """Return the pytest arguments of each planned pytest step, in plan order."""

    return tuple(
        argv[len(PYTEST_ARGV) :]
        for argv in pytest_argvs(step.argv for step in plan.steps)
    )


def plan_pytest_targets(plan: SelectedGatePlan) -> frozenset[str]:
    """Return every pytest argument the plan's pytest steps carry."""

    return frozenset(
        argument for arguments in plan_pytest_arguments(plan) for argument in arguments
    )


def l3_fixture_paths() -> frozenset[str]:
    """Return the fixture paths the generator composed at the L3 level."""

    return frozenset(
        test_file.path
        for test_file in l3_fixture_files()
        if test_file.level == L3_LEVEL
    )


def default_suite_fixture_paths() -> frozenset[str]:
    """Return the fixture paths the generator composed at every other level."""

    return frozenset(
        test_file.path
        for test_file in l3_fixture_files()
        if test_file.level != L3_LEVEL
    )


def write_fixture(root: Path, files: Sequence[GeneratedTestFile]) -> None:
    """Write ``files`` as passing test files beneath ``root``."""

    for test_file in files:
        target = root / test_file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(FIXTURE_TEST_SOURCE, encoding="utf-8")


@dataclass(frozen=True)
class FixtureCollection:
    """The test files one real pytest collection reports over the fixture."""

    exit_code: int
    collected_files: frozenset[str]
    output: str


def fixture_collection(
    files: Sequence[GeneratedTestFile], pytest_arguments: Sequence[str]
) -> FixtureCollection:
    """Collect ``pytest_arguments`` over a fixture of ``files`` with real pytest.

    Arguments are relative to the fixture root, which carries its own empty
    pytest configuration so the collection depends on the arguments alone.
    """

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture(root, files)
        (root / FIXTURE_PYTEST_CONFIG_NAME).write_text(
            FIXTURE_PYTEST_CONFIG, encoding="utf-8"
        )
        completed = subprocess.run(
            (*COLLECTION_ARGV, *pytest_arguments),
            cwd=root,
            env={**os.environ, PYTHONPATH_VARIABLE: str(REPOSITORY_ROOT)},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=COLLECTION_TIMEOUT_SECONDS,
            check=False,
        )
    return FixtureCollection(
        exit_code=completed.returncode,
        collected_files=frozenset(
            line.strip().split(PYTEST_NODE_ID_SEPARATOR, maxsplit=1)[0]
            for line in completed.stdout.splitlines()
            if PYTEST_NODE_ID_SEPARATOR in line
        ),
        output=completed.stdout + completed.stderr,
    )


def fixture_collected_files(pytest_argv: Sequence[str]) -> frozenset[str]:
    """Return the fixture files real pytest collects for a pytest argv's arguments."""

    return fixture_collection(
        l3_fixture_files(), pytest_argument_tail(pytest_argv)
    ).collected_files


def plan_collected_files(plan: SelectedGatePlan) -> tuple[frozenset[str], ...]:
    """Return the fixture files real pytest collects for each planned pytest step."""

    return tuple(
        fixture_collected_files(argv)
        for argv in pytest_argvs(step.argv for step in plan.steps)
    )


def recipe_dispatch_spawns(
    argv: Sequence[str], files: Sequence[GeneratedTestFile]
) -> tuple[tuple[str, ...], ...]:
    """Return the argvs the entry point spawns for ``argv`` against ``files``."""

    spawner = RecordingSpawner(exit_codes=[os.EX_OK] * SPAWN_BUDGET)
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture(root, files)
        validation_main(list(argv), spawner=spawner, sink=io.StringIO(), repo=root)
    return tuple(spawner.spawn_calls)


def justfile_recipe_command(recipe: str, *arguments: str) -> tuple[str, ...]:
    """Return the command line the repository `justfile` resolves ``recipe`` to.

    ``arguments`` are the words a caller passes to the recipe.
    """

    completed = subprocess.run(
        (*JUST_DRY_RUN_ARGV, str(REPOSITORY_ROOT / "justfile"), recipe, *arguments),
        cwd=REPOSITORY_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=JUST_TIMEOUT_SECONDS,
        check=False,
    )
    lines = [line for line in completed.stderr.splitlines() if line.strip()]
    if completed.returncode != 0 or len(lines) != 1:
        raise RuntimeError(
            f"just --dry-run {recipe} exited {completed.returncode}: {completed.stderr}"
        )
    return tuple(shlex.split(lines[0]))
