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
        reaches another step
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, cast

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


StepEnvironment = tuple[str, Mapping[str, str]]


def _environment(section: Mapping[str, Any]) -> dict[str, str]:
    return dict(cast("dict[str, str]", section.get(WORKFLOW_ENVIRONMENT_KEY) or {}))


def effective_step_environments(
    workflow: Mapping[str, Any],
) -> tuple[StepEnvironment, ...]:
    """Return each gate-job step's normalized `run:` body and the environment it receives."""

    job = cast("Mapping[str, Any]", workflow[WORKFLOW_JOBS_KEY][GATE_JOB_NAME])
    inherited = {**_environment(workflow), **_environment(job)}
    return tuple(
        (
            cast("str", step.get(STEP_RUN_KEY, "")).strip(),
            {**inherited, **_environment(step)},
        )
        for step in cast("list[Mapping[str, Any]]", job[JOB_STEPS_KEY])
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

    workflow = cast(
        "Mapping[str, Any]",
        yaml.load(workflow_path.read_text(), Loader=yaml.BaseLoader),
    )
    return credential_violations(effective_step_environments(workflow))


def main() -> int:
    """Report each credential violation of the committed gate workflow."""

    violations = workflow_credential_violations()
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
    "credential_violations",
    "effective_step_environments",
    "main",
    "workflow_credential_violations",
]
