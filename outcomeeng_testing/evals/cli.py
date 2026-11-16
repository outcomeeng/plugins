"""Test infrastructure for exercising the eval Click CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Final

import click
from click.testing import CliRunner, Result

from outcomeeng_evals.cli import (
    main,
)
from outcomeeng_evals.cli.commands.run import (
    RUNNER_FACTORY_KEY,
    _history_row,
    _runner_factory_from_context,
)
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.history import (
    HISTORY_MAX_BUDGET_USD_FIELD,
    HISTORY_MODEL_FIELD,
    HISTORY_TIMEOUT_SECONDS_FIELD,
    HISTORY_TIMESTAMP_FIELD,
    HISTORY_TRANSCRIPT_FIELD,
)
from outcomeeng_evals.runner import ModelRunner
from outcomeeng_testing.evals.factories import (
    load_history_rows_fixture,
    make_eval_dir,
    make_suite_result,
)
from outcomeeng_testing.evals.fakes import RecordingRunner, StubModelRunner
from outcomeeng_testing.harnesses.eval_setup import EvalHarnessSetupError

PLAN_PLUGIN_DIR: Final = "dist/claude/product-tree"
PLAN_OWNED_PATH_PATTERN: Final = "src/plugins/product-tree/skills/manage-pr/**"
PLAN_SMOKE_CASE_ID: Final = "happy-path"
PLAN_OWNED_PATH_CHANGE: Final = "src/plugins/product-tree/skills/manage-pr/SKILL.md\n"
PLAN_RENAMED_OWNED_PATH_CHANGE: Final = (
    "R100\tsrc/plugins/product-tree/skills/manage-pr/SKILL.md\tdocs/manage-pr.md\n"
)
PLAN_HARNESS_PATH_CHANGE: Final = "outcomeeng_evals/suite.py\n"
PLAN_TEST_GENERATOR_PATH_CHANGE: Final = "outcomeeng_testing/generators/gate.py\n"
PLAN_TEST_HARNESS_PATH_CHANGE: Final = "outcomeeng_testing/harnesses/gate.py\n"
PLAN_COPIED_HARNESS_PATH_CHANGE: Final = (
    "C100\toutcomeeng_evals/suite.py\tdocs/copied-suite.py\n"
)
PLAN_OWNED_AND_HARNESS_PATH_CHANGE: Final = (
    f"{PLAN_OWNED_PATH_CHANGE}{PLAN_HARNESS_PATH_CHANGE}"
)
PLAN_UNRELATED_PATH_CHANGE: Final = "README.md\n"
PLAN_RELATIVE_EVAL_ROOT: Final = "spx"
PLAN_MANUAL_CASE_ID: Final = "manual-smoke"
RUN_CASE_ALPHA: Final = (
    '{"id":"alpha","input":{"x":1},"expected_verdict":{"must_contain":[{"ok":true}]}}'
)
RUN_CASE_BETA: Final = (
    '{"id":"beta","input":{"x":2},"expected_verdict":{"must_contain":[{"ok":true}]}}'
)
RUN_CASE_GAMMA: Final = (
    '{"id":"gamma","input":{"x":3},"expected_verdict":{"must_contain":[{"ok":true}]}}'
)
RUN_DEFAULT_MODEL: Final = "claude-sonnet-4-5"
RUN_OVERRIDE_MODEL: Final = "sonnet"
HISTORY_VERSION_1_COMPATIBILITY_FIXTURE: Final = (
    Path(__file__).parents[2]
    / "outcomeeng_testing/fixtures/evals/history_version_1_compatibility.jsonl"
)
HISTORY_ROWS_FIXTURE: Final = (
    Path(__file__).parents[2] / "outcomeeng_testing/fixtures/evals/history_rows.json"
)


@dataclass(frozen=True)
class RunCliHarness:
    """Temporary run-command fixture with an injectable recording runner."""

    eval_toml: Path
    plugin_dir: Path
    runner: CliRunner
    recorder: RecordingRunner
    models: list[str] = field(default_factory=list)
    max_budgets_usd: list[float] = field(default_factory=list)
    timeouts_seconds: list[int] = field(default_factory=list)

    @property
    def runner_context(self) -> dict[str, object]:
        def runner_factory(
            *,
            plugin_dir: Path,
            model: str,
            max_budget_usd: float,
            timeout_seconds: int,
        ) -> ModelRunner:
            del plugin_dir
            self.models.append(model)
            self.max_budgets_usd.append(max_budget_usd)
            self.timeouts_seconds.append(timeout_seconds)
            return self.recorder

        return {RUNNER_FACTORY_KEY: runner_factory}


def build_run_cli_harness(
    tmp_path: Path,
    *,
    cases_jsonl: str,
    prompt_template: str = "Case {case_id}: {input_json}",
    model: str | None = None,
) -> RunCliHarness:
    """Create a temporary eval suite wired to a recording model runner."""
    eval_dir = tmp_path / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    model_line = f'model = "{model}"\n' if model is not None else ""
    (eval_dir / EVAL_TOML_FILENAME).write_text(
        f'title = "rule"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n{model_line}',
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text(cases_jsonl, encoding="utf-8")
    (eval_dir / "prompt.md").write_text(prompt_template, encoding="utf-8")
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    recorder = RecordingRunner(inner=StubModelRunner(response='{"ok": true}'))
    return RunCliHarness(
        eval_toml=eval_dir / EVAL_TOML_FILENAME,
        plugin_dir=plugin_dir,
        runner=CliRunner(),
        recorder=recorder,
    )


def invoke_main_help() -> Result:
    """Invoke the CLI group's help and return the observed result."""

    return CliRunner().invoke(main, ["--help"])


def run_argv(harness: RunCliHarness, *extra_args: str) -> list[str]:
    """Build the run-command argv for a harness, plus extra arguments."""

    return [
        "run",
        str(harness.eval_toml),
        "--plugin-dir",
        str(harness.plugin_dir),
        *extra_args,
    ]


def invoke_run_with_workers(tmp_path: Path, workers: int) -> Result:
    """Invoke the run subcommand with an explicit ``--workers`` value."""

    eval_toml = tmp_path / EVAL_TOML_FILENAME
    eval_toml.write_text("", encoding="utf-8")
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    return CliRunner().invoke(
        main,
        [
            "run",
            str(eval_toml),
            "--plugin-dir",
            str(plugin_dir),
            "--workers",
            str(workers),
        ],
    )


def write_discoverable_eval(root: Path) -> Path:
    """Write one complete eval definition beneath ``root`` and return its path."""

    nested_eval = root / "subtree" / "evals" / "rule-one" / EVAL_TOML_FILENAME
    nested_eval.parent.mkdir(parents=True)
    nested_eval.write_text(
        'title = "rule-one"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
        encoding="utf-8",
    )
    (nested_eval.parent / "cases.jsonl").write_text("", encoding="utf-8")
    (nested_eval.parent / "prompt.md").write_text("", encoding="utf-8")
    return nested_eval


@dataclass(frozen=True)
class HistoryObservation:
    """The history subcommand's output over the version-1 compatibility fixture."""

    result: Result
    rows: tuple[dict[str, object], ...]


def observe_history_over_version_1_rows(tmp_path: Path) -> HistoryObservation:
    """Run ``history`` over the captured version-1 rows."""

    eval_dir = tmp_path / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    history_path = eval_dir / "history.jsonl"
    history_path.write_bytes(HISTORY_VERSION_1_COMPATIBILITY_FIXTURE.read_bytes())

    result = CliRunner().invoke(main, ["history", str(history_path)])

    with HISTORY_VERSION_1_COMPATIBILITY_FIXTURE.open(encoding="utf-8") as fixture_file:
        rows = tuple(json.loads(line) for line in fixture_file if line.strip())
    return HistoryObservation(result=result, rows=rows)


def current_history_row() -> tuple[dict[str, object], dict[str, object]]:
    """Return a captured source row and the row the run command writes today."""

    source_row = load_history_rows_fixture(HISTORY_ROWS_FIXTURE)[0]
    current_row = _history_row(
        timestamp=source_row[HISTORY_TIMESTAMP_FIELD],
        result=make_suite_result(),
        model=source_row[HISTORY_MODEL_FIELD],
        max_budget_usd=source_row[HISTORY_MAX_BUDGET_USD_FIELD],
        timeout_seconds=source_row[HISTORY_TIMEOUT_SECONDS_FIELD],
        transcript_relative=source_row[HISTORY_TRANSCRIPT_FIELD],
    )
    return dict(source_row), dict(current_row)


def default_runner_factory() -> object:
    """Return the runner factory the run command resolves without injected context."""

    with click.Context(main):
        return _runner_factory_from_context()


@dataclass(frozen=True)
class PlanObservation:
    """Observed plan output over one eval definition."""

    exit_code: int
    plan: list[dict[str, object]]
    eval_toml: Path


def _parse_plan(output: str) -> list[dict[str, object]]:
    parsed: object = json.loads(output)
    if not isinstance(parsed, list):
        raise EvalHarnessSetupError("plan output is not a JSON array")
    return parsed


def _plan_eval_dir(root: Path) -> Path:
    return make_eval_dir(
        root / "evals" / "rule",
        title="rule",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=(PLAN_OWNED_PATH_PATTERN,),
        smoke_case_ids=(PLAN_SMOKE_CASE_ID,),
    )


def _plan_pr(scan_root: Path, changed_paths: Path, eval_toml: Path) -> PlanObservation:
    result = CliRunner().invoke(
        main,
        [
            "plan",
            str(scan_root),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )
    return PlanObservation(
        exit_code=result.exit_code,
        plan=_parse_plan(result.output),
        eval_toml=eval_toml,
    )


def observe_pr_plan(tmp_path: Path, changed_paths_text: str) -> PlanObservation:
    """Plan a PR whose changed-paths file holds ``changed_paths_text``."""

    eval_toml = _plan_eval_dir(tmp_path)
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text(changed_paths_text, encoding="utf-8")
    return _plan_pr(tmp_path, changed_paths, eval_toml)


def observe_pr_plan_for_absolute_eval_artifact(tmp_path: Path) -> PlanObservation:
    """Plan a PR changing an eval artifact named by its absolute path."""

    eval_toml = _plan_eval_dir(tmp_path)
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text(f"{eval_toml.parent / 'cases.jsonl'}\n", encoding="utf-8")
    return _plan_pr(tmp_path, changed_paths, eval_toml)


def observe_pr_plan_for_relative_eval_artifact(tmp_path: Path) -> PlanObservation:
    """Plan a PR changing an eval artifact named by a path relative to the cwd."""

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        eval_root = Path(PLAN_RELATIVE_EVAL_ROOT)
        eval_toml = _plan_eval_dir(eval_root)
        changed_paths = Path("changed.txt")
        changed_paths.write_text(
            f"{eval_toml.parent.as_posix()}/cases.jsonl\n",
            encoding="utf-8",
        )
        return _plan_pr(eval_root, changed_paths, eval_toml)
    finally:
        os.chdir(original_cwd)


def observe_plan_full_mode_with_manual_eval(tmp_path: Path) -> PlanObservation:
    """Run full-mode planning over an automatic and a manual eval definition."""

    automatic_eval = make_eval_dir(
        tmp_path / "evals" / "automatic",
        title="automatic",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=(PLAN_OWNED_PATH_PATTERN,),
        smoke_case_ids=(PLAN_SMOKE_CASE_ID,),
    )
    make_eval_dir(
        tmp_path / "evals" / "manual",
        title="manual",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=("src/plugins/product-tree/skills/review-changes/**",),
        smoke_case_ids=(PLAN_MANUAL_CASE_ID,),
        ci_policy="manual",
    )

    result = CliRunner().invoke(main, ["plan", str(tmp_path), "--mode", "full"])

    return PlanObservation(
        exit_code=result.exit_code,
        plan=_parse_plan(result.output),
        eval_toml=automatic_eval,
    )
