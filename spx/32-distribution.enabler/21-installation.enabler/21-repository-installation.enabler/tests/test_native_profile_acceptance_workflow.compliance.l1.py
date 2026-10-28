"""Compliance evidence for the native profile acceptance workflow's declared policy."""

from __future__ import annotations

import re
from enum import StrEnum

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
    AcceptanceWorkflow,
    observe_acceptance_workflow,
    recipe_artifact_directories,
    uploaded_paths,
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


class Violation(StrEnum):
    RECIPE_MISSING = "recipe_missing"
    RECIPE_NOT_UPLOADED = "recipe_not_uploaded"
    CLAUDE_CREDENTIAL_COUNT = "claude_credential_count"
    CODEX_CREDENTIAL_NOT_SELECTED_BY_MODE = "codex_credential_not_selected_by_mode"
    CREDENTIAL_NOT_FROM_SECRET = "credential_not_from_secret"
    CREDENTIAL_OUTSIDE_JOB_ENVIRONMENT = "credential_outside_job_environment"
    RUNNER_NOT_HOSTED = "runner_not_hosted"


def policy_violations(workflow: AcceptanceWorkflow) -> set[str]:
    found: set[str] = set()
    for recipe in RECIPES:
        if not any(recipe_artifact_directories(job, recipe) for job in workflow.jobs):
            found.add(Violation.RECIPE_MISSING)
    for job in workflow.jobs:
        uploads = uploaded_paths(job, UPLOAD_ACTION)
        for recipe in RECIPES:
            for directory in recipe_artifact_directories(job, recipe):
                if not any(directory.is_relative_to(path) for path in uploads):
                    found.add(Violation.RECIPE_NOT_UPLOADED)
        if len(job.env.keys() & CLAUDE_CREDENTIAL_VARIABLES) != 1:
            found.add(Violation.CLAUDE_CREDENTIAL_COUNT)
        selected = CODEX_CREDENTIAL_BY_MODE.get(
            job.env.get(DISCOVERY_AUTH_MODE_ENVIRONMENT, "")
        )
        if selected is None or job.env.keys() & CREDENTIAL_ENVIRONMENTS != {selected}:
            found.add(Violation.CODEX_CREDENTIAL_NOT_SELECTED_BY_MODE)
        if any(
            not SECRET_REFERENCE.fullmatch(job.env[name])
            for name in job.env.keys() & CREDENTIALS
        ):
            found.add(Violation.CREDENTIAL_NOT_FROM_SECRET)
        if any(
            "secrets." in (step.run or "")
            or any(name in (step.run or "") for name in CREDENTIALS)
            or step.env.keys() & CREDENTIALS
            for step in job.steps
        ):
            found.add(Violation.CREDENTIAL_OUTSIDE_JOB_ENVIRONMENT)
        if HOSTED_RUNNER_EXCLUSION in job.runs_on:
            found.add(Violation.RUNNER_NOT_HOSTED)
    return found


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


def test_policy_detection_flags_each_violation_its_fixture_commits() -> None:
    fixtures = {path.stem: path for path in violating_policy_workflow_paths()}

    assert fixtures.keys() == {violation.value for violation in Violation}
    for stem, path in fixtures.items():
        assert stem in policy_violations(observe_acceptance_workflow(path)), stem


def test_committed_workflow_runs_both_recipes_with_one_credential_each_and_uploads() -> (
    None
):
    workflow = observe_acceptance_workflow()

    assert workflow.jobs
    assert policy_violations(workflow) == set()
