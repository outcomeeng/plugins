"""Compliance evidence for the CI quality-gate workflow contract."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.ci_gate import (
    CI_STEP_ENVIRONMENT_REQUIREMENTS,
    CI_TOOL_REQUIREMENTS,
    CONTINUE_ON_ERROR_TRUTHY,
    FAIL_FAST_PREAMBLE,
    GATE_PULL_REQUEST_EVENT,
    GATE_PUSH_BRANCH,
    GATE_PUSH_EVENT,
    GATE_RECIPE_COMMAND,
    SOFT_PASS_SHELL_SNIPPETS,
    TRAP_COMMAND_PREFIX,
)
from outcomeeng_testing.harnesses.ci_gate import (
    gate_fixture_path,
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


def _inlined_gate_steps(workflow_path: Path | None = None) -> set[str]:
    """Return gate-step commands a workflow runs as their own shell line."""
    recipes = {" ".join(argv) for argv in observe_validation_step_argvs()}
    return {
        line
        for step in observe_gate_steps(workflow_path)
        for line in step.shell_lines
        if line in recipes
    }


def test_gate_workflow_never_inlines_a_gate_step() -> None:
    assert _inlined_gate_steps() == set()


def test_inlined_gate_steps_are_detected() -> None:
    assert _inlined_gate_steps(gate_fixture_path("inlined_gate_steps.yml")) != set()


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
        assert step.continue_on_error not in CONTINUE_ON_ERROR_TRUTHY
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
    assert observation.continue_on_error not in CONTINUE_ON_ERROR_TRUTHY


def test_conforming_fixture_satisfies_every_gate_rule() -> None:
    workflow_path = gate_fixture_path("conforming_gate.yml")
    triggers = observe_gate_triggers(workflow_path)

    assert GATE_PULL_REQUEST_EVENT in triggers.events
    assert GATE_PUSH_BRANCH in triggers.push_branches
    assert GATE_RECIPE_COMMAND in observe_gate_run_commands(workflow_path)
    assert not observe_gate_job(workflow_path).has_condition
    for step in observe_gate_steps(workflow_path):
        assert not step.has_condition
        assert step.continue_on_error not in CONTINUE_ON_ERROR_TRUTHY
        assert not any(snippet in step.run for snippet in SOFT_PASS_SHELL_SNIPPETS)


def test_job_level_condition_is_detected() -> None:
    assert observe_gate_job(gate_fixture_path("job_level_condition.yml")).has_condition


def test_job_level_continue_on_error_is_detected() -> None:
    observation = observe_gate_job(gate_fixture_path("job_level_continue_on_error.yml"))

    assert observation.continue_on_error in CONTINUE_ON_ERROR_TRUTHY


def test_step_level_condition_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("step_level_condition.yml"))

    assert any(step.has_condition for step in steps)


def test_step_level_continue_on_error_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("step_level_continue_on_error.yml"))

    assert any(step.continue_on_error in CONTINUE_ON_ERROR_TRUTHY for step in steps)


def test_missing_fail_fast_preamble_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("missing_fail_fast_preamble.yml"))

    assert any(
        len(step.shell_lines) > 1 and step.shell_lines[0] != FAIL_FAST_PREAMBLE
        for step in steps
    )


def test_soft_passed_step_shell_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("soft_passed_step.yml"))

    assert any(
        snippet in step.run for step in steps for snippet in SOFT_PASS_SHELL_SNIPPETS
    )


def test_trap_soft_passed_step_shell_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("trap_soft_passed_step.yml"))

    assert any(
        line.startswith(TRAP_COMMAND_PREFIX)
        for step in steps
        for line in step.shell_lines
    )
    assert not any(
        snippet in step.run for step in steps for snippet in SOFT_PASS_SHELL_SNIPPETS
    )


def test_missing_pull_request_trigger_is_detected() -> None:
    triggers = observe_gate_triggers(
        gate_fixture_path("missing_pull_request_trigger.yml")
    )

    assert GATE_PULL_REQUEST_EVENT not in triggers.events


def test_missing_main_push_branch_is_detected() -> None:
    triggers = observe_gate_triggers(gate_fixture_path("missing_main_push_branch.yml"))

    assert GATE_PUSH_BRANCH not in triggers.push_branches


def test_missing_push_trigger_is_detected() -> None:
    triggers = observe_gate_triggers(gate_fixture_path("missing_push_trigger.yml"))

    assert GATE_PUSH_EVENT not in triggers.events
