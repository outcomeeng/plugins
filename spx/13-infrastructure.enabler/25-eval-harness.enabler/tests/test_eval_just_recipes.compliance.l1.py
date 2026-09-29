"""Compliance tests for the repository-local eval Just recipes."""

from __future__ import annotations

from outcomeeng.models import EVAL_PROFILE_MODELS
from outcomeeng_evals.ci_execution import DEFAULT_CI_WORKERS, UV_RUN_EVALS_ARGV_PREFIX
from outcomeeng_evals.cli.commands.run import (
    MAX_BUDGET_USD_OPTION,
    PLUGIN_DIR_OPTION,
    PROFILE_OPTION,
    TIMEOUT_SECONDS_OPTION,
)
from outcomeeng_evals.definition import DEFAULT_PROFILE
from outcomeeng_evals.settings import (
    DEFAULT_MAX_BUDGET_USD_TEXT,
    DEFAULT_TIMEOUT_SECONDS_TEXT,
)
from outcomeeng_testing.evals.just_recipes import (
    DEFINITION_PROFILE,
    OVERRIDE_PROFILE,
    PRODUCER_SECTION_NAME,
    RUNNING_LINE_PREFIX,
    UNSUPPORTED_PROFILE,
    run_eval_node_recipe,
    run_eval_recipe,
    run_materialize_prompts_recipe,
)

EVAL_RUN_COMMAND = " ".join(UV_RUN_EVALS_ARGV_PREFIX)
WORKERS_OPTION = "--workers"
CASE_ID_OPTION = "--case-id"
SUITE_RESULT_PREFIX = "suite pass_rate="
SUITE_PASSED_LINE = f"{SUITE_RESULT_PREFIX}100.00%"


def test_eval_recipe_runs_suite_with_toml_plugin_dir() -> None:
    run = run_eval_recipe()

    stdout = run.completed.stdout
    assert run.completed.returncode == 0, stdout + run.completed.stderr
    assert EVAL_RUN_COMMAND in stdout
    assert f"{PLUGIN_DIR_OPTION} {run.plugin_dir}" in stdout
    assert f"{WORKERS_OPTION} {DEFAULT_CI_WORKERS}" in stdout
    assert f"{MAX_BUDGET_USD_OPTION} {DEFAULT_MAX_BUDGET_USD_TEXT}" in stdout
    (running_line,) = run.running_lines
    assert f"{PROFILE_OPTION} {DEFAULT_PROFILE}" in running_line
    assert f"model {EVAL_PROFILE_MODELS[DEFAULT_PROFILE].model}" in running_line
    assert f"effort {EVAL_PROFILE_MODELS[DEFAULT_PROFILE].effort}" in running_line
    assert f"{TIMEOUT_SECONDS_OPTION} {DEFAULT_TIMEOUT_SECONDS_TEXT}" in stdout
    assert CASE_ID_OPTION not in stdout
    assert SUITE_PASSED_LINE in stdout
    assert stdout.index(RUNNING_LINE_PREFIX) < stdout.index(SUITE_PASSED_LINE)


def test_eval_case_recipe_runs_selected_case_with_toml_plugin_dir() -> None:
    run = run_eval_recipe(select_case=True)

    stdout = run.completed.stdout
    assert run.completed.returncode == 0, stdout + run.completed.stderr
    assert EVAL_RUN_COMMAND in stdout
    assert f"{PLUGIN_DIR_OPTION} {run.plugin_dir}" in stdout
    assert f"{WORKERS_OPTION} {DEFAULT_CI_WORKERS}" in stdout
    assert f"{MAX_BUDGET_USD_OPTION} {DEFAULT_MAX_BUDGET_USD_TEXT}" in stdout
    (running_line,) = run.running_lines
    assert f"{PROFILE_OPTION} {DEFAULT_PROFILE}" in running_line
    assert f"model {EVAL_PROFILE_MODELS[DEFAULT_PROFILE].model}" in running_line
    assert f"effort {EVAL_PROFILE_MODELS[DEFAULT_PROFILE].effort}" in running_line
    assert f"{TIMEOUT_SECONDS_OPTION} {DEFAULT_TIMEOUT_SECONDS_TEXT}" in stdout
    assert f"{CASE_ID_OPTION} {run.case_id}" in stdout
    assert SUITE_PASSED_LINE in stdout
    assert stdout.index(RUNNING_LINE_PREFIX) < stdout.index(SUITE_PASSED_LINE)


def test_eval_recipe_uses_plugin_dir_env_override() -> None:
    run = run_eval_recipe(override_plugin_dir=True)

    stdout = run.completed.stdout
    assert run.completed.returncode == 0, stdout + run.completed.stderr
    assert f"{PLUGIN_DIR_OPTION} {run.override_plugin_dir}" in stdout
    assert f"{PLUGIN_DIR_OPTION} {run.plugin_dir}" not in stdout
    assert SUITE_PASSED_LINE in stdout
    assert stdout.index(RUNNING_LINE_PREFIX) < stdout.index(SUITE_PASSED_LINE)


def test_eval_recipe_uses_toml_profile() -> None:
    run = run_eval_recipe(definition_profile=DEFINITION_PROFILE)

    stdout = run.completed.stdout
    assert run.completed.returncode == 0, stdout + run.completed.stderr
    (running_line,) = run.running_lines
    assert f"{PROFILE_OPTION} {DEFINITION_PROFILE}" in running_line
    assert f"model {EVAL_PROFILE_MODELS[DEFINITION_PROFILE].model}" in running_line
    assert f"effort {EVAL_PROFILE_MODELS[DEFINITION_PROFILE].effort}" in running_line
    assert SUITE_PASSED_LINE in stdout
    assert stdout.index(RUNNING_LINE_PREFIX) < stdout.index(SUITE_PASSED_LINE)


def test_eval_recipe_uses_profile_env_override() -> None:
    run = run_eval_recipe(
        definition_profile=DEFINITION_PROFILE, profile_override=OVERRIDE_PROFILE
    )

    stdout = run.completed.stdout
    assert run.completed.returncode == 0, stdout + run.completed.stderr
    (running_line,) = run.running_lines
    assert f"{PROFILE_OPTION} {OVERRIDE_PROFILE}" in running_line
    assert f"model {EVAL_PROFILE_MODELS[OVERRIDE_PROFILE].model}" in running_line
    assert f"effort {EVAL_PROFILE_MODELS[OVERRIDE_PROFILE].effort}" in running_line
    assert f"{PROFILE_OPTION} {DEFINITION_PROFILE}" not in stdout
    assert SUITE_PASSED_LINE in stdout
    assert stdout.index(RUNNING_LINE_PREFIX) < stdout.index(SUITE_PASSED_LINE)


def test_eval_case_recipe_uses_profile_env_override() -> None:
    run = run_eval_recipe(
        select_case=True,
        definition_profile=DEFINITION_PROFILE,
        profile_override=OVERRIDE_PROFILE,
    )

    stdout = run.completed.stdout
    assert run.completed.returncode == 0, stdout + run.completed.stderr
    (running_line,) = run.running_lines
    assert f"{PROFILE_OPTION} {OVERRIDE_PROFILE}" in running_line
    assert f"model {EVAL_PROFILE_MODELS[OVERRIDE_PROFILE].model}" in running_line
    assert f"effort {EVAL_PROFILE_MODELS[OVERRIDE_PROFILE].effort}" in running_line
    assert f"{PROFILE_OPTION} {DEFINITION_PROFILE}" not in stdout
    assert f"{CASE_ID_OPTION} {run.case_id}" in stdout
    assert SUITE_PASSED_LINE in stdout
    assert stdout.index(RUNNING_LINE_PREFIX) < stdout.index(SUITE_PASSED_LINE)


def test_eval_recipe_refuses_unsupported_profile_override() -> None:
    run = run_eval_recipe(
        definition_profile=DEFINITION_PROFILE, profile_override=UNSUPPORTED_PROFILE
    )

    assert run.completed.returncode != 0
    assert run.running_lines == ()
    assert SUITE_RESULT_PREFIX not in run.completed.stdout


def test_eval_case_recipe_refuses_unsupported_profile_override() -> None:
    run = run_eval_recipe(
        select_case=True,
        definition_profile=DEFINITION_PROFILE,
        profile_override=UNSUPPORTED_PROFILE,
    )

    assert run.completed.returncode != 0
    assert run.running_lines == ()
    assert SUITE_RESULT_PREFIX not in run.completed.stdout


def test_eval_node_recipe_runs_all_node_evals_serially() -> None:
    run = run_eval_node_recipe()

    stdout = run.completed.stdout
    assert run.completed.returncode == 0, stdout + run.completed.stderr
    assert EVAL_RUN_COMMAND in stdout
    assert stdout.count(SUITE_PASSED_LINE) == len(run.eval_tomls)
    suite_positions = [stdout.index(str(eval_toml)) for eval_toml in run.eval_tomls]
    assert suite_positions == sorted(suite_positions)
    assert stdout.index(RUNNING_LINE_PREFIX) < stdout.index(SUITE_PASSED_LINE)


def test_eval_materialize_prompts_recipe_writes_producer_prompt() -> None:
    run = run_materialize_prompts_recipe(check=False)

    assert run.completed.returncode == 0, run.completed.stdout + run.completed.stderr
    assert f"materialized: {run.prompt_path}" in run.completed.stdout
    assert PRODUCER_SECTION_NAME in run.prompt_text


def test_eval_materialize_prompts_check_recipe_accepts_current_prompt() -> None:
    run = run_materialize_prompts_recipe(check=True)

    assert run.completed.returncode == 0, run.completed.stdout + run.completed.stderr
    assert f"checked: {run.prompt_path}" in run.completed.stdout
