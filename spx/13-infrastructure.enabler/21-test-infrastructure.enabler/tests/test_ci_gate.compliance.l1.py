"""Compliance evidence for the CI quality-gate workflow contract.

Verifies that the GitHub Actions quality-gate workflow enforces the full gate
on every path to `main`, per the governing decision
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`.
The workflow runs the gate by invoking the source-owned full gate recipe through
`just check-full` rather than a re-enumerated subset of the recipe step constants.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Final, cast

# PyYAML ships without inline types; this test casts parsed workflow structure below.
import yaml  # type: ignore[import-untyped]

from outcomeeng.validation import (
    ACTIONLINT_ARGV,
    RECIPE_CHECK_FULL,
    SHELLCHECK_ARGV,
    VALIDATION_STEPS,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[4]
GATE_WORKFLOW: Final = REPO_ROOT / ".github" / "workflows" / "check.yml"
PROJECT_METADATA: Final = REPO_ROOT / "pyproject.toml"

GATE_JOB: Final = "check"
MAIN_BRANCH: Final = "main"
JUST_BINARY: Final = "just"

# Shell constructs that deliberately convert failures into success.
SOFT_PASS_SHELL_SNIPPETS: Final = (
    "|| true",
    "|| :",
    "|| exit 0",
    "set +e",
    "exit 0",
    "if !",
)
FAIL_FAST_PREAMBLE: Final = "set -euo pipefail"


def _workflow() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        yaml.load(GATE_WORKFLOW.read_text(), Loader=yaml.BaseLoader),
    )


def _gate_job(workflow: dict[str, Any]) -> dict[str, Any]:
    return cast("dict[str, Any]", workflow["jobs"][GATE_JOB])


def _gate_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    return cast("list[dict[str, Any]]", _gate_job(workflow)["steps"])


def _setup_python_version(workflow: dict[str, Any]) -> str:
    setup_step = next(
        step for step in _gate_steps(workflow) if step.get("name") == "Set up Python"
    )
    return cast("str", setup_step["with"]["python-version"])


def _requires_python_version() -> str:
    metadata = tomllib.loads(PROJECT_METADATA.read_text())
    requires_python = cast("str", metadata["project"]["requires-python"])
    return requires_python.removeprefix(">=")


def _shell_lines(run: str) -> list[str]:
    return [
        line.strip()
        for line in run.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_gate_workflow_triggers_on_pull_request_and_main_push() -> None:
    on_section = cast("dict[str, Any]", _workflow()["on"])

    assert "pull_request" in on_section
    push_branches = cast("list[str]", on_section["push"]["branches"])
    assert MAIN_BRANCH in push_branches


def test_gate_workflow_invokes_the_full_gate_recipe() -> None:
    runs = [
        cast("str", step["run"]) for step in _gate_steps(_workflow()) if "run" in step
    ]

    assert any(run.strip() == f"{JUST_BINARY} {RECIPE_CHECK_FULL}" for run in runs)


def test_gate_declares_workflow_and_shell_lint_steps() -> None:
    step_argvs = {step.argv for step in VALIDATION_STEPS}

    assert ACTIONLINT_ARGV in step_argvs
    assert SHELLCHECK_ARGV in step_argvs


def test_gate_workflow_provisions_workflow_and_shell_lint_tools() -> None:
    workflow = _workflow()
    env = cast("dict[str, str]", _gate_job(workflow)["env"])
    runs = [cast("str", step["run"]) for step in _gate_steps(workflow) if "run" in step]

    assert "JUST_VERSION" in env
    assert "ACTIONLINT_VERSION" in env
    assert "SHELLCHECK_VERSION" in env
    assert any(f"{JUST_BINARY} --version" in run for run in runs)
    assert any("actionlint" in run for run in runs)
    assert any("shellcheck" in run for run in runs)


def test_gate_workflow_python_matches_project_metadata() -> None:
    assert _setup_python_version(_workflow()) == _requires_python_version()


def test_gate_workflow_has_no_soft_passed_step() -> None:
    for step in _gate_steps(_workflow()):
        assert step.get("continue-on-error", "false") == "false"
        assert "if" not in step
        run = cast("str", step.get("run", ""))
        lines = _shell_lines(run)
        if len(lines) > 1:
            assert lines[0] == FAIL_FAST_PREAMBLE
        assert not any(snippet in run for snippet in SOFT_PASS_SHELL_SNIPPETS)
        assert not any(line.startswith("trap ") for line in lines)


def test_gate_job_runs_unconditionally() -> None:
    job = _gate_job(_workflow())
    assert "if" not in job
    # Mirror the step-level continue-on-error check: a falsy value is a harmless
    # no-op; only a truthy continue-on-error lets a failed job report success.
    assert job.get("continue-on-error", "false") == "false"
