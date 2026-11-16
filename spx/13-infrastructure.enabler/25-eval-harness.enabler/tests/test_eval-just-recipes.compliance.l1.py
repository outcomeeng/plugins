"""Compliance evidence for the repository-local eval Just recipes."""

from __future__ import annotations

from pathlib import Path

from outcomeeng_evals.settings import (
    DEFAULT_MAX_BUDGET_USD_TEXT,
    DEFAULT_TIMEOUT_SECONDS_TEXT,
)
from outcomeeng_testing.evals.just_recipes import (
    PRODUCER_FIXTURE_SECTION,
    RECIPE_COMMAND_BANNER,
    SUITE_PASS_LINE,
    materialize_prompts_then_check,
    observe_eval_materialize_prompts_recipe,
    run_just_eval,
    write_eval_fixture,
    write_eval_suite,
    write_fake_claude,
)

OVERRIDE_MODEL = "claude-sonnet-4-5"


def test_eval_recipe_runs_suite_with_toml_plugin_dir(tmp_path: Path) -> None:
    eval_toml, plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(tmp_path, fake_claude, "eval", str(eval_toml))

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "uv run outcomeeng-evals run" in completed.stdout
    assert f"--plugin-dir {plugin_dir}" in completed.stdout
    assert "--workers 1" in completed.stdout
    assert f"--max-budget-usd {DEFAULT_MAX_BUDGET_USD_TEXT}" in completed.stdout
    assert "--model sonnet" in completed.stdout
    assert f"--timeout-seconds {DEFAULT_TIMEOUT_SECONDS_TEXT}" in completed.stdout
    assert "--case-id" not in completed.stdout
    assert SUITE_PASS_LINE in completed.stdout
    assert completed.stdout.index(RECIPE_COMMAND_BANNER) < completed.stdout.index(
        SUITE_PASS_LINE
    )


def test_eval_case_recipe_runs_selected_case_with_toml_plugin_dir(
    tmp_path: Path,
) -> None:
    eval_toml, plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path, fake_claude, "eval-case", str(eval_toml), "case-pass"
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "uv run outcomeeng-evals run" in completed.stdout
    assert f"--plugin-dir {plugin_dir}" in completed.stdout
    assert "--workers 1" in completed.stdout
    assert f"--max-budget-usd {DEFAULT_MAX_BUDGET_USD_TEXT}" in completed.stdout
    assert "--model sonnet" in completed.stdout
    assert f"--timeout-seconds {DEFAULT_TIMEOUT_SECONDS_TEXT}" in completed.stdout
    assert "--case-id case-pass" in completed.stdout
    assert SUITE_PASS_LINE in completed.stdout
    assert completed.stdout.index(RECIPE_COMMAND_BANNER) < completed.stdout.index(
        SUITE_PASS_LINE
    )


def test_eval_recipe_uses_plugin_dir_env_override(tmp_path: Path) -> None:
    eval_toml, plugin_dir, fake_claude = write_eval_fixture(tmp_path)
    override_plugin_dir = tmp_path / "override-plugin"
    override_plugin_dir.mkdir()

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval",
        str(eval_toml),
        env_overrides={"PLUGIN_DIR": str(override_plugin_dir)},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"--plugin-dir {override_plugin_dir}" in completed.stdout
    assert f"--plugin-dir {plugin_dir}" not in completed.stdout
    assert SUITE_PASS_LINE in completed.stdout
    assert completed.stdout.index(RECIPE_COMMAND_BANNER) < completed.stdout.index(
        SUITE_PASS_LINE
    )


def test_eval_recipe_uses_model_env_override(tmp_path: Path) -> None:
    eval_toml, _plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval",
        str(eval_toml),
        env_overrides={"EVAL_MODEL": OVERRIDE_MODEL},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"--model {OVERRIDE_MODEL}" in completed.stdout
    assert SUITE_PASS_LINE in completed.stdout
    assert completed.stdout.index(RECIPE_COMMAND_BANNER) < completed.stdout.index(
        SUITE_PASS_LINE
    )


def test_eval_case_recipe_uses_model_env_override(tmp_path: Path) -> None:
    eval_toml, _plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval-case",
        str(eval_toml),
        "case-pass",
        env_overrides={"EVAL_MODEL": OVERRIDE_MODEL},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"--model {OVERRIDE_MODEL}" in completed.stdout
    assert "--case-id case-pass" in completed.stdout
    assert SUITE_PASS_LINE in completed.stdout
    assert completed.stdout.index(RECIPE_COMMAND_BANNER) < completed.stdout.index(
        SUITE_PASS_LINE
    )


def test_eval_node_recipe_runs_all_node_evals_serially(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    node_dir = tmp_path / "node"
    alpha_eval_toml = write_eval_suite(
        node_dir, plugin_dir, suite_name="alpha", case_id="case-alpha"
    )
    beta_eval_toml = write_eval_suite(
        node_dir, plugin_dir, suite_name="beta", case_id="case-beta"
    )
    eval_tomls = (alpha_eval_toml, beta_eval_toml)

    completed = run_just_eval(
        tmp_path, write_fake_claude(tmp_path), "eval-node", str(node_dir)
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "uv run outcomeeng-evals run" in completed.stdout
    assert completed.stdout.count(SUITE_PASS_LINE) == len(eval_tomls)
    assert completed.stdout.index(str(alpha_eval_toml)) < completed.stdout.index(
        str(beta_eval_toml)
    )
    assert completed.stdout.index(RECIPE_COMMAND_BANNER) < completed.stdout.index(
        SUITE_PASS_LINE
    )


def test_eval_materialize_prompts_recipe_writes_producer_prompt() -> None:
    observed = observe_eval_materialize_prompts_recipe()

    assert observed.completed.returncode == 0, (
        observed.completed.stdout + observed.completed.stderr
    )
    assert (
        f"materialized: {observed.prompt_path.resolve()}" in observed.completed.stdout
    )
    assert PRODUCER_FIXTURE_SECTION in observed.prompt_text


def test_eval_materialize_prompts_check_recipe_accepts_current_prompt() -> None:
    observed = materialize_prompts_then_check()

    assert observed.completed.returncode == 0, (
        observed.completed.stdout + observed.completed.stderr
    )
    assert f"checked: {observed.prompt_path.resolve()}" in observed.completed.stdout
