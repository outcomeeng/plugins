"""Controlled first-failure evidence for repository installation."""

import json

from outcomeeng.distribution.installation import (
    Agent,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    CANONICAL_MARKETPLACE_SOURCE,
    Operation,
    SourceAction,
    USER_SCOPE_COLLISION_DIAGNOSTIC,
    VERIFICATION_RECIPE_COMMAND,
)
from outcomeeng_testing.harnesses.installation import (
    observe_claude_user_collision,
    observe_persistent_execution,
    observe_persistent_plan,
    observe_verification_recipe,
)


def test_persistent_installation_refreshes_canonical_sources_and_catalogs() -> None:
    observation = observe_persistent_execution()
    plan = observation.report.plan

    assert observation.preflight.claude_source_action is SourceAction.REFRESH
    assert any(
        command.agent is Agent.CLAUDE
        and command.operation is Operation.MARKETPLACE_REFRESH
        for command in plan.commands
    )
    assert any(
        command.agent is Agent.CODEX
        and command.operation is Operation.MARKETPLACE_REFRESH
        for command in plan.commands
    )
    assert {
        command.plugin
        for command in plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation is Operation.PLUGIN_INSTALL
    } == {
        plugin[CATALOG_PLUGIN_NAME_FIELD]
        for plugin in json.loads(observation.claude_catalog)[CATALOG_PLUGINS_FIELD]
    }
    assert {
        command.plugin
        for command in plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation is Operation.PLUGIN_ENABLE
    } == {
        plugin[CATALOG_PLUGIN_NAME_FIELD]
        for plugin in json.loads(observation.claude_catalog)[CATALOG_PLUGINS_FIELD]
    }
    assert {
        command.plugin
        for command in plan.commands
        if command.agent is Agent.CODEX
        and command.operation is Operation.PLUGIN_INSTALL
    } == {
        plugin[CATALOG_PLUGIN_NAME_FIELD]
        for plugin in json.loads(observation.codex_catalog)[CATALOG_PLUGINS_FIELD]
    }
    assert observation.attempted[1:] == plan.commands


def test_verification_recipe_aliases_the_exact_l2_evidence() -> None:
    observation = observe_verification_recipe()

    assert observation.exit_code == 0, observation.stderr
    assert observation.invoked == VERIFICATION_RECIPE_COMMAND


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
    assert USER_SCOPE_COLLISION_DIAGNOSTIC in observation.error
    assert observation.attempted == ()
