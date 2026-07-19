"""Marketplace-owned fixtures for repository-local eval Just recipe tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

from outcomeeng_evals.producer_prompt import (
    PRODUCER_PATH_PLACEHOLDER,
    PRODUCER_SECTION_NAME_PLACEHOLDER,
    PRODUCER_SECTION_PLACEHOLDER,
)
from outcomeeng_evals.settings import (
    DEFAULT_MAX_BUDGET_USD_TEXT,
    DEFAULT_TIMEOUT_SECONDS_TEXT,
)
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace

REPO_ROOT = Path(__file__).resolve().parents[2]


@with_temp_workspace
def assert_eval_recipe_runs_suite_with_toml_plugin_dir(tmp_path: Path) -> None:
    eval_toml, plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval",
        str(eval_toml),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "uv run outcomeeng-evals run" in completed.stdout
    assert f"--plugin-dir {plugin_dir}" in completed.stdout
    assert "--workers 1" in completed.stdout
    assert f"--max-budget-usd {DEFAULT_MAX_BUDGET_USD_TEXT}" in completed.stdout
    assert "--model sonnet" in completed.stdout
    assert f"--timeout-seconds {DEFAULT_TIMEOUT_SECONDS_TEXT}" in completed.stdout
    assert "--case-id" not in completed.stdout
    assert "suite pass_rate=100.00%" in completed.stdout
    assert_printed_command_precedes_suite_result(completed)


@with_temp_workspace
def assert_eval_case_recipe_runs_selected_case_with_toml_plugin_dir(
    tmp_path: Path,
) -> None:
    eval_toml, plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval-case",
        str(eval_toml),
        "case-pass",
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "uv run outcomeeng-evals run" in completed.stdout
    assert f"--plugin-dir {plugin_dir}" in completed.stdout
    assert "--workers 1" in completed.stdout
    assert f"--max-budget-usd {DEFAULT_MAX_BUDGET_USD_TEXT}" in completed.stdout
    assert "--model sonnet" in completed.stdout
    assert f"--timeout-seconds {DEFAULT_TIMEOUT_SECONDS_TEXT}" in completed.stdout
    assert "--case-id case-pass" in completed.stdout
    assert "suite pass_rate=100.00%" in completed.stdout
    assert_printed_command_precedes_suite_result(completed)


@with_temp_workspace
def assert_eval_recipe_uses_plugin_dir_env_override(tmp_path: Path) -> None:
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
    assert "suite pass_rate=100.00%" in completed.stdout
    assert_printed_command_precedes_suite_result(completed)


@with_temp_workspace
def assert_eval_recipe_uses_model_env_override(tmp_path: Path) -> None:
    eval_toml, _plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval",
        str(eval_toml),
        env_overrides={"EVAL_MODEL": "claude-sonnet-4-5"},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "--model claude-sonnet-4-5" in completed.stdout
    assert "suite pass_rate=100.00%" in completed.stdout
    assert_printed_command_precedes_suite_result(completed)


@with_temp_workspace
def assert_eval_case_recipe_uses_model_env_override(tmp_path: Path) -> None:
    eval_toml, _plugin_dir, fake_claude = write_eval_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval-case",
        str(eval_toml),
        "case-pass",
        env_overrides={"EVAL_MODEL": "claude-sonnet-4-5"},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "--model claude-sonnet-4-5" in completed.stdout
    assert "--case-id case-pass" in completed.stdout
    assert "suite pass_rate=100.00%" in completed.stdout
    assert_printed_command_precedes_suite_result(completed)


@with_temp_workspace
def assert_eval_node_recipe_runs_all_node_evals_serially(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    node_dir = tmp_path / "node"
    alpha_eval_toml = write_eval_suite(
        node_dir,
        plugin_dir,
        suite_name="alpha",
        case_id="case-alpha",
    )
    beta_eval_toml = write_eval_suite(
        node_dir,
        plugin_dir,
        suite_name="beta",
        case_id="case-beta",
    )
    fake_claude = write_fake_claude(tmp_path)
    eval_tomls = (alpha_eval_toml, beta_eval_toml)

    completed = run_just_eval(
        tmp_path,
        fake_claude,
        "eval-node",
        str(node_dir),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "uv run outcomeeng-evals run" in completed.stdout
    assert completed.stdout.count("suite pass_rate=100.00%") == len(eval_tomls)
    assert completed.stdout.index(str(alpha_eval_toml)) < completed.stdout.index(
        str(beta_eval_toml)
    )
    assert_printed_command_precedes_suite_result(completed)


@with_temp_workspace
def assert_eval_materialize_prompts_recipe_writes_producer_prompt(
    tmp_path: Path,
) -> None:
    eval_root, prompt_path = write_producer_prompt_fixture(tmp_path)

    completed = run_just_eval(
        tmp_path,
        write_fake_claude(tmp_path),
        "eval-materialize-prompts",
        str(eval_root),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"materialized: {prompt_path.resolve()}" in completed.stdout
    assert "pr_wait_and_reentry_policy" in prompt_path.read_text(encoding="utf-8")


@with_temp_workspace
def assert_eval_materialize_prompts_check_recipe_accepts_current_prompt(
    tmp_path: Path,
) -> None:
    eval_root, prompt_path = write_producer_prompt_fixture(tmp_path)
    run_just_eval(
        tmp_path,
        write_fake_claude(tmp_path),
        "eval-materialize-prompts",
        str(eval_root),
    )

    completed = run_just_eval(
        tmp_path,
        write_fake_claude(tmp_path),
        "eval-materialize-prompts-check",
        str(eval_root),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert f"checked: {prompt_path.resolve()}" in completed.stdout


def run_just_eval(
    tmp_path: Path,
    fake_claude: Path,
    *args: str,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLAUDE_BIN"] = str(fake_claude)
    env["XDG_CACHE_HOME"] = str(tmp_path / "xdg-cache")
    if env_overrides is not None:
        env.update(env_overrides)
    return subprocess.run(
        ["just", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


def assert_printed_command_precedes_suite_result(
    completed: subprocess.CompletedProcess[str],
) -> None:
    assert completed.stdout.index("Running:") < completed.stdout.index(
        "suite pass_rate=100.00%"
    )


def write_eval_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    eval_toml = write_eval_suite(
        tmp_path / "node",
        plugin_dir,
        suite_name="recipe",
        case_id="case-pass",
    )
    fake_claude = write_fake_claude(tmp_path)
    return eval_toml, plugin_dir, fake_claude


def write_eval_suite(
    node_dir: Path,
    plugin_dir: Path,
    *,
    suite_name: str,
    case_id: str,
) -> Path:
    eval_dir = node_dir / "evals" / suite_name
    eval_dir.mkdir(parents=True)
    eval_toml = eval_dir / "eval.toml"
    eval_toml.write_text(
        "\n".join(
            [
                f'title = "{suite_name}-smoke"',
                'cases = "cases.jsonl"',
                'prompt = "prompt.md"',
                f'plugin_dir = "{plugin_dir.as_posix()}"',
                "threshold = 1.0",
                "trials = 1",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (eval_dir / "prompt.md").write_text(
        "Case {case_id}\n\n{input_json}\n",
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text(
        json.dumps(
            {
                "id": case_id,
                "input": {"subject": suite_name},
                "expected_verdict": {
                    "must_contain": [{"overall": "PASS"}],
                    "must_not_contain": [{"overall": "FAIL"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return eval_toml


def write_producer_prompt_fixture(tmp_path: Path) -> tuple[Path, Path]:
    eval_root = tmp_path / "node"
    eval_dir = eval_root / "evals" / "producer"
    eval_dir.mkdir(parents=True)
    prompt_path = eval_dir / "prompt.md"
    (eval_dir / "prompt.template.md").write_text(
        f"Producer: {PRODUCER_PATH_PLACEHOLDER}\n"
        f"Section: {PRODUCER_SECTION_NAME_PLACEHOLDER}\n"
        f"{PRODUCER_SECTION_PLACEHOLDER}\n",
        encoding="utf-8",
    )
    (eval_dir / "eval.toml").write_text(
        "\n".join(
            [
                'title = "producer"',
                'cases = "cases.jsonl"',
                'prompt = "prompt.md"',
                "",
                "[prompt_source]",
                'kind = "producer-section"',
                'producer = "src/plugins/spec-tree/skills/manage-pr/SKILL.md"',
                'section = "pr_wait_and_reentry_policy"',
                'template = "prompt.template.md"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    return eval_root, prompt_path


def write_fake_claude(tmp_path: Path) -> Path:
    fake_claude = tmp_path / "fake-claude"
    fake_claude.write_text(
        """#!/usr/bin/env python3
import json
import sys

sys.stdin.read()
print(json.dumps({
    "result": json.dumps({"schema_version": 1, "overall": "PASS"}),
    "duration_ms": 1,
    "total_cost_usd": 0,
    "usage": {
        "input_tokens": 1,
        "output_tokens": 1,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    },
    "num_turns": 1,
    "stop_reason": "end_turn",
}))
""",
        encoding="utf-8",
    )
    fake_claude.chmod(fake_claude.stat().st_mode | stat.S_IXUSR)
    return fake_claude
