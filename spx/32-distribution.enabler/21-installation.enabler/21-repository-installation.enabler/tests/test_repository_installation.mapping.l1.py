"""First-failure evidence across every operation a repository plan performs."""

import json

import pytest

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_CATALOG_PATH,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_USER_SCOPE,
    CODEX_CATALOG_PATH,
    CODEX_PLUGIN_ENTRIES_FIELD,
    CODEX_PLUGIN_ID_FIELD,
    CODEX_PLUGIN_MARKETPLACE_FIELD,
    InstallationMode,
    MARKETPLACE_NAME,
    PLUGIN_OPERATIONS,
    ReportField,
    UNPUBLISHED_PLUGIN_FRAGMENT,
    Operation,
    installed_plugin_names,
)
from outcomeeng_testing.generators.installation import (
    catalog_plugin_names_from_document,
    generated_failure_classification_cases,
)
from outcomeeng_testing.harnesses.installation import (
    committed_catalog_plugin_names,
    observe_designated_failure,
    observe_failure_operation_domains,
    observe_first_failure,
    observe_planned_operations,
    repository_root,
)


def test_claude_inventory_maps_only_the_invocation_checkout_project_scope() -> None:
    checkout = repository_root()
    catalog = catalog_plugin_names_from_document(checkout / CLAUDE_CATALOG_PATH)
    entries = []
    for index, plugin in enumerate(catalog):
        entry = {
            CLAUDE_PLUGIN_ID_FIELD: f"{plugin}@{MARKETPLACE_NAME}",
            CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
            CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
        }
        if index % 3 == 1:
            entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD] = str(checkout.parent)
        elif index % 3 == 2:
            entry[CLAUDE_PLUGIN_SCOPE_FIELD] = CLAUDE_USER_SCOPE
            del entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]
        entries.append(entry)

    observed = installed_plugin_names(
        Agent.CLAUDE,
        json.dumps(entries),
        checkout=checkout,
    )

    assert observed == frozenset(
        plugin for index, plugin in enumerate(catalog) if index % 3 == 0
    )


def test_codex_inventory_maps_only_outcomeeng_marketplace_entries() -> None:
    checkout = repository_root()
    catalog = catalog_plugin_names_from_document(checkout / CODEX_CATALOG_PATH)
    entries = [
        {
            CODEX_PLUGIN_ID_FIELD: f"{plugin}@{MARKETPLACE_NAME}",
            CODEX_PLUGIN_MARKETPLACE_FIELD: (
                MARKETPLACE_NAME if index % 2 == 0 else f"{MARKETPLACE_NAME}-other"
            ),
        }
        for index, plugin in enumerate(catalog)
    ]

    observed = installed_plugin_names(
        Agent.CODEX,
        json.dumps({CODEX_PLUGIN_ENTRIES_FIELD: entries}),
        checkout=checkout,
    )

    assert observed == frozenset(
        plugin for index, plugin in enumerate(catalog) if index % 2 == 0
    )


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
    source: str,
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
        stderr=UNPUBLISHED_PLUGIN_FRAGMENT,
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
