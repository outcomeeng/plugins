"""State-boundary and failure evidence for repository installation."""

from pathlib import Path

from outcomeeng.distribution.installation import (
    Agent,
    CODEX_HOME_ENV,
    InstallationMode,
    Operation,
    STATE_ENV_NAMES,
)
from outcomeeng_testing.harnesses.installation import (
    observe_first_failure,
    observe_missing_codex_home,
    observe_persistent_execution,
    observe_repository_plan,
)


def test_every_command_uses_the_explicit_checkout_and_agent_homes() -> None:
    observation = observe_repository_plan()

    assert all(
        command.cwd == observation.plan.roots.checkout
        for command in observation.plan.commands
    )
    assert all(
        value not in observation.ambient_state_values
        for command in observation.plan.commands
        for name, value in command.environment
        if name in STATE_ENV_NAMES
    )
    assert all(
        all(
            Path(value).is_relative_to(observation.plan.roots.state)
            for name, value in command.environment
            if name in STATE_ENV_NAMES
        )
        for command in observation.plan.commands
    )


def test_persistent_installation_requires_selected_codex_home() -> None:
    error = observe_missing_codex_home()

    assert CODEX_HOME_ENV in error


def test_persistent_commands_use_project_scope_and_selected_codex_home() -> None:
    observation = observe_persistent_execution()
    plan = observation.report.plan

    assert plan.mode is InstallationMode.PERSISTENT
    assert all(
        "--scope" in command.argv and "project" in command.argv
        for command in plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation
        in {
            Operation.MARKETPLACE_REMOVE,
            Operation.MARKETPLACE_ADD,
            Operation.PLUGIN_INSTALL,
            Operation.PLUGIN_ENABLE,
        }
    )
    assert all(
        dict(command.environment)[CODEX_HOME_ENV] == str(plan.roots.codex_home)
        for command in plan.commands
        if command.agent is Agent.CODEX
    )
    assert observation.attempted[1:] == plan.commands


def test_first_agent_cli_failure_reports_the_operation_and_stops() -> None:
    observation = observe_first_failure()

    assert observation.failure.command.agent is Agent.CLAUDE
    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL
    assert observation.failure.command.plugin is not None
    assert observation.failure.result.exit_code != 0
    assert observation.failure.result.stderr == Operation.PLUGIN_INSTALL.value
    assert all(result.exit_code == 0 for result in observation.failure.completed)
    assert observation.attempted[-1] == observation.failure.command
    assert len(observation.attempted) < len(observation.plan.commands)
