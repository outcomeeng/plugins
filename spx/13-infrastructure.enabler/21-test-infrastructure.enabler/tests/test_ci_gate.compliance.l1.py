"""Compliance evidence for the CI quality-gate workflow contract."""

from __future__ import annotations

from outcomeeng_testing.harnesses.ci_gate import (
    assert_gate_declares_workflow_and_shell_lint_steps,
    assert_gate_job_runs_unconditionally,
    assert_workflow_has_no_soft_passed_step,
    assert_workflow_invokes_full_gate_recipe,
    assert_workflow_provisions_workflow_and_shell_lint_tools,
    assert_workflow_python_matches_project_metadata,
    assert_workflow_triggers_on_pull_request_and_main_push,
)


def test_gate_workflow_triggers_on_pull_request_and_main_push() -> None:
    assert_workflow_triggers_on_pull_request_and_main_push()


def test_gate_workflow_invokes_the_full_gate_recipe() -> None:
    assert_workflow_invokes_full_gate_recipe()


def test_gate_declares_workflow_and_shell_lint_steps() -> None:
    assert_gate_declares_workflow_and_shell_lint_steps()


def test_gate_workflow_provisions_workflow_and_shell_lint_tools() -> None:
    assert_workflow_provisions_workflow_and_shell_lint_tools()


def test_gate_workflow_python_matches_project_metadata() -> None:
    assert_workflow_python_matches_project_metadata()


def test_gate_workflow_has_no_soft_passed_step() -> None:
    assert_workflow_has_no_soft_passed_step()


def test_gate_job_runs_unconditionally() -> None:
    assert_gate_job_runs_unconditionally()
