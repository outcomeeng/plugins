"""Mapping evidence for the outcomeeng-evals Click CLI."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from outcomeeng_evals.ci_plan import (
    PLAN_CASE_IDS_FIELD,
    PLAN_EVAL_TOML_FIELD,
    PLAN_PLUGIN_DIR_FIELD,
)
from outcomeeng_evals.cli import (
    EXIT_GENERAL_ERROR,
    EXIT_INVOCATION_ERROR,
    EXIT_SUCCESS,
    SUBCOMMANDS,
    main,
)
from outcomeeng_evals.cli.commands.history import HISTORY_PASS_VERDICT
from outcomeeng_evals.cli.commands.run import (
    _FORMAT_SUFFIX,
    MAX_WORKERS,
    MIN_WORKERS,
)
from outcomeeng_evals.cli.wiring import build_claude_runner
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.history import (
    HISTORY_CASES_PASSED_FIELD,
    HISTORY_CASES_TOTAL_FIELD,
    HISTORY_GIT_SHA_FIELD,
    HISTORY_MAX_BUDGET_USD_FIELD,
    HISTORY_MODEL_FIELD,
    HISTORY_PASS_RATE_FIELD,
    HISTORY_PASSED_FIELD,
    HISTORY_SCHEMA_VERSION_FIELD,
    HISTORY_TIMEOUT_SECONDS_FIELD,
    HISTORY_TIMESTAMP_FIELD,
)
from outcomeeng_evals.report import JSON_SCHEMA_VERSION
from outcomeeng_evals.settings import DEFAULT_MAX_BUDGET_USD, DEFAULT_TIMEOUT_SECONDS
from outcomeeng_testing.evals.cli import (
    PLAN_COPIED_HARNESS_PATH_CHANGE,
    PLAN_HARNESS_PATH_CHANGE,
    PLAN_OWNED_AND_HARNESS_PATH_CHANGE,
    PLAN_OWNED_PATH_CHANGE,
    PLAN_PLUGIN_DIR,
    PLAN_RENAMED_OWNED_PATH_CHANGE,
    PLAN_SMOKE_CASE_ID,
    PLAN_TEST_GENERATOR_PATH_CHANGE,
    PLAN_TEST_HARNESS_PATH_CHANGE,
    PLAN_UNRELATED_PATH_CHANGE,
    RUN_CASE_ALPHA,
    RUN_CASE_BETA,
    RUN_CASE_GAMMA,
    RUN_DEFAULT_MODEL,
    RUN_OVERRIDE_MODEL,
    build_run_cli_harness,
    current_history_row,
    default_runner_factory,
    invoke_main_help,
    invoke_run_with_workers,
    observe_history_over_version_1_rows,
    observe_plan_full_mode_with_manual_eval,
    observe_pr_plan,
    observe_pr_plan_for_absolute_eval_artifact,
    observe_pr_plan_for_relative_eval_artifact,
    run_argv,
    write_discoverable_eval,
)
from outcomeeng_testing.evals.factories import make_default_ci_command_harness


def _plan_entry(eval_toml: Path, case_ids: tuple[str, ...]) -> dict[str, object]:
    return {
        PLAN_EVAL_TOML_FIELD: str(eval_toml),
        PLAN_PLUGIN_DIR_FIELD: PLAN_PLUGIN_DIR,
        PLAN_CASE_IDS_FIELD: list(case_ids),
    }


def test_main_group_exposes_documented_subcommands() -> None:
    result = invoke_main_help()

    assert result.exit_code == EXIT_SUCCESS
    _, _, commands_section = result.output.partition("Commands:\n")
    listed_names = {
        line.split()[0]
        for line in commands_section.splitlines()
        if line.startswith("  ") and not line.startswith("   ") and line.strip()
    }
    assert listed_names == {subcommand.name for subcommand in SUBCOMMANDS}


def test_run_subcommand_requires_eval_toml_path() -> None:
    result = CliRunner().invoke(main, ["run"])

    assert result.exit_code == EXIT_INVOCATION_ERROR


def test_run_subcommand_rejects_missing_eval_toml(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist" / EVAL_TOML_FILENAME

    result = CliRunner().invoke(main, ["run", str(missing_path)])

    assert result.exit_code != EXIT_SUCCESS


def test_run_subcommand_rejects_workers_above_cap(tmp_path: Path) -> None:
    result = invoke_run_with_workers(tmp_path, MAX_WORKERS + 1)

    assert result.exit_code == EXIT_INVOCATION_ERROR
    assert "workers" in result.output.lower()


def test_run_subcommand_rejects_workers_below_minimum(tmp_path: Path) -> None:
    result = invoke_run_with_workers(tmp_path, MIN_WORKERS - 1)

    assert result.exit_code == EXIT_INVOCATION_ERROR
    assert "workers" in result.output.lower()


def test_run_command_uses_default_runner_factory_without_injected_context() -> None:
    assert default_runner_factory() is build_claude_runner


def test_discover_subcommand_lists_eval_toml_files(tmp_path: Path) -> None:
    nested_eval = write_discoverable_eval(tmp_path)

    result = CliRunner().invoke(main, ["discover", str(tmp_path)])

    assert result.exit_code == EXIT_SUCCESS
    assert str(nested_eval) in result.output


def test_discover_subcommand_succeeds_on_empty_tree(tmp_path: Path) -> None:
    result = CliRunner().invoke(main, ["discover", str(tmp_path)])

    assert result.exit_code == EXIT_SUCCESS


def test_history_subcommand_reads_version_1_compatible_rows(tmp_path: Path) -> None:
    observed = observe_history_over_version_1_rows(tmp_path)

    assert observed.result.exit_code == EXIT_SUCCESS
    assert all(
        row[HISTORY_SCHEMA_VERSION_FIELD] == JSON_SCHEMA_VERSION
        for row in observed.rows
    )
    expected_summaries = []
    for row in observed.rows:
        assert row[HISTORY_PASSED_FIELD] is True
        pass_rate = row[HISTORY_PASS_RATE_FIELD]
        assert isinstance(pass_rate, float)
        expected_summaries.append(
            f"{row[HISTORY_TIMESTAMP_FIELD]}  {HISTORY_PASS_VERDICT}  "
            f"pass_rate={pass_rate:.1%}  "
            f"cases={row[HISTORY_CASES_PASSED_FIELD]}/"
            f"{row[HISTORY_CASES_TOTAL_FIELD]}  "
            f"git={row[HISTORY_GIT_SHA_FIELD]}"
        )
    assert observed.result.output.splitlines() == expected_summaries

    source_row, current_row = current_history_row()
    assert current_row[HISTORY_SCHEMA_VERSION_FIELD] == JSON_SCHEMA_VERSION
    assert HISTORY_MAX_BUDGET_USD_FIELD in current_row
    assert HISTORY_TIMEOUT_SECONDS_FIELD in current_row
    assert current_row[HISTORY_MODEL_FIELD] == source_row[HISTORY_MODEL_FIELD]


def test_history_subcommand_handles_missing_file(tmp_path: Path) -> None:
    result = CliRunner().invoke(main, ["history", str(tmp_path / "history.jsonl")])

    assert result.exit_code != EXIT_SUCCESS


def test_view_subcommand_requires_run_path_or_latest_flag() -> None:
    result = CliRunner().invoke(main, ["view"])

    assert result.exit_code != EXIT_SUCCESS


def test_ci_subcommand_executes_selected_plan(tmp_path: Path) -> None:
    harness = make_default_ci_command_harness(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "ci",
            str(harness.eval_root),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(harness.changed_paths_file),
        ],
        env=harness.fake_uv.env,
    )

    assert result.exit_code == EXIT_SUCCESS
    assert harness.fake_uv.commands() == (harness.expected_command,)


def test_run_command_appends_format_suffix_to_every_prompt(tmp_path: Path) -> None:
    harness = build_run_cli_harness(tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n")

    harness.runner.invoke(main, run_argv(harness), obj=harness.runner_context)

    assert len(harness.recorder.transcripts) == 1
    captured_prompt, _ = harness.recorder.transcripts[0]
    assert captured_prompt.endswith(_FORMAT_SUFFIX)
    assert "Case alpha" in captured_prompt


def test_run_command_filters_cases_by_case_id(tmp_path: Path) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl="\n".join((RUN_CASE_ALPHA, RUN_CASE_BETA))
    )

    result = harness.runner.invoke(
        main, run_argv(harness, "--case-id", "beta"), obj=harness.runner_context
    )

    assert result.exit_code == EXIT_SUCCESS
    assert len(harness.recorder.transcripts) == 1
    captured_prompt, _ = harness.recorder.transcripts[0]
    assert "Case beta" in captured_prompt
    assert "Case alpha" not in captured_prompt


def test_run_command_rejects_unknown_case_id(tmp_path: Path) -> None:
    harness = build_run_cli_harness(tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n")

    result = harness.runner.invoke(
        main, run_argv(harness, "--case-id", "missing"), obj=harness.runner_context
    )

    assert result.exit_code == EXIT_GENERAL_ERROR
    assert "missing" in result.output
    assert harness.recorder.transcripts == []


def test_run_command_filters_repeated_case_ids_in_case_file_order(
    tmp_path: Path,
) -> None:
    harness = build_run_cli_harness(
        tmp_path,
        cases_jsonl="\n".join((RUN_CASE_ALPHA, RUN_CASE_BETA, RUN_CASE_GAMMA)),
    )

    result = harness.runner.invoke(
        main,
        run_argv(harness, "--case-id", "gamma", "--case-id", "alpha"),
        obj=harness.runner_context,
    )

    assert result.exit_code == EXIT_SUCCESS
    captured_case_ids = [
        prompt.split("Case ", 1)[1].split(":", 1)[0]
        for prompt, _metadata in harness.recorder.transcripts
    ]
    assert captured_case_ids == ["alpha", "gamma"]
    assert all(
        prompt.endswith(_FORMAT_SUFFIX)
        for prompt, _metadata in harness.recorder.transcripts
    )


def test_run_command_uses_eval_definition_model(tmp_path: Path) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n", model=RUN_DEFAULT_MODEL
    )

    result = harness.runner.invoke(main, run_argv(harness), obj=harness.runner_context)

    assert result.exit_code == EXIT_SUCCESS
    assert harness.models == [RUN_DEFAULT_MODEL]


def test_run_command_model_option_overrides_eval_definition_model(
    tmp_path: Path,
) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n", model=RUN_DEFAULT_MODEL
    )

    result = harness.runner.invoke(
        main,
        run_argv(harness, "--model", RUN_OVERRIDE_MODEL),
        obj=harness.runner_context,
    )

    assert result.exit_code == EXIT_SUCCESS
    assert harness.models == [RUN_OVERRIDE_MODEL]


def test_run_command_records_selected_model_in_artifacts(tmp_path: Path) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n", model=RUN_DEFAULT_MODEL
    )
    configured_budget = DEFAULT_MAX_BUDGET_USD * 2
    configured_timeout = DEFAULT_TIMEOUT_SECONDS * 2

    result = harness.runner.invoke(
        main,
        run_argv(
            harness,
            "--model",
            RUN_OVERRIDE_MODEL,
            "--max-budget-usd",
            str(configured_budget),
            "--timeout-seconds",
            str(configured_timeout),
        ),
        obj=harness.runner_context,
    )

    assert result.exit_code == EXIT_SUCCESS
    eval_dir = harness.eval_toml.parent
    result_json = next((eval_dir / "runs").glob("*.json"))
    history_row = json.loads((eval_dir / "history.jsonl").read_text(encoding="utf-8"))
    result_payload = json.loads(result_json.read_text(encoding="utf-8"))
    assert result_payload[HISTORY_MODEL_FIELD] == RUN_OVERRIDE_MODEL
    assert result_payload[HISTORY_MAX_BUDGET_USD_FIELD] == configured_budget
    assert result_payload[HISTORY_TIMEOUT_SECONDS_FIELD] == configured_timeout
    assert history_row[HISTORY_MODEL_FIELD] == RUN_OVERRIDE_MODEL
    assert history_row[HISTORY_MAX_BUDGET_USD_FIELD] == configured_budget
    assert history_row[HISTORY_TIMEOUT_SECONDS_FIELD] == configured_timeout
    assert harness.max_budgets_usd == [configured_budget]
    assert harness.timeouts_seconds == [configured_timeout]


def test_run_command_rejects_inherit_model_option(tmp_path: Path) -> None:
    harness = build_run_cli_harness(tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n")

    result = harness.runner.invoke(
        main, run_argv(harness, "--model", "inherit"), obj=harness.runner_context
    )

    assert result.exit_code == EXIT_GENERAL_ERROR
    assert "inherit" in result.output
    assert harness.models == []


def test_plan_subcommand_selects_smoke_cases_for_owned_path_change(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_OWNED_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, (PLAN_SMOKE_CASE_ID,))]


def test_plan_subcommand_selects_smoke_cases_for_renamed_owned_path(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_RENAMED_OWNED_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, (PLAN_SMOKE_CASE_ID,))]


def test_plan_subcommand_selects_full_suite_when_harness_change_follows_owned_path(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_OWNED_AND_HARNESS_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_selects_full_suite_for_harness_change(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_HARNESS_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_selects_full_suite_for_copied_harness_path(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_COPIED_HARNESS_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_selects_full_suite_for_test_harness_change(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_TEST_HARNESS_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_selects_full_suite_for_test_generator_change(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_TEST_GENERATOR_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_selects_full_suite_for_absolute_eval_definition_change(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan_for_absolute_eval_artifact(tmp_path)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_selects_full_suite_for_eval_definition_change(
    tmp_path: Path,
) -> None:
    observed = observe_pr_plan_for_relative_eval_artifact(tmp_path)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_full_mode_excludes_manual_evals(tmp_path: Path) -> None:
    observed = observe_plan_full_mode_with_manual_eval(tmp_path)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == [_plan_entry(observed.eval_toml, ())]


def test_plan_subcommand_skips_unrelated_pr_change(tmp_path: Path) -> None:
    observed = observe_pr_plan(tmp_path, PLAN_UNRELATED_PATH_CHANGE)

    assert observed.exit_code == EXIT_SUCCESS
    assert observed.plan == []
