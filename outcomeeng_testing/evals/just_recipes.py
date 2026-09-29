"""Marketplace-owned infrastructure for repository-local eval Just recipe tests.

Each runner builds a temporary eval suite, runs one real Just recipe against a
fake ``claude`` binary, and returns the completed process with the observations
the linked tests judge; the tests own every predicate.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.models import EVAL_PROFILE_MODELS, AgentProfile
from outcomeeng_evals.case import (
    CASE_ID_FIELD,
    CASE_INPUT_FIELD,
    EXPECTED_VERDICT_FIELD,
    MUST_CONTAIN_FIELD,
    MUST_NOT_CONTAIN_FIELD,
)
from outcomeeng_evals.definition import (
    CASES_FIELD,
    DEFAULT_PROFILE,
    EVAL_TOML_FILENAME,
    PLUGIN_DIR_FIELD,
    PROFILE_FIELD,
    PROMPT_FIELD,
    THRESHOLD_FIELD,
    TITLE_FIELD,
    TRIALS_FIELD,
)
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    PRODUCER_FIELD,
    PRODUCER_PATH_PLACEHOLDER,
    PRODUCER_SECTION_KIND,
    PRODUCER_SECTION_NAME_PLACEHOLDER,
    PRODUCER_SECTION_PLACEHOLDER,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
)
from outcomeeng_evals.runner import (
    ENVELOPE_DURATION_MS_KEY,
    ENVELOPE_NUM_TURNS_KEY,
    ENVELOPE_RESULT_KEY,
    ENVELOPE_STOP_REASON_KEY,
    ENVELOPE_TOTAL_COST_USD_KEY,
    ENVELOPE_USAGE_KEY,
    USAGE_CACHE_CREATION_INPUT_TOKENS_KEY,
    USAGE_CACHE_READ_INPUT_TOKENS_KEY,
    USAGE_INPUT_TOKENS_KEY,
    USAGE_OUTPUT_TOKENS_KEY,
)
from outcomeeng_testing.harnesses.eval_workspaces import temporary_workspace

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
EVAL_RECIPE: Final = "eval"
EVAL_CASE_RECIPE: Final = "eval-case"
EVAL_NODE_RECIPE: Final = "eval-node"
MATERIALIZE_PROMPTS_RECIPE: Final = "eval-materialize-prompts"
MATERIALIZE_PROMPTS_CHECK_RECIPE: Final = "eval-materialize-prompts-check"
RUNNING_LINE_PREFIX: Final = "Running:"
EVAL_PROFILE_ENV: Final = "EVAL_PROFILE"
PLUGIN_DIR_ENV: Final = "PLUGIN_DIR"
RECIPE_CASE_ID: Final = "case-pass"
NODE_SUITE_NAMES: Final = ("alpha", "beta")
PRODUCER_SECTION_NAME: Final = "pr_wait_and_reentry_policy"
_PRODUCER_PATH: Final = "src/plugins/spec-tree/skills/manage-pr/SKILL.md"
_RECIPE_TIMEOUT_SECONDS: Final = 90
_PASSING_VERDICT: Final = {"overall": "PASS"}
_FAILING_VERDICT: Final = {"overall": "FAIL"}

DEFINITION_PROFILE: Final = next(
    profile for profile in AgentProfile if profile is not DEFAULT_PROFILE
)
OVERRIDE_PROFILE: Final = next(
    profile
    for profile in AgentProfile
    if profile not in (DEFAULT_PROFILE, DEFINITION_PROFILE)
)
# A model identity is not a profile: the recipes must refuse it as a profile.
UNSUPPORTED_PROFILE: Final = str(EVAL_PROFILE_MODELS[DEFAULT_PROFILE].model)


@dataclass(frozen=True)
class EvalRecipeRun:
    """A completed ``eval`` or ``eval-case`` recipe run and its arrangement."""

    completed: subprocess.CompletedProcess[str]
    eval_toml: Path
    plugin_dir: Path
    override_plugin_dir: Path | None
    case_id: str | None
    running_lines: tuple[str, ...]


@dataclass(frozen=True)
class EvalNodeRecipeRun:
    """A completed ``eval-node`` recipe run over a node with several suites."""

    completed: subprocess.CompletedProcess[str]
    eval_tomls: tuple[Path, ...]


@dataclass(frozen=True)
class MaterializePromptsRecipeRun:
    """A completed prompt-materialization recipe run and the prompt it governs."""

    completed: subprocess.CompletedProcess[str]
    prompt_path: Path
    prompt_text: str


def run_eval_recipe(
    *,
    select_case: bool = False,
    definition_profile: AgentProfile | None = None,
    profile_override: str | None = None,
    override_plugin_dir: bool = False,
) -> EvalRecipeRun:
    """Run ``eval`` (or ``eval-case`` for one case) over a one-case suite.

    ``definition_profile`` is written into the suite's ``eval.toml``;
    ``profile_override`` and ``override_plugin_dir`` set the recipe's profile
    and plugin-directory environment overrides.
    """

    with temporary_workspace() as workspace:
        plugin_dir = workspace / "plugin"
        plugin_dir.mkdir()
        eval_toml = write_eval_suite(
            workspace / "node",
            plugin_dir,
            suite_name="recipe",
            case_id=RECIPE_CASE_ID,
            profile=definition_profile,
        )
        env_overrides: dict[str, str] = {}
        override_dir: Path | None = None
        if override_plugin_dir:
            override_dir = workspace / "override-plugin"
            override_dir.mkdir()
            env_overrides[PLUGIN_DIR_ENV] = str(override_dir)
        if profile_override is not None:
            env_overrides[EVAL_PROFILE_ENV] = profile_override
        recipe_args = (
            (EVAL_CASE_RECIPE, str(eval_toml), RECIPE_CASE_ID)
            if select_case
            else (EVAL_RECIPE, str(eval_toml))
        )
        completed = _run_just(
            workspace,
            write_fake_claude(workspace),
            *recipe_args,
            env_overrides=env_overrides,
        )
        return EvalRecipeRun(
            completed=completed,
            eval_toml=eval_toml,
            plugin_dir=plugin_dir,
            override_plugin_dir=override_dir,
            case_id=RECIPE_CASE_ID if select_case else None,
            running_lines=tuple(
                line
                for line in completed.stdout.splitlines()
                if line.startswith(RUNNING_LINE_PREFIX)
            ),
        )


def run_eval_node_recipe() -> EvalNodeRecipeRun:
    """Run ``eval-node`` over a node carrying one suite per ``NODE_SUITE_NAMES``."""

    with temporary_workspace() as workspace:
        plugin_dir = workspace / "plugin"
        plugin_dir.mkdir()
        node_dir = workspace / "node"
        eval_tomls = tuple(
            write_eval_suite(
                node_dir,
                plugin_dir,
                suite_name=suite_name,
                case_id=f"case-{suite_name}",
            )
            for suite_name in NODE_SUITE_NAMES
        )
        completed = _run_just(
            workspace,
            write_fake_claude(workspace),
            EVAL_NODE_RECIPE,
            str(node_dir),
        )
        return EvalNodeRecipeRun(completed=completed, eval_tomls=eval_tomls)


def run_materialize_prompts_recipe(*, check: bool) -> MaterializePromptsRecipeRun:
    """Run prompt materialization, then with ``check`` the drift check, in-repo."""

    with temporary_workspace(REPO_ROOT) as workspace:
        eval_root, prompt_path = write_producer_prompt_fixture(workspace)
        fake_claude = write_fake_claude(workspace)
        completed = _run_just(
            workspace, fake_claude, MATERIALIZE_PROMPTS_RECIPE, str(eval_root)
        )
        if check:
            completed = _run_just(
                workspace,
                fake_claude,
                MATERIALIZE_PROMPTS_CHECK_RECIPE,
                str(eval_root),
            )
        return MaterializePromptsRecipeRun(
            completed=completed,
            prompt_path=prompt_path.resolve(),
            prompt_text=(
                prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
            ),
        )


def _run_just(
    workspace: Path,
    fake_claude: Path,
    *args: str,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLAUDE_BIN"] = str(fake_claude)
    env["XDG_CACHE_HOME"] = str(workspace / "xdg-cache")
    env.pop(EVAL_PROFILE_ENV, None)
    env.pop(PLUGIN_DIR_ENV, None)
    if env_overrides is not None:
        env.update(env_overrides)
    return subprocess.run(
        ["just", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=_RECIPE_TIMEOUT_SECONDS,
    )


def write_eval_suite(
    node_dir: Path,
    plugin_dir: Path,
    *,
    suite_name: str,
    case_id: str,
    profile: AgentProfile | None = None,
) -> Path:
    eval_dir = node_dir / "evals" / suite_name
    eval_dir.mkdir(parents=True)
    eval_toml = eval_dir / EVAL_TOML_FILENAME
    profile_lines = [f'{PROFILE_FIELD} = "{profile}"'] if profile is not None else []
    eval_toml.write_text(
        "\n".join(
            [
                f'{TITLE_FIELD} = "{suite_name}-smoke"',
                f'{CASES_FIELD} = "cases.jsonl"',
                f'{PROMPT_FIELD} = "prompt.md"',
                f'{PLUGIN_DIR_FIELD} = "{plugin_dir.as_posix()}"',
                *profile_lines,
                f"{THRESHOLD_FIELD} = 1.0",
                f"{TRIALS_FIELD} = 1",
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
                CASE_ID_FIELD: case_id,
                CASE_INPUT_FIELD: {"subject": suite_name},
                EXPECTED_VERDICT_FIELD: {
                    MUST_CONTAIN_FIELD: [_PASSING_VERDICT],
                    MUST_NOT_CONTAIN_FIELD: [_FAILING_VERDICT],
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
    template_name = "prompt.template.md"
    (eval_dir / template_name).write_text(
        f"Producer: {PRODUCER_PATH_PLACEHOLDER}\n"
        f"Section: {PRODUCER_SECTION_NAME_PLACEHOLDER}\n"
        f"{PRODUCER_SECTION_PLACEHOLDER}\n",
        encoding="utf-8",
    )
    (eval_dir / EVAL_TOML_FILENAME).write_text(
        "\n".join(
            [
                f'{TITLE_FIELD} = "producer"',
                f'{CASES_FIELD} = "cases.jsonl"',
                f'{PROMPT_FIELD} = "prompt.md"',
                "",
                f"[{PROMPT_SOURCE_TABLE}]",
                f'{KIND_FIELD} = "{PRODUCER_SECTION_KIND}"',
                f'{PRODUCER_FIELD} = "{_PRODUCER_PATH}"',
                f'{SECTION_FIELD} = "{PRODUCER_SECTION_NAME}"',
                f'{TEMPLATE_FIELD} = "{template_name}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    return eval_root, prompt_path


def write_fake_claude(tmp_path: Path) -> Path:
    """Write a ``claude`` stand-in that answers every prompt with a passing verdict."""

    envelope = {
        ENVELOPE_RESULT_KEY: json.dumps({"schema_version": 1, **_PASSING_VERDICT}),
        ENVELOPE_DURATION_MS_KEY: 1,
        ENVELOPE_TOTAL_COST_USD_KEY: 0,
        ENVELOPE_USAGE_KEY: {
            USAGE_INPUT_TOKENS_KEY: 1,
            USAGE_OUTPUT_TOKENS_KEY: 1,
            USAGE_CACHE_READ_INPUT_TOKENS_KEY: 0,
            USAGE_CACHE_CREATION_INPUT_TOKENS_KEY: 0,
        },
        ENVELOPE_NUM_TURNS_KEY: 1,
        ENVELOPE_STOP_REASON_KEY: "end_turn",
    }
    fake_claude = tmp_path / "fake-claude"
    fake_claude.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "\n"
        "sys.stdin.read()\n"
        f"print({json.dumps(json.dumps(envelope))})\n",
        encoding="utf-8",
    )
    fake_claude.chmod(fake_claude.stat().st_mode | stat.S_IXUSR)
    return fake_claude
