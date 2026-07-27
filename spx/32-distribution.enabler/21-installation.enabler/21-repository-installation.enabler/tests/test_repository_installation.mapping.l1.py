"""First-failure evidence across every operation a repository plan performs."""

from outcomeeng.distribution.installation import Operation
from outcomeeng_testing.harnesses.installation import (
    observe_first_failure,
    observe_inspection_failure,
    observe_planned_operations,
)


def test_every_planned_operation_reports_its_failure_and_stops_installation() -> None:
    for operation in observe_planned_operations():
        observation = observe_first_failure(operation)
        attempted = observation.attempted

        assert observation.failure.command.operation is operation
        assert observation.failure.command.agent is not None
        assert all(result.exit_code == 0 for result in observation.failure.completed)
        assert attempted[-1] == observation.failure.command
        assert attempted == observation.plan.commands[: len(attempted)]


def test_marketplace_inspection_failure_stops_before_any_plan_operation() -> None:
    observation = observe_inspection_failure()

    assert observation.failure.command.operation is Operation.MARKETPLACE_INSPECT
    assert observation.failure.command.agent is not None
    assert observation.failure.completed == ()
    assert observation.attempted == (observation.failure.command,)
    assert not any(
        command in observation.attempted for command in observation.plan.commands
    )
