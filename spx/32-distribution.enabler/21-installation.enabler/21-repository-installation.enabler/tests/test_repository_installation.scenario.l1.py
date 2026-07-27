"""Controlled first-failure evidence for repository installation."""

from outcomeeng.distribution.installation import Operation
from outcomeeng_testing.harnesses.installation import observe_first_failure


def test_repository_installation_stops_after_the_first_failed_operation() -> None:
    observation = observe_first_failure()

    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL
    assert observation.failure.command.plugin is not None
    assert all(result.exit_code == 0 for result in observation.failure.completed)
    assert observation.attempted[-1] == observation.failure.command
    assert len(observation.attempted) < len(observation.plan.commands)
