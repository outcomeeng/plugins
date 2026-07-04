"""Mapping evidence for Python-owned CI eval execution."""

from __future__ import annotations

from outcomeeng_evals.ci_execution import (
    CiRunSettings,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    command_for_plan_item,
    execute_ci_plan,
)
from outcomeeng_evals.testing.factories import (
    DEFAULT_PLAN_CASE_IDS,
    make_eval_plan_item,
    make_eval_plan_command_cases,
)
from outcomeeng_evals.testing.fakes import RecordingCommandRunner


def test_plan_items_map_to_run_commands_with_settings_and_case_selectors() -> None:
    for case in make_eval_plan_command_cases():
        command = command_for_plan_item(case.item, settings=CiRunSettings())

        assert command == case.expected_command


def test_multi_case_plan_item_preserves_case_selector_order() -> None:
    item = make_eval_plan_item(case_ids=DEFAULT_PLAN_CASE_IDS)

    command = command_for_plan_item(item, settings=CiRunSettings())

    assert command[-4:] == (
        "--case-id",
        *DEFAULT_PLAN_CASE_IDS[:1],
        "--case-id",
        *DEFAULT_PLAN_CASE_IDS[1:],
    )


def test_empty_plan_exits_successfully_without_commands() -> None:
    runner = RecordingCommandRunner()

    result = execute_ci_plan(
        (),
        settings=CiRunSettings(),
        runner=runner,
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.attempted == 0
    assert runner.calls == []


def test_failing_suite_fails_aggregate_after_attempting_every_suite() -> None:
    first = make_eval_plan_item(rule="first")
    second = make_eval_plan_item(rule="second")
    runner = RecordingCommandRunner(exit_codes=(EXIT_FAILURE, EXIT_SUCCESS))

    result = execute_ci_plan((first, second), settings=CiRunSettings(), runner=runner)

    assert result.exit_code == EXIT_FAILURE
    assert result.attempted == 2
    assert result.failed == (first,)
    assert len(runner.calls) == 2
