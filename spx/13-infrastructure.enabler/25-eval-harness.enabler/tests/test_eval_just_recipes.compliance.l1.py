"""Compliance tests for the repository-local eval Just recipes."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def test_eval_recipe_runs_suite_with_toml_plugin_dir(
    tmp_path: Path,
) -> None:
    eval_toml, plugin_dir, fake_claude = _write_eval_fixture(tmp_path)

    completed = _run_just_eval(
        tmp_path,
        fake_claude,
        "eval",
        str(eval_toml),
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "uv run outcomeeng-evals run" in completed.stdout
    assert f"--plugin-dir {plugin_dir}" in completed.stdout
    assert "--workers 1" in completed.stdout
    assert "--max-budget-usd 0.50" in completed.stdout
    assert "--model sonnet" in completed.stdout
    assert "--timeout-seconds 120" in completed.stdout
    assert "--case-id" not in completed.stdout
    assert "suite pass_rate=100.00%" in completed.stdout


def test_eval_case_recipe_runs_selected_case_with_toml_plugin_dir(
    tmp_path: Path,
) -> None:
    eval_toml, plugin_dir, fake_claude = _write_eval_fixture(tmp_path)

    completed = _run_just_eval(
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
    assert "--max-budget-usd 0.50" in completed.stdout
    assert "--model sonnet" in completed.stdout
    assert "--timeout-seconds 120" in completed.stdout
    assert "--case-id case-pass" in completed.stdout
    assert "suite pass_rate=100.00%" in completed.stdout


def test_eval_recipe_uses_plugin_dir_env_override(
    tmp_path: Path,
) -> None:
    eval_toml, plugin_dir, fake_claude = _write_eval_fixture(tmp_path)
    override_plugin_dir = tmp_path / "override-plugin"
    override_plugin_dir.mkdir()

    completed = _run_just_eval(
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


def test_eval_recipe_uses_model_env_override(
    tmp_path: Path,
) -> None:
    eval_toml, _plugin_dir, fake_claude = _write_eval_fixture(tmp_path)

    completed = _run_just_eval(
        tmp_path,
        fake_claude,
        "eval",
        str(eval_toml),
        env_overrides={"EVAL_MODEL": "claude-sonnet-4-5"},
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "--model claude-sonnet-4-5" in completed.stdout
    assert "suite pass_rate=100.00%" in completed.stdout


def test_eval_node_recipe_runs_all_node_evals_serially(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    node_dir = tmp_path / "node"
    alpha_eval_toml = _write_eval_suite(
        node_dir,
        plugin_dir,
        suite_name="alpha",
        case_id="case-alpha",
    )
    beta_eval_toml = _write_eval_suite(
        node_dir,
        plugin_dir,
        suite_name="beta",
        case_id="case-beta",
    )
    fake_claude = _write_fake_claude(tmp_path)
    eval_tomls = (alpha_eval_toml, beta_eval_toml)

    completed = _run_just_eval(
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


def _run_just_eval(
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


def _write_eval_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    eval_toml = _write_eval_suite(
        tmp_path / "node",
        plugin_dir,
        suite_name="recipe",
        case_id="case-pass",
    )
    fake_claude = _write_fake_claude(tmp_path)
    return eval_toml, plugin_dir, fake_claude


def _write_eval_suite(
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


def _write_fake_claude(tmp_path: Path) -> Path:
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
