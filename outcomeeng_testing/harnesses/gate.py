"""Recording doubles for the gate orchestrator.

These harnesses implement the `ProcessSpawner` and `ProcessHandle` Protocols
declared in `outcomeeng.validation`. They are spies (recording calls) and
stubs (returning scripted exit codes), used by `l1` tests to verify
orchestration behavior without launching real subprocesses.

Exception case: Stage 5, Interaction protocols — the orchestrator's
correctness depends on the sequence and shape of spawn/wait/signal calls.
Recording doubles let `l1` tests assert on those interactions.
"""

from __future__ import annotations

import ast
import inspect
import io
import json
import math
import os
import signal
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TextIO, TypeVar, cast

from hypothesis import given, seed, settings

from outcomeeng import validation as validation_pkg
from outcomeeng.distribution.installation import CODEX_HOME_ENV
from outcomeeng.validation import (
    POST_KILL_REAP_ATTEMPTS,
    PREFLIGHT_STEPS,
    RECIPE_CHECK,
    SIGNAL_GRACE_SECONDS,
    SIGNAL_POLL_INTERVAL_SECONDS,
    SUMMARY_KEY_RECIPES,
    SUMMARY_KEY_STEPS,
    SUMMARY_PATH_LABEL,
    TEST_STEPS,
    VALIDATION_RECIPE,
    VALIDATION_STEPS,
    ProcessHandle,
    ProcessSpawner,
    Recipe,
    Step,
    run,
    run_check,
    run_recipe,
    terminate_process_group,
)
from outcomeeng.validation.__main__ import main as validation_main
from outcomeeng.validation._git import GitCommandResult
from outcomeeng.validation.ci_gate import (
    CODEX_API_KEY_ENVIRONMENT,
    DISCOVERY_AUTH_MODE_ENVIRONMENT,
)
from outcomeeng.validation.infrastructure_index import (
    InfrastructureIndex,
    index_test_infrastructure,
)
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
    GIT_DISCOVERY_FAILURE_EXIT_CODE,
    RECIPE_CHECK_FULL,
    GIT_DIFF_STAGED_ARGV,
    GIT_DIFF_UNSTAGED_ARGV,
    GIT_LS_UNTRACKED_ARGV,
    branch_diff_argv,
    collect_changed_paths,
    run_selected_check as production_run_selected_check,
)
from outcomeeng_testing.generators.gate import (
    MODIFIED_GIT_STATUS,
    REPOSITORY_ROOT,
    infrastructure_module_paths,
    selected_gate_changed_paths,
    step_lists,
)
from outcomeeng_testing.harnesses.changeset_scope import build_repo_without_origin
from outcomeeng_testing.harnesses.discovery_auth import (
    CREDENTIAL_ENVIRONMENTS,
    SAVED_LOGIN_API_KEY_FIELD,
    AuthenticationMode,
)
from outcomeeng_testing.harnesses.discovery_auth_cases import API_FIXTURE_PATH
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

SELECTED_GATE_PROPERTY_SEED = 20260705
SELECTED_GATE_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/tests/"
    "test_selected_gate.property.l1.py::"
    "test_selection_is_deterministic_for_path_order_and_duplicates"
)
SELECTED_GATE_PROPERTY_EXAMPLES = 40
GATE_STEP_PROPERTY_SEED = 20260706
GATE_STEP_PROPERTY_REPLAY_PATH = (
    "just test spx/15-validation.enabler/65-gate.enabler/tests/test_gate.property.l1.py"
)
GATE_STEP_PROPERTY_EXAMPLES = 50
# A killed process reports the conventional shell exit status for its signal.
KILLED_EXIT_CODE = 128 + signal.SIGKILL


class GateSummaryDecodeError(ValueError):
    """A structured summary file does not decode to the JSON shape being read."""

    def __init__(self, location: str, expected: str) -> None:
        self.location = location
        self.expected = expected
        super().__init__(f"summary {location} is not a JSON {expected}")


def _json_records(value: object, location: str) -> list[dict[str, object]]:
    if not isinstance(value, list) or not all(
        isinstance(record, dict) for record in value
    ):
        raise GateSummaryDecodeError(location, "array of objects")
    return cast("list[dict[str, object]]", value)


def read_summary(path: Path) -> dict[str, object]:
    """Decode a validation summary JSON object."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GateSummaryDecodeError(str(path), "object")
    return cast("dict[str, object]", data)


def summary_steps(summary: dict[str, object]) -> list[dict[str, object]]:
    """Decode the step records of a summary."""

    return _json_records(summary.get(SUMMARY_KEY_STEPS), SUMMARY_KEY_STEPS)


def summary_recipes(summary: dict[str, object]) -> list[dict[str, object]]:
    """Decode the primitive recipe records of a wrapper summary."""

    return _json_records(summary.get(SUMMARY_KEY_RECIPES), SUMMARY_KEY_RECIPES)


def selected_gate_runner_for_paths(
    *,
    base_ref: str = DEFAULT_BASE_REF,
    branch_path: str = "",
    branch_old_path: str = "",
    staged_path: str = "",
    staged_old_path: str = "",
    unstaged_path: str = "",
    unstaged_old_path: str = "",
    untracked_path: str = "",
    branch_status: str = MODIFIED_GIT_STATUS,
    staged_status: str = MODIFIED_GIT_STATUS,
    unstaged_status: str = MODIFIED_GIT_STATUS,
    branch_returncode: int = 0,
    branch_stderr: str = "",
) -> RecordingGitRunner:
    """Build a git runner for selected-gate path discovery tests."""

    return RecordingGitRunner(
        outputs={
            branch_diff_argv(base_ref): (
                GitCommandResult(
                    returncode=branch_returncode,
                    stdout=_selected_gate_name_status_output(
                        status=branch_status,
                        path=branch_path,
                        old_path=branch_old_path,
                    ),
                    stderr=branch_stderr,
                )
            ),
            GIT_DIFF_STAGED_ARGV: GitCommandResult(
                returncode=0,
                stdout=_selected_gate_name_status_output(
                    status=staged_status,
                    path=staged_path,
                    old_path=staged_old_path,
                ),
            ),
            GIT_DIFF_UNSTAGED_ARGV: GitCommandResult(
                returncode=0,
                stdout=_selected_gate_name_status_output(
                    status=unstaged_status,
                    path=unstaged_path,
                    old_path=unstaged_old_path,
                ),
            ),
            GIT_LS_UNTRACKED_ARGV: GitCommandResult(
                returncode=0,
                stdout=f"{untracked_path}\n" if untracked_path else "",
            ),
        }
    )


def collect_selected_gate_paths(
    repo: Path,
    *,
    runner: RecordingGitRunner,
) -> tuple[str, ...]:
    """Collect synthetic paths against the harness-owned base ref."""
    return collect_changed_paths(repo, base_ref=DEFAULT_BASE_REF, runner=runner)


def run_selected_check(
    *,
    spawner: ProcessSpawner,
    sink: TextIO,
    repo: Path,
    runner: RecordingGitRunner,
) -> int:
    """Run the selected gate against the harness-owned base ref."""
    return production_run_selected_check(
        spawner=spawner,
        sink=sink,
        repo=repo,
        base_ref=DEFAULT_BASE_REF,
        runner=runner,
    )


def _selected_gate_name_status_output(
    *,
    status: str,
    path: str,
    old_path: str = "",
) -> str:
    if not path:
        return ""
    if old_path:
        return f"{status}\t{old_path}\t{path}\n"
    return f"{status}\t{path}\n"


def gate_step_property(
    test_func: Callable[[tuple[Step, ...]], None],
) -> Callable[[], None]:
    """Run a step-list property with reproducible failure diagnostics."""

    configured = seed(GATE_STEP_PROPERTY_SEED)(
        settings(max_examples=GATE_STEP_PROPERTY_EXAMPLES, deadline=None)(
            given(steps=step_lists())(test_func)
        )
    )

    def wrapper() -> None:
        run_replayable_property(
            configured,
            seed_value=GATE_STEP_PROPERTY_SEED,
            replay_path=GATE_STEP_PROPERTY_REPLAY_PATH,
        )

    return wrapper


def repository_index() -> InfrastructureIndex:
    """Build the static import index over this checkout."""

    return index_test_infrastructure(REPOSITORY_ROOT)


def selected_gate_property(
    test_func: Callable[[list[str], InfrastructureIndex], None],
) -> Callable[[], None]:
    """Run the selected-gate property with reproducible failure diagnostics.

    The checkout's import index is built once per run, outside the generated
    cases, and handed to every case beside its generated changed paths.
    """

    def wrapper() -> None:
        index = repository_index()

        def bound(paths: list[str]) -> None:
            test_func(paths, index)

        configured = seed(SELECTED_GATE_PROPERTY_SEED)(
            settings(max_examples=SELECTED_GATE_PROPERTY_EXAMPLES, deadline=None)(
                given(
                    paths=selected_gate_changed_paths(
                        infrastructure_module_paths(index)
                    )
                )(bound)
            )
        )
        run_replayable_property(
            configured,
            seed_value=SELECTED_GATE_PROPERTY_SEED,
            replay_path=SELECTED_GATE_PROPERTY_REPLAY_PATH,
        )

    return wrapper


def validation_package_modules() -> list[Path]:
    """Return the gate orchestrator's own modules."""

    package_dir = Path(inspect.getfile(validation_pkg)).parent
    return sorted(p for p in package_dir.glob("*.py") if p.name.startswith("_"))


def validation_subprocess_importers() -> list[Path]:
    """Return validation modules that import subprocess."""

    importers: list[Path] = []
    for module_path in validation_package_modules():
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "subprocess" or alias.name.startswith(
                        "subprocess."
                    ):
                        importers.append(module_path)
                        break
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and (
                    node.module == "subprocess" or node.module.startswith("subprocess.")
                )
            ):
                importers.append(module_path)
    return importers


def validation_package_source_text() -> str:
    """Return concatenated validation package module source text."""

    return "\n".join(
        path.read_text(encoding="utf-8") for path in validation_package_modules()
    )


def popen_calls_from(module_path: Path) -> list[ast.Call]:
    """Return subprocess.Popen call nodes from a module."""

    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Attribute) and node.func.attr == "Popen")
            or (isinstance(node.func, ast.Name) and node.func.id == "Popen")
        )
    ]


def call_keyword_map(call: ast.Call) -> dict[str, ast.expr]:
    """Return keyword arguments with concrete names."""

    return {kw.arg: kw.value for kw in call.keywords if kw.arg is not None}


@dataclass(frozen=True)
class PipelineRunObservation:
    """One ad-hoc pipeline run's exit code, live output, and child records."""

    exit_code: int
    output: str
    spawn_calls: tuple[tuple[str, ...], ...]
    written_outputs: tuple[str, ...]
    retained_logs: tuple[str | None, ...]
    log_paths: tuple[str, ...]
    summary: dict[str, object] | None


def pipeline_run_observation(
    *,
    steps: tuple[Step, ...],
    exit_codes: Sequence[int],
    outputs: Sequence[str] = (),
) -> PipelineRunObservation:
    """Run the ad-hoc pipeline over ``steps`` with scripted children."""

    spawner = RecordingSpawner(exit_codes=list(exit_codes), outputs=list(outputs))
    sink = io.StringIO()
    exit_code = run(spawner=spawner, sink=sink, steps=steps)
    output = sink.getvalue()
    return PipelineRunObservation(
        exit_code=exit_code,
        output=output,
        spawn_calls=tuple(spawner.spawn_calls),
        written_outputs=tuple(spawner.written_outputs),
        retained_logs=tuple(
            path.read_text(encoding="utf-8") if path.exists() else None
            for path in spawner.output_paths
        ),
        log_paths=tuple(str(path) for path in spawner.output_paths),
        summary=_reported_summary(output),
    )


@dataclass(frozen=True)
class RecipeRunObservation:
    """One recipe run's exit code, output, child records, and summary."""

    exit_code: int
    output: str
    spawn_calls: tuple[tuple[str, ...], ...]
    retained_logs: tuple[str | None, ...]
    log_paths: tuple[str, ...]
    summary: dict[str, object]
    summary_path: str


def recipe_run_observation(
    *,
    recipe: Recipe,
    exit_codes: Sequence[int],
    outputs: Sequence[str] = (),
) -> RecipeRunObservation:
    """Run one recipe with scripted children and report its summary."""

    spawner = RecordingSpawner(exit_codes=list(exit_codes), outputs=list(outputs))
    return _observe_recipe_run(recipe=recipe, spawner=spawner)


def spawn_failure_observation(*, recipe: Recipe, message: str) -> RecipeRunObservation:
    """Run one recipe whose spawner fails with ``message`` before returning a handle."""

    spawner = SpawnFailingSpawner(message=message)
    return _observe_recipe_run(recipe=recipe, spawner=spawner)


def _observe_recipe_run(
    *, recipe: Recipe, spawner: RecordingSpawner | SpawnFailingSpawner
) -> RecipeRunObservation:
    sink = io.StringIO()
    with TemporaryDirectory() as tmp:
        summary_path = Path(tmp) / "summary.json"
        exit_code = run_recipe(
            spawner=spawner,
            sink=sink,
            recipe=recipe,
            summary_path=summary_path,
        )
        summary = read_summary(summary_path)
    return RecipeRunObservation(
        exit_code=exit_code,
        output=sink.getvalue(),
        spawn_calls=tuple(spawner.spawn_calls),
        retained_logs=tuple(
            path.read_text(encoding="utf-8") if path.exists() else None
            for path in spawner.output_paths
        ),
        log_paths=tuple(str(path) for path in spawner.output_paths),
        summary=summary,
        summary_path=str(summary_path),
    )


@dataclass(frozen=True)
class CheckRunObservation:
    """One check-wrapper run's exit code, output, child records, and summary."""

    exit_code: int
    output: str
    spawn_calls: tuple[tuple[str, ...], ...]
    summary: dict[str, object]


def check_run_observation(
    *,
    recipes: tuple[Recipe, ...],
    exit_codes: Sequence[int],
    outputs: Sequence[str] = (),
) -> CheckRunObservation:
    """Run the check wrapper over ``recipes`` with scripted children."""

    spawner = RecordingSpawner(exit_codes=list(exit_codes), outputs=list(outputs))
    return _observe_check_run(recipes=recipes, spawner=spawner)


def signal_interrupt_observation(signum: int) -> CheckRunObservation:
    """Run the check wrapper with a spawner that raises ``signum`` during spawn."""

    return _observe_check_run(
        recipes=(VALIDATION_RECIPE,), spawner=SignalRaisingSpawner(signum=signum)
    )


def _observe_check_run(
    *,
    recipes: tuple[Recipe, ...],
    spawner: RecordingSpawner | SignalRaisingSpawner,
) -> CheckRunObservation:
    sink = io.StringIO()
    with TemporaryDirectory() as tmp:
        summary_path = Path(tmp) / "check-summary.json"
        exit_code = run_check(
            spawner=spawner,
            sink=sink,
            recipes=recipes,
            summary_path=summary_path,
        )
        summary = read_summary(summary_path)
    return CheckRunObservation(
        exit_code=exit_code,
        output=sink.getvalue(),
        spawn_calls=tuple(spawner.spawn_calls),
        summary=summary,
    )


@dataclass(frozen=True)
class ShutdownObservation:
    """One bounded shutdown of a hanging child under a controlled clock."""

    received_signals: tuple[int, ...]
    sleep_call_count: int
    monotonic_calls: int
    poll_calls: int
    sleep_budget: int


def bounded_shutdown_observation() -> ShutdownObservation:
    """Terminate a hanging child under a clock that rejects unbounded waits."""

    grace_sleep_calls = math.ceil(SIGNAL_GRACE_SECONDS / SIGNAL_POLL_INTERVAL_SECONDS)
    sleep_budget = grace_sleep_calls + POST_KILL_REAP_ATTEMPTS
    clock = BoundedAdvancingClock(max_sleep_calls=sleep_budget)
    handle = HangingHandle(pid=10_000, exit_on_kill=False)
    terminate_process_group(
        handle,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    return ShutdownObservation(
        received_signals=tuple(handle.received_signals),
        sleep_call_count=len(clock.sleep_calls),
        monotonic_calls=clock.monotonic_calls,
        poll_calls=handle.poll_calls,
        sleep_budget=sleep_budget,
    )


def while_loops_in_gate_modules() -> tuple[tuple[str, ast.While], ...]:
    """Every while loop in the gate package modules, paired with its module name."""

    loops: list[tuple[str, ast.While]] = []
    for module_path in validation_package_modules():
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                loops.append((module_path.name, node))
    return tuple(loops)


@dataclass(frozen=True)
class CollectionObservation:
    """Collected changed paths beside the recorded git interactions."""

    inputs: tuple[str, ...]
    collected: tuple[str, ...]
    runner_calls: tuple[tuple[str, ...], ...]
    runner_repos: tuple[Path, ...]
    repo: Path
    command_count: int


def collected_paths_observation(
    *,
    branch_path: str = "",
    branch_old_path: str = "",
    branch_status: str = MODIFIED_GIT_STATUS,
    staged_path: str = "",
    unstaged_path: str = "",
    untracked_path: str = "",
) -> CollectionObservation:
    """Collect the given synthetic paths and report every recorded interaction."""

    runner = selected_gate_runner_for_paths(
        branch_path=branch_path,
        branch_old_path=branch_old_path,
        branch_status=branch_status,
        staged_path=staged_path,
        unstaged_path=unstaged_path,
        untracked_path=untracked_path,
    )
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        collected = collect_selected_gate_paths(repo, runner=runner)
    inputs = tuple(
        path
        for path in (
            branch_old_path,
            branch_path,
            staged_path,
            unstaged_path,
            untracked_path,
        )
        if path
    )
    return CollectionObservation(
        inputs=inputs,
        collected=collected,
        runner_calls=tuple(runner.calls),
        runner_repos=tuple(runner.repos),
        repo=repo,
        command_count=len(runner.outputs),
    )


@dataclass(frozen=True)
class ResolvedBaseObservation:
    """Collection through an injected base-ref resolver."""

    branch_path: str
    base_ref: str
    collected: tuple[str, ...]
    resolver_repos: tuple[Path, ...]
    repo: Path
    first_runner_call: tuple[str, ...]


def resolved_base_observation(
    *, base_ref: str, branch_path: str
) -> ResolvedBaseObservation:
    """Collect ``branch_path`` through a resolver that answers ``base_ref``."""

    resolver_repos: list[Path] = []

    def resolve_base_ref(candidate_repo: Path) -> str:
        resolver_repos.append(candidate_repo)
        return base_ref

    runner = selected_gate_runner_for_paths(
        base_ref=base_ref,
        branch_path=branch_path,
    )
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        collected = collect_changed_paths(
            repo,
            base_ref_resolver=resolve_base_ref,
            runner=runner,
        )
    return ResolvedBaseObservation(
        branch_path=branch_path,
        base_ref=base_ref,
        collected=collected,
        resolver_repos=tuple(resolver_repos),
        repo=repo,
        first_runner_call=runner.calls[0],
    )


@dataclass(frozen=True)
class RunObservation:
    """One selected-check run's exit code, live output, and spawned argvs.

    ``output_before_first_spawn`` is the live output written before the first
    child started, or the whole output when no child started; ``summary`` is the
    structured summary the run reported writing, when it reported one.
    """

    exit_code: int
    output: str
    spawn_calls: tuple[tuple[str, ...], ...]
    runner_calls: tuple[tuple[str, ...], ...]
    output_before_first_spawn: str
    summary: dict[str, object] | None


_CHILD_OUTPUT_BUDGET = (
    2 * len(PREFLIGHT_STEPS) + len(VALIDATION_STEPS) + len(TEST_STEPS)
)


def run_check_observation(
    *,
    branch_path: str = "",
    branch_old_path: str = "",
    branch_status: str = MODIFIED_GIT_STATUS,
    branch_returncode: int = 0,
    branch_stderr: str = "",
    staged_path: str = "",
    staged_status: str = MODIFIED_GIT_STATUS,
    child_output: str = "",
    create_repo_file: str | None = None,
) -> RunObservation:
    """Run the selected check against scripted git state and record the run."""

    runner = selected_gate_runner_for_paths(
        branch_path=branch_path,
        branch_old_path=branch_old_path,
        branch_status=branch_status,
        branch_returncode=branch_returncode,
        branch_stderr=branch_stderr,
        staged_path=staged_path,
        staged_status=staged_status,
    )
    sink = io.StringIO()
    spawner = RecordingSpawner(
        exit_codes=[os.EX_OK] * _CHILD_OUTPUT_BUDGET,
        outputs=[child_output] * _CHILD_OUTPUT_BUDGET if child_output else (),
        observed_sink=sink,
    )
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        if create_repo_file is not None:
            (repo / create_repo_file).parent.mkdir(parents=True, exist_ok=True)
            (repo / create_repo_file).touch()
        exit_code = run_selected_check(
            spawner=spawner,
            sink=sink,
            repo=repo,
            runner=runner,
        )
    return _run_observation(
        exit_code=exit_code,
        sink=sink,
        spawner=spawner,
        runner_calls=tuple(runner.calls),
    )


def _run_observation(
    *,
    exit_code: int,
    sink: io.StringIO,
    spawner: RecordingSpawner,
    runner_calls: tuple[tuple[str, ...], ...],
) -> RunObservation:
    output = sink.getvalue()
    return RunObservation(
        exit_code=exit_code,
        output=output,
        spawn_calls=tuple(spawner.spawn_calls),
        runner_calls=runner_calls,
        output_before_first_spawn=(
            spawner.sink_at_spawn[0] if spawner.sink_at_spawn else output
        ),
        summary=_reported_summary(output),
    )


def _reported_summary(output: str) -> dict[str, object] | None:
    """Read the structured summary whose path the run printed, if it printed one."""

    reported = [
        line.removeprefix(SUMMARY_PATH_LABEL).strip()
        for line in output.splitlines()
        if line.startswith(SUMMARY_PATH_LABEL)
    ]
    if not reported:
        return None
    return read_summary(Path(reported[-1]))


def check_full_observation() -> RunObservation:
    """Run the entry point's explicit full-verification recipe with scripted children."""

    sink = io.StringIO()
    spawner = RecordingSpawner(
        exit_codes=[os.EX_OK] * _CHILD_OUTPUT_BUDGET, observed_sink=sink
    )
    exit_code = validation_main([RECIPE_CHECK_FULL], spawner=spawner, sink=sink)
    return _run_observation(
        exit_code=exit_code,
        sink=sink,
        spawner=spawner,
        runner_calls=(),
    )


def entry_point_check_observation(repo: Path) -> RunObservation:
    """Run the entry point's selected-check recipe with ``repo`` as working directory.

    The entry point resolves its repository from the working directory, so the
    harness enters ``repo`` for the run and restores the prior directory.
    """

    sink = io.StringIO()
    spawner = RecordingSpawner(exit_codes=[os.EX_OK], observed_sink=sink)
    previous = Path.cwd()
    os.chdir(repo)
    try:
        exit_code = validation_main([RECIPE_CHECK], spawner=spawner, sink=sink)
    finally:
        os.chdir(previous)
    return _run_observation(
        exit_code=exit_code,
        sink=sink,
        spawner=spawner,
        runner_calls=(),
    )


class CredentialAvailability(StrEnum):
    """Whether live-discovery credentials are present in the process environment."""

    PRESENT = "present"
    ABSENT = "absent"


# Every environment name through which live discovery finds a credential: the
# mode selector, each credential variable, and the home holding a saved login.
_DISCOVERY_CREDENTIAL_NAMES = (
    DISCOVERY_AUTH_MODE_ENVIRONMENT,
    CODEX_HOME_ENV,
    *sorted(CREDENTIAL_ENVIRONMENTS),
)


def _present_credential_environment() -> dict[str, str]:
    """The API-mode selection with the inert fixture's key as its credential."""

    document = json.loads(API_FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        DISCOVERY_AUTH_MODE_ENVIRONMENT: AuthenticationMode.API.value,
        CODEX_API_KEY_ENVIRONMENT: document[SAVED_LOGIN_API_KEY_FIELD],
    }


@contextmanager
def discovery_credentials(availability: CredentialAvailability) -> Iterator[None]:
    """Hold the process environment at one credential availability for the block.

    Present selects API-mode discovery with a key; absent removes every mode
    selector and credential variable and points the saved-login home at an
    empty directory. The prior environment is restored on every exit path.
    """

    saved = {name: os.environ.get(name) for name in _DISCOVERY_CREDENTIAL_NAMES}
    with TemporaryDirectory() as empty_home:
        for name in _DISCOVERY_CREDENTIAL_NAMES:
            os.environ.pop(name, None)
        if availability is CredentialAvailability.PRESENT:
            os.environ.update(_present_credential_environment())
        else:
            os.environ[CODEX_HOME_ENV] = empty_home
        try:
            yield
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


_Observed = TypeVar("_Observed")


def across_credential_availability(
    observe: Callable[[], _Observed],
) -> dict[CredentialAvailability, _Observed]:
    """Return ``observe()`` taken once under each credential availability."""

    observed: dict[CredentialAvailability, _Observed] = {}
    for availability in CredentialAvailability:
        with discovery_credentials(availability):
            observed[availability] = observe()
    return observed


@contextmanager
def repository_without_origin() -> Iterator[Path]:
    """Yield a real git repository that has no origin remote."""

    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        build_repo_without_origin(repo)
        yield repo


def production_check_observation(repo: Path) -> RunObservation:
    """Run the production selected check, with its real base-ref resolution, in ``repo``."""

    sink = io.StringIO()
    spawner = RecordingSpawner(exit_codes=[os.EX_OK], observed_sink=sink)
    exit_code = production_run_selected_check(
        spawner=spawner,
        sink=sink,
        repo=repo,
    )
    return _run_observation(
        exit_code=exit_code,
        sink=sink,
        spawner=spawner,
        runner_calls=(),
    )


def failing_discovery_runner(*, stdout: str, stderr: str) -> RecordingGitRunner:
    """A git runner whose branch discovery fails with ``stdout`` and ``stderr``."""

    return selected_gate_runner_for_paths(
        branch_path=stdout,
        branch_returncode=GIT_DISCOVERY_FAILURE_EXIT_CODE,
        branch_stderr=stderr,
    )


def captured_property_failure_notes(
    failing_property: Callable[[], None],
) -> tuple[str, ...]:
    """Run a configured property expected to fail and return its error notes."""

    try:
        failing_property()
    except Exception as error:  # noqa: BLE001 - the notes of any failure are the observation
        return tuple(getattr(error, "__notes__", ()))
    return ()


@dataclass
class RecordingHandle:
    """A ProcessHandle that returns a scripted exit code on wait().

    poll() returns None until wait() has been called once, then returns the
    scripted exit code. send_signal_to_group records the signal but does not
    affect the next poll()/wait() — tests that need "child ignores SIGTERM"
    behavior can use this directly; tests that need "child exits on SIGTERM"
    should set `exit_on_signal=True`.
    """

    pid: int
    exit_code: int
    exit_on_signal: bool = False
    received_signals: list[int] = field(default_factory=list)
    _exited: bool = False

    def poll(self) -> int | None:
        if self._exited:
            return self.exit_code
        return None

    def wait(self) -> int:
        self._exited = True
        return self.exit_code

    def send_signal_to_group(self, sig: int) -> None:
        self.received_signals.append(sig)
        if self.exit_on_signal:
            self._exited = True


@dataclass
class RecordingSpawner:
    """A ProcessSpawner that returns scripted handles in order of spawn calls.

    The exit_codes sequence drives the i-th spawn() call's handle. spawn_calls
    records the argv tuples passed to spawn(), in order. When observed_sink is
    the run's live sink, sink_at_spawn records its content at each spawn() call.
    """

    exit_codes: Sequence[int]
    outputs: Sequence[str] = ()
    observed_sink: io.StringIO | None = None
    spawn_calls: list[tuple[str, ...]] = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)
    written_outputs: list[str] = field(default_factory=list)
    sink_at_spawn: list[str] = field(default_factory=list)
    handles: list[RecordingHandle] = field(default_factory=list)
    _next_pid: int = 10_000

    def spawn(self, argv: Sequence[str], output_path: Path) -> ProcessHandle:
        index = len(self.spawn_calls)
        if self.observed_sink is not None:
            self.sink_at_spawn.append(self.observed_sink.getvalue())
        self.spawn_calls.append(tuple(argv))
        self.output_paths.append(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output = self.outputs[index] if index < len(self.outputs) else ""
        output_path.write_text(output, encoding="utf-8")
        self.written_outputs.append(output)
        exit_code = self.exit_codes[index] if index < len(self.exit_codes) else 0
        handle = RecordingHandle(pid=self._next_pid + index, exit_code=exit_code)
        self.handles.append(handle)
        return handle


@dataclass
class RecordingGitRunner:
    """A git runner double keyed by command argv."""

    outputs: Mapping[tuple[str, ...], GitCommandResult]
    calls: list[tuple[str, ...]] = field(default_factory=list)
    repos: list[Path] = field(default_factory=list)

    def __call__(self, command: Sequence[str], repo: Path) -> GitCommandResult:
        key = tuple(command)
        self.calls.append(key)
        self.repos.append(repo)
        return self.outputs[key]


@dataclass
class SignalRaisingSpawner:
    """A ProcessSpawner that raises a real signal during spawn()."""

    signum: int
    spawn_calls: list[tuple[str, ...]] = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)

    def spawn(self, argv: Sequence[str], output_path: Path) -> ProcessHandle:
        self.spawn_calls.append(tuple(argv))
        self.output_paths.append(output_path)
        os.kill(os.getpid(), self.signum)
        msg = "signal handler returned without interrupting"
        raise RuntimeError(msg)


@dataclass
class SpawnFailingSpawner:
    """A ProcessSpawner that fails before it can return a handle."""

    message: str
    spawn_calls: list[tuple[str, ...]] = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)

    def spawn(self, argv: Sequence[str], output_path: Path) -> ProcessHandle:
        self.spawn_calls.append(tuple(argv))
        self.output_paths.append(output_path)
        raise OSError(self.message)


@dataclass
class HangingHandle:
    """A ProcessHandle that never exits on its own — for signal-handling tests.

    poll() always returns None. wait() blocks indefinitely (tests should not
    call wait directly on this; the signal handler escalates to SIGKILL after
    the grace period). send_signal_to_group records the signal; if
    `exit_on_kill=True`, a subsequent poll() returns the killed exit status
    after SIGKILL is received.
    """

    pid: int
    exit_on_kill: bool = True
    received_signals: list[int] = field(default_factory=list)
    poll_calls: int = 0
    _killed: bool = False

    def poll(self) -> int | None:
        self.poll_calls += 1
        if self._killed:
            return KILLED_EXIT_CODE
        return None

    def wait(self) -> int:
        if self._killed:
            return KILLED_EXIT_CODE
        msg = "HangingHandle.wait would block indefinitely"
        raise RuntimeError(msg)

    def send_signal_to_group(self, sig: int) -> None:
        self.received_signals.append(sig)
        if self.exit_on_kill and sig == signal.SIGKILL:
            self._killed = True


class SleepBudgetExceeded(RuntimeError):
    """A controlled clock received more sleep calls than its budget allows."""

    def __init__(self, max_sleep_calls: int) -> None:
        self.max_sleep_calls = max_sleep_calls
        super().__init__(
            f"signal shutdown exceeded its bounded sleep budget of {max_sleep_calls}"
        )


@dataclass
class BoundedAdvancingClock:
    """A clock that advances on sleep and stops an unbounded wait."""

    max_sleep_calls: int
    current: float = 0.0
    monotonic_calls: int = 0
    sleep_calls: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        self.monotonic_calls += 1
        return self.current

    def sleep(self, seconds: float) -> None:
        if len(self.sleep_calls) >= self.max_sleep_calls:
            raise SleepBudgetExceeded(self.max_sleep_calls)
        self.sleep_calls.append(seconds)
        self.current += seconds


__all__ = [
    "HangingHandle",
    "RecordingGitRunner",
    "RecordingHandle",
    "RecordingSpawner",
    "SignalRaisingSpawner",
    "SpawnFailingSpawner",
]


# The double classes implement the Protocols structurally.
_: type[ProcessSpawner] = RecordingSpawner
_2: type[ProcessHandle] = RecordingHandle
_3: type[ProcessHandle] = HangingHandle
_4: type[ProcessSpawner] = SignalRaisingSpawner
_5: type[ProcessSpawner] = SpawnFailingSpawner
