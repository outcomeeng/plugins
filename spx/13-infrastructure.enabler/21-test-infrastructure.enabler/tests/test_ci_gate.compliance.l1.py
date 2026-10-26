"""Compliance evidence for the CI quality-gate workflow contract."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from outcomeeng.validation import (
    ACTIONLINT_ARGV,
    CI_CREDENTIALS_ARGV,
    RECIPE_TEST_L3,
    SHELLCHECK_ARGV,
    VALIDATION_ENTRY_COMMAND,
)
from outcomeeng.validation.ci_credentials import (
    CredentialViolation,
    CredentialViolationKind,
    workflow_credential_violations,
)
from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL
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
    GATE_RECIPE_COMMANDS,
    GITHUB_TOKEN_ENVIRONMENT,
    L3_RECIPE_COMMAND,
    MAXIMUM_JOB_TIMEOUT_MINUTES,
    PINNED_VERSION_ENVIRONMENT_SUFFIX,
    SOFT_PASS_SHELL_SNIPPETS,
    TRAP_COMMAND_PREFIX,
)
from outcomeeng_testing.harnesses.ci_gate import (
    credential_violation_fixture_paths,
    GATE_FIXTURES,
    fixture_directory_names,
    l3_value_violation_fixture_paths,
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
from outcomeeng_testing.harnesses.l3_collection import justfile_recipe_dispatch
from outcomeeng_testing.harnesses.python_code_quality import run_check_full_dispatch


def test_gate_workflow_triggers_on_pull_request_and_main_push() -> None:
    observation = observe_gate_triggers()

    assert GATE_PULL_REQUEST_EVENT in observation.events
    assert GATE_PUSH_EVENT in observation.events
    assert GATE_PUSH_BRANCH in observation.push_branches


def test_gate_workflow_runs_the_full_gate_and_then_the_l3_tests() -> None:
    commands = observe_gate_run_commands()

    assert (
        tuple(command for command in commands if command in GATE_RECIPE_COMMANDS)
        == GATE_RECIPE_COMMANDS
    )


@pytest.mark.parametrize("recipe", (RECIPE_CHECK_FULL, RECIPE_TEST_L3))
def test_each_gate_recipe_dispatches_its_own_validation_command(recipe: str) -> None:
    dispatch = justfile_recipe_dispatch(recipe)

    assert dispatch.entry == VALIDATION_ENTRY_COMMAND
    assert dispatch.recipe_words == (recipe,)


def test_a_gate_job_without_the_l3_tests_is_detected() -> None:
    commands = observe_gate_run_commands(GATE_FIXTURES.missing_l3_recipe)

    assert (
        tuple(command for command in commands if command in GATE_RECIPE_COMMANDS)
        != GATE_RECIPE_COMMANDS
    )


def test_l3_tests_before_the_full_gate_are_detected() -> None:
    commands = observe_gate_run_commands(GATE_FIXTURES.l3_before_full_gate)

    assert set(commands) >= set(GATE_RECIPE_COMMANDS)
    assert (
        tuple(command for command in commands if command in GATE_RECIPE_COMMANDS)
        != GATE_RECIPE_COMMANDS
    )


def _required_credentials() -> set[tuple[str, str, str]]:
    return {
        (requirement.run_command, requirement.environment_name, requirement.value)
        for requirement in CI_STEP_ENVIRONMENT_REQUIREMENTS
    }


def test_gate_runs_the_credential_check() -> None:
    run = run_check_full_dispatch()

    assert run.exit_code == 0
    assert CI_CREDENTIALS_ARGV in run.spawn_calls


def test_only_the_l3_step_receives_the_l3_credentials() -> None:
    assert workflow_credential_violations() == ()


def test_credential_violation_fixtures_are_present() -> None:
    assert credential_violation_fixture_paths()


@pytest.mark.parametrize(
    "fixture", credential_violation_fixture_paths(), ids=lambda path: path.name
)
def test_a_credential_reaching_the_full_gate_step_is_detected(fixture: Path) -> None:
    assert CredentialViolation(
        CredentialViolationKind.FOREIGN_STEP,
        GATE_RECIPE_COMMAND,
        GITHUB_TOKEN_ENVIRONMENT,
    ) in workflow_credential_violations(fixture)


def test_l3_value_violation_fixtures_are_present() -> None:
    assert l3_value_violation_fixture_paths()


@pytest.mark.parametrize(
    "fixture", l3_value_violation_fixture_paths(), ids=lambda path: path.name
)
def test_a_wrong_l3_credential_value_is_detected(fixture: Path) -> None:
    assert any(
        violation.kind is CredentialViolationKind.WRONG_VALUE
        and violation.run_command == L3_RECIPE_COMMAND
        for violation in workflow_credential_violations(fixture)
    )


def test_a_missing_l3_credential_is_detected() -> None:
    violations = workflow_credential_violations(GATE_FIXTURES.l3_credentials_missing)

    assert set(violations) == {
        CredentialViolation(
            CredentialViolationKind.MISSING,
            requirement.run_command,
            requirement.environment_name,
        )
        for requirement in CI_STEP_ENVIRONMENT_REQUIREMENTS
    }


def test_gate_runs_the_workflow_and_shell_lint_steps() -> None:
    run = run_check_full_dispatch()

    assert run.exit_code == 0
    assert ACTIONLINT_ARGV in run.spawn_calls
    assert SHELLCHECK_ARGV in run.spawn_calls


def test_gate_workflow_never_inlines_a_gate_step() -> None:
    step_commands = {" ".join(argv) for argv in observe_validation_step_argvs()}

    assert not any(
        line in step_commands
        for step in observe_gate_steps()
        for line in step.shell_lines
    )


def test_inlined_gate_steps_are_detected() -> None:
    step_commands = {" ".join(argv) for argv in observe_validation_step_argvs()}

    assert any(
        line in step_commands
        for step in observe_gate_steps(GATE_FIXTURES.inlined_gate_steps)
        for line in step.shell_lines
    )


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
    for step_requirement in CI_STEP_ENVIRONMENT_REQUIREMENTS:
        assert any(
            run_command == step_requirement.run_command
            and environment.get(step_requirement.environment_name)
            == step_requirement.value
            for run_command, environment in observation.run_environments
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
        (run_command, name, value)
        for run_command, environment in observation.run_environments
        for name, value in environment.items()
    } == _required_credentials()


def test_missing_tool_provisioning_is_detected() -> None:
    observation = observe_ci_toolchain(GATE_FIXTURES.missing_tool_provisioning)

    assert any(
        not any(
            requirement.provision_fragment in surface
            for surface in (*observation.action_references, *observation.run_commands)
        )
        for requirement in CI_TOOL_REQUIREMENTS
    )
    assert not any(
        run_command == requirement.run_command
        and requirement.environment_name in environment
        for run_command, environment in observation.run_environments
        for requirement in CI_STEP_ENVIRONMENT_REQUIREMENTS
    )


def test_mismatched_python_version_is_detected() -> None:
    observation = observe_gate_python_versions(GATE_FIXTURES.mismatched_python_version)

    assert observation.workflow_version != observation.project_version


def test_missing_gate_recipe_is_detected() -> None:
    commands = observe_gate_run_commands(GATE_FIXTURES.missing_gate_recipe)

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
    workflow_path = GATE_FIXTURES.conforming_gate
    triggers = observe_gate_triggers(workflow_path)

    assert GATE_PULL_REQUEST_EVENT in triggers.events
    assert GATE_PUSH_BRANCH in triggers.push_branches
    commands = observe_gate_run_commands(workflow_path)
    assert (
        tuple(command for command in commands if command in GATE_RECIPE_COMMANDS)
        == GATE_RECIPE_COMMANDS
    )
    assert workflow_credential_violations(workflow_path) == ()
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
    assert observe_gate_job(GATE_FIXTURES.job_level_condition).has_condition


def test_unbounded_gate_job_is_detected() -> None:
    unbounded = observe_gate_job(GATE_FIXTURES.unbounded_gate_job)

    assert unbounded.timeout_minutes is None


def test_yaml_suffixed_workflow_jobs_are_observed() -> None:
    observations = observe_workflow_jobs(GATE_FIXTURES.yaml_extension_workflows)

    assert [(each.workflow, each.timeout_minutes) for each in observations] == [
        (name, None)
        for name in fixture_directory_names(GATE_FIXTURES.yaml_extension_workflows)
    ]


def test_timeout_above_the_maximum_is_detected() -> None:
    over_bound = next(
        each
        for each in observe_workflow_jobs(GATE_FIXTURES.violating_bounds)
        if not each.calls_reusable_workflow
    )

    assert over_bound.timeout_minutes is not None
    assert int(over_bound.timeout_minutes) > MAXIMUM_JOB_TIMEOUT_MINUTES


def test_reusable_caller_declaring_a_timeout_is_detected() -> None:
    caller = next(
        each
        for each in observe_workflow_jobs(GATE_FIXTURES.violating_bounds)
        if each.calls_reusable_workflow
    )

    assert caller.timeout_minutes is not None


def test_job_level_continue_on_error_is_detected() -> None:
    observation = observe_gate_job(GATE_FIXTURES.job_level_continue_on_error)

    assert observation.continue_on_error not in CONTINUE_ON_ERROR_FALSY


def test_step_level_condition_is_detected() -> None:
    steps = observe_gate_steps(GATE_FIXTURES.step_level_condition)

    assert any(step.has_condition for step in steps)


def test_step_level_continue_on_error_is_detected() -> None:
    steps = observe_gate_steps(GATE_FIXTURES.step_level_continue_on_error)

    assert any(step.continue_on_error not in CONTINUE_ON_ERROR_FALSY for step in steps)


def test_expression_continue_on_error_is_detected() -> None:
    workflow_path = GATE_FIXTURES.expression_continue_on_error
    job = observe_gate_job(workflow_path)
    steps = observe_gate_steps(workflow_path)

    assert job.continue_on_error not in CONTINUE_ON_ERROR_FALSY
    assert any(step.continue_on_error not in CONTINUE_ON_ERROR_FALSY for step in steps)


def test_missing_fail_fast_preamble_is_detected() -> None:
    steps = observe_gate_steps(GATE_FIXTURES.missing_fail_fast_preamble)

    assert any(
        len(step.shell_lines) > 1 and step.shell_lines[0] != FAIL_FAST_PREAMBLE
        for step in steps
    )


def test_every_soft_pass_snippet_is_detected() -> None:
    steps = observe_gate_steps(GATE_FIXTURES.soft_pass_snippets)

    assert len(steps) == len(SOFT_PASS_SHELL_SNIPPETS)
    assert all(
        any(snippet in step.run for step in steps)
        for snippet in SOFT_PASS_SHELL_SNIPPETS
    )


def test_trap_soft_passed_step_shell_is_detected() -> None:
    steps = observe_gate_steps(GATE_FIXTURES.trap_soft_passed_step)

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
    triggers = observe_gate_triggers(GATE_FIXTURES.missing_pull_request_trigger)

    assert GATE_PULL_REQUEST_EVENT not in triggers.events


def test_missing_main_push_branch_is_detected() -> None:
    triggers = observe_gate_triggers(GATE_FIXTURES.missing_main_push_branch)

    assert GATE_PUSH_BRANCH not in triggers.push_branches


def test_missing_push_trigger_is_detected() -> None:
    triggers = observe_gate_triggers(GATE_FIXTURES.missing_push_trigger)

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
    workflow_path = GATE_FIXTURES.spx_installed_from_registry
    observation = observe_ci_toolchain(workflow_path)

    assert RETIRED_SPX_VERSION_ENVIRONMENT in observation.job_environment
    assert any(
        SPX_PACKAGE_NAME in surface
        for surface in (*observation.action_references, *observation.run_commands)
    )
    assert observe_spx_source(workflow_path).commit_pin is None


def test_spx_pinned_to_a_moving_ref_is_detected() -> None:
    observation = observe_spx_source(GATE_FIXTURES.spx_pinned_to_moving_ref)

    assert observation.commit_pin is not None
    assert not re.fullmatch(FULL_COMMIT_SHA_PATTERN, observation.commit_pin)
    assert (SPX_REPOSITORY, SPX_CHECKOUT_REFERENCE) not in observation.checkouts


def test_spx_built_from_a_pinned_commit_satisfies_the_provisioning_rule() -> None:
    workflow_path = GATE_FIXTURES.spx_built_from_commit
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
