"""Observations for real-agent Codex test selection in the selected and full gates.

The full-gate runs drive the production entry point through the gate harness's
recording spawner and scripted git runner, and the direct-execution run drives
the `test` recipe the direct entry point composes through the same recording
spawner. Exception case: Stage 5, Interaction protocols — the claim is which
argvs the gate and the direct recipe spawn, and the recording spawner exposes
them without launching validators or the real-agent tests themselves.

Pytest collection runs for real: the observation is the set of test node ids a
pytest argument tail collects, which is what the gate's exclusion decides.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, fields
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.distribution import agents as agent_conversion
from outcomeeng.distribution.agents import AGENT_SOURCE_DIRECTORY_NAME
from outcomeeng.distribution.build import project_emissions
from outcomeeng.distribution.contracts import DIST_DIR_NAME
from outcomeeng.distribution.installation import (
    CODEX_HOME_ENV,
    apply_agent_home_plan,
    generated_codex_agent_definitions,
)
from outcomeeng.validation import (
    PREFLIGHT_STEPS,
    TEST_STEPS,
    VALIDATION_STEPS,
    test_recipe as direct_test_recipe,
)
from outcomeeng.validation.ci_gate import (
    CODEX_API_KEY_ENVIRONMENT,
    DISCOVERY_AUTH_MODE_ENVIRONMENT,
)
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
    FIRST_PARENT_BASE_REF,
    PYTEST_NODE_ID_SEPARATOR,
    run_full_check as production_run_full_check,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    WORKSPACE_TOKEN_ENV,
    AuthenticationMode,
)
from outcomeeng_testing.harnesses.changeset_scope import build_repo_without_origin
from outcomeeng_testing.harnesses.gate import (
    RecipeRunObservation,
    RecordingSpawner,
    RunObservation,
    recipe_run_observation,
    selected_gate_runner_for_paths,
)
from outcomeeng_testing.harnesses.installation import PluginLifecycleHarness

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]
SOURCE_ROOT: Final = REPOSITORY_ROOT / "src"
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
PLACEHOLDER_CREDENTIAL: Final = "placeholder-credential-for-selection"
CODEX_CREDENTIAL_VARIABLES: Final = (
    CODEX_API_KEY_ENVIRONMENT,
    WORKSPACE_TOKEN_ENV,
    DISCOVERY_AUTH_MODE_ENVIRONMENT,
    CODEX_HOME_ENV,
)
_SPAWN_BUDGET: Final = (
    2 * len(PREFLIGHT_STEPS) + len(VALIDATION_STEPS) + len(TEST_STEPS)
)


def repository_relative_path(module_file: str) -> str:
    """Return ``module_file`` relative to this checkout, in posix form."""

    return Path(module_file).resolve().relative_to(REPOSITORY_ROOT).as_posix()


def _module_path(function: Callable[..., object]) -> str:
    return repository_relative_path(sys.modules[function.__module__].__file__ or "")


@dataclass(frozen=True)
class AgentDefinitionInventory:
    """The checkout's agent definitions by kind, derived independently of the selector.

    Each kind comes from the owner that produces or places the artifact: the
    build's emission projection names every authored agent source, the
    rendering it emits, and every rendering of the shipped placement script;
    the conversion module, the module defining that projection, and the module
    defining repository installation's agent-home placement are the code that
    converts, emits, and places definitions; and the plugin-lifecycle harness
    that executes the shipped placement script names its authored template.
    """

    authored_sources: tuple[str, ...]
    renderings: tuple[str, ...]
    conversion_code: tuple[str, ...]
    emission_code: tuple[str, ...]
    placement_code: tuple[str, ...]
    placement_scripts: tuple[str, ...]

    def by_kind(self) -> Mapping[str, tuple[str, ...]]:
        """Return every kind's paths keyed by the kind's field name."""

        return {kind.name: getattr(self, kind.name) for kind in fields(self)}


def _shipped_placement_script(relative_path: Path) -> bool:
    # The plugin-lifecycle harness that executes the shipped placement script
    # names where a plugin's lifecycle skill carries it; a target-tree output
    # at that place for its own plugin is a rendering of the script.
    if not relative_path.parts:
        return False
    lifecycle = PluginLifecycleHarness(root=Path(), plugin_name=relative_path.parts[0])
    shipped = lifecycle.script_path.relative_to(lifecycle.skill_root.parents[1])
    return relative_path.parts[1:] == shipped.parts


def checkout_agent_definition_inventory() -> AgentDefinitionInventory:
    """Return the checkout's agent definitions by kind."""

    projection = project_emissions(SOURCE_ROOT)
    authored: set[str] = set()
    renderings: set[str] = set()
    placement_scripts: set[str] = set()
    for emission in projection.emissions:
        rendering = (
            Path(DIST_DIR_NAME) / emission.target.value / emission.relative_path
        ).as_posix()
        if emission.source.parent.name == AGENT_SOURCE_DIRECTORY_NAME:
            authored.add(repository_relative_path(str(emission.source)))
            renderings.add(rendering)
        elif _shipped_placement_script(emission.relative_path):
            placement_scripts.add(repository_relative_path(str(emission.source)))
            placement_scripts.add(rendering)
    return AgentDefinitionInventory(
        authored_sources=tuple(sorted(authored)),
        renderings=tuple(sorted(renderings)),
        conversion_code=(repository_relative_path(agent_conversion.__file__),),
        emission_code=(_module_path(project_emissions),),
        placement_code=tuple(
            sorted(
                {
                    _module_path(generated_codex_agent_definitions),
                    _module_path(apply_agent_home_plan),
                }
            )
        ),
        placement_scripts=tuple(sorted(placement_scripts)),
    )


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


def run_full_check_observation(
    *,
    branch_path: str = "",
    branch_status: str = "M",
) -> RunObservation:
    """Run the explicit full gate against scripted git state and record the run."""

    runner = selected_gate_runner_for_paths(
        branch_path=branch_path,
        branch_status=branch_status,
    )
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


@contextmanager
def codex_credential_environment(*, present: bool) -> Iterator[None]:
    """Set or clear every Codex credential variable, restoring them on exit."""

    saved = {name: os.environ.get(name) for name in CODEX_CREDENTIAL_VARIABLES}
    with TemporaryDirectory() as codex_home:
        try:
            for name in CODEX_CREDENTIAL_VARIABLES:
                os.environ.pop(name, None)
            if present:
                os.environ[CODEX_API_KEY_ENVIRONMENT] = PLACEHOLDER_CREDENTIAL
                os.environ[WORKSPACE_TOKEN_ENV] = PLACEHOLDER_CREDENTIAL
                os.environ[DISCOVERY_AUTH_MODE_ENVIRONMENT] = AuthenticationMode.API
                os.environ[CODEX_HOME_ENV] = codex_home
            yield
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
