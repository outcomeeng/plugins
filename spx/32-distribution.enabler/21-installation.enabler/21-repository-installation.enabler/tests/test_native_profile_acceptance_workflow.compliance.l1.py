"""Compliance evidence for the native profile acceptance workflow's declared policy."""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path

from outcomeeng.validation.ci_gate import (
    CODEX_API_KEY_ENVIRONMENT,
    DISCOVERY_AUTH_MODE_ENVIRONMENT,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    CREDENTIAL_ENVIRONMENTS,
    WORKSPACE_TOKEN_ENV,
    AuthenticationMode,
)
from outcomeeng_testing.harnesses.native_acceptance_workflow import (
    PIN_SOURCE_WORKFLOW,
    observe_acceptance_workflow,
    observe_pin_source_environment,
    recipe_artifact_directories,
    run_pin_read_step,
    shell_variable_references,
    uploaded_paths,
    violating_pin_source_paths,
    violating_policy_workflow_paths,
    violating_trigger_workflow_paths,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
)

FORBIDDEN_TRIGGERS = frozenset({"pull_request", "push", "schedule"})
DISPATCH_TRIGGER = "workflow_dispatch"
RECIPES = ("verify-native-profile-execution", "verify-native-auditor-dispatch")
UPLOAD_ACTION = "actions/upload-artifact"
HOSTED_RUNNER_EXCLUSION = "self-hosted"
SECRET_REFERENCE = re.compile(r"^\$\{\{\s*secrets\.\w+\s*\}\}$")
CODEX_CREDENTIAL_BY_MODE = {
    AuthenticationMode.API.value: CODEX_API_KEY_ENVIRONMENT,
    AuthenticationMode.WORKSPACE_TOKEN.value: WORKSPACE_TOKEN_ENV,
}
CREDENTIALS = CLAUDE_CREDENTIAL_VARIABLES | CREDENTIAL_ENVIRONMENTS
SECRETS_REFERENCE_PREFIX = "secrets."


class Violation(StrEnum):
    RECIPE_MISSING = "recipe_missing"
    RECIPE_NOT_UPLOADED = "recipe_not_uploaded"
    CLAUDE_CREDENTIAL_COUNT = "claude_credential_count"
    CODEX_CREDENTIAL_NOT_SELECTED_BY_MODE = "codex_credential_not_selected_by_mode"
    CREDENTIAL_NOT_FROM_SECRET = "credential_not_from_secret"
    CREDENTIAL_OUTSIDE_JOB_ENVIRONMENT = "credential_outside_job_environment"
    RUNNER_NOT_HOSTED = "runner_not_hosted"


def fixture(violation: Violation) -> Path:
    """The inert workflow file committing the named violation."""
    return next(
        path
        for path in violating_policy_workflow_paths()
        if path.stem == violation.value
    )


def test_trigger_detection_flags_every_violating_workflow() -> None:
    violating_paths = violating_trigger_workflow_paths()

    assert violating_paths
    for path in violating_paths:
        observed = observe_acceptance_workflow(path).triggers
        assert observed & FORBIDDEN_TRIGGERS, path.name


def test_committed_workflow_declares_only_workflow_dispatch() -> None:
    observed = observe_acceptance_workflow().triggers

    assert observed == {DISPATCH_TRIGGER}
    assert not observed & FORBIDDEN_TRIGGERS


def test_policy_fixtures_name_exactly_the_policy_clauses() -> None:
    fixtures = {path.stem for path in violating_policy_workflow_paths()}

    assert fixtures == {violation.value for violation in Violation}


def test_a_workflow_missing_a_recipe_is_flagged_and_the_committed_one_is_not() -> None:
    flagged = observe_acceptance_workflow(fixture(Violation.RECIPE_MISSING))
    committed = observe_acceptance_workflow()

    verdicts = [
        any(
            not any(recipe_artifact_directories(job, recipe) for job in workflow.jobs)
            for recipe in RECIPES
        )
        for workflow in (flagged, committed)
    ]

    assert committed.jobs
    assert verdicts == [True, False]


def test_a_recipe_whose_artifact_directory_is_not_uploaded_is_flagged_and_the_committed_workflow_is_not() -> (
    None
):
    flagged = observe_acceptance_workflow(fixture(Violation.RECIPE_NOT_UPLOADED))
    committed = observe_acceptance_workflow()

    verdicts = [
        any(
            not any(
                directory.is_relative_to(path)
                for path in uploaded_paths(job, UPLOAD_ACTION)
            )
            for job in workflow.jobs
            for recipe in RECIPES
            for directory in recipe_artifact_directories(job, recipe)
        )
        for workflow in (flagged, committed)
    ]

    assert verdicts == [True, False]


def test_a_job_without_exactly_one_claude_credential_is_flagged_and_the_committed_workflow_is_not() -> (
    None
):
    flagged = observe_acceptance_workflow(fixture(Violation.CLAUDE_CREDENTIAL_COUNT))
    committed = observe_acceptance_workflow()

    verdicts = [
        any(
            len(job.env.keys() & CLAUDE_CREDENTIAL_VARIABLES) != 1
            for job in workflow.jobs
        )
        for workflow in (flagged, committed)
    ]

    assert verdicts == [True, False]


def test_a_codex_credential_the_mode_does_not_select_is_flagged_and_the_committed_workflow_is_not() -> (
    None
):
    flagged = observe_acceptance_workflow(
        fixture(Violation.CODEX_CREDENTIAL_NOT_SELECTED_BY_MODE)
    )
    committed = observe_acceptance_workflow()

    verdicts = [
        any(
            CODEX_CREDENTIAL_BY_MODE.get(
                job.env.get(DISCOVERY_AUTH_MODE_ENVIRONMENT, "")
            )
            is None
            or job.env.keys() & CREDENTIAL_ENVIRONMENTS
            != {CODEX_CREDENTIAL_BY_MODE[job.env[DISCOVERY_AUTH_MODE_ENVIRONMENT]]}
            for job in workflow.jobs
        )
        for workflow in (flagged, committed)
    ]

    assert verdicts == [True, False]


def test_a_credential_not_drawn_from_a_secret_is_flagged_and_the_committed_workflow_is_not() -> (
    None
):
    flagged = observe_acceptance_workflow(fixture(Violation.CREDENTIAL_NOT_FROM_SECRET))
    committed = observe_acceptance_workflow()

    verdicts = [
        any(
            not SECRET_REFERENCE.fullmatch(job.env[name])
            for job in workflow.jobs
            for name in job.env.keys() & CREDENTIALS
        )
        for workflow in (flagged, committed)
    ]

    assert verdicts == [True, False]


def test_a_credential_outside_the_job_environment_is_flagged_and_the_committed_workflow_is_not() -> (
    None
):
    flagged = observe_acceptance_workflow(
        fixture(Violation.CREDENTIAL_OUTSIDE_JOB_ENVIRONMENT)
    )
    committed = observe_acceptance_workflow()

    verdicts = [
        any(
            SECRETS_REFERENCE_PREFIX in (step.run or "")
            or any(name in (step.run or "") for name in CREDENTIALS)
            or step.env.keys() & CREDENTIALS
            for job in workflow.jobs
            for step in job.steps
        )
        for workflow in (flagged, committed)
    ]

    assert verdicts == [True, False]


def test_a_self_hosted_runner_is_flagged_and_the_committed_workflow_is_not() -> None:
    flagged = observe_acceptance_workflow(fixture(Violation.RUNNER_NOT_HOSTED))
    committed = observe_acceptance_workflow()

    verdicts = [
        any(HOSTED_RUNNER_EXCLUSION in job.runs_on for job in workflow.jobs)
        for workflow in (flagged, committed)
    ]

    assert verdicts == [True, False]


def consumed_pin_names() -> frozenset[str]:
    """The pins the job's other run bodies reference that the job environment does not declare and the quality gate does."""
    workflow = observe_acceptance_workflow()
    return (
        frozenset().union(
            *(shell_variable_references(job) - job.env.keys() for job in workflow.jobs)
        )
        & observe_pin_source_environment().keys()
    )


def test_the_pin_reading_step_yields_the_values_the_quality_gate_declares() -> None:
    names = consumed_pin_names()
    declared = observe_pin_source_environment()
    runs = [
        run_pin_read_step(job, PIN_SOURCE_WORKFLOW)
        for job in observe_acceptance_workflow().jobs
    ]

    assert names
    for run in runs:
        assert run.returncode == 0, run.stderr
        assert run.environment == {name: declared[name] for name in names}


def test_a_quality_gate_whose_pins_the_step_cannot_read_is_flagged_and_the_committed_one_is_not() -> (
    None
):
    names = consumed_pin_names()
    violating_paths = violating_pin_source_paths()
    jobs = observe_acceptance_workflow().jobs

    def flagged(source: Path) -> bool:
        declared = observe_pin_source_environment(source)
        expected = {name: declared[name] for name in names if name in declared}
        return any(
            run.returncode != 0 or run.environment != expected
            for run in (run_pin_read_step(job, source) for job in jobs)
        )

    assert violating_paths
    assert [flagged(path) for path in violating_paths] == [True] * len(violating_paths)
    assert not flagged(PIN_SOURCE_WORKFLOW)
