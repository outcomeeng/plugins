"""Mapping evidence for Python-owned CI eval execution."""

from __future__ import annotations

from outcomeeng_testing.evals.factories import (
    assert_changed_paths_file_reads_git_name_status_rows,
    assert_empty_plan_exits_successfully_without_commands,
    assert_failing_suite_fails_aggregate_after_attempting_every_suite,
    assert_root_instruction_changes_select_full_suites,
)
from outcomeeng_testing.harnesses.evals import (
    assert_multi_case_plan_item_preserves_case_selector_order,
    assert_plan_items_map_to_run_commands_with_settings_and_case_selectors,
)


def test_plan_items_map_to_run_commands_with_settings_and_case_selectors() -> None:
    assert_plan_items_map_to_run_commands_with_settings_and_case_selectors()


def test_multi_case_plan_item_preserves_case_selector_order() -> None:
    assert_multi_case_plan_item_preserves_case_selector_order()


def test_root_instruction_changes_select_full_suites() -> None:
    assert_root_instruction_changes_select_full_suites()


def test_changed_paths_file_reads_git_name_status_rows() -> None:
    assert_changed_paths_file_reads_git_name_status_rows()


def test_empty_plan_exits_successfully_without_commands() -> None:
    assert_empty_plan_exits_successfully_without_commands()


def test_failing_suite_fails_aggregate_after_attempting_every_suite() -> None:
    assert_failing_suite_fails_aggregate_after_attempting_every_suite()
