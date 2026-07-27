"""Catalog, state-boundary, and failure evidence for repository installation."""

import json
from pathlib import Path
from typing import cast

from outcomeeng.distribution.installation import (
    Agent,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    CODEX_HOME_ENV,
    InstallationMode,
    Operation,
    STATE_ENV_NAMES,
)
from outcomeeng_testing.harnesses.installation import (
    observe_first_failure,
    observe_persistent_execution,
    observe_repository_plan,
)


def test_each_mode_uses_each_catalogs_complete_ordered_plugin_set() -> None:
    isolated = observe_repository_plan()
    persistent = observe_persistent_execution()
    claude_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(isolated.claude_catalog)
    )
    codex_catalog = cast(
        dict[str, list[dict[str, object]]], json.loads(isolated.codex_catalog)
    )
    expected_claude = tuple(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in claude_catalog[CATALOG_PLUGINS_FIELD]
    )
    expected_codex = tuple(
        cast(str, plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in codex_catalog[CATALOG_PLUGINS_FIELD]
    )

    assert isolated.plan.claude_plugins == expected_claude
    assert isolated.plan.codex_plugins == expected_codex
    assert persistent.report.plan.claude_plugins == expected_claude
    assert persistent.report.plan.codex_plugins == expected_codex


def test_every_command_uses_the_explicit_checkout_and_agent_homes() -> None:
    observation = observe_repository_plan()

    assert all(
        command.cwd == observation.plan.roots.checkout
        for command in observation.plan.commands
    )
    assert all(
        all(
            Path(value).is_relative_to(observation.plan.roots.state)
            for name, value in command.environment
            if name in STATE_ENV_NAMES
        )
        for command in observation.plan.commands
    )


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
        dict(command.environment)[CODEX_HOME_ENV]
        == str(plan.roots.codex_home)
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
