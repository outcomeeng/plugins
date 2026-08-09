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
    committed_catalog_plugin_names,
    observe_unpublished_plugin,
    NONCANONICAL_MARKETPLACE_SOURCE,
    observe_claude_user_collision,
    observe_inspection_failure,
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
        claude_repository=NONCANONICAL_MARKETPLACE_SOURCE,
        codex_source=NONCANONICAL_MARKETPLACE_SOURCE,
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


def test_marketplace_inspection_failure_stops_before_any_plan_operation() -> None:
    observation = observe_inspection_failure()

    assert observation.failure is not None
    assert observation.failure.command.operation is Operation.MARKETPLACE_INSPECT
    assert observation.failure.command.agent is not None
    assert observation.failure.completed == ()
    assert observation.attempted == (observation.failure.command,)
    assert not any(
        command in observation.attempted for command in observation.plan.commands
    )


def test_claude_user_scope_collision_stops_before_mutation() -> None:
    observation = observe_claude_user_collision()

    assert observation.error is not None
    assert str(observation.settings_path) in observation.error
    assert USER_SCOPE_COLLISION_DIAGNOSTIC in observation.error
    assert observation.attempted == ()


def test_persistent_installation_reports_an_unpublished_plugin_and_completes() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=False, unpublished=frozenset({absent})
    )

    assert observation.failure is None
    assert observation.report is not None
    assert observation.report.pending_publication == (absent,)
    installed = {
        call.plugin
        for call in observation.calls
        if call.operation is Operation.PLUGIN_INSTALL
    }
    assert absent in installed
    assert len(installed) > 1


def test_isolated_installation_treats_an_absent_plugin_as_terminal() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=True, unpublished=frozenset({absent})
    )

    assert observation.report is None
    assert observation.failure is not None
    assert observation.failure.command.plugin == absent
    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL
