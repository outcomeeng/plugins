"""Compliance evidence for the CI quality-gate workflow contract."""

from __future__ import annotations

from outcomeeng.validation import ACTIONLINT_ARGV, SHELLCHECK_ARGV
from outcomeeng.validation.ci_gate import (
    CI_STEP_ENVIRONMENT_REQUIREMENTS,
    CI_TOOL_REQUIREMENTS,
    CONTINUE_ON_ERROR_DISABLED,
    FAIL_FAST_PREAMBLE,
    GATE_PULL_REQUEST_EVENT,
    GATE_PUSH_BRANCH,
    GATE_PUSH_EVENT,
    GATE_RECIPE_COMMAND,
    SOFT_PASS_SHELL_SNIPPETS,
    TRAP_COMMAND_PREFIX,
)
from outcomeeng_testing.harnesses.ci_gate import (
    observe_ci_toolchain,
    observe_gate_job,
    observe_gate_python_versions,
    observe_gate_run_commands,
    observe_gate_steps,
    observe_gate_triggers,
    observe_validation_step_argvs,
)


def test_gate_workflow_triggers_on_pull_request_and_main_push() -> None:
    observation = observe_gate_triggers()

    assert GATE_PULL_REQUEST_EVENT in observation.events
    assert GATE_PUSH_EVENT in observation.events
    assert GATE_PUSH_BRANCH in observation.push_branches


def test_gate_workflow_invokes_the_full_gate_recipe() -> None:
    assert GATE_RECIPE_COMMAND in observe_gate_run_commands()


def test_gate_declares_workflow_and_shell_lint_steps() -> None:
    step_argvs = observe_validation_step_argvs()

    assert ACTIONLINT_ARGV in step_argvs
    assert SHELLCHECK_ARGV in step_argvs


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
    observation = observe_gate_python_versions()

    assert observation.workflow_version == observation.project_version


def test_gate_workflow_has_no_soft_passed_step() -> None:
    for step in observe_gate_steps():
        assert step.continue_on_error == CONTINUE_ON_ERROR_DISABLED
        assert not step.has_condition
        if len(step.shell_lines) > 1:
            assert step.shell_lines[0] == FAIL_FAST_PREAMBLE
        assert not any(snippet in step.run for snippet in SOFT_PASS_SHELL_SNIPPETS)
        assert not any(
            line.startswith(TRAP_COMMAND_PREFIX) for line in step.shell_lines
        )


def test_gate_job_runs_unconditionally() -> None:
    observation = observe_gate_job()

    assert not observation.has_condition
    assert observation.continue_on_error == CONTINUE_ON_ERROR_DISABLED
