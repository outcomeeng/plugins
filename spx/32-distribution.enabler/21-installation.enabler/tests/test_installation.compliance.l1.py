"""State-boundary and failure evidence for repository installation."""

from pathlib import Path

from outcomeeng.distribution.installation import Operation, STATE_ENV_NAMES
from outcomeeng_testing.harnesses.installation import (
    observe_first_failure,
    observe_repository_plan,
)


def test_every_command_uses_the_explicit_checkout_and_agent_homes() -> None:
    observation = observe_repository_plan()

    assert all(
        command.cwd == observation.plan.roots.checkout
        for command in observation.plan.commands
    )
    assert all(
        all(
            Path(value).is_relative_to(observation.plan.roots.state)
            for name, value in command.environment
            if name in STATE_ENV_NAMES
        )
        for command in observation.plan.commands
    )


def test_first_agent_cli_failure_reports_the_operation_and_stops() -> None:
    observation = observe_first_failure()

    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL
    assert observation.failure.command.plugin is not None
    assert observation.failure.result.exit_code != 0
    assert observation.failure.result.stderr == Operation.PLUGIN_INSTALL.value
    assert all(result.exit_code == 0 for result in observation.failure.completed)
    assert observation.attempted[-1] == observation.failure.command
    assert len(observation.attempted) < len(observation.plan.commands)
