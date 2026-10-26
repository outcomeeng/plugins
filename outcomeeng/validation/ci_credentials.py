"""Enforce which gate-job step receives the L3 credentials, and with which value.

Only the L3 tests read ``GH_TOKEN``, ``SUBAGENT_DISCOVERY_AUTH_MODE``, and
``OPENAI_API_KEY``, so the gate job's ``just test-l3`` step receives each with the
value ``CI_STEP_ENVIRONMENT_REQUIREMENTS`` names, and no other step receives any
of them. A step receives the workflow's, the job's, and its own environment, a
narrower scope's value replacing a wider one's, so a credential declared at any
of the three reaches the step.

Usage::

    uv run python -m outcomeeng.validation.ci_credentials

Exit codes:
    0 - The committed gate workflow meets every credential requirement
    1 - A credential is missing from the L3 step, carries another value, or
        reaches another step, or the workflow lacks the gate job's shape
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Final

import yaml

from outcomeeng.validation.ci_gate import (
    CI_STEP_ENVIRONMENT_REQUIREMENTS,
    GATE_JOB_NAME,
    CiStepEnvironmentRequirement,
)

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
GATE_WORKFLOW_PATH: Final = _REPO_ROOT / ".github" / "workflows" / "check.yml"
WORKFLOW_ENVIRONMENT_KEY: Final = "env"
WORKFLOW_JOBS_KEY: Final = "jobs"
JOB_STEPS_KEY: Final = "steps"
STEP_RUN_KEY: Final = "run"


class CredentialViolationKind(StrEnum):
    """How a gate step breaks a credential requirement."""

    MISSING = "missing"
    WRONG_VALUE = "wrong-value"
    FOREIGN_STEP = "foreign-step"


@dataclass(frozen=True)
class CredentialViolation:
    """One credential a gate step lacks, carries with another value, or must not receive."""

    kind: CredentialViolationKind
    run_command: str
    environment_name: str


class WorkflowShapeError(ValueError):
    """The workflow file lacks the shape the gate job's credential check reads."""


@dataclass(frozen=True)
class WorkflowStep:
    """One gate-job step: its normalized `run:` body and its own environment."""

    run_command: str
    environment: Mapping[str, str]


@dataclass(frozen=True)
class WorkflowJob:
    """One workflow job: its own environment and its steps in order."""

    environment: Mapping[str, str]
    steps: tuple[WorkflowStep, ...]


@dataclass(frozen=True)
class GateWorkflow:
    """A parsed workflow: its own environment and the gate job."""

    environment: Mapping[str, str]
    gate_job: WorkflowJob


StepEnvironment = tuple[str, Mapping[str, str]]


def _mapping(value: object, where: str) -> Mapping[object, object]:
    if not isinstance(value, Mapping):
        raise WorkflowShapeError(f"{where} is not a mapping")
    return value


def _string(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise WorkflowShapeError(f"{where} is not a string")
    return value


def _environment(section: Mapping[object, object], where: str) -> Mapping[str, str]:
    raw = section.get(WORKFLOW_ENVIRONMENT_KEY)
    if raw is None:
        return MappingProxyType({})
    where = f"{where} {WORKFLOW_ENVIRONMENT_KEY}"
    return MappingProxyType(
        {
            _string(name, where): _string(value, f"{where} {name}")
            for name, value in _mapping(raw, where).items()
        }
    )


def _step(value: object, where: str) -> WorkflowStep:
    step = _mapping(value, where)
    run = step.get(STEP_RUN_KEY, "")
    return WorkflowStep(
        run_command=_string(run, f"{where} {STEP_RUN_KEY}").strip(),
        environment=_environment(step, where),
    )


def parse_gate_workflow(text: str) -> GateWorkflow:
    """Parse workflow YAML into its environment and the gate job's typed steps.

    Raises ``WorkflowShapeError`` when the document, the gate job, a step, or an
    environment lacks the shape the credential check reads.
    """

    workflow = _mapping(yaml.load(text, Loader=yaml.BaseLoader), "the workflow")
    jobs = _mapping(workflow.get(WORKFLOW_JOBS_KEY), WORKFLOW_JOBS_KEY)
    where = f"job {GATE_JOB_NAME}"
    job = _mapping(jobs.get(GATE_JOB_NAME), where)
    steps = job.get(JOB_STEPS_KEY)
    if not isinstance(steps, list):
        raise WorkflowShapeError(f"{where} {JOB_STEPS_KEY} is not a list")
    return GateWorkflow(
        environment=_environment(workflow, "the workflow"),
        gate_job=WorkflowJob(
            environment=_environment(job, where),
            steps=tuple(
                _step(step, f"{where} step {index}") for index, step in enumerate(steps)
            ),
        ),
    )


def effective_step_environments(
    workflow: GateWorkflow,
) -> tuple[StepEnvironment, ...]:
    """Return each gate-job step's normalized `run:` body and the environment it receives."""

    job = workflow.gate_job
    inherited = {**workflow.environment, **job.environment}
    return tuple(
        (step.run_command, MappingProxyType({**inherited, **step.environment}))
        for step in job.steps
    )


def credential_violations(
    steps: Sequence[StepEnvironment],
    requirements: Sequence[CiStepEnvironmentRequirement] = (
        CI_STEP_ENVIRONMENT_REQUIREMENTS
    ),
) -> tuple[CredentialViolation, ...]:
    """Return every way ``steps`` break ``requirements``, in step and requirement order."""

    required = {
        (requirement.run_command, requirement.environment_name)
        for requirement in requirements
    }
    credentials = {requirement.environment_name for requirement in requirements}
    foreign = tuple(
        CredentialViolation(CredentialViolationKind.FOREIGN_STEP, run_command, name)
        for run_command, environment in steps
        for name in environment
        if name in credentials and (run_command, name) not in required
    )
    return foreign + tuple(
        violation
        for requirement in requirements
        for violation in _requirement_violations(steps, requirement)
    )


def _requirement_violations(
    steps: Sequence[StepEnvironment], requirement: CiStepEnvironmentRequirement
) -> tuple[CredentialViolation, ...]:
    values = [
        environment.get(requirement.environment_name)
        for run_command, environment in steps
        if run_command == requirement.run_command
    ]
    if not values or None in values:
        kind = CredentialViolationKind.MISSING
    elif any(value != requirement.value for value in values):
        kind = CredentialViolationKind.WRONG_VALUE
    else:
        return ()
    return (
        CredentialViolation(
            kind, requirement.run_command, requirement.environment_name
        ),
    )


def workflow_credential_violations(
    workflow_path: Path = GATE_WORKFLOW_PATH,
) -> tuple[CredentialViolation, ...]:
    """Return every credential violation the workflow file at ``workflow_path`` carries."""

    workflow = parse_gate_workflow(workflow_path.read_text())
    return credential_violations(effective_step_environments(workflow))


def main() -> int:
    """Report each credential violation of the committed gate workflow."""

    try:
        violations = workflow_credential_violations()
    except WorkflowShapeError as error:
        print(f"error: {GATE_WORKFLOW_PATH}: {error}")
        return 1
    for violation in violations:
        print(
            f"{violation.kind}: {violation.environment_name} on the gate step "
            f"running `{violation.run_command}`"
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "GATE_WORKFLOW_PATH",
    "CredentialViolation",
    "CredentialViolationKind",
    "GateWorkflow",
    "WorkflowJob",
    "WorkflowShapeError",
    "WorkflowStep",
    "credential_violations",
    "effective_step_environments",
    "main",
    "parse_gate_workflow",
    "workflow_credential_violations",
]
