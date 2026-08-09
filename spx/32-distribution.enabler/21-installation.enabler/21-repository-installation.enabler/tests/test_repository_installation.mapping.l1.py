"""First-failure evidence across every operation a repository plan performs."""

import pytest

from outcomeeng.distribution.installation import (
    UNPUBLISHED_PLUGIN_FRAGMENT,
    Operation,
)
from outcomeeng_testing.harnesses.installation import (
    committed_catalog_plugin_names,
    observe_designated_failure,
    observe_first_failure,
    observe_planned_operations,
)

PENDING = "pending"
TERMINAL = "terminal"

# Every combination of installation mode and operation kind, each failing with
# the wording that reports a plugin absent from the marketplace. Only a
# persistent plugin operation is classified as pending publication.
CARVE_OUT_DOMAIN = (
    (False, Operation.PLUGIN_INSTALL, PENDING),
    (False, Operation.PLUGIN_ENABLE, PENDING),
    (False, Operation.MARKETPLACE_REFRESH, TERMINAL),
    (True, Operation.PLUGIN_INSTALL, TERMINAL),
)


def test_every_planned_operation_reports_its_failure_and_stops_installation() -> None:
    for operation in observe_planned_operations():
        observation = observe_first_failure(operation)
        attempted = observation.attempted

        assert observation.failure is not None
        assert observation.failure.command.operation is operation
        assert observation.failure.command.agent is not None
        assert all(result.exit_code == 0 for result in observation.failure.completed)
        assert attempted[-1] == observation.failure.command
        assert attempted == observation.plan.commands[: len(attempted)]


@pytest.mark.parametrize(("isolated", "operation", "expected"), CARVE_OUT_DOMAIN)
def test_absent_plugin_wording_is_pending_only_for_persistent_plugin_operations(
    isolated: bool,
    operation: Operation,
    expected: str,
) -> None:
    plugin = sorted(committed_catalog_plugin_names())[0]
    carries_plugin = operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}

    observation = observe_designated_failure(
        isolated=isolated,
        operation=operation,
        plugin=plugin if carries_plugin else None,
        stderr=f"Error: plugin `{plugin}` was {UNPUBLISHED_PLUGIN_FRAGMENT} `outcomeeng`",
    )

    if expected == PENDING:
        assert observation.failure is None
        assert observation.report is not None
        assert plugin in observation.report.pending_publication
    else:
        assert observation.report is None
        assert observation.failure is not None
        assert observation.failure.command.operation is operation
