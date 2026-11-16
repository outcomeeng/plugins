"""Mapping evidence for the eval run command's threshold exit contract."""

from outcomeeng_evals.cli import EXIT_SUCCESS
from outcomeeng_testing.harnesses.eval_run_exit import observe_run_command_exits


def test_run_command_exit_follows_definition_threshold() -> None:
    observed = observe_run_command_exits()

    assert observed.passing == EXIT_SUCCESS
    assert observed.failing != EXIT_SUCCESS
    assert observed.default_rejects_configured_boundary != EXIT_SUCCESS
    assert observed.default_passing == EXIT_SUCCESS
