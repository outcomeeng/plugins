"""Harness for the native profile acceptance workflow's declared policy.

The harness reads workflow files from disk, so the observations come from the
declaration the CI provider reads. It returns observations only; linked tests
own every comparison.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
NATIVE_ACCEPTANCE_WORKFLOW: Final = (
    REPO_ROOT / ".github" / "workflows" / "native-profile-acceptance.yml"
)
FIXTURE_ROOT: Final = (
    Path(__file__).resolve().parents[1] / "fixtures" / "native_acceptance_workflow"
)
TRIGGER_FIXTURES: Final = FIXTURE_ROOT / "triggers"
POLICY_FIXTURES: Final = FIXTURE_ROOT / "policy"
_JUST_COMMAND: Final = "just"
_SHELL_VARIABLE: Final = re.compile(r"\$\{(\w+)\}")
_EXPRESSION_VARIABLE: Final = re.compile(r"\$\{\{\s*env\.(\w+)\s*\}\}")


@dataclass(frozen=True)
class WorkflowStep:
    """One step's run body, action reference, inputs, and step-level environment."""

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
        run=document.get("run"),  # type: ignore[arg-type]
        uses=document.get("uses"),  # type: ignore[arg-type]
        inputs=dict(document.get("with", {})),  # type: ignore[call-overload]
        env=dict(document.get("env", {})),  # type: ignore[call-overload]
    )


def resolve_environment_references(text: str, environment: Mapping[str, str]) -> str:
    """Substitute `${NAME}` and `${{ env.NAME }}` with the job environment's values."""

    def substitute(match: re.Match[str]) -> str:
        return environment.get(match.group(1), match.group(0))

    return _EXPRESSION_VARIABLE.sub(
        substitute, _SHELL_VARIABLE.sub(substitute, text)
    )


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
