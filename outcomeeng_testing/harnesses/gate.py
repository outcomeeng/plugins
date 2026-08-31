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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TextIO, cast

from hypothesis import given, seed, settings

from outcomeeng import validation as validation_pkg
from outcomeeng.validation import (
    CHECK_RECIPES,
    MYPY_ARGV,
    POST_KILL_REAP_ATTEMPTS,
    PURPOSE_CONFORMANCE,
    PREFLIGHT_STEPS,
    PYRIGHT_ARGV,
    RUFF_CHECK_ARGV,
    SIGNAL_GRACE_SECONDS,
    SIGNAL_POLL_INTERVAL_SECONDS,
    TEST_STEPS,
    VALIDATION_RECIPE,
    VALIDATION_STEPS,
    VERIFICATION_TYPE_VALIDATION,
    ProcessHandle,
    ProcessSpawner,
    Recipe,
    Step,
    run,
    run_check,
    run_recipe,
    terminate_process_group,
)
from outcomeeng.validation._git import GitCommandResult
from outcomeeng.validation.selected_gate import (
    DEFAULT_BASE_REF,
    GIT_DISCOVERY_FAILURE_EXIT_CODE,
    GIT_DIFF_BRANCH_ARGV_PREFIX,
    GIT_DIFF_STAGED_ARGV,
    GIT_DIFF_UNSTAGED_ARGV,
    GIT_LS_UNTRACKED_ARGV,
    SELECTED_CHECK_PLAN_HEADER,
    collect_changed_paths,
    run_selected_check as production_run_selected_check,
)
from outcomeeng_testing.generators.gate import (
    SELECTED_GATE_PYTHON_SOURCE_PATH,
    SELECTED_GATE_PYTHON_TEST_PATH,
    SELECTED_GATE_SKILL_PATH,
    SELECTED_GATE_WORKFLOW_PATH,
    selected_gate_changed_paths,
)
from outcomeeng_testing.harnesses.changeset_scope import build_repo_without_origin
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

SELECTED_GATE_PROPERTY_SEED = 20260705
SELECTED_GATE_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/tests/"
    "test_selected_gate.property.l1.py::"
    "test_selection_is_deterministic_for_path_order_and_duplicates"
)
SELECTED_GATE_PROPERTY_EXAMPLES = 40
STATIC_ANALYSIS_ARGVS = (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV)
PASS_EXIT_CODE = 0
FAIL_EXIT_CODE = 2
PASSING_CHILD_OUTPUT = "passing validator output"
FAILING_CHILD_OUTPUT_PREFIX = "failing validator output line"
SPAWN_FAILURE_MESSAGE = "missing executable"
HIGH_VOLUME_CHILD_OUTPUT = "\n".join("captured child output" for _ in range(200))
PYTEST_TARGET_ARG = (
    "spx/15-validation.enabler/65-gate.enabler/tests/test_gate.compliance.l1.py"
)
SELECTED_GATE_RENAMED_TARGET_ARG = "docs/renamed-selected-gate.py"
SELECTED_GATE_WHITESPACE_PATH = " docs/selected gate edge spaces.py "


def selected_check_plan_block(*, labels: Sequence[str], reason: str) -> str:
    """Expected selected-check plan block for tests that inspect CLI output."""

    lines = [SELECTED_CHECK_PLAN_HEADER, *(f"  {label}: {reason}" for label in labels)]
    return "\n".join(lines) + "\n"


def three_no_op_steps() -> tuple[Step, ...]:
    """Stable three-step recipe domain for orchestrator scenario tests."""

    return (
        Step(label="alpha", argv=("noop-alpha",)),
        Step(label="beta", argv=("noop-beta",)),
        Step(label="gamma", argv=("noop-gamma",)),
    )


def single_step_recipe(name: str) -> Recipe:
    """Recipe with one preflight and one recipe step."""

    return Recipe(
        name=name,
        verification_type=VERIFICATION_TYPE_VALIDATION,
        purpose=PURPOSE_CONFORMANCE,
        preflight_steps=(Step(label=f"{name}-preflight", argv=(f"{name}-preflight",)),),
        steps=(Step(label=f"{name}-step", argv=(f"{name}-step",)),),
    )


def read_summary(path: Path) -> dict[str, object]:
    """Read a validation summary JSON object."""

    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast("dict[str, object]", data)


def summary_steps(summary: dict[str, object]) -> list[dict[str, object]]:
    """Return typed step summaries."""

    steps = summary["steps"]
    assert isinstance(steps, list)
    for step in steps:
        assert isinstance(step, dict)
    return cast("list[dict[str, object]]", steps)


def summary_recipes(summary: dict[str, object]) -> list[dict[str, object]]:
    """Return typed recipe summaries."""

    recipes = summary["recipes"]
    assert isinstance(recipes, list)
    for recipe in recipes:
        assert isinstance(recipe, dict)
    return cast("list[dict[str, object]]", recipes)


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
    branch_status: str = "M",
    staged_status: str = "M",
    unstaged_status: str = "M",
    branch_returncode: int = 0,
    branch_stderr: str = "",
) -> RecordingGitRunner:
    """Build a git runner for selected-gate path discovery tests."""

    return RecordingGitRunner(
        outputs={
            (*GIT_DIFF_BRANCH_ARGV_PREFIX, f"{base_ref}...HEAD"): (
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


def selected_gate_branch_discovery_argv(
    base_ref: str = DEFAULT_BASE_REF,
) -> tuple[str, ...]:
    """Return the branch discovery argv used first by changed-path collection."""

    return (*GIT_DIFF_BRANCH_ARGV_PREFIX, f"{base_ref}...HEAD")


def selected_gate_changed_path_domain() -> tuple[str, str, str, str]:
    """Representative changed paths for selected local gate routing."""

    return (
        SELECTED_GATE_PYTHON_SOURCE_PATH,
        SELECTED_GATE_WORKFLOW_PATH,
        SELECTED_GATE_SKILL_PATH,
        SELECTED_GATE_PYTHON_TEST_PATH,
    )


def selected_gate_property(
    test_func: Callable[[list[str]], None],
) -> Callable[[], None]:
    """Run the selected-gate property with reproducible failure diagnostics."""

    configured = seed(SELECTED_GATE_PROPERTY_SEED)(
        settings(max_examples=SELECTED_GATE_PROPERTY_EXAMPLES, deadline=None)(
            given(paths=selected_gate_changed_paths())(test_func)
        )
    )

    def wrapper() -> None:
        run_replayable_property(
            configured,
            seed_value=SELECTED_GATE_PROPERTY_SEED,
            replay_path=SELECTED_GATE_PROPERTY_REPLAY_PATH,
        )

    return wrapper


def expected_full_check_spawn_calls() -> tuple[tuple[str, ...], ...]:
    """Expected argv calls when selected-check escalates to the full wrapper."""

    return tuple(
        step.argv
        for recipe in CHECK_RECIPES
        for step in (*PREFLIGHT_STEPS, *recipe.steps)
    )


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
    return PipelineRunObservation(
        exit_code=exit_code,
        output=sink.getvalue(),
        spawn_calls=tuple(spawner.spawn_calls),
        written_outputs=tuple(spawner.written_outputs),
        retained_logs=tuple(
            path.read_text(encoding="utf-8") if path.exists() else None
            for path in spawner.output_paths
        ),
    )


@dataclass(frozen=True)
class RecipeRunObservation:
    """One recipe run's exit code, output, child records, and summary."""

    exit_code: int
    output: str
    spawn_calls: tuple[tuple[str, ...], ...]
    written_outputs: tuple[str, ...]
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


def spawn_failure_observation(*, recipe: Recipe) -> RecipeRunObservation:
    """Run one recipe whose spawner fails before returning a handle."""

    spawner = SpawnFailingSpawner(message=SPAWN_FAILURE_MESSAGE)
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
        written_outputs=tuple(spawner.written_outputs),
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


def signal_interrupt_observation(signum: int) -> CheckRunObservation:
    """Run the check wrapper with a spawner that raises ``signum`` during spawn."""

    spawner = SignalRaisingSpawner(signum=signum)
    sink = io.StringIO()
    with TemporaryDirectory() as tmp:
        summary_path = Path(tmp) / "signal-summary.json"
        exit_code = run_check(
            spawner=spawner,
            sink=sink,
            recipes=(VALIDATION_RECIPE,),
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


def modules_with_while_true_sleep() -> tuple[str, ...]:
    """Name the gate modules holding a ``while True`` loop that sleeps."""

    offenders: list[str] = []
    for module_path in validation_package_modules():
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.While):
                continue
            test = node.test
            if not (isinstance(test, ast.Constant) and test.value is True):
                continue
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "sleep"
                ):
                    offenders.append(module_path.name)
    return tuple(sorted(set(offenders)))


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
    branch_status: str = "M",
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


RESOLVED_BASE_REF = "origin/release"


def resolved_base_observation() -> ResolvedBaseObservation:
    """Collect one branch path through a recording base-ref resolver."""

    branch_path = SELECTED_GATE_PYTHON_SOURCE_PATH
    resolver_repos: list[Path] = []

    def resolve_base_ref(candidate_repo: Path) -> str:
        resolver_repos.append(candidate_repo)
        return RESOLVED_BASE_REF

    runner = selected_gate_runner_for_paths(
        base_ref=RESOLVED_BASE_REF,
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
        base_ref=RESOLVED_BASE_REF,
        collected=collected,
        resolver_repos=tuple(resolver_repos),
        repo=repo,
        first_runner_call=runner.calls[0],
    )


@dataclass(frozen=True)
class RunObservation:
    """One selected-check run's exit code, live output, and spawned argvs."""

    exit_code: int
    output: str
    spawn_calls: tuple[tuple[str, ...], ...]
    runner_calls: tuple[tuple[str, ...], ...]


_CHILD_OUTPUT_BUDGET = (
    2 * len(PREFLIGHT_STEPS) + len(VALIDATION_STEPS) + len(TEST_STEPS)
)


def run_check_observation(
    *,
    branch_path: str = "",
    branch_old_path: str = "",
    branch_status: str = "M",
    branch_returncode: int = 0,
    branch_stderr: str = "",
    staged_path: str = "",
    staged_status: str = "M",
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
    spawner = RecordingSpawner(
        exit_codes=[os.EX_OK] * _CHILD_OUTPUT_BUDGET,
        outputs=[child_output] * _CHILD_OUTPUT_BUDGET if child_output else (),
    )
    sink = io.StringIO()
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
    return RunObservation(
        exit_code=exit_code,
        output=sink.getvalue(),
        spawn_calls=tuple(spawner.spawn_calls),
        runner_calls=tuple(runner.calls),
    )


def missing_origin_observation() -> RunObservation:
    """Run the production selected check in a repository with no origin."""

    spawner = RecordingSpawner(exit_codes=[os.EX_OK])
    sink = io.StringIO()
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        build_repo_without_origin(repo)
        exit_code = production_run_selected_check(
            spawner=spawner,
            sink=sink,
            repo=repo,
        )
    return RunObservation(
        exit_code=exit_code,
        output=sink.getvalue(),
        spawn_calls=tuple(spawner.spawn_calls),
        runner_calls=(),
    )


GIT_DISCOVERY_FAILURE_STDOUT = "fatal: bad revision"
GIT_DISCOVERY_FAILURE_STDERR = "fatal: ambiguous argument"


def failing_discovery_runner() -> RecordingGitRunner:
    """A git runner whose branch discovery fails with scripted diagnostics."""

    return selected_gate_runner_for_paths(
        branch_path=GIT_DISCOVERY_FAILURE_STDOUT,
        branch_returncode=GIT_DISCOVERY_FAILURE_EXIT_CODE,
        branch_stderr=GIT_DISCOVERY_FAILURE_STDERR,
    )


def captured_property_failure_notes(
    failing_property: Callable[[], None],
) -> tuple[str, ...]:
    """Run a configured property expected to fail and return its error notes."""

    try:
        failing_property()
    except AssertionError as error:
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
    records the argv tuples passed to spawn(), in order.
    """

    exit_codes: Sequence[int]
    outputs: Sequence[str] = ()
    spawn_calls: list[tuple[str, ...]] = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)
    written_outputs: list[str] = field(default_factory=list)
    handles: list[RecordingHandle] = field(default_factory=list)
    _next_pid: int = 10_000

    def spawn(self, argv: Sequence[str], output_path: Path) -> ProcessHandle:
        index = len(self.spawn_calls)
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
    written_outputs: list[str] = field(default_factory=list)

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
    `exit_on_kill=True`, a subsequent poll() returns 137 after SIGKILL (9)
    is received.
    """

    pid: int
    exit_on_kill: bool = True
    received_signals: list[int] = field(default_factory=list)
    poll_calls: int = 0
    _killed: bool = False

    def poll(self) -> int | None:
        self.poll_calls += 1
        if self._killed:
            return 137
        return None

    def wait(self) -> int:
        if self._killed:
            return 137
        msg = "HangingHandle.wait would block indefinitely"
        raise RuntimeError(msg)

    def send_signal_to_group(self, sig: int) -> None:
        self.received_signals.append(sig)
        if self.exit_on_kill and sig == 9:
            self._killed = True


@dataclass
class BoundedAdvancingClock:
    """A clock that advances on sleep and rejects an unbounded wait."""

    max_sleep_calls: int
    current: float = 0.0
    monotonic_calls: int = 0
    sleep_calls: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        self.monotonic_calls += 1
        return self.current

    def sleep(self, seconds: float) -> None:
        if len(self.sleep_calls) >= self.max_sleep_calls:
            raise AssertionError("signal shutdown exceeded its bounded sleep budget")
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
