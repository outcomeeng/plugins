"""Controlled CLI and first-failure evidence for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    Agent,
    FIRST_INSTALL_WARNING,
    SPEC_TREE_PLUGIN,
    report_document,
    CANONICAL_MARKETPLACE_SOURCE,
    Operation,
    SourceAction,
    USER_SCOPE_COLLISION_DIAGNOSTIC,
    VERIFICATION_RECIPE_COMMAND,
)
from outcomeeng_testing.harnesses.installation import (
    absent_from_every_agent,
    committed_catalog_plugin_names,
    observe_unpublished_plugin,
    NONCANONICAL_MARKETPLACE_SOURCE,
    observe_claude_user_collision,
    observe_inspection_failure,
    observe_invalid_isolated_selection,
    observe_invalid_persistent_selection,
    observe_first_persistent_cli,
    observe_persistent_plan,
    observe_verification_recipe,
)


def test_verification_recipe_aliases_the_exact_installation_evidence() -> None:
    observation = observe_verification_recipe()

    assert observation.exit_code == 0, observation.stderr
    assert observation.invoked == VERIFICATION_RECIPE_COMMAND


def test_first_persistent_run_installs_only_spec_tree_and_warns() -> None:
    observation = observe_first_persistent_cli()
    document = json.loads(observation.stdout)

    assert observation.exit_code == 0
    assert document["claude_plugins"] == [SPEC_TREE_PLUGIN]
    assert document["codex_plugins"] == [SPEC_TREE_PLUGIN]
    assert document["warnings"] == [
        {
            "agent": agent.value,
            "message": FIRST_INSTALL_WARNING.format(agent=agent.value),
        }
        for agent in Agent
    ]
    assert observation.stderr.splitlines() == [
        f"warning: {FIRST_INSTALL_WARNING.format(agent=agent.value)}" for agent in Agent
    ]


def test_invalid_persistent_subset_is_rejected_before_mutation() -> None:
    observation = observe_invalid_persistent_selection()

    assert observation.error is not None
    assert SPEC_TREE_PLUGIN in observation.error
    assert all(
        command.operation in {Operation.MARKETPLACE_INSPECT, Operation.PLUGIN_INSPECT}
        for command in observation.attempted
    )


def test_invalid_isolated_subset_is_rejected_before_mutation() -> None:
    observation = observe_invalid_isolated_selection()

    assert observation.error is not None
    assert SPEC_TREE_PLUGIN in observation.error
    assert observation.attempted == ()


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
    assert observation.failure.completed
    assert observation.attempted[-1] == observation.failure.command
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
        isolated=False, unpublished=absent_from_every_agent(frozenset({absent}))
    )

    assert observation.failure is None
    assert observation.report is not None
    assert {entry.plugin for entry in observation.report.pending_publication} == {
        absent
    }
    installed = {
        call.plugin
        for call in observation.calls
        if call.operation is Operation.PLUGIN_INSTALL
    }
    # Every catalog plugin, not merely more than one: "every other plugin still
    # installs" fails the moment the run stops early, and a count threshold
    # passes a run that stopped after the second plugin.
    assert installed == committed_catalog_plugin_names()


def test_isolated_installation_treats_an_absent_plugin_as_terminal() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=True, unpublished=absent_from_every_agent(frozenset({absent}))
    )

    assert observation.report is None
    assert observation.failure is not None
    assert observation.failure.command.plugin == absent
    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL


def test_the_json_report_never_lists_a_pending_plugin_as_installed() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=False, unpublished={Agent.CLAUDE: frozenset({absent})}
    )

    assert observation.report is not None
    document = report_document(observation.report)
    pending = {
        cast(str, entry["plugin"])
        for entry in cast(list[dict[str, str]], document["pending_publication"])
    }

    # The text summary and this document answer from the same accessor. Reading
    # the plan directly here reported a plugin as installed in one field while
    # the next field reported it unpublished, and the two disagreed inside one
    # document.
    assert pending == {absent}
    assert not pending & set(cast(list[str], document["claude_plugins"]))
    assert absent in cast(list[str], document["codex_plugins"])


def test_a_plugin_absent_from_one_agent_stays_installed_for_the_other() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=False, unpublished={Agent.CLAUDE: frozenset({absent})}
    )

    assert observation.failure is None
    assert observation.report is not None
    # The two marketplaces refresh separately, so one agent reporting a plugin
    # unpublished says nothing about the other. A pending record carrying only
    # the plugin name cannot express that, and drops the plugin from both
    # agents' installed counts on either one's failure.
    assert observation.report.pending_for(Agent.CLAUDE) == frozenset({absent})
    assert observation.report.pending_for(Agent.CODEX) == frozenset()
