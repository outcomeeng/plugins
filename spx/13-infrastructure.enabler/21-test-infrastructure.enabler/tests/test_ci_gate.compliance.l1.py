"""Compliance evidence for the CI quality-gate workflow contract."""

from __future__ import annotations

import re
from pathlib import Path

from outcomeeng.validation import ACTIONLINT_ARGV, SHELLCHECK_ARGV
from outcomeeng.validation.spx_version import SPX_PACKAGE_NAME
from outcomeeng.validation.ci_gate import (
    CI_STEP_ENVIRONMENT_REQUIREMENTS,
    CI_TOOL_REQUIREMENTS,
    CONTINUE_ON_ERROR_FALSY,
    FULL_COMMIT_SHA_PATTERN,
    RETIRED_SPX_VERSION_ENVIRONMENT,
    SPX_CHECKOUT_REFERENCE,
    SPX_REPOSITORY,
    FAIL_FAST_PREAMBLE,
    GATE_PULL_REQUEST_EVENT,
    GATE_PUSH_BRANCH,
    GATE_PUSH_EVENT,
    GATE_RECIPE_COMMAND,
    MAXIMUM_JOB_TIMEOUT_MINUTES,
    PINNED_VERSION_ENVIRONMENT_SUFFIX,
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
    observe_spx_source,
    observe_validation_step_argvs,
    observe_workflow_jobs,
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


def test_gate_declares_the_workflow_and_shell_lint_steps() -> None:
    argvs = observe_validation_step_argvs()

    assert ACTIONLINT_ARGV in argvs
    assert SHELLCHECK_ARGV in argvs


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


def test_every_provisioned_tool_is_declared() -> None:
    observation = observe_ci_toolchain()

    assert all(
        any(
            requirement.provision_fragment in reference
            for requirement in CI_TOOL_REQUIREMENTS
        )
        for reference in observation.action_references
    )
    assert {
        name
        for name in observation.job_environment
        if name.endswith(PINNED_VERSION_ENVIRONMENT_SUFFIX)
    } == {
        requirement.version_environment
        for requirement in CI_TOOL_REQUIREMENTS
        if requirement.version_environment is not None
    }
    assert {
        (step_name, name)
        for step_name, environment in observation.step_environments
        for name in environment
    } == {
        (requirement.step_name, requirement.environment_name)
        for requirement in CI_STEP_ENVIRONMENT_REQUIREMENTS
    }


def test_missing_tool_provisioning_is_detected() -> None:
    observation = observe_ci_toolchain(
        gate_fixture_path("missing_tool_provisioning.yml")
    )

    assert any(
        not any(
            requirement.provision_fragment in surface
            for surface in (*observation.action_references, *observation.run_commands)
        )
        for requirement in CI_TOOL_REQUIREMENTS
    )
    assert not any(
        step_name == requirement.step_name
        and requirement.environment_name in environment
        for step_name, environment in observation.step_environments
        for requirement in CI_STEP_ENVIRONMENT_REQUIREMENTS
    )


def test_mismatched_python_version_is_detected() -> None:
    observation = observe_gate_python_versions(
        gate_fixture_path("mismatched_python_version.yml")
    )

    assert observation.workflow_version != observation.project_version


def test_missing_gate_recipe_is_detected() -> None:
    commands = observe_gate_run_commands(gate_fixture_path("missing_gate_recipe.yml"))

    assert GATE_RECIPE_COMMAND not in commands


def test_gate_workflow_python_matches_project_metadata() -> None:
    observation = observe_gate_python_versions()

    assert observation.workflow_version == observation.project_version


def test_gate_workflow_has_no_soft_passed_step() -> None:
    for step in observe_gate_steps():
        assert step.continue_on_error in CONTINUE_ON_ERROR_FALSY
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
    assert observation.continue_on_error in CONTINUE_ON_ERROR_FALSY


def test_every_repository_defined_workflow_job_declares_a_timeout() -> None:
    for observation in observe_workflow_jobs():
        if observation.calls_reusable_workflow:
            continue
        assert observation.timeout_minutes is not None
        assert 0 < int(observation.timeout_minutes) <= MAXIMUM_JOB_TIMEOUT_MINUTES


def test_reusable_workflow_callers_declare_no_timeout() -> None:
    callers = [
        observation
        for observation in observe_workflow_jobs()
        if observation.calls_reusable_workflow
    ]

    assert callers
    for observation in callers:
        assert observation.timeout_minutes is None


def test_conforming_fixture_satisfies_every_gate_rule() -> None:
    workflow_path = gate_fixture_path("conforming_gate.yml")
    triggers = observe_gate_triggers(workflow_path)

    assert GATE_PULL_REQUEST_EVENT in triggers.events
    assert GATE_PUSH_BRANCH in triggers.push_branches
    assert GATE_RECIPE_COMMAND in observe_gate_run_commands(workflow_path)
    job = observe_gate_job(workflow_path)

    assert not job.has_condition
    assert job.continue_on_error in CONTINUE_ON_ERROR_FALSY
    assert job.timeout_minutes is not None
    assert 0 < int(job.timeout_minutes) <= MAXIMUM_JOB_TIMEOUT_MINUTES
    for step in observe_gate_steps(workflow_path):
        assert not step.has_condition
        assert step.continue_on_error in CONTINUE_ON_ERROR_FALSY
        assert not any(snippet in step.run for snippet in SOFT_PASS_SHELL_SNIPPETS)


def test_job_level_condition_is_detected() -> None:
    assert observe_gate_job(gate_fixture_path("job_level_condition.yml")).has_condition


def test_unbounded_gate_job_is_detected() -> None:
    unbounded = observe_gate_job(gate_fixture_path("unbounded_gate_job.yml"))

    assert unbounded.timeout_minutes is None


def test_yaml_suffixed_workflow_jobs_are_observed() -> None:
    observations = observe_workflow_jobs(gate_fixture_path("yaml_extension_workflows"))

    assert [(each.workflow, each.timeout_minutes) for each in observations] == [
        ("unbounded.yaml", None)
    ]


def test_timeout_above_the_maximum_is_detected() -> None:
    over_bound = next(
        each
        for each in observe_workflow_jobs(gate_fixture_path("violating_bounds"))
        if not each.calls_reusable_workflow
    )

    assert over_bound.timeout_minutes is not None
    assert int(over_bound.timeout_minutes) > MAXIMUM_JOB_TIMEOUT_MINUTES


def test_reusable_caller_declaring_a_timeout_is_detected() -> None:
    caller = next(
        each
        for each in observe_workflow_jobs(gate_fixture_path("violating_bounds"))
        if each.calls_reusable_workflow
    )

    assert caller.timeout_minutes is not None


def test_job_level_continue_on_error_is_detected() -> None:
    observation = observe_gate_job(gate_fixture_path("job_level_continue_on_error.yml"))

    assert observation.continue_on_error not in CONTINUE_ON_ERROR_FALSY


def test_step_level_condition_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("step_level_condition.yml"))

    assert any(step.has_condition for step in steps)


def test_step_level_continue_on_error_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("step_level_continue_on_error.yml"))

    assert any(step.continue_on_error not in CONTINUE_ON_ERROR_FALSY for step in steps)


def test_expression_continue_on_error_is_detected() -> None:
    workflow_path = gate_fixture_path("expression_continue_on_error.yml")
    job = observe_gate_job(workflow_path)
    steps = observe_gate_steps(workflow_path)

    assert job.continue_on_error not in CONTINUE_ON_ERROR_FALSY
    assert any(step.continue_on_error not in CONTINUE_ON_ERROR_FALSY for step in steps)


def test_missing_fail_fast_preamble_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("missing_fail_fast_preamble.yml"))

    assert any(
        len(step.shell_lines) > 1 and step.shell_lines[0] != FAIL_FAST_PREAMBLE
        for step in steps
    )


def test_every_soft_pass_snippet_is_detected() -> None:
    steps = observe_gate_steps(gate_fixture_path("soft_pass_snippets.yml"))

    assert len(steps) == len(SOFT_PASS_SHELL_SNIPPETS)
    assert all(
        any(snippet in step.run for step in steps)
        for snippet in SOFT_PASS_SHELL_SNIPPETS
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
    assert any(len(step.shell_lines) > 1 for step in steps)


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


def test_gate_workflow_pins_one_full_spx_commit() -> None:
    pin = observe_spx_source().commit_pin

    assert pin is not None
    assert re.fullmatch(FULL_COMMIT_SHA_PATTERN, pin)


def test_gate_workflow_checks_out_spx_at_the_pinned_commit() -> None:
    assert (SPX_REPOSITORY, SPX_CHECKOUT_REFERENCE) in observe_spx_source().checkouts


def test_gate_workflow_never_installs_spx_from_the_registry() -> None:
    observation = observe_ci_toolchain()

    assert RETIRED_SPX_VERSION_ENVIRONMENT not in observation.job_environment
    assert not any(
        SPX_PACKAGE_NAME in surface
        for surface in (*observation.action_references, *observation.run_commands)
    )


def test_registry_installed_spx_is_detected() -> None:
    workflow_path = gate_fixture_path("spx_installed_from_registry.yml")
    observation = observe_ci_toolchain(workflow_path)

    assert RETIRED_SPX_VERSION_ENVIRONMENT in observation.job_environment
    assert any(
        SPX_PACKAGE_NAME in surface
        for surface in (*observation.action_references, *observation.run_commands)
    )
    assert observe_spx_source(workflow_path).commit_pin is None


def test_spx_pinned_to_a_moving_ref_is_detected() -> None:
    observation = observe_spx_source(gate_fixture_path("spx_pinned_to_moving_ref.yml"))

    assert observation.commit_pin is not None
    assert not re.fullmatch(FULL_COMMIT_SHA_PATTERN, observation.commit_pin)
    assert (SPX_REPOSITORY, SPX_CHECKOUT_REFERENCE) not in observation.checkouts


def test_spx_built_from_a_pinned_commit_satisfies_the_provisioning_rule() -> None:
    workflow_path = gate_fixture_path("spx_built_from_commit.yml")
    observation = observe_spx_source(workflow_path)

    assert observation.commit_pin is not None
    assert re.fullmatch(FULL_COMMIT_SHA_PATTERN, observation.commit_pin)
    assert (SPX_REPOSITORY, SPX_CHECKOUT_REFERENCE) in observation.checkouts
    toolchain = observe_ci_toolchain(workflow_path)
    assert RETIRED_SPX_VERSION_ENVIRONMENT not in toolchain.job_environment
    assert not any(
        SPX_PACKAGE_NAME in surface
        for surface in (*toolchain.action_references, *toolchain.run_commands)
    )
