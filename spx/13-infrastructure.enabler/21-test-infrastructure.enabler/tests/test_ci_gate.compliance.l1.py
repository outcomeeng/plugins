"""Compliance evidence for the CI quality-gate workflow contract."""

from __future__ import annotations

from outcomeeng.validation.ci_gate import (
    CI_STEP_ENVIRONMENT_REQUIREMENTS,
    CI_TOOL_REQUIREMENTS,
)
from outcomeeng_testing.harnesses.ci_gate import (
    assert_gate_declares_workflow_and_shell_lint_steps,
    assert_gate_job_runs_unconditionally,
    assert_workflow_has_no_soft_passed_step,
    assert_workflow_invokes_full_gate_recipe,
    assert_workflow_python_matches_project_metadata,
    assert_workflow_triggers_on_pull_request_and_main_push,
    observe_ci_toolchain,
)


def test_gate_workflow_triggers_on_pull_request_and_main_push() -> None:
    assert_workflow_triggers_on_pull_request_and_main_push()


def test_gate_workflow_invokes_the_full_gate_recipe() -> None:
    assert_workflow_invokes_full_gate_recipe()


def test_gate_declares_workflow_and_shell_lint_steps() -> None:
    assert_gate_declares_workflow_and_shell_lint_steps()


def test_gate_workflow_provisions_the_declared_toolchain() -> None:
    observation = observe_ci_toolchain()

    for requirement in CI_TOOL_REQUIREMENTS:
        if requirement.version_environment is not None:
            assert requirement.version_environment in observation.job_environment
        assert any(
            requirement.provision_fragment in surface
            for surface in (
                *observation.action_references,
                *observation.run_commands,
            )
        )
        if requirement.verification_fragment is not None:
            assert any(
                requirement.verification_fragment in command
                for command in observation.run_commands
            )
    for requirement in CI_STEP_ENVIRONMENT_REQUIREMENTS:
        assert any(
            step_name == requirement.step_name
            and requirement.environment_name in environment
            for step_name, environment in observation.step_environments
        )


def test_gate_workflow_python_matches_project_metadata() -> None:
    assert_workflow_python_matches_project_metadata()


def test_gate_workflow_has_no_soft_passed_step() -> None:
    assert_workflow_has_no_soft_passed_step()


def test_gate_job_runs_unconditionally() -> None:
    assert_gate_job_runs_unconditionally()
