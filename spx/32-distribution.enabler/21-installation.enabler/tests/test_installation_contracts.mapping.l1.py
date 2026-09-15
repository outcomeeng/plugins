"""Operation failure mapping across installation modes."""

from outcomeeng.distribution.installation import (
    Agent,
    InstallationMode,
    PLUGIN_OPERATIONS,
    ReportField,
    Operation,
)
from outcomeeng_testing.generators.installation import (
    generated_failure_classification_cases,
)
from outcomeeng_testing.harnesses.installation import (
    captured_unpublished_plugin_stderr,
    committed_catalog_plugin_names,
    observe_designated_failure,
    observe_failure_operation_domains,
    observe_first_failure,
    observe_planned_operations,
)
import json
import pytest


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


@pytest.mark.parametrize("plugin", committed_catalog_plugin_names())
@pytest.mark.parametrize(
    ("mode", "source", "operation"),
    generated_failure_classification_cases(observe_failure_operation_domains()),
)
def test_absent_plugin_wording_is_pending_only_for_persistent_plugin_operations(
    mode: InstallationMode,
    source: str,
    operation: Operation,
    plugin: str,
) -> None:
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
