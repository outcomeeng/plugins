"""State-boundary and failure evidence for repository installation."""

from pathlib import Path

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_SCOPE_BEARING_OPERATIONS,
    CLAUDE_SCOPELESS_OPERATIONS,
    CODEX_HOME_ENV,
    InstallationMode,
    Operation,
    SPEC_TREE_PLUGIN,
    STATE_ENV_NAMES,
)
from outcomeeng_testing.harnesses.installation import (
    NONCANONICAL_MARKETPLACE_SOURCE,
    observe_first_failure,
    observe_inspection_failure,
    observe_invalid_persistent_selections,
    observe_missing_codex_home,
    observe_persistent_execution,
    observe_persistent_plan,
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

    assert error is not None
    assert CODEX_HOME_ENV in error


def test_persistent_commands_use_project_scope_and_selected_codex_home() -> None:
    refreshing = observe_persistent_execution()
    replacing = observe_persistent_plan(
        claude_repository=NONCANONICAL_MARKETPLACE_SOURCE,
        codex_source=NONCANONICAL_MARKETPLACE_SOURCE,
    )
    plans = (refreshing.report.plan, replacing.plan)
    claude_commands = [
        command
        for plan in plans
        for command in plan.commands
        if command.agent is Agent.CLAUDE
    ]

    assert all(plan.mode is InstallationMode.PERSISTENT for plan in plans)
    assert {command.operation for command in claude_commands} == (
        CLAUDE_SCOPE_BEARING_OPERATIONS | CLAUDE_SCOPELESS_OPERATIONS
    )
    assert all(
        "--scope" in command.argv and CLAUDE_PROJECT_SCOPE in command.argv
        for command in claude_commands
        if command.operation in CLAUDE_SCOPE_BEARING_OPERATIONS
    )
    assert all(
        "--scope" not in command.argv
        for command in claude_commands
        if command.operation in CLAUDE_SCOPELESS_OPERATIONS
    )
    assert all(
        dict(command.environment)[CODEX_HOME_ENV] == str(plan.roots.codex_home)
        for plan in plans
        for command in plan.commands
        if command.agent is Agent.CODEX
    )
    assert (
        refreshing.attempted[len(refreshing.preflight.inspections) :]
        == refreshing.report.plan.commands
    )


def test_an_enable_failure_stops_the_run_rather_than_reading_as_idempotent() -> None:
    observation = observe_first_failure(Operation.PLUGIN_ENABLE)

    assert observation.failure is not None
    assert observation.failure.command.agent is Agent.CLAUDE
    assert observation.failure.command.operation is Operation.PLUGIN_ENABLE
    assert observation.failure.command.plugin is not None
    assert observation.failure.result.exit_code != 0
    assert observation.attempted[-1] == observation.failure.command
    assert (
        observation.attempted == observation.plan.commands[: len(observation.attempted)]
    )


def test_a_failed_inspection_stops_before_any_planned_operation() -> None:
    observation = observe_inspection_failure()

    assert observation.failure is not None
    assert observation.failure.command.operation is Operation.MARKETPLACE_INSPECT
    assert observation.attempted[-1] == observation.failure.command
    assert not any(
        command in observation.attempted for command in observation.plan.commands
    )


def test_invalid_installed_selection_never_reaches_a_state_changing_operation() -> None:
    for observation in observe_invalid_persistent_selections():
        assert observation.error is not None
        assert SPEC_TREE_PLUGIN in observation.error
        assert observation.attempted
        assert all(
            command.operation
            in {Operation.MARKETPLACE_INSPECT, Operation.PLUGIN_INSPECT}
            for command in observation.attempted
        )


def test_a_codex_operation_failure_reports_the_codex_agent_and_stops() -> None:
    observation = observe_first_failure(Operation.LIFECYCLE_PLACE)

    assert observation.failure is not None
    assert observation.failure.command.agent is Agent.CODEX
    assert observation.failure.command.operation is Operation.LIFECYCLE_PLACE
    assert observation.failure.command.plugin is not None
    assert observation.failure.result.exit_code != 0
    assert all(result.exit_code == 0 for result in observation.failure.completed)
    assert observation.attempted[-1] == observation.failure.command
    assert (
        observation.attempted == observation.plan.commands[: len(observation.attempted)]
    )


def test_first_agent_cli_failure_reports_the_operation_and_stops() -> None:
    observation = observe_first_failure(Operation.PLUGIN_INSTALL)

    assert observation.failure is not None
    assert observation.failure.command.agent is Agent.CLAUDE
    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL
    assert observation.failure.command.plugin is not None
    assert observation.failure.result.exit_code != 0
    assert observation.failure.result.stderr == Operation.PLUGIN_INSTALL.value
    assert all(result.exit_code == 0 for result in observation.failure.completed)
    assert observation.attempted[-1] == observation.failure.command
    assert len(observation.attempted) < len(observation.plan.commands)
