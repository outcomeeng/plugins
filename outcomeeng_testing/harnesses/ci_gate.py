"""Harness-owned CI gate workflow parsing for compliance tests."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, cast

import yaml

from outcomeeng.validation import VALIDATION_STEPS
from outcomeeng.validation.ci_gate import (
    GATE_JOB_NAME,
    JOB_TIMEOUT_KEY,
    SPX_COMMIT_ENVIRONMENT,
    PYTHON_SETUP_STEP_NAME,
    REUSABLE_WORKFLOW_CALL_KEY,
    WORKFLOW_FILE_GLOBS,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WORKFLOW_DIRECTORY: Final = REPO_ROOT / ".github" / "workflows"
GATE_WORKFLOW: Final = WORKFLOW_DIRECTORY / "check.yml"


def workflow_paths(directory: Path | None = None) -> tuple[Path, ...]:
    """Return every workflow file in a directory, across both YAML extensions."""
    source = WORKFLOW_DIRECTORY if directory is None else directory
    return tuple(
        sorted(path for glob in WORKFLOW_FILE_GLOBS for path in source.glob(glob))
    )


PROJECT_METADATA: Final = REPO_ROOT / "pyproject.toml"


@dataclass(frozen=True)
class CiToolchainObservation:
    """Raw workflow, job, action, command, and step-environment observations.

    Each step environment is keyed by the step's normalized `run:` body, empty
    for a step that runs no command, so a step's name never decides which
    command its environment reaches. Every environment maps each name to the
    value the workflow writes for it. `run_environments` holds what a step
    declares itself; `effective_run_environments` holds what the step receives
    from the workflow, the job, and the step together, a narrower scope's value
    replacing a wider one's.
    """

    workflow_environment: Mapping[str, str]
    job_environment: Mapping[str, str]
    action_references: tuple[str, ...]
    run_commands: tuple[str, ...]
    run_environments: tuple[tuple[str, Mapping[str, str]], ...]
    effective_run_environments: tuple[tuple[str, Mapping[str, str]], ...]


@dataclass(frozen=True)
class GateTriggerObservation:
    """Events and push branches the gate workflow declares."""

    events: frozenset[str]
    push_branches: tuple[str, ...]


@dataclass(frozen=True)
class GateStepObservation:
    """One gate step's condition, soft-pass surface, and shell body."""

    name: str
    run: str
    shell_lines: tuple[str, ...]
    continue_on_error: str | None
    has_condition: bool


@dataclass(frozen=True)
class GateJobObservation:
    """The gate job's own condition, soft-pass, and completion-bound surface."""

    has_condition: bool
    continue_on_error: str | None
    timeout_minutes: str | None


@dataclass(frozen=True)
class WorkflowJobObservation:
    """One workflow job's identity, call kind, and declared completion bound."""

    workflow: str
    job: str
    calls_reusable_workflow: bool
    timeout_minutes: str | None


@dataclass(frozen=True)
class SpxSourceObservation:
    """The spx commit pin and every repository checkout the gate job declares."""

    commit_pin: str | None
    checkouts: tuple[tuple[str | None, str | None], ...]


@dataclass(frozen=True)
class GatePythonObservation:
    """Python versions the workflow provisions and the project declares."""

    workflow_version: str
    project_version: str


CI_GATE_FIXTURES: Final = REPO_ROOT / "outcomeeng_testing" / "fixtures" / "ci_gate"


# Each fixture under this name puts a gate credential on the `just check-full`
# step from one scope or step layout.
CREDENTIAL_VIOLATION_FIXTURE_GLOB: Final = "credentials_*.yml"
# Each fixture under this name gives the `just test-l3` step every credential
# name with one value other than the one the gate requires.
L3_VALUE_VIOLATION_FIXTURE_GLOB: Final = "l3_value_*.yml"


def gate_fixture_path(name: str) -> Path:
    """Return the path to an inert violating- or conforming-workflow fixture."""
    return CI_GATE_FIXTURES / name


def credential_violation_fixture_paths() -> tuple[Path, ...]:
    """Return every inert fixture that reaches the full-gate step with a credential."""
    return tuple(sorted(CI_GATE_FIXTURES.glob(CREDENTIAL_VIOLATION_FIXTURE_GLOB)))


def l3_value_violation_fixture_paths() -> tuple[Path, ...]:
    """Return every inert fixture that gives the L3 step a wrong credential value."""
    return tuple(sorted(CI_GATE_FIXTURES.glob(L3_VALUE_VIOLATION_FIXTURE_GLOB)))


def workflow(workflow_path: Path | None = None) -> dict[str, Any]:
    source = GATE_WORKFLOW if workflow_path is None else workflow_path
    return cast(
        "dict[str, Any]",
        yaml.load(source.read_text(), Loader=yaml.BaseLoader),
    )


def gate_job(workflow_data: dict[str, Any]) -> dict[str, Any]:
    return cast("dict[str, Any]", workflow_data["jobs"][GATE_JOB_NAME])


def gate_steps(workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
    return cast("list[dict[str, Any]]", gate_job(workflow_data)["steps"])


def setup_python_version(workflow_data: dict[str, Any]) -> str:
    setup_step = next(
        step
        for step in gate_steps(workflow_data)
        if step.get("name") == PYTHON_SETUP_STEP_NAME
    )
    return cast("str", setup_step["with"]["python-version"])


def required_python_version() -> str:
    metadata = tomllib.loads(PROJECT_METADATA.read_text())
    requires_python = cast("str", metadata["project"]["requires-python"])
    return requires_python.removeprefix(">=")


def shell_lines(run: str) -> list[str]:
    return [
        line.strip()
        for line in run.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def observe_gate_triggers(workflow_path: Path | None = None) -> GateTriggerObservation:
    """Return the events and push branches the gate workflow declares."""
    on_section = cast("dict[str, object]", workflow(workflow_path)["on"])
    push_section = cast("dict[str, object]", on_section.get("push", {}))
    return GateTriggerObservation(
        events=frozenset(on_section),
        push_branches=tuple(cast("list[str]", push_section.get("branches", []))),
    )


def observe_gate_run_commands(workflow_path: Path | None = None) -> tuple[str, ...]:
    """Return every normalized `run:` body the gate job declares."""
    return tuple(
        cast("str", step["run"]).strip()
        for step in gate_steps(workflow(workflow_path))
        if "run" in step
    )


def observe_validation_step_argvs() -> frozenset[tuple[str, ...]]:
    """Return the argv of every step the full validation recipe composes."""
    return frozenset(step.argv for step in VALIDATION_STEPS)


def _environment(section: dict[str, Any]) -> Mapping[str, str]:
    return MappingProxyType(dict(cast("dict[str, str]", section.get("env", {}))))


def observe_ci_toolchain(
    workflow_path: Path | None = None,
) -> CiToolchainObservation:
    """Return the workflow surfaces that provision and authenticate gate tools."""
    workflow_data = workflow(workflow_path)
    workflow_env = _environment(workflow_data)
    env = _environment(gate_job(workflow_data))
    steps = gate_steps(workflow_data)
    runs = tuple(cast("str", step["run"]) for step in steps if "run" in step)
    run_environments = tuple(
        (cast("str", step.get("run", "")).strip(), _environment(step)) for step in steps
    )
    return CiToolchainObservation(
        workflow_environment=workflow_env,
        job_environment=env,
        action_references=tuple(
            cast("str", step["uses"]) for step in steps if "uses" in step
        ),
        run_commands=runs,
        run_environments=run_environments,
        effective_run_environments=tuple(
            (run_command, MappingProxyType({**workflow_env, **env, **step_env}))
            for run_command, step_env in run_environments
        ),
    )


def observe_gate_python_versions(
    workflow_path: Path | None = None,
) -> GatePythonObservation:
    """Return the workflow-provisioned and project-declared Python versions."""
    return GatePythonObservation(
        workflow_version=setup_python_version(workflow(workflow_path)),
        project_version=required_python_version(),
    )


def observe_gate_steps(
    workflow_path: Path | None = None,
) -> tuple[GateStepObservation, ...]:
    """Return each gate step's condition, soft-pass surface, and shell body."""
    observations: list[GateStepObservation] = []
    for step in gate_steps(workflow(workflow_path)):
        run = cast("str", step.get("run", ""))
        observations.append(
            GateStepObservation(
                name=cast("str", step.get("name", "")),
                run=run,
                shell_lines=tuple(shell_lines(run)),
                continue_on_error=cast("str | None", step.get("continue-on-error")),
                has_condition="if" in step,
            )
        )
    return tuple(observations)


def observe_gate_job(workflow_path: Path | None = None) -> GateJobObservation:
    """Return the gate job's own condition, soft-pass, and completion bound."""
    job = gate_job(workflow(workflow_path))
    return GateJobObservation(
        has_condition="if" in job,
        continue_on_error=cast("str | None", job.get("continue-on-error")),
        timeout_minutes=cast("str | None", job.get(JOB_TIMEOUT_KEY)),
    )


def observe_workflow_jobs(
    workflow_directory: Path | None = None,
) -> tuple[WorkflowJobObservation, ...]:
    """Return every job this repository declares in its own workflow files."""
    directory = WORKFLOW_DIRECTORY if workflow_directory is None else workflow_directory
    observations: list[WorkflowJobObservation] = []
    for path in workflow_paths(directory):
        jobs = cast("dict[str, Any]", workflow(path).get("jobs") or {})
        observations.extend(
            WorkflowJobObservation(
                workflow=path.name,
                job=job_id,
                calls_reusable_workflow=REUSABLE_WORKFLOW_CALL_KEY in job,
                timeout_minutes=cast("str | None", job.get(JOB_TIMEOUT_KEY)),
            )
            for job_id, job in jobs.items()
        )
    return tuple(observations)


def observe_spx_source(workflow_path: Path | None = None) -> SpxSourceObservation:
    """Return the spx commit pin and the (repository, ref) of each checkout step."""
    job = gate_job(workflow(workflow_path))
    env = cast("dict[str, str]", job.get("env", {}))
    checkouts = tuple(
        (
            cast("dict[str, str]", step.get("with", {})).get("repository"),
            cast("dict[str, str]", step.get("with", {})).get("ref"),
        )
        for step in gate_steps(workflow(workflow_path))
        if "actions/checkout@" in cast("str", step.get("uses", ""))
    )
    return SpxSourceObservation(
        commit_pin=env.get(SPX_COMMIT_ENVIRONMENT), checkouts=checkouts
    )
