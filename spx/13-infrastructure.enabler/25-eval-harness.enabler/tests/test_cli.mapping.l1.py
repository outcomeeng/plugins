"""Mapping tests for the outcomeeng-evals Click CLI."""

from __future__ import annotations

import json
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from outcomeeng.models import EVAL_PROFILE_MODELS
from outcomeeng_evals.ci_plan import CiMode, EvalPlanItem, plan_to_jsonable
from outcomeeng_evals.cli import (
    EXIT_GENERAL_ERROR,
    EXIT_INVOCATION_ERROR,
    EXIT_SUCCESS,
    main,
)
from outcomeeng_evals.cli.commands.ci import ci_command
from outcomeeng_evals.cli.commands.ci_triggers import ci_triggers_command
from outcomeeng_evals.cli.commands.discover import discover_command
from outcomeeng_evals.cli.commands.history import (
    HISTORY_PASS_VERDICT,
    history_command,
)
from outcomeeng_evals.cli.commands.materialize_prompts import (
    materialize_prompts_command,
)
from outcomeeng_evals.cli.commands.plan import plan_command
from outcomeeng_evals.cli.commands.run import (
    MAX_BUDGET_USD_OPTION,
    MAX_WORKERS,
    MIN_WORKERS,
    PROFILE_OPTION,
    TIMEOUT_SECONDS_OPTION,
    _FORMAT_SUFFIX,
    _history_row,
    _runner_factory_from_context,
    run_command,
)
from outcomeeng_evals.cli.commands.view import view_command
from outcomeeng_evals.cli.wiring import build_claude_runner
from outcomeeng_evals.definition import DEFAULT_PROFILE, EVAL_TOML_FILENAME
from outcomeeng_evals.history import (
    HISTORY_CASES_PASSED_FIELD,
    HISTORY_CASES_TOTAL_FIELD,
    HISTORY_FILENAME,
    HISTORY_GIT_SHA_FIELD,
    HISTORY_MAX_BUDGET_USD_FIELD,
    HISTORY_MODEL_FIELD,
    HISTORY_PASSED_FIELD,
    HISTORY_PASS_RATE_FIELD,
    HISTORY_SCHEMA_VERSION_FIELD,
    HISTORY_TIMEOUT_SECONDS_FIELD,
    HISTORY_TIMESTAMP_FIELD,
    HISTORY_TRANSCRIPT_FIELD,
)
from outcomeeng_evals.report import JSON_SCHEMA_VERSION
from outcomeeng_testing.evals.cli import (
    DISCOVER_RULE,
    HISTORY_ROWS_FIXTURE,
    HISTORY_VERSION_1_COMPATIBILITY_FIXTURE,
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
    RUN_CASE_ALPHA_ID,
    RUN_CASE_BETA,
    RUN_CASE_BETA_ID,
    RUN_CASE_GAMMA,
    RUN_CASE_GAMMA_ID,
    RUN_CONFIGURED_MAX_BUDGET_USD,
    RUN_CONFIGURED_TIMEOUT_SECONDS,
    RUN_DEFINITION_PROFILE,
    RUN_OVERRIDE_PROFILE,
    RUN_UNKNOWN_CASE_ID,
    build_run_cli_harness,
    invoke_plan,
    invoke_run_with_workers,
    make_discoverable_eval,
    make_mixed_policy_plan_evals,
    make_plan_eval_dir,
    relative_plan_suite,
    write_changed_paths,
)
from outcomeeng_testing.evals.factories import (
    EVAL_CASES_FILENAME,
    load_history_rows_fixture,
    make_suite_result,
    run_default_ci_subcommand,
)

CASE_ID_OPTION = "--case-id"


def test_main_group_exposes_documented_subcommands() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == EXIT_SUCCESS
    for command in (
        run_command,
        history_command,
        view_command,
        discover_command,
        plan_command,
        ci_command,
        materialize_prompts_command,
        ci_triggers_command,
    ):
        assert str(command.name) in result.output


def test_run_subcommand_requires_eval_toml_path() -> None:
    result = CliRunner().invoke(main, [str(run_command.name)])

    assert result.exit_code == EXIT_INVOCATION_ERROR


def test_run_subcommand_rejects_missing_eval_toml(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist" / EVAL_TOML_FILENAME

    result = CliRunner().invoke(main, [str(run_command.name), str(missing_path)])

    assert result.exit_code != EXIT_SUCCESS


@pytest.mark.parametrize("workers", (MAX_WORKERS + 1, MIN_WORKERS - 1))
def test_run_subcommand_rejects_workers_outside_range(
    tmp_path: Path, workers: int
) -> None:
    result = invoke_run_with_workers(tmp_path, workers)

    assert result.exit_code == EXIT_INVOCATION_ERROR
    assert "workers" in result.output.lower()


def test_run_command_uses_default_runner_factory_without_injected_context() -> None:
    with click.Context(main):
        runner_factory = _runner_factory_from_context()

    assert runner_factory is build_claude_runner


def test_discover_subcommand_lists_eval_toml_files(tmp_path: Path) -> None:
    nested_eval = make_discoverable_eval(tmp_path)

    result = CliRunner().invoke(main, [str(discover_command.name), str(tmp_path)])

    assert result.exit_code == EXIT_SUCCESS
    assert DISCOVER_RULE in result.output or str(nested_eval) in result.output


def test_discover_subcommand_succeeds_on_empty_tree(tmp_path: Path) -> None:
    result = CliRunner().invoke(main, [str(discover_command.name), str(tmp_path)])

    assert result.exit_code == EXIT_SUCCESS


def test_history_subcommand_reads_version_1_compatible_rows(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    history_path.write_bytes(HISTORY_VERSION_1_COMPATIBILITY_FIXTURE.read_bytes())

    result = CliRunner().invoke(main, [str(history_command.name), str(history_path)])

    assert result.exit_code == EXIT_SUCCESS
    with HISTORY_VERSION_1_COMPATIBILITY_FIXTURE.open(encoding="utf-8") as fixture:
        rows = tuple(json.loads(line) for line in fixture if line.strip())
    assert all(row[HISTORY_SCHEMA_VERSION_FIELD] == JSON_SCHEMA_VERSION for row in rows)
    assert all(row[HISTORY_PASSED_FIELD] is True for row in rows)
    assert all(isinstance(row[HISTORY_PASS_RATE_FIELD], float) for row in rows)
    assert result.output.splitlines() == [
        f"{row[HISTORY_TIMESTAMP_FIELD]}  {HISTORY_PASS_VERDICT}  "
        f"pass_rate={row[HISTORY_PASS_RATE_FIELD]:.1%}  "
        f"cases={row[HISTORY_CASES_PASSED_FIELD]}/{row[HISTORY_CASES_TOTAL_FIELD]}  "
        f"git={row[HISTORY_GIT_SHA_FIELD]}"
        for row in rows
    ]

    source_row = load_history_rows_fixture(HISTORY_ROWS_FIXTURE)[0]
    current_row = _history_row(
        timestamp=source_row[HISTORY_TIMESTAMP_FIELD],
        result=make_suite_result(),
        model=source_row[HISTORY_MODEL_FIELD],
        max_budget_usd=source_row[HISTORY_MAX_BUDGET_USD_FIELD],
        timeout_seconds=source_row[HISTORY_TIMEOUT_SECONDS_FIELD],
        transcript_relative=source_row[HISTORY_TRANSCRIPT_FIELD],
    )
    assert current_row[HISTORY_SCHEMA_VERSION_FIELD] == JSON_SCHEMA_VERSION
    assert HISTORY_MAX_BUDGET_USD_FIELD in current_row
    assert HISTORY_TIMEOUT_SECONDS_FIELD in current_row
    assert current_row[HISTORY_MODEL_FIELD] == source_row[HISTORY_MODEL_FIELD]


def test_history_subcommand_handles_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / HISTORY_FILENAME

    result = CliRunner().invoke(main, [str(history_command.name), str(missing_path)])

    assert result.exit_code != EXIT_SUCCESS


def test_view_subcommand_requires_run_path_or_latest_flag() -> None:
    result = CliRunner().invoke(main, [str(view_command.name)])

    assert result.exit_code != EXIT_SUCCESS


def test_ci_subcommand_executes_selected_plan(tmp_path: Path) -> None:
    run = run_default_ci_subcommand(tmp_path)

    assert run.result.exit_code == EXIT_SUCCESS
    assert run.commands == (run.expected_command,)


def test_run_command_appends_format_suffix_to_every_prompt(tmp_path: Path) -> None:
    harness = build_run_cli_harness(tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n")

    harness.invoke_run()

    (prompt,) = harness.recorded_prompts()
    assert prompt.endswith(_FORMAT_SUFFIX)
    assert harness.recorded_case_ids() == (RUN_CASE_ALPHA_ID,)


def test_run_command_filters_cases_by_case_id(tmp_path: Path) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl="\n".join((RUN_CASE_ALPHA, RUN_CASE_BETA))
    )

    result = harness.invoke_run(CASE_ID_OPTION, RUN_CASE_BETA_ID)

    assert result.exit_code == EXIT_SUCCESS
    assert harness.recorded_case_ids() == (RUN_CASE_BETA_ID,)


def test_run_command_rejects_unknown_case_id(tmp_path: Path) -> None:
    harness = build_run_cli_harness(tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n")

    result = harness.invoke_run(CASE_ID_OPTION, RUN_UNKNOWN_CASE_ID)

    assert result.exit_code == EXIT_GENERAL_ERROR
    assert RUN_UNKNOWN_CASE_ID in result.output
    assert harness.recorded_prompts() == ()


def test_run_command_filters_repeated_case_ids_in_case_file_order(
    tmp_path: Path,
) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl="\n".join((RUN_CASE_ALPHA, RUN_CASE_BETA, RUN_CASE_GAMMA))
    )

    result = harness.invoke_run(
        CASE_ID_OPTION, RUN_CASE_GAMMA_ID, CASE_ID_OPTION, RUN_CASE_ALPHA_ID
    )

    assert result.exit_code == EXIT_SUCCESS
    assert harness.recorded_case_ids() == (RUN_CASE_ALPHA_ID, RUN_CASE_GAMMA_ID)
    assert all(prompt.endswith(_FORMAT_SUFFIX) for prompt in harness.recorded_prompts())


def test_run_command_uses_default_profile_when_definition_omits_it(
    tmp_path: Path,
) -> None:
    harness = build_run_cli_harness(tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n")

    result = harness.invoke_run()

    assert result.exit_code == EXIT_SUCCESS
    assert harness.profiles == [DEFAULT_PROFILE]


def test_run_command_uses_eval_definition_profile(tmp_path: Path) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n", profile=RUN_DEFINITION_PROFILE
    )

    result = harness.invoke_run()

    assert result.exit_code == EXIT_SUCCESS
    assert harness.profiles == [RUN_DEFINITION_PROFILE]


def test_run_command_profile_option_overrides_eval_definition_profile(
    tmp_path: Path,
) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n", profile=RUN_DEFINITION_PROFILE
    )

    result = harness.invoke_run(PROFILE_OPTION, RUN_OVERRIDE_PROFILE)

    assert result.exit_code == EXIT_SUCCESS
    assert harness.profiles == [RUN_OVERRIDE_PROFILE]


def test_run_command_records_selected_model_in_artifacts(tmp_path: Path) -> None:
    harness = build_run_cli_harness(
        tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n", profile=RUN_DEFINITION_PROFILE
    )

    result = harness.invoke_run(
        PROFILE_OPTION,
        RUN_OVERRIDE_PROFILE,
        MAX_BUDGET_USD_OPTION,
        str(RUN_CONFIGURED_MAX_BUDGET_USD),
        TIMEOUT_SECONDS_OPTION,
        str(RUN_CONFIGURED_TIMEOUT_SECONDS),
    )

    assert result.exit_code == EXIT_SUCCESS
    selected_model = EVAL_PROFILE_MODELS[RUN_OVERRIDE_PROFILE].model
    (result_payload,) = harness.result_payloads()
    (history_row,) = harness.history_rows()
    assert result_payload["model"] == selected_model
    assert result_payload["max_budget_usd"] == RUN_CONFIGURED_MAX_BUDGET_USD
    assert result_payload["timeout_seconds"] == RUN_CONFIGURED_TIMEOUT_SECONDS
    assert history_row[HISTORY_MODEL_FIELD] == selected_model
    assert history_row[HISTORY_MAX_BUDGET_USD_FIELD] == RUN_CONFIGURED_MAX_BUDGET_USD
    assert history_row[HISTORY_TIMEOUT_SECONDS_FIELD] == RUN_CONFIGURED_TIMEOUT_SECONDS
    assert harness.max_budgets_usd == [RUN_CONFIGURED_MAX_BUDGET_USD]
    assert harness.timeouts_seconds == [RUN_CONFIGURED_TIMEOUT_SECONDS]


def test_run_command_rejects_model_name_as_profile_option(tmp_path: Path) -> None:
    harness = build_run_cli_harness(tmp_path, cases_jsonl=f"{RUN_CASE_ALPHA}\n")

    result = harness.invoke_run(
        PROFILE_OPTION, EVAL_PROFILE_MODELS[DEFAULT_PROFILE].model
    )

    assert result.exit_code == EXIT_GENERAL_ERROR
    assert PROFILE_OPTION in result.output
    assert harness.profiles == []


@pytest.mark.parametrize(
    ("changed_paths_text", "expected_case_ids"),
    (
        (PLAN_OWNED_PATH_CHANGE, (PLAN_SMOKE_CASE_ID,)),
        (PLAN_RENAMED_OWNED_PATH_CHANGE, (PLAN_SMOKE_CASE_ID,)),
        (PLAN_OWNED_AND_HARNESS_PATH_CHANGE, ()),
        (PLAN_HARNESS_PATH_CHANGE, ()),
        (PLAN_COPIED_HARNESS_PATH_CHANGE, ()),
        (PLAN_TEST_HARNESS_PATH_CHANGE, ()),
        (PLAN_TEST_GENERATOR_PATH_CHANGE, ()),
    ),
    ids=(
        "smoke-cases-for-owned-path-change",
        "smoke-cases-for-renamed-owned-path",
        "full-suite-when-harness-change-follows-owned-path",
        "full-suite-for-harness-change",
        "full-suite-for-copied-harness-path",
        "full-suite-for-test-harness-change",
        "full-suite-for-test-generator-change",
    ),
)
def test_plan_subcommand_selects_suite_cases_for_changed_paths(
    tmp_path: Path,
    changed_paths_text: str,
    expected_case_ids: tuple[str, ...],
) -> None:
    eval_toml = make_plan_eval_dir(tmp_path)
    changed_paths = write_changed_paths(tmp_path, changed_paths_text)

    result = invoke_plan(tmp_path, mode=CiMode.PR, changed_paths_file=changed_paths)

    assert result.exit_code == EXIT_SUCCESS
    assert json.loads(result.output) == plan_to_jsonable(
        [
            EvalPlanItem(
                eval_toml=eval_toml,
                plugin_dir=Path(PLAN_PLUGIN_DIR),
                case_ids=expected_case_ids,
            )
        ]
    )


def test_plan_subcommand_selects_full_suite_for_absolute_eval_definition_change(
    tmp_path: Path,
) -> None:
    eval_toml = make_plan_eval_dir(tmp_path)
    changed_paths = write_changed_paths(
        tmp_path, f"{eval_toml.parent / EVAL_CASES_FILENAME}\n"
    )

    result = invoke_plan(tmp_path, mode=CiMode.PR, changed_paths_file=changed_paths)

    assert result.exit_code == EXIT_SUCCESS
    assert json.loads(result.output) == plan_to_jsonable(
        [
            EvalPlanItem(
                eval_toml=eval_toml, plugin_dir=Path(PLAN_PLUGIN_DIR), case_ids=()
            )
        ]
    )


def test_plan_subcommand_selects_full_suite_for_eval_definition_change(
    tmp_path: Path,
) -> None:
    with relative_plan_suite(tmp_path) as suite:
        result = invoke_plan(
            suite.eval_root,
            mode=CiMode.PR,
            changed_paths_file=suite.changed_paths_file,
        )

    assert result.exit_code == EXIT_SUCCESS
    assert json.loads(result.output) == plan_to_jsonable(
        [
            EvalPlanItem(
                eval_toml=suite.eval_toml,
                plugin_dir=Path(PLAN_PLUGIN_DIR),
                case_ids=(),
            )
        ]
    )


def test_plan_subcommand_full_mode_excludes_manual_evals(tmp_path: Path) -> None:
    automatic_eval = make_mixed_policy_plan_evals(tmp_path)

    result = invoke_plan(tmp_path, mode=CiMode.FULL)

    assert result.exit_code == EXIT_SUCCESS
    assert json.loads(result.output) == plan_to_jsonable(
        [
            EvalPlanItem(
                eval_toml=automatic_eval,
                plugin_dir=Path(PLAN_PLUGIN_DIR),
                case_ids=(),
            )
        ]
    )


def test_plan_subcommand_skips_unrelated_pr_change(tmp_path: Path) -> None:
    make_plan_eval_dir(tmp_path)
    changed_paths = write_changed_paths(tmp_path, PLAN_UNRELATED_PATH_CHANGE)

    result = invoke_plan(tmp_path, mode=CiMode.PR, changed_paths_file=changed_paths)

    assert result.exit_code == EXIT_SUCCESS
    assert json.loads(result.output) == []
