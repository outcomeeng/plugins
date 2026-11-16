"""Marketplace-owned fixtures for repository-local eval Just recipe tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from outcomeeng_testing.harnesses.eval_workspaces import temporary_workspace

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCER_FIXTURE_SECTION = "pr_wait_and_reentry_policy"
RECIPE_COMMAND_BANNER = "Running:"
SUITE_PASS_LINE = "suite pass_rate=100.00%"


@dataclass(frozen=True)
class CheckRecipeObservation:
    """Observed outcome of the drift-check recipe over a materialized prompt."""

    completed: subprocess.CompletedProcess[str]
    prompt_path: Path


@dataclass(frozen=True)
class MaterializePromptsObservation:
    """Observed outcome of the materialize-prompts recipe over a producer fixture."""

    completed: subprocess.CompletedProcess[str]
    prompt_path: Path
    prompt_text: str


def observe_eval_materialize_prompts_recipe() -> MaterializePromptsObservation:
    """Run the materialize-prompts recipe over a producer-section fixture."""

    with temporary_workspace(REPO_ROOT) as tmp_path:
        eval_root, prompt_path = write_producer_prompt_fixture(tmp_path)

        completed = run_just_eval(
            tmp_path,
            write_fake_claude(tmp_path),
            "eval-materialize-prompts",
            str(eval_root),
        )

        return MaterializePromptsObservation(
            completed=completed,
            prompt_path=prompt_path,
            prompt_text=prompt_path.read_text(encoding="utf-8"),
        )


def materialize_prompts_then_check() -> CheckRecipeObservation:
    """Materialize a producer prompt, then run the drift-check recipe over it."""

    with temporary_workspace(REPO_ROOT) as tmp_path:
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

        return CheckRecipeObservation(completed=completed, prompt_path=prompt_path)


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
    producer_path = eval_root / "producer" / "SKILL.md"
    producer_path.parent.mkdir()
    producer_path.write_text(
        f'<step name="{PRODUCER_FIXTURE_SECTION}">\nWait for the checks.\n</step>\n',
        encoding="utf-8",
    )
    producer_repo_path = producer_path.relative_to(REPO_ROOT).as_posix()
    prompt_path = eval_dir / "prompt.md"
    (eval_dir / "prompt.template.md").write_text(
        "Producer: {producer_path}\nSection: {producer_section_name}\n{producer_section}\n",
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
                f'producer = "{producer_repo_path}"',
                f'section = "{PRODUCER_FIXTURE_SECTION}"',
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
