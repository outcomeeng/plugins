"""Mapping tests for the outcomeeng-evals Click CLI."""

from __future__ import annotations

from outcomeeng_evals.testing.cli import (
    assert_ci_subcommand_executes_selected_plan,
    assert_discover_subcommand_lists_eval_toml_files,
    assert_discover_subcommand_succeeds_on_empty_tree,
    assert_history_subcommand_handles_missing_file,
    assert_history_subcommand_reads_history_file,
    assert_main_group_exposes_documented_subcommands,
    assert_plan_full_mode_excludes_manual_evals,
    assert_plan_selects_full_suite_for_absolute_eval_definition_change,
    assert_plan_selects_full_suite_for_copied_harness_path,
    assert_plan_selects_full_suite_for_eval_definition_change,
    assert_plan_selects_full_suite_for_harness_change,
    assert_plan_selects_full_suite_for_test_harness_change,
    assert_plan_selects_full_suite_for_test_generator_change,
    assert_plan_selects_full_suite_when_harness_change_follows_owned_path,
    assert_plan_selects_smoke_cases_for_owned_path_change,
    assert_plan_selects_smoke_cases_for_renamed_owned_path,
    assert_plan_skips_unrelated_pr_change,
    assert_run_command_appends_format_suffix_to_every_prompt,
    assert_run_command_filters_cases_by_case_id,
    assert_run_command_filters_repeated_case_ids_in_case_file_order,
    assert_run_command_model_option_overrides_eval_definition_model,
    assert_run_command_records_selected_model_in_artifacts,
    assert_run_command_rejects_inherit_model_option,
    assert_run_command_rejects_unknown_case_id,
    assert_run_command_uses_default_runner_factory_without_injected_context,
    assert_run_command_uses_eval_definition_model,
    assert_run_subcommand_rejects_missing_eval_toml,
    assert_run_subcommand_rejects_workers_above_cap,
    assert_run_subcommand_rejects_workers_below_minimum,
    assert_run_subcommand_requires_eval_toml_path,
    assert_view_subcommand_requires_run_path_or_latest_flag,
)


def test_main_group_exposes_documented_subcommands() -> None:
    assert_main_group_exposes_documented_subcommands()


def test_run_subcommand_requires_eval_toml_path() -> None:
    assert_run_subcommand_requires_eval_toml_path()


def test_run_subcommand_rejects_missing_eval_toml() -> None:
    assert_run_subcommand_rejects_missing_eval_toml()


def test_run_subcommand_rejects_workers_above_cap() -> None:
    assert_run_subcommand_rejects_workers_above_cap()


def test_run_subcommand_rejects_workers_below_minimum() -> None:
    assert_run_subcommand_rejects_workers_below_minimum()


def test_run_command_uses_default_runner_factory_without_injected_context() -> None:
    assert_run_command_uses_default_runner_factory_without_injected_context()


def test_discover_subcommand_lists_eval_toml_files() -> None:
    assert_discover_subcommand_lists_eval_toml_files()


def test_discover_subcommand_succeeds_on_empty_tree() -> None:
    assert_discover_subcommand_succeeds_on_empty_tree()


def test_history_subcommand_reads_history_file() -> None:
    assert_history_subcommand_reads_history_file()


def test_history_subcommand_handles_missing_file() -> None:
    assert_history_subcommand_handles_missing_file()


def test_view_subcommand_requires_run_path_or_latest_flag() -> None:
    assert_view_subcommand_requires_run_path_or_latest_flag()


def test_ci_subcommand_executes_selected_plan() -> None:
    assert_ci_subcommand_executes_selected_plan()


def test_run_command_appends_format_suffix_to_every_prompt() -> None:
    assert_run_command_appends_format_suffix_to_every_prompt()


def test_run_command_filters_cases_by_case_id() -> None:
    assert_run_command_filters_cases_by_case_id()


def test_run_command_rejects_unknown_case_id() -> None:
    assert_run_command_rejects_unknown_case_id()


def test_run_command_filters_repeated_case_ids_in_case_file_order() -> None:
    assert_run_command_filters_repeated_case_ids_in_case_file_order()


def test_run_command_uses_eval_definition_model() -> None:
    assert_run_command_uses_eval_definition_model()


def test_run_command_model_option_overrides_eval_definition_model() -> None:
    assert_run_command_model_option_overrides_eval_definition_model()


def test_run_command_records_selected_model_in_artifacts() -> None:
    assert_run_command_records_selected_model_in_artifacts()


def test_run_command_rejects_inherit_model_option() -> None:
    assert_run_command_rejects_inherit_model_option()


def test_plan_subcommand_selects_smoke_cases_for_owned_path_change() -> None:
    assert_plan_selects_smoke_cases_for_owned_path_change()


def test_plan_subcommand_selects_smoke_cases_for_renamed_owned_path() -> None:
    assert_plan_selects_smoke_cases_for_renamed_owned_path()


def test_plan_subcommand_selects_full_suite_when_harness_change_follows_owned_path() -> (
    None
):
    assert_plan_selects_full_suite_when_harness_change_follows_owned_path()


def test_plan_subcommand_selects_full_suite_for_harness_change() -> None:
    assert_plan_selects_full_suite_for_harness_change()


def test_plan_subcommand_selects_full_suite_for_copied_harness_path() -> None:
    assert_plan_selects_full_suite_for_copied_harness_path()


def test_plan_subcommand_selects_full_suite_for_test_harness_change() -> None:
    assert_plan_selects_full_suite_for_test_harness_change()


def test_plan_subcommand_selects_full_suite_for_test_generator_change() -> None:
    assert_plan_selects_full_suite_for_test_generator_change()


def test_plan_subcommand_selects_full_suite_for_absolute_eval_definition_change() -> (
    None
):
    assert_plan_selects_full_suite_for_absolute_eval_definition_change()


def test_plan_subcommand_selects_full_suite_for_eval_definition_change() -> None:
    assert_plan_selects_full_suite_for_eval_definition_change()


def test_plan_subcommand_full_mode_excludes_manual_evals() -> None:
    assert_plan_full_mode_excludes_manual_evals()


def test_plan_subcommand_skips_unrelated_pr_change() -> None:
    assert_plan_skips_unrelated_pr_change()
