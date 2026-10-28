"""Harness for the native profile acceptance workflow's declared policy.

The harness reads workflow files from disk, so the observations come from the
declaration the CI provider reads. It returns observations only; linked tests
own every comparison.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from outcomeeng.validation.ci_gate import (
    GATE_JOB_NAME,
    JOB_ENV_KEY,
    WORKFLOW_JOBS_KEY,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
NATIVE_ACCEPTANCE_WORKFLOW: Final = (
    REPO_ROOT / ".github" / "workflows" / "native-profile-acceptance.yml"
)
FIXTURE_ROOT: Final = (
    Path(__file__).resolve().parents[1] / "fixtures" / "native_acceptance_workflow"
)
TRIGGER_FIXTURES: Final = FIXTURE_ROOT / "triggers"
POLICY_FIXTURES: Final = FIXTURE_ROOT / "policy"
PIN_SOURCE_FIXTURES: Final = FIXTURE_ROOT / "pin_source"
PIN_READ_STEP_NAME: Final = "Read tool pins from the quality gate workflow"
PIN_SOURCE_WORKFLOW: Final = REPO_ROOT / ".github" / "workflows" / "check.yml"
PIN_SOURCE_RELATIVE_PATH: Final = Path(".github") / "workflows" / "check.yml"
_SHELL: Final = "bash"
_GITHUB_ENV_VARIABLE: Final = "GITHUB_ENV"
_ENVIRONMENT_ASSIGNMENT: Final = re.compile(r"^(\w+)=(.*)$")
_JUST_COMMAND: Final = "just"
_SHELL_VARIABLE: Final = re.compile(r"\$\{(\w+)\}")
_EXPRESSION_VARIABLE: Final = re.compile(r"\$\{\{\s*env\.(\w+)\s*\}\}")


@dataclass(frozen=True)
class WorkflowStep:
    """One step's name, run body, action reference, inputs, and step-level environment."""

    name: str | None
    run: str | None
    uses: str | None
    inputs: Mapping[str, str]
    env: Mapping[str, str]


@dataclass(frozen=True)
class WorkflowJob:
    """One job's runner, job-level environment, and ordered steps."""

    runs_on: str
    env: Mapping[str, str]
    steps: tuple[WorkflowStep, ...]


@dataclass(frozen=True)
class AcceptanceWorkflow:
    """The events a workflow file declares and the jobs it runs."""

    triggers: frozenset[str]
    jobs: tuple[WorkflowJob, ...]


def violating_trigger_workflow_paths() -> tuple[Path, ...]:
    """Return the inert workflow files that each declare a forbidden trigger."""
    return tuple(sorted(TRIGGER_FIXTURES.glob("*.yml")))


def violating_policy_workflow_paths() -> tuple[Path, ...]:
    """Return the inert workflow files that each violate one run policy."""
    return tuple(sorted(POLICY_FIXTURES.glob("*.yml")))


def observe_acceptance_workflow(path: Path | None = None) -> AcceptanceWorkflow:
    """Return what a workflow file declares; without an argument, the committed one."""
    source = NATIVE_ACCEPTANCE_WORKFLOW if path is None else path
    document = yaml.load(source.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    declared = document["on"]
    triggers = frozenset({declared} if isinstance(declared, str) else declared)
    return AcceptanceWorkflow(
        triggers=triggers,
        jobs=tuple(_job(job) for job in document["jobs"].values()),
    )


def _job(document: Mapping[str, object]) -> WorkflowJob:
    return WorkflowJob(
        runs_on=str(document["runs-on"]),
        env=dict(document.get("env", {})),  # type: ignore[call-overload]
        steps=tuple(_step(step) for step in document["steps"]),  # type: ignore[attr-defined]
    )


def _step(document: Mapping[str, object]) -> WorkflowStep:
    return WorkflowStep(
        name=document.get("name"),  # type: ignore[arg-type]
        run=document.get("run"),  # type: ignore[arg-type]
        uses=document.get("uses"),  # type: ignore[arg-type]
        inputs=dict(document.get("with", {})),  # type: ignore[call-overload]
        env=dict(document.get("env", {})),  # type: ignore[call-overload]
    )


def resolve_environment_references(text: str, environment: Mapping[str, str]) -> str:
    """Substitute `${NAME}` and `${{ env.NAME }}` with the job environment's values."""

    def substitute(match: re.Match[str]) -> str:
        return environment.get(match.group(1), match.group(0))

    return _EXPRESSION_VARIABLE.sub(substitute, _SHELL_VARIABLE.sub(substitute, text))


def recipe_artifact_directories(job: WorkflowJob, recipe: str) -> tuple[Path, ...]:
    """The resolved directory argument of every `just <recipe>` command in the job's run bodies."""
    directories: list[Path] = []
    for step in job.steps:
        for line in (step.run or "").splitlines():
            tokens = (
                shlex.split(line.strip(), posix=True)
                if line.strip().startswith(f"{_JUST_COMMAND} ")
                else []
            )
            if len(tokens) >= 3 and tokens[1] == recipe:
                directories.append(
                    Path(resolve_environment_references(tokens[2], job.env))
                )
    return tuple(directories)


def uploaded_paths(job: WorkflowJob, action: str) -> tuple[Path, ...]:
    """The resolved `path` input of every step that uses the named upload action."""
    paths: list[Path] = []
    for step in job.steps:
        if step.uses is not None and step.uses.partition("@")[0] == action:
            for line in step.inputs.get("path", "").splitlines():
                if line.strip():
                    paths.append(
                        Path(resolve_environment_references(line.strip(), job.env))
                    )
    return tuple(paths)


@dataclass(frozen=True)
class PinReadRun:
    """The exit status, diagnostics, and environment file one pin-reading run produced."""

    returncode: int
    stderr: str
    environment: Mapping[str, str]


def violating_pin_source_paths() -> tuple[Path, ...]:
    """Return the inert quality gate workflow files that each format their pins differently."""
    return tuple(sorted(PIN_SOURCE_FIXTURES.glob("*.yml")))


def observe_pin_source_environment(path: Path | None = None) -> Mapping[str, str]:
    """The pin values the quality gate job's environment declares, read as YAML."""
    source = PIN_SOURCE_WORKFLOW if path is None else path
    document = yaml.load(source.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    return dict(document[WORKFLOW_JOBS_KEY][GATE_JOB_NAME][JOB_ENV_KEY])


def pin_read_step(job: WorkflowJob) -> WorkflowStep:
    """The job step that reads the tool pins from the quality gate workflow."""
    return next(step for step in job.steps if step.name == PIN_READ_STEP_NAME)


def shell_variable_references(job: WorkflowJob) -> frozenset[str]:
    """Every `${NAME}` the job's run bodies outside the pin-reading step reference."""
    pin_step = pin_read_step(job)
    return frozenset(
        match.group(1)
        for step in job.steps
        if step is not pin_step
        for match in _SHELL_VARIABLE.finditer(step.run or "")
    )


def run_pin_read_step(job: WorkflowJob, pin_source: Path) -> PinReadRun:
    """Execute the pin-reading step's run body in a shell against a checkout holding `pin_source`."""
    with tempfile.TemporaryDirectory() as root:
        checkout = Path(root) / "checkout"
        workflow = checkout / PIN_SOURCE_RELATIVE_PATH
        workflow.parent.mkdir(parents=True)
        workflow.write_text(pin_source.read_text(encoding="utf-8"), encoding="utf-8")
        environment_file = Path(root) / "github-env"
        environment_file.write_text("", encoding="utf-8")
        completed = subprocess.run(
            [_SHELL, "-c", pin_read_step(job).run or ""],
            cwd=checkout,
            env={
                "PATH": os.environ["PATH"],
                _GITHUB_ENV_VARIABLE: str(environment_file),
            },
            capture_output=True,
            text=True,
            check=False,
        )
        assignments = (
            _ENVIRONMENT_ASSIGNMENT.match(line)
            for line in environment_file.read_text(encoding="utf-8").splitlines()
        )
        return PinReadRun(
            returncode=completed.returncode,
            stderr=completed.stderr,
            environment={m.group(1): m.group(2) for m in assignments if m},
        )
