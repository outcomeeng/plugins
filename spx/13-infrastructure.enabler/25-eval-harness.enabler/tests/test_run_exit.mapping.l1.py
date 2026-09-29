"""Mapping test for the eval run command's threshold exit contract."""

from outcomeeng_evals.cli import EXIT_SUCCESS
from outcomeeng_testing.harnesses.eval_run_exit import run_threshold_exit_codes


def test_run_command_exit_follows_definition_threshold() -> None:
    exit_codes = run_threshold_exit_codes()

    assert exit_codes.configured_threshold_passing == EXIT_SUCCESS
    assert exit_codes.configured_threshold_failing != EXIT_SUCCESS
    assert exit_codes.default_threshold_at_configured_boundary != EXIT_SUCCESS
    assert exit_codes.default_threshold_all_passing == EXIT_SUCCESS
