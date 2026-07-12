"""Mapping wrapper for the eval run command's threshold exit contract."""

from outcomeeng_testing.harnesses.eval_run_exit import (
    assert_run_command_exit_follows_definition_threshold,
)


def test_run_command_exit_follows_definition_threshold() -> None:
    assert_run_command_exit_follows_definition_threshold()
