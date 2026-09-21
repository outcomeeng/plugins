"""Operation failure mapping across installation modes."""

import json
import os

import pytest

from outcomeeng.distribution.installation import (
    InstallationMode,
    ReportField,
)
from outcomeeng_testing.generators.installation import (
    FailureClassificationCase,
    generated_failure_classification_cases,
)
from outcomeeng_testing.harnesses.installation import (
    committed_catalog_plugin_names,
    observe_designated_failure,
    observe_failure_operation_domains,
    observe_first_failure,
    observe_planned_operations,
)


def test_every_planned_operation_reports_its_failure_and_stops_installation() -> None:
    for agent, operation in observe_planned_operations():
        observation = observe_first_failure(operation, agent=agent)
        attempted = observation.attempted
        document = json.loads(observation.stderr)

        assert observation.exit_code != os.EX_OK
        assert observation.stdout == ""
        assert document[ReportField.OPERATION] == operation.value
        assert document[ReportField.AGENT] == attempted[-1].agent.value
        assert document[ReportField.COMPLETED_OPERATIONS] == len(attempted[:-1])
        assert document[ReportField.EXIT_CODE] == observation.exit_code
        assert attempted == observation.command_sequence[: len(attempted)]


@pytest.mark.parametrize(
    "case",
    generated_failure_classification_cases(
        observe_failure_operation_domains(), committed_catalog_plugin_names()
    ),
)
def test_every_reachable_command_failure_maps_to_its_declared_disposition(
    case: FailureClassificationCase,
) -> None:
    observation = observe_designated_failure(
        isolated=case.mode is InstallationMode.ISOLATED,
        source=case.source,
        agent=case.agent,
        operation=case.operation,
        plugin=case.plugin,
        stderr=case.stderr,
    )

    if case.pending_publication:
        assert case.plugin is not None
        assert observation.failure is None
        assert observation.report is not None
        assert case.plugin in {
            entry.plugin for entry in observation.report.pending_publication
        }
    else:
        assert observation.report is None
        assert observation.failure is not None
        assert observation.failure.command.agent is case.agent
        assert observation.failure.command.operation is case.operation
