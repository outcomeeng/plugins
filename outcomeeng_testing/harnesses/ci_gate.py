"""Harness-owned CI gate workflow parsing for compliance tests."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

import yaml

from outcomeeng.validation import VALIDATION_STEPS
from outcomeeng.validation.ci_gate import CONTINUE_ON_ERROR_DISABLED, GATE_JOB_NAME

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
GATE_WORKFLOW: Final = REPO_ROOT / ".github" / "workflows" / "check.yml"
PROJECT_METADATA: Final = REPO_ROOT / "pyproject.toml"

GATE_JOB: Final = GATE_JOB_NAME


@dataclass(frozen=True)
class CiToolchainObservation:
    """Raw job environment, action, command, and step-environment observations."""

    job_environment: frozenset[str]
    action_references: tuple[str, ...]
    run_commands: tuple[str, ...]
    step_environments: tuple[tuple[str, frozenset[str]], ...]


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
    continue_on_error: str
    has_condition: bool


@dataclass(frozen=True)
class GateJobObservation:
    """The gate job's own condition and soft-pass surface."""

    has_condition: bool
    continue_on_error: str


@dataclass(frozen=True)
class GatePythonObservation:
    """Python versions the workflow provisions and the project declares."""

    workflow_version: str
    project_version: str


def workflow() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        yaml.load(GATE_WORKFLOW.read_text(), Loader=yaml.BaseLoader),
    )


def gate_job(workflow_data: dict[str, Any]) -> dict[str, Any]:
    return cast("dict[str, Any]", workflow_data["jobs"][GATE_JOB])


def gate_steps(workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
    return cast("list[dict[str, Any]]", gate_job(workflow_data)["steps"])


def setup_python_version(workflow_data: dict[str, Any]) -> str:
    setup_step = next(
        step
        for step in gate_steps(workflow_data)
        if step.get("name") == "Set up Python"
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


def observe_gate_triggers() -> GateTriggerObservation:
    """Return the events and push branches the gate workflow declares."""
    on_section = cast("dict[str, object]", workflow()["on"])
    push_section = cast("dict[str, object]", on_section.get("push", {}))
    return GateTriggerObservation(
        events=frozenset(on_section),
        push_branches=tuple(cast("list[str]", push_section.get("branches", []))),
    )


def observe_gate_run_commands() -> tuple[str, ...]:
    """Return every normalized `run:` body the gate job declares."""
    return tuple(
        cast("str", step["run"]).strip()
        for step in gate_steps(workflow())
        if "run" in step
    )


def observe_validation_step_argvs() -> frozenset[tuple[str, ...]]:
    """Return the argv of every step the full validation recipe composes."""
    return frozenset(step.argv for step in VALIDATION_STEPS)


def observe_ci_toolchain() -> CiToolchainObservation:
    """Return the workflow surfaces that provision and authenticate gate tools."""
    workflow_data = workflow()
    env = cast("dict[str, str]", gate_job(workflow_data)["env"])
    steps = gate_steps(workflow_data)
    runs = tuple(
        cast("str", step["run"]) for step in gate_steps(workflow_data) if "run" in step
    )
    return CiToolchainObservation(
        job_environment=frozenset(env),
        action_references=tuple(
            cast("str", step["uses"]) for step in steps if "uses" in step
        ),
        run_commands=runs,
        step_environments=tuple(
            (
                cast("str", step.get("name", "")),
                frozenset(cast("dict[str, str]", step.get("env", {}))),
            )
            for step in steps
        ),
    )


def observe_gate_python_versions() -> GatePythonObservation:
    """Return the workflow-provisioned and project-declared Python versions."""
    return GatePythonObservation(
        workflow_version=setup_python_version(workflow()),
        project_version=required_python_version(),
    )


def observe_gate_steps() -> tuple[GateStepObservation, ...]:
    """Return each gate step's condition, soft-pass surface, and shell body."""
    observations: list[GateStepObservation] = []
    for step in gate_steps(workflow()):
        run = cast("str", step.get("run", ""))
        observations.append(
            GateStepObservation(
                name=cast("str", step.get("name", "")),
                run=run,
                shell_lines=tuple(shell_lines(run)),
                continue_on_error=cast(
                    "str", step.get("continue-on-error", CONTINUE_ON_ERROR_DISABLED)
                ),
                has_condition="if" in step,
            )
        )
    return tuple(observations)


def observe_gate_job() -> GateJobObservation:
    """Return the gate job's own condition and soft-pass surface."""
    job = gate_job(workflow())
    return GateJobObservation(
        has_condition="if" in job,
        continue_on_error=cast(
            "str", job.get("continue-on-error", CONTINUE_ON_ERROR_DISABLED)
        ),
    )
