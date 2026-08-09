"""First-failure evidence across every operation a repository plan performs."""

import pytest

from outcomeeng.distribution.installation import (
    CANONICAL_MARKETPLACE_SOURCE,
    PLUGIN_OPERATIONS,
    UNPUBLISHED_PLUGIN_FRAGMENT,
    Operation,
)
from outcomeeng_testing.harnesses.installation import (
    NONCANONICAL_MARKETPLACE_SOURCE,
    committed_catalog_plugin_names,
    designated_failure_operations,
    observe_designated_failure,
    observe_first_failure,
    observe_planned_operations,
)

CARVE_OUT_SOURCES = (CANONICAL_MARKETPLACE_SOURCE, NONCANONICAL_MARKETPLACE_SOURCE)


def _carve_out_domain() -> tuple[tuple[bool, str, Operation], ...]:
    """Every operation a run can fail at, paired with a plan that performs it.

    An isolated run registers the checkout itself, so its plan carries no
    source reconciliation, and a persistent run reconciles by refreshing an
    already-canonical source or by replacing a noncanonical one. Each case
    carries the source whose plan reaches its operation, because a designated
    operation absent from the plan fails nothing.
    """
    reached: dict[tuple[bool, Operation], str] = {}
    for isolated in (False, True):
        for source in CARVE_OUT_SOURCES:
            for operation in designated_failure_operations(
                isolated=isolated, source=source
            ):
                reached.setdefault((isolated, operation), source)
    return tuple(
        (isolated, source, operation)
        for (isolated, operation), source in reached.items()
    )


CARVE_OUT_DOMAIN = _carve_out_domain()


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


def test_the_carve_out_domain_agrees_with_the_planned_operation_enumeration() -> None:
    """Pin the domain to the other route through the same plan builders.

    Both sides reach `build_isolated_installation_plan` and
    `build_persistent_installation_plan`, so their agreement is consistency
    between two harness routes rather than an independent completeness proof.
    It catches the domain drifting away from the planned-operation enumeration;
    what the carve-out assertion actually rests on is the parametrized case
    below, which drives each operation through a real classification.
    """
    covered = {operation for _, _, operation in CARVE_OUT_DOMAIN}

    assert covered == set(observe_planned_operations())
    assert PLUGIN_OPERATIONS <= covered


@pytest.mark.parametrize(("isolated", "source", "operation"), CARVE_OUT_DOMAIN)
def test_absent_plugin_wording_is_pending_only_for_persistent_plugin_operations(
    isolated: bool,
    source: str,
    operation: Operation,
) -> None:
    plugin = sorted(committed_catalog_plugin_names())[0]
    carries_plugin = operation in PLUGIN_OPERATIONS
    pending = not isolated and carries_plugin

    observation = observe_designated_failure(
        isolated=isolated,
        source=source,
        operation=operation,
        plugin=plugin if carries_plugin else None,
        stderr=f"Error: plugin `{plugin}` was {UNPUBLISHED_PLUGIN_FRAGMENT} `outcomeeng`",
    )

    if pending:
        assert observation.failure is None
        assert observation.report is not None
        assert plugin in observation.report.pending_publication
    else:
        assert observation.report is None
        assert observation.failure is not None
        assert observation.failure.command.operation is operation
