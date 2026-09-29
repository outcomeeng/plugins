"""Mapping evidence for Python-owned CI eval execution."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_evals.ci_execution import (
    EXIT_FAILURE,
    EXIT_SUCCESS,
    CiRunSettings,
    execute_ci_plan,
)
from outcomeeng_evals.ci_plan import (
    ROOT_INSTRUCTION_PATHS,
    CiMode,
    EvalPlanItem,
    build_ci_plan,
    read_changed_paths_file,
)
from outcomeeng_testing.evals.factories import (
    DEFAULT_CI_OWNED_PATH,
    DEFAULT_CI_PLUGIN_DIR,
    DEFAULT_PLAN_CASE_IDS,
    DEFAULT_PLAN_RULES,
    make_changed_paths_file_cases,
    make_changed_paths_file_error_cases,
    make_eval_dir,
    make_eval_plan_item,
)
from outcomeeng_testing.evals.fakes import RecordingCommandRunner
from outcomeeng_testing.harnesses.evals import (
    assert_multi_case_plan_item_preserves_case_selector_order,
    assert_plan_items_map_to_run_commands_with_settings_and_case_selectors,
)


def test_plan_items_map_to_run_commands_with_settings_and_case_selectors() -> None:
    assert_plan_items_map_to_run_commands_with_settings_and_case_selectors()


def test_multi_case_plan_item_preserves_case_selector_order() -> None:
    assert_multi_case_plan_item_preserves_case_selector_order()


def test_root_instruction_changes_select_full_suites(tmp_path: Path) -> None:
    eval_toml = make_eval_dir(
        tmp_path / "evals" / "rule",
        plugin_dir=str(DEFAULT_CI_PLUGIN_DIR),
        owned_paths=(DEFAULT_CI_OWNED_PATH,),
        smoke_case_ids=DEFAULT_PLAN_CASE_IDS,
    )

    for root_instruction_path in ROOT_INSTRUCTION_PATHS:
        plan = build_ci_plan(
            eval_toml.parent.parent,
            mode=CiMode.PR,
            changed_paths=(root_instruction_path,),
        )

        assert plan == [
            EvalPlanItem(
                eval_toml=eval_toml,
                plugin_dir=DEFAULT_CI_PLUGIN_DIR,
                case_ids=(),
            )
        ]


def test_changed_paths_file_reads_git_name_status_rows(tmp_path: Path) -> None:
    for index, case in enumerate(make_changed_paths_file_cases()):
        changed_paths_file = tmp_path / f"changed-paths-{index}.txt"
        changed_paths_file.write_text(case.content, encoding="utf-8")

        assert read_changed_paths_file(changed_paths_file) == case.expected_paths

    for index, error_case in enumerate(make_changed_paths_file_error_cases()):
        changed_paths_file = tmp_path / f"changed-paths-error-{index}.txt"
        changed_paths_file.write_text(error_case.content, encoding="utf-8")

        with pytest.raises(ValueError):
            read_changed_paths_file(changed_paths_file)


def test_empty_plan_exits_successfully_without_commands() -> None:
    runner = RecordingCommandRunner()

    result = execute_ci_plan((), settings=CiRunSettings(), runner=runner)

    assert result.exit_code == EXIT_SUCCESS
    assert result.attempted == 0
    assert runner.calls == []


def test_failing_suite_fails_aggregate_after_attempting_every_suite() -> None:
    first, second = (make_eval_plan_item(rule=rule) for rule in DEFAULT_PLAN_RULES)
    runner = RecordingCommandRunner(exit_codes=(EXIT_FAILURE, EXIT_SUCCESS))

    result = execute_ci_plan((first, second), settings=CiRunSettings(), runner=runner)

    assert result.exit_code == EXIT_FAILURE
    assert result.attempted == len((first, second))
    assert result.failed == (first,)
    assert len(runner.calls) == len((first, second))
