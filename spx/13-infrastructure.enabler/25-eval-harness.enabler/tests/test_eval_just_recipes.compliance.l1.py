"""Compliance tests for the repository-local eval Just recipes."""

from __future__ import annotations

from outcomeeng_testing.evals.just_recipes import (
    assert_eval_case_recipe_runs_selected_case_with_toml_plugin_dir,
    assert_eval_case_recipe_uses_model_env_override,
    assert_eval_materialize_prompts_check_recipe_accepts_current_prompt,
    assert_eval_materialize_prompts_recipe_writes_producer_prompt,
    assert_eval_node_recipe_runs_all_node_evals_serially,
    assert_eval_recipe_runs_suite_with_toml_plugin_dir,
    assert_eval_recipe_uses_model_env_override,
    assert_eval_recipe_uses_plugin_dir_env_override,
)


def test_eval_recipe_runs_suite_with_toml_plugin_dir() -> None:
    assert_eval_recipe_runs_suite_with_toml_plugin_dir()


def test_eval_case_recipe_runs_selected_case_with_toml_plugin_dir() -> None:
    assert_eval_case_recipe_runs_selected_case_with_toml_plugin_dir()


def test_eval_recipe_uses_plugin_dir_env_override() -> None:
    assert_eval_recipe_uses_plugin_dir_env_override()


def test_eval_recipe_uses_model_env_override() -> None:
    assert_eval_recipe_uses_model_env_override()


def test_eval_case_recipe_uses_model_env_override() -> None:
    assert_eval_case_recipe_uses_model_env_override()


def test_eval_node_recipe_runs_all_node_evals_serially() -> None:
    assert_eval_node_recipe_runs_all_node_evals_serially()


def test_eval_materialize_prompts_recipe_writes_producer_prompt() -> None:
    assert_eval_materialize_prompts_recipe_writes_producer_prompt()


def test_eval_materialize_prompts_check_recipe_accepts_current_prompt() -> None:
    assert_eval_materialize_prompts_check_recipe_accepts_current_prompt()
