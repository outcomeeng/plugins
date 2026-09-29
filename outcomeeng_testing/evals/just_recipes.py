"""Marketplace-owned infrastructure for repository-local eval Just recipe tests.

Each runner builds a temporary eval suite, runs one real Just recipe against a
fake ``claude`` binary, and returns the completed process with the observations
the linked tests judge; the tests own every predicate.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.models import EVAL_PROFILE_MODELS, AgentProfile
from outcomeeng_evals.case import (
    CASE_ID_FIELD,
    CASE_INPUT_FIELD,
    EXPECTED_VERDICT_FIELD,
    MUST_CONTAIN_FIELD,
)
from outcomeeng_evals.cli.commands.run import (
    CASE_ID_PLACEHOLDER,
    INPUT_JSON_PLACEHOLDER,
)
from outcomeeng_evals.cli.wiring import CLAUDE_BIN_ENV
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
from outcomeeng_evals.producer_prompt import PROMPT_SOURCE_TABLE, SECTION_FIELD
from outcomeeng_evals.recipes import (
    EVAL_CASE_RECIPE,
    EVAL_NODE_RECIPE,
    EVAL_PROFILE_ENV,
    EVAL_RECIPE,
    MATERIALIZE_PROMPTS_CHECK_RECIPE,
    MATERIALIZE_PROMPTS_RECIPE,
    PLUGIN_DIR_ENV,
    RUNNING_LINE_PREFIX,
)
from outcomeeng_evals.runner import ENVELOPE_RESULT_KEY
from outcomeeng_testing.harnesses.eval_runner import captured_process_fixture
from outcomeeng_testing.harnesses.eval_workspaces import temporary_workspace

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
RECIPE_CASE_ID: Final = "case-pass"
NODE_SUITE_NAMES: Final = ("alpha", "beta")
# A whole producer-section eval definition, its template, and the producer it
# names by repository-relative path.
_PRODUCER_SECTION_FIXTURE: Final = (
    Path(__file__).parents[1] / "fixtures/evals/producer_section_recipe"
)
_RECIPE_TIMEOUT_SECONDS: Final = 90
# The verdict every recipe case expects and the fake ``claude`` answers with.
_VERDICT_FIXTURE: Final = (
    Path(__file__).parents[1] / "fixtures/evals/verdict_approved.json"
)

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
    section_name: str


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
        eval_root, prompt_path, section_name = copy_producer_prompt_fixture(workspace)
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
            section_name=section_name,
        )


def _run_just(
    workspace: Path,
    fake_claude: Path,
    *args: str,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env[CLAUDE_BIN_ENV] = str(fake_claude)
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
        f"Case {CASE_ID_PLACEHOLDER}\n\n{INPUT_JSON_PLACEHOLDER}\n",
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text(
        json.dumps(
            {
                CASE_ID_FIELD: case_id,
                CASE_INPUT_FIELD: {"subject": suite_name},
                EXPECTED_VERDICT_FIELD: {
                    MUST_CONTAIN_FIELD: [
                        json.loads(_VERDICT_FIXTURE.read_text(encoding="utf-8"))
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return eval_toml


def copy_producer_prompt_fixture(tmp_path: Path) -> tuple[Path, Path, str]:
    """Copy the producer-section eval fixture under ``tmp_path``.

    Returns the eval root to materialize, the prompt path the copied definition
    declares, and the section name that definition selects.
    """

    eval_root = tmp_path / "node"
    eval_dir = eval_root / "evals" / _PRODUCER_SECTION_FIXTURE.name
    shutil.copytree(_PRODUCER_SECTION_FIXTURE, eval_dir)
    definition = tomllib.loads(
        (eval_dir / EVAL_TOML_FILENAME).read_text(encoding="utf-8")
    )
    return (
        eval_root,
        eval_dir / definition[PROMPT_FIELD],
        definition[PROMPT_SOURCE_TABLE][SECTION_FIELD],
    )


def write_fake_claude(tmp_path: Path) -> Path:
    """Write a ``claude`` stand-in that answers every prompt with the verdict fixture.

    The answer is the captured ``claude`` envelope with its result replaced by
    the verdict every recipe case expects.
    """

    envelope = {
        **captured_process_fixture().envelope,
        ENVELOPE_RESULT_KEY: _VERDICT_FIXTURE.read_text(encoding="utf-8"),
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
