"""Compliance evidence for the CI quality-gate workflow contract.

Verifies that the GitHub Actions quality-gate workflow enforces the full gate
on every path to `main`, per the governing decision
`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/15-ci-gate.adr.md`.
The workflow runs the gate by invoking the source-owned module entry point
(`python -m outcomeeng.validation`, equivalently `just check`) rather than a
re-enumerated subset of `outcomeeng.validation.STEPS`.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Final, cast

import yaml

from outcomeeng import validation

REPO_ROOT: Final = Path(__file__).resolve().parents[4]
GATE_WORKFLOW: Final = REPO_ROOT / ".github" / "workflows" / "check.yml"
PROJECT_METADATA: Final = REPO_ROOT / "pyproject.toml"

# The gate's source-owned module entry point. The workflow must invoke this
# (equivalently the `just check` recipe), never a filtered subset of STEPS.
GATE_MODULE: Final = validation.__name__

GATE_JOB: Final = "check"
MAIN_BRANCH: Final = "main"

# Shell operators that swallow a failing exit code — the rule's prohibited set.
SOFT_PASS_OPERATORS: Final = ("|| true", "|| :", "; true", "; :")


def _workflow() -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        yaml.load(GATE_WORKFLOW.read_text(), Loader=yaml.BaseLoader),
    )


def _gate_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    job = cast("dict[str, Any]", workflow["jobs"][GATE_JOB])
    return cast("list[dict[str, Any]]", job["steps"])


def _setup_python_version(workflow: dict[str, Any]) -> str:
    setup_step = next(
        step for step in _gate_steps(workflow) if step.get("name") == "Set up Python"
    )
    return cast("str", setup_step["with"]["python-version"])


def _requires_python_version() -> str:
    metadata = tomllib.loads(PROJECT_METADATA.read_text())
    requires_python = cast("str", metadata["project"]["requires-python"])
    return requires_python.removeprefix(">=")


def test_gate_workflow_triggers_on_pull_request_and_main_push() -> None:
    on_section = cast("dict[str, Any]", _workflow()["on"])

    assert "pull_request" in on_section
    push_branches = cast("list[str]", on_section["push"]["branches"])
    assert MAIN_BRANCH in push_branches


def test_gate_workflow_invokes_the_full_gate_recipe() -> None:
    runs = [
        cast("str", step["run"]) for step in _gate_steps(_workflow()) if "run" in step
    ]

    assert any(GATE_MODULE in run for run in runs)


def test_gate_workflow_python_matches_project_metadata() -> None:
    assert _setup_python_version(_workflow()) == _requires_python_version()


def test_gate_workflow_has_no_soft_passed_step() -> None:
    for step in _gate_steps(_workflow()):
        assert step.get("continue-on-error", "false") == "false"
        assert "if" not in step
        run = cast("str", step.get("run", ""))
        assert not any(operator in run for operator in SOFT_PASS_OPERATORS)
