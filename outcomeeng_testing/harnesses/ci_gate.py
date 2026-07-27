"""Harness-owned CI gate workflow parsing for compliance tests."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

import yaml

from outcomeeng.validation import (
    ACTIONLINT_ARGV,
    RECIPE_CHECK_FULL,
    SHELLCHECK_ARGV,
    VALIDATION_STEPS,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
GATE_WORKFLOW: Final = REPO_ROOT / ".github" / "workflows" / "check.yml"
PROJECT_METADATA: Final = REPO_ROOT / "pyproject.toml"

GATE_JOB: Final = "check"
MAIN_BRANCH: Final = "main"
JUST_BINARY: Final = "just"
SOFT_PASS_SHELL_SNIPPETS: Final = (
    "|| true",
    "|| :",
    "|| exit 0",
    "set +e",
    "exit 0",
    "if !",
)
FAIL_FAST_PREAMBLE: Final = "set -euo pipefail"


@dataclass(frozen=True)
class CiToolchainObservation:
    """Raw job environment, action, command, and step-environment observations."""

    job_environment: frozenset[str]
    action_references: tuple[str, ...]
    run_commands: tuple[str, ...]
    step_environments: tuple[tuple[str, frozenset[str]], ...]


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


def full_gate_recipe_command() -> str:
    return f"{JUST_BINARY} {RECIPE_CHECK_FULL}"


def assert_workflow_triggers_on_pull_request_and_main_push() -> None:
    on_section = cast("dict[str, object]", workflow()["on"])

    assert "pull_request" in on_section
    push_section = cast("dict[str, object]", on_section["push"])
    push_branches = cast("list[str]", push_section["branches"])
    assert MAIN_BRANCH in push_branches


def assert_workflow_invokes_full_gate_recipe() -> None:
    runs = [
        cast("str", step["run"]) for step in gate_steps(workflow()) if "run" in step
    ]

    assert any(run.strip() == full_gate_recipe_command() for run in runs)


def assert_gate_declares_workflow_and_shell_lint_steps() -> None:
    step_argvs = {step.argv for step in VALIDATION_STEPS}

    assert ACTIONLINT_ARGV in step_argvs
    assert SHELLCHECK_ARGV in step_argvs


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


def assert_workflow_python_matches_project_metadata() -> None:
    assert setup_python_version(workflow()) == required_python_version()


def assert_workflow_has_no_soft_passed_step() -> None:
    for step in gate_steps(workflow()):
        assert step.get("continue-on-error", "false") == "false"
        assert "if" not in step
        run = cast("str", step.get("run", ""))
        lines = shell_lines(run)
        if len(lines) > 1:
            assert lines[0] == FAIL_FAST_PREAMBLE
        assert not any(snippet in run for snippet in SOFT_PASS_SHELL_SNIPPETS)
        assert not any(line.startswith("trap ") for line in lines)


def assert_gate_job_runs_unconditionally() -> None:
    job = gate_job(workflow())
    assert "if" not in job
    assert job.get("continue-on-error", "false") == "false"
