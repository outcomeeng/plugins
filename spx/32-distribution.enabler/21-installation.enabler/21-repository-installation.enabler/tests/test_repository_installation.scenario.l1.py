"""Controlled CLI and first-failure evidence for repository installation."""

import json
from typing import cast

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_INSTALLED_PLUGINS_FIELD,
    CLAUDE_INSTALLED_RECORD_COMMIT_FIELD,
    CLAUDE_INSTALLED_RECORD_PATH_FIELD,
    CLAUDE_INSTALLED_RECORD_VERSION_FIELD,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    CLAUDE_PLUGIN_VERSION_FIELD,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_SCOPE_FLAG,
    FIRST_INSTALL_WARNING,
    Operation,
    PATHLESS_LISTING_ENTRY_WARNING,
    VERSIONLESS_LISTING_ENTRY_WARNING,
    ReportField,
    SPEC_TREE_PLUGIN,
    UNREADABLE_SETTINGS_WARNING,
    WITHHELD_REGISTRATION_WARNING,
    marketplace_plugin_identifier,
    marketplace_plugin_name,
    report_document,
)
from pathlib import Path

from outcomeeng_testing.generators.installation import (
    ClosingDisposition,
    MOVED_DISPOSITIONS,
    RecordDisposition,
)
from outcomeeng_testing.harnesses.installation import (
    RegistryState,
    UnreadableSourceCase,
    absent_from_every_agent,
    committed_catalog_plugin_names,
    observe_first_persistent_cli,
    observe_inspection_failure,
    observe_invalid_isolated_selection,
    observe_invalid_persistent_selection,
    observe_persistent_plan,
    observe_bootstrap_record_drift,
    observe_defective_record_listing,
    observe_unreadable_source,
    observe_record_refresh_plan,
    observe_unpublished_plugin,
    observe_verification_recipe,
)


def test_verification_recipe_uses_pytest_discovery_for_the_node() -> None:
    observation = observe_verification_recipe()

    assert observation.exit_code == 0, observation.stderr
    assert observation.invoked == (
        "test",
        "spx/32-distribution.enabler/21-installation.enabler/"
        "21-repository-installation.enabler/tests",
    )


def test_first_persistent_run_installs_only_spec_tree_and_warns() -> None:
    observation = observe_first_persistent_cli()
    document = json.loads(observation.stdout)
    install_commands = [
        command
        for command in observation.attempted
        if command.operation is Operation.PLUGIN_INSTALL
    ]
    enable_commands = [
        command
        for command in observation.attempted
        if command.operation is Operation.PLUGIN_ENABLE
    ]

    assert observation.exit_code == 0
    assert [command.agent for command in install_commands] == list(Agent)
    assert {command.plugin for command in install_commands} == {SPEC_TREE_PLUGIN}
    assert [command.agent for command in enable_commands] == [Agent.CLAUDE]
    assert {command.plugin for command in enable_commands} == {SPEC_TREE_PLUGIN}
    assert document[ReportField.CLAUDE_PLUGINS] == [SPEC_TREE_PLUGIN]
    assert document[ReportField.CODEX_PLUGINS] == [SPEC_TREE_PLUGIN]
    assert document[ReportField.WARNINGS] == [
        {
            ReportField.AGENT: agent.value,
            ReportField.MESSAGE: FIRST_INSTALL_WARNING.format(agent=agent.value),
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
    assert observation.attempted
    assert all(
        command.operation in {Operation.MARKETPLACE_INSPECT, Operation.PLUGIN_INSPECT}
        for command in observation.attempted
    )


def test_invalid_isolated_subset_is_rejected_before_mutation() -> None:
    observation = observe_invalid_isolated_selection()

    assert observation.error is not None
    assert SPEC_TREE_PLUGIN in observation.error
    assert observation.attempted == ()


def test_marketplace_inspection_failure_stops_before_any_plan_operation() -> None:
    observation = observe_inspection_failure()
    document = json.loads(observation.stderr)

    assert observation.exit_code != 0
    assert observation.stdout == ""
    assert document[ReportField.OPERATION] == Operation.MARKETPLACE_INSPECT.value
    assert document[ReportField.AGENT] == observation.attempted[-1].agent.value
    assert document[ReportField.COMPLETED_OPERATIONS] == len(observation.attempted) - 1
    assert (
        observation.attempted
        == observation.command_sequence[: len(observation.attempted)]
    )
    assert not any(
        command in observation.attempted for command in observation.plan.commands
    )


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
        cast(str, entry[ReportField.PLUGIN])
        for entry in cast(
            list[dict[str, str]], document[ReportField.PENDING_PUBLICATION]
        )
    }

    # The text summary and this document answer from the same accessor. Reading
    # the plan directly here reported a plugin as installed in one field while
    # the next field reported it unpublished, and the two disagreed inside one
    # document.
    assert pending == {absent}
    assert not pending & set(cast(list[str], document[ReportField.CLAUDE_PLUGINS]))
    assert absent in cast(list[str], document[ReportField.CODEX_PLUGINS])


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


def test_fresh_home_plan_adds_the_declared_marketplace() -> None:
    observation = observe_persistent_plan(claude_marketplace_listed=False)

    source_operations = [
        command.operation
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation
        in {Operation.MARKETPLACE_ADD, Operation.MARKETPLACE_REFRESH}
    ]
    assert source_operations == [Operation.MARKETPLACE_ADD]


def test_persistent_run_moves_every_record_without_a_command_in_another_checkout() -> (
    None
):
    observation = observe_record_refresh_plan()
    claude_commands = [
        command
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
    ]
    updates = [
        command
        for command in claude_commands
        if command.operation is Operation.PLUGIN_UPDATE
    ]
    native = {
        (
            marketplace_plugin_name(
                entry[CLAUDE_PLUGIN_ID_FIELD], observation.marketplace
            ),
            entry[CLAUDE_PLUGIN_SCOPE_FIELD],
        )
        for entry, disposition in observation.cases
        if disposition is RecordDisposition.INVOCATION_NATIVE
    }
    rewritten = {
        (
            marketplace_plugin_name(
                entry[CLAUDE_PLUGIN_ID_FIELD], observation.marketplace
            ),
            entry[CLAUDE_PLUGIN_SCOPE_FIELD],
            Path(entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]),
        )
        for entry, disposition in observation.cases
        if disposition
        in {RecordDisposition.FILE_REWRITE, RecordDisposition.MISSING_DIRECTORY}
    }

    assert not any(
        command.operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for command in claude_commands
    )
    assert {(command.plugin, command.argv[-1]) for command in updates} == native
    assert len(updates) == len(native)
    assert all(command.argv[-2] == CLAUDE_SCOPE_FLAG for command in updates)
    assert all(command.cwd == observation.checkout for command in observation.attempted)
    assert {
        (rewrite.record.plugin, rewrite.record.scope, rewrite.record.project_path)
        for rewrite in observation.report.rewrites
    } == rewritten
    assert observation.report.rewrite_warnings == ()
    moved = {
        (
            marketplace_plugin_name(
                entry[CLAUDE_PLUGIN_ID_FIELD], observation.marketplace
            ),
            entry[CLAUDE_PLUGIN_SCOPE_FIELD],
            Path(entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]),
        )
        for entry, disposition in observation.cases
        if disposition in MOVED_DISPOSITIONS
    }
    reported = {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            Path(cast(str, record[ReportField.PROJECT_PATH])),
        ): (record[ReportField.VERSION_BEFORE], record[ReportField.VERSION_AFTER])
        for record in cast(
            list[dict[str, str]], observation.document[ReportField.CLAUDE_RECORDS]
        )
    }
    assert set(reported) == moved
    for entry, disposition in observation.cases:
        if disposition not in MOVED_DISPOSITIONS:
            continue
        plugin = marketplace_plugin_name(
            entry[CLAUDE_PLUGIN_ID_FIELD], observation.marketplace
        )
        assert plugin is not None
        key = (
            plugin,
            entry[CLAUDE_PLUGIN_SCOPE_FIELD],
            Path(entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]),
        )
        assert reported[key][0] == entry[CLAUDE_PLUGIN_VERSION_FIELD], key
        if disposition is not RecordDisposition.INVOCATION_NATIVE:
            assert reported[key][1] == observation.target_version, key
    assert observation.document[ReportField.OFF_TARGET_RECORDS] == []
    assert observation.exit_code == 0


def test_a_record_whose_directory_is_gone_is_rewritten_and_never_named_by_a_command() -> (
    None
):
    observation = observe_record_refresh_plan()
    gone = [
        entry
        for entry, disposition in observation.cases
        if disposition is RecordDisposition.MISSING_DIRECTORY
        and Path(entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]) == observation.absent_path
    ]
    assert gone
    for entry in gone:
        plugin = marketplace_plugin_name(
            entry[CLAUDE_PLUGIN_ID_FIELD], observation.marketplace
        )
        rewrite = next(
            rewrite
            for rewrite in observation.report.rewrites
            if rewrite.record.plugin == plugin
            and rewrite.record.scope == entry[CLAUDE_PLUGIN_SCOPE_FIELD]
            and rewrite.record.project_path == observation.absent_path
        )
        after = next(
            item
            for item in cast(
                "dict[str, list[dict[str, object]]]",
                observation.record_file_after[CLAUDE_INSTALLED_PLUGINS_FIELD],
            )[entry[CLAUDE_PLUGIN_ID_FIELD]]
            if item.get(CLAUDE_PLUGIN_SCOPE_FIELD) == entry[CLAUDE_PLUGIN_SCOPE_FIELD]
            and item.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD)
            == str(observation.absent_path)
        )
        assert (
            after[CLAUDE_INSTALLED_RECORD_VERSION_FIELD] == observation.target_version
        )
        assert after[CLAUDE_INSTALLED_RECORD_PATH_FIELD] == str(rewrite.install_path)
        assert after[CLAUDE_INSTALLED_RECORD_COMMIT_FIELD] == rewrite.commit
    assert not any(
        str(observation.absent_path) in argument
        for command in observation.attempted
        for argument in (*command.argv, str(command.cwd))
    )


def test_a_defective_refresh_scope_entry_is_reported_and_the_run_continues() -> None:
    observation = observe_defective_record_listing()

    assert (
        PATHLESS_LISTING_ENTRY_WARNING.format(
            plugin=SPEC_TREE_PLUGIN, scope=CLAUDE_PROJECT_SCOPE
        )
        in observation.warnings
    )
    assert (
        VERSIONLESS_LISTING_ENTRY_WARNING.format(
            plugin=SPEC_TREE_PLUGIN,
            scope=CLAUDE_PROJECT_SCOPE,
            project_path=observation.defect_checkout,
        )
        in observation.warnings
    )
    assert [record.project_path for record in observation.plan.rewrite_records] == [
        observation.other_checkout
    ]
    assert [
        command.operation
        for command in observation.attempted
        if command.agent is Agent.CLAUDE
    ] == [
        Operation.MARKETPLACE_INSPECT,
        Operation.PLUGIN_INSPECT,
        Operation.MARKETPLACE_REFRESH,
        Operation.PLUGIN_INSTALL,
        Operation.PLUGIN_ENABLE,
        Operation.MARKETPLACE_HEAD,
        Operation.PLUGIN_LIST,
    ]
    assert (
        _recorded_version(
            observation.record_file_after,
            SPEC_TREE_PLUGIN,
            observation.plan.roots.marketplace,
            observation.other_checkout,
        )
        == observation.target_version
    )
    assert observation.exit_code != 0


def test_a_bootstrap_run_reports_the_records_it_moved_and_the_records_it_did_not() -> (
    None
):
    observation = observe_bootstrap_record_drift()
    moved = {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            record[ReportField.PROJECT_PATH],
        ): (record[ReportField.VERSION_BEFORE], record[ReportField.VERSION_AFTER])
        for record in cast(
            "list[dict[str, str]]",
            observation.document[ReportField.CLAUDE_RECORDS],
        )
    }
    unrefreshed = {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            record[ReportField.PROJECT_PATH],
        ): record[ReportField.VERSION]
        for record in cast(
            "list[dict[str, str]]",
            observation.document[ReportField.UNREFRESHED_RECORDS],
        )
    }

    assert observation.document[ReportField.TARGET] is None
    assert moved == {
        (SPEC_TREE_PLUGIN, CLAUDE_PROJECT_SCOPE, str(observation.checkout)): (
            observation.listed_version,
            observation.target_version,
        )
    }
    assert unrefreshed == {
        (SPEC_TREE_PLUGIN, CLAUDE_PROJECT_SCOPE, str(observation.other_checkout)): (
            observation.listed_version
        )
    }
    assert observation.document[ReportField.OFF_TARGET_RECORDS] == []
    assert observation.exit_code != 0


def test_unreadable_invocation_settings_stop_bootstrap_and_nothing_else() -> None:
    both_registered = RegistryState(claude=True, codex=True)
    codex_unregistered = RegistryState(claude=True, codex=False)
    claude_unregistered = RegistryState(claude=False, codex=True)
    observation = observe_unreadable_source(
        (both_registered, codex_unregistered, claude_unregistered)
    )

    by_state = {case.state: case for case in observation.cases}
    marketplace = by_state[both_registered].plan.roots.marketplace
    settings_suffix = UNREADABLE_SETTINGS_WARNING.format(diagnostic="")
    withheld_suffix = WITHHELD_REGISTRATION_WARNING.format(
        diagnostic="", marketplace=marketplace
    )
    for state, case in by_state.items():
        settings_warnings = [
            warning
            for warning in case.warnings
            if warning.message.endswith(settings_suffix)
        ]
        assert len(settings_warnings) == 1, state
        assert str(observation.settings_path) in settings_warnings[0].message, state
        assert settings_warnings[0].blocking, state
        claude_operations = _agent_operations(case, Agent.CLAUDE)
        assert Operation.PLUGIN_INSTALL not in claude_operations, state
        assert Operation.PLUGIN_ENABLE not in claude_operations, state
        assert {
            warning.agent
            for warning in case.warnings
            if warning.message.endswith(withheld_suffix)
        } == {
            agent
            for agent, registered in (
                (Agent.CLAUDE, state.claude),
                (Agent.CODEX, state.codex),
            )
            if not registered
        }, state
        assert case.exit_code != 0, state

    for state in (both_registered, codex_unregistered):
        case = by_state[state]
        assert _agent_operations(case, Agent.CLAUDE) == (
            Operation.MARKETPLACE_INSPECT,
            Operation.PLUGIN_INSPECT,
            Operation.MARKETPLACE_REFRESH,
            Operation.MARKETPLACE_HEAD,
            Operation.PLUGIN_LIST,
        ), state
        assert [record.project_path for record in case.plan.rewrite_records] == [
            observation.other_checkout
        ], state
        assert (
            _recorded_version(
                case.record_file_after,
                SPEC_TREE_PLUGIN,
                marketplace,
                observation.other_checkout,
            )
            == case.target_version
        ), state

    assert _agent_operations(by_state[codex_unregistered], Agent.CODEX) == (
        Operation.MARKETPLACE_INSPECT,
        Operation.PLUGIN_INSPECT,
    )
    assert _agent_operations(by_state[claude_unregistered], Agent.CLAUDE) == (
        Operation.MARKETPLACE_INSPECT,
        Operation.PLUGIN_INSPECT,
        Operation.PLUGIN_LIST,
    )
    assert by_state[claude_unregistered].plan.rewrite_records == ()


def _agent_operations(
    case: UnreadableSourceCase, agent: Agent
) -> tuple[Operation, ...]:
    return tuple(
        command.operation for command in case.attempted if command.agent is agent
    )


def _recorded_version(
    document: dict[str, object], plugin: str, marketplace: str, project_path: Path
) -> object:
    entries = cast(
        "dict[str, list[dict[str, object]]]",
        document[CLAUDE_INSTALLED_PLUGINS_FIELD],
    )[marketplace_plugin_identifier(plugin, marketplace)]
    return next(
        item[CLAUDE_INSTALLED_RECORD_VERSION_FIELD]
        for item in entries
        if item.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD) == str(project_path)
    )


def test_a_record_written_between_the_listing_reads_is_reported_and_fails_the_run() -> (
    None
):
    observation = observe_record_refresh_plan(supplied_closing_listing=True)
    appeared = [
        entry
        for entry, disposition in observation.closing_cases
        if disposition is ClosingDisposition.APPEARED
    ]
    assert len(appeared) == 1
    (entry,) = appeared
    plugin = marketplace_plugin_name(
        entry[CLAUDE_PLUGIN_ID_FIELD], observation.marketplace
    )
    appeared_report = {
        ReportField.PLUGIN: plugin,
        ReportField.SCOPE: entry[CLAUDE_PLUGIN_SCOPE_FIELD],
        ReportField.PROJECT_PATH: str(observation.appearing_checkout),
        ReportField.VERSION: entry[CLAUDE_PLUGIN_VERSION_FIELD],
    }

    assert appeared_report in cast(
        "list[dict[str, str]]", observation.document[ReportField.UNREFRESHED_RECORDS]
    )
    assert appeared_report in cast(
        "list[dict[str, str]]", observation.document[ReportField.OFF_TARGET_RECORDS]
    )
    assert not any(
        str(observation.appearing_checkout) in argument
        for command in observation.attempted
        for argument in (*command.argv, str(command.cwd))
    )
    claude_operations = [
        command.operation
        for command in observation.attempted
        if command.agent is Agent.CLAUDE
    ]
    assert claude_operations.count(Operation.PLUGIN_LIST) == 1
    assert claude_operations[-1] is Operation.PLUGIN_LIST
    assert observation.exit_code != 0
