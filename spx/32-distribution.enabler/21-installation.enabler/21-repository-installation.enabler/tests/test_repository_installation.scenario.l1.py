"""Controlled first-failure evidence for repository installation."""

from outcomeeng.distribution.installation import (
    Agent,
    CANONICAL_MARKETPLACE_SOURCE,
    Operation,
    SourceAction,
)
from outcomeeng_testing.harnesses.installation import (
    observe_claude_user_collision,
    observe_first_failure,
    observe_persistent_plan,
)


def test_persistent_installation_refreshes_canonical_sources_and_catalogs() -> None:
    observation = observe_persistent_plan()

    assert observation.preflight.claude_source_action is SourceAction.REFRESH
    assert any(
        command.agent is Agent.CLAUDE
        and command.operation is Operation.MARKETPLACE_REFRESH
        for command in observation.plan.commands
    )
    assert any(
        command.agent is Agent.CODEX
        and command.operation is Operation.MARKETPLACE_REFRESH
        for command in observation.plan.commands
    )
    assert {
        command.plugin
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation is Operation.PLUGIN_INSTALL
    } == set(observation.plan.claude_plugins)
    assert {
        command.plugin
        for command in observation.plan.commands
        if command.agent is Agent.CODEX
        and command.operation is Operation.PLUGIN_INSTALL
    } == set(observation.plan.codex_plugins)


def test_persistent_installation_replaces_noncanonical_sources() -> None:
    observation = observe_persistent_plan(
        claude_repository="/tmp/local-marketplace",
        codex_source="/tmp/local-marketplace",
    )

    assert observation.preflight.claude_source_action is SourceAction.REPLACE
    assert [
        command.operation
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation
        in {Operation.MARKETPLACE_REMOVE, Operation.MARKETPLACE_ADD}
    ] == [Operation.MARKETPLACE_REMOVE, Operation.MARKETPLACE_ADD]
    assert [
        command.operation
        for command in observation.plan.commands
        if command.agent is Agent.CODEX
        and command.operation
        in {Operation.MARKETPLACE_REMOVE, Operation.MARKETPLACE_ADD}
    ] == [Operation.MARKETPLACE_REMOVE, Operation.MARKETPLACE_ADD]
    assert any(
        CANONICAL_MARKETPLACE_SOURCE in command.argv
        for command in observation.plan.commands
        if command.operation is Operation.MARKETPLACE_ADD
    )


def test_claude_user_scope_collision_stops_before_mutation() -> None:
    observation = observe_claude_user_collision()

    assert str(observation.settings_path) in observation.error
    assert "user-scope marketplace collision" in observation.error
    assert observation.attempted == ()


def test_repository_installation_stops_after_the_first_failed_operation() -> None:
    observation = observe_first_failure()

    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL
    assert observation.failure.command.plugin is not None
    assert all(result.exit_code == 0 for result in observation.failure.completed)
    assert observation.attempted[-1] == observation.failure.command
    assert len(observation.attempted) < len(observation.plan.commands)
