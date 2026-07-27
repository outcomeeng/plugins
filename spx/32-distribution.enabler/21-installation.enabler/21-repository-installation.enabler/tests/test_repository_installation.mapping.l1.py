"""First-failure evidence across every operation a repository plan performs."""

from outcomeeng_testing.harnesses.installation import (
    observe_first_failure,
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
