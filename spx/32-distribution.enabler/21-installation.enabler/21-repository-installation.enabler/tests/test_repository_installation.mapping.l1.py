"""First-failure evidence across every operation a repository plan performs."""

import json

import pytest

from outcomeeng.distribution.installation import (
    NO_DIRECTORY_PATH_WARNING,
    Agent,
    CLAUDE_CATALOG_PATH,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    NONCANONICAL_SOURCE_WARNING,
    OUT_OF_SCOPE_RECORD_WARNING,
    PATHLESS_OUT_OF_SCOPE_RECORD_WARNING,
    UNREADABLE_SETTINGS_WARNING,
    UNCATALOGED_RECORD_WARNING,
    CODEX_CATALOG_PATH,
    CODEX_PLUGIN_ENTRIES_FIELD,
    InstallationMode,
    PLUGIN_OPERATIONS,
    ReportField,
    Operation,
    installed_plugin_names,
    marketplace_plugin_name,
)
from outcomeeng_testing.generators.installation import (
    RecordDisposition,
    catalog_plugin_names_from_document,
    generated_claude_listing_entries,
    generated_codex_listing_entries,
    generated_failure_classification_cases,
)
from outcomeeng_testing.harnesses.installation import (
    captured_unpublished_plugin_stderr,
    committed_catalog_plugin_names,
    observe_designated_failure,
    observe_failure_operation_domains,
    observe_first_failure,
    observe_isolated_subset_plan,
    observe_planned_operations,
    observe_record_refresh_plan,
    repository_root,
)


def test_explicit_isolated_subsets_map_to_their_selection_in_catalog_order() -> None:
    observation = observe_isolated_subset_plan()

    catalogs = {
        Agent.CLAUDE: catalog_plugin_names_from_document(
            repository_root() / CLAUDE_CATALOG_PATH
        ),
        Agent.CODEX: catalog_plugin_names_from_document(
            repository_root() / CODEX_CATALOG_PATH
        ),
    }
    planned = {
        Agent.CLAUDE: observation.plan.claude_plugins,
        Agent.CODEX: observation.plan.codex_plugins,
    }
    for agent in Agent:
        assert set(planned[agent]) == set(observation.subsets[agent])
        positions = [catalogs[agent].index(plugin) for plugin in planned[agent]]
        assert positions == sorted(set(positions))


def test_claude_inventory_maps_only_the_invocation_checkout_refresh_scopes() -> None:
    checkout = repository_root()
    catalog = catalog_plugin_names_from_document(checkout / CLAUDE_CATALOG_PATH)
    entries, in_scope = generated_claude_listing_entries(catalog, checkout)

    observed = installed_plugin_names(
        Agent.CLAUDE,
        json.dumps(list(entries)),
        checkout=checkout,
    )

    assert observed == in_scope


def test_codex_inventory_maps_only_outcomeeng_marketplace_entries() -> None:
    checkout = repository_root()
    catalog = catalog_plugin_names_from_document(checkout / CODEX_CATALOG_PATH)
    entries, in_scope = generated_codex_listing_entries(catalog)

    observed = installed_plugin_names(
        Agent.CODEX,
        json.dumps({CODEX_PLUGIN_ENTRIES_FIELD: list(entries)}),
        checkout=checkout,
    )

    assert observed == in_scope


def test_every_planned_operation_reports_its_failure_and_stops_installation() -> None:
    for operation in observe_planned_operations():
        observation = observe_first_failure(operation)
        attempted = observation.attempted
        document = json.loads(observation.stderr)

        assert observation.exit_code != 0
        assert observation.stdout == ""
        assert document[ReportField.OPERATION] == operation.value
        assert document[ReportField.AGENT] == attempted[-1].agent.value
        assert document[ReportField.COMPLETED_OPERATIONS] == len(attempted) - 1
        assert document[ReportField.EXIT_CODE] == observation.exit_code
        assert attempted == observation.command_sequence[: len(attempted)]


@pytest.mark.parametrize(
    ("mode", "source", "operation"),
    generated_failure_classification_cases(observe_failure_operation_domains()),
)
def test_absent_plugin_wording_is_pending_only_for_persistent_plugin_operations(
    mode: InstallationMode,
    source: str | None,
    operation: Operation,
) -> None:
    plugin = sorted(committed_catalog_plugin_names())[0]
    carries_plugin = operation in PLUGIN_OPERATIONS
    pending = mode is InstallationMode.PERSISTENT and carries_plugin

    observation = observe_designated_failure(
        isolated=mode is InstallationMode.ISOLATED,
        source=source,
        operation=operation,
        plugin=plugin if carries_plugin else None,
        stderr=captured_unpublished_plugin_stderr(Agent.CODEX, plugin),
    )

    if pending:
        assert observation.failure is None
        assert observation.report is not None
        assert plugin in {
            entry.plugin for entry in observation.report.pending_publication
        }
    else:
        assert observation.report is None
        assert observation.failure is not None
        assert observation.failure.command.operation is operation


def test_every_claude_install_record_maps_to_one_update_or_one_warning() -> None:
    observation = observe_record_refresh_plan()
    updates = [
        command
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation is Operation.PLUGIN_UPDATE
    ]
    warnings = [
        warning.message
        for warning in observation.plan.warnings
        if warning.agent is Agent.CLAUDE
    ]
    unmatched_updates = list(updates)
    unmatched_warnings = list(warnings)
    templates = {
        RecordDisposition.NO_DIRECTORY_PATH: NO_DIRECTORY_PATH_WARNING,
        RecordDisposition.OUT_OF_SCOPE: OUT_OF_SCOPE_RECORD_WARNING,
        RecordDisposition.PATHLESS_OUT_OF_SCOPE: PATHLESS_OUT_OF_SCOPE_RECORD_WARNING,
        RecordDisposition.UNCATALOGED: UNCATALOGED_RECORD_WARNING,
        RecordDisposition.NONCANONICAL_SOURCE: NONCANONICAL_SOURCE_WARNING,
        RecordDisposition.UNREADABLE_SETTINGS: UNREADABLE_SETTINGS_WARNING,
    }

    for entry, disposition in observation.cases:
        plugin = marketplace_plugin_name(entry[CLAUDE_PLUGIN_ID_FIELD])
        if disposition is RecordDisposition.EXCLUDED:
            assert plugin is None, (entry, disposition)
            continue
        assert plugin is not None, (entry, disposition)
        scope = entry[CLAUDE_PLUGIN_SCOPE_FIELD]
        project_path = entry.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD)
        matching_updates = [
            command
            for command in unmatched_updates
            if command.plugin == plugin
            and command.argv[-1] == scope
            and str(command.cwd) == project_path
        ]
        if disposition is RecordDisposition.UPDATE:
            assert len(matching_updates) == 1, (entry, disposition)
            unmatched_updates.remove(matching_updates[0])
            continue
        assert matching_updates == [], (entry, disposition)
        template = templates[disposition]
        expected = template.format(
            plugin=plugin, scope=scope, project_path=project_path
        )
        assert unmatched_warnings.count(expected) == 1, (entry, disposition, warnings)
        unmatched_warnings.remove(expected)

    assert unmatched_updates == []
    assert unmatched_warnings == []
    positions = [observation.catalog.index(command.plugin) for command in updates]
    assert positions == sorted(positions)
