"""Test infrastructure for exercising the eval Click CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

import click
from click.testing import CliRunner

from outcomeeng_evals.cli import (
    EXIT_GENERAL_ERROR,
    EXIT_INVOCATION_ERROR,
    EXIT_SUCCESS,
    main,
)
from outcomeeng_evals.cli.commands.run import (
    MAX_WORKERS,
    MIN_WORKERS,
    RUNNER_FACTORY_KEY,
    _FORMAT_SUFFIX,
    _runner_factory_from_context,
)
from outcomeeng_evals.cli.wiring import build_claude_runner
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.runner import ModelRunner
from outcomeeng_evals.testing.factories import (
    assert_ci_subcommand_builds_plan_and_executes_with_default_ceilings as _assert_ci_subcommand_builds_plan_and_executes_with_default_ceilings,
    make_eval_dir,
)
from outcomeeng_evals.testing.fakes import RecordingRunner, StubModelRunner

PLAN_PLUGIN_DIR: Final = "dist/claude/spec-tree"
PLAN_OWNED_PATH_PATTERN: Final = "src/plugins/spec-tree/skills/manage-pr/**"
PLAN_SMOKE_CASE_ID: Final = "happy-path"
PLAN_OWNED_PATH_CHANGE: Final = "src/plugins/spec-tree/skills/manage-pr/SKILL.md\n"
PLAN_RENAMED_OWNED_PATH_CHANGE: Final = (
    "R100\tsrc/plugins/spec-tree/skills/manage-pr/SKILL.md\tdocs/manage-pr.md\n"
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


@dataclass(frozen=True)
class RunCliHarness:
    """Temporary run-command fixture with an injectable recording runner."""

    eval_toml: Path
    plugin_dir: Path
    runner: CliRunner
    recorder: RecordingRunner
    models: list[str] = field(default_factory=list)

    @property
    def runner_context(self) -> dict[str, object]:
        def runner_factory(
            *,
            plugin_dir: Path,
            model: str,
            max_budget_usd: float,
            timeout_seconds: int,
        ) -> ModelRunner:
            del plugin_dir, max_budget_usd, timeout_seconds
            self.models.append(model)
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


def assert_main_group_exposes_documented_subcommands() -> None:
    """Assert the CLI help surface lists every documented subcommand."""

    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == EXIT_SUCCESS
    for subcommand in (
        "run",
        "history",
        "view",
        "discover",
        "plan",
        "ci",
        "materialize-prompts",
        "materialize-ci-triggers",
    ):
        assert subcommand in result.output


def assert_run_subcommand_requires_eval_toml_path() -> None:
    """Assert the run subcommand requires an eval.toml path."""

    result = CliRunner().invoke(main, ["run"])

    assert result.exit_code == EXIT_INVOCATION_ERROR


def assert_run_subcommand_rejects_missing_eval_toml() -> None:
    """Assert the run subcommand rejects a missing eval.toml path."""

    with TemporaryDirectory() as tmp:
        missing_path = Path(tmp) / "does-not-exist" / EVAL_TOML_FILENAME

        result = CliRunner().invoke(main, ["run", str(missing_path)])

        assert result.exit_code != EXIT_SUCCESS


def assert_run_subcommand_rejects_workers_above_cap() -> None:
    """Assert the run subcommand rejects workers above the cap."""

    _assert_run_subcommand_rejects_worker_count(MAX_WORKERS + 1)


def assert_run_subcommand_rejects_workers_below_minimum() -> None:
    """Assert the run subcommand rejects workers below the minimum."""

    _assert_run_subcommand_rejects_worker_count(MIN_WORKERS - 1)


def assert_run_command_uses_default_runner_factory_without_injected_context() -> None:
    """Assert the run command defaults to the Claude runner factory."""

    with click.Context(main):
        runner_factory = _runner_factory_from_context()

    assert runner_factory is build_claude_runner


def assert_discover_subcommand_lists_eval_toml_files() -> None:
    """Assert discover lists eval.toml files under the requested tree."""

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested_eval = root / "subtree" / "evals" / "rule-one" / EVAL_TOML_FILENAME
        nested_eval.parent.mkdir(parents=True)
        nested_eval.write_text(
            'title = "rule-one"\ncases = "cases.jsonl"\nprompt = "prompt.md"\n',
            encoding="utf-8",
        )
        (nested_eval.parent / "cases.jsonl").write_text("", encoding="utf-8")
        (nested_eval.parent / "prompt.md").write_text("", encoding="utf-8")

        result = CliRunner().invoke(main, ["discover", str(root)])

        assert result.exit_code == EXIT_SUCCESS
        assert "rule-one" in result.output or str(nested_eval) in result.output


def assert_discover_subcommand_succeeds_on_empty_tree() -> None:
    """Assert discover succeeds when no eval definitions exist."""

    with TemporaryDirectory() as tmp:
        result = CliRunner().invoke(main, ["discover", tmp])

        assert result.exit_code == EXIT_SUCCESS


def assert_history_subcommand_reads_history_file() -> None:
    """Assert history reads and renders a history JSONL file."""

    with TemporaryDirectory() as tmp:
        eval_dir = Path(tmp) / "evals" / "rule"
        eval_dir.mkdir(parents=True)
        history_text = (
            '{"timestamp":"2026-05-11T15:48:00Z","schema_version":"1","git_sha":"abc",'
            '"passed":true,"pass_rate":1.0,"cases_total":4,"cases_passed":4,'
            '"total_cost_usd":1.04,"total_duration_ms":18960,"transcript":"runs/x.json"}\n'
        )
        history_path = eval_dir / "history.jsonl"
        history_path.write_text(history_text, encoding="utf-8")

        result = CliRunner().invoke(main, ["history", str(history_path)])

        assert result.exit_code == EXIT_SUCCESS
        assert "1.0" in result.output or "100" in result.output


def assert_history_subcommand_handles_missing_file() -> None:
    """Assert history rejects a missing history file."""

    with TemporaryDirectory() as tmp:
        missing_path = Path(tmp) / "history.jsonl"

        result = CliRunner().invoke(main, ["history", str(missing_path)])

        assert result.exit_code != EXIT_SUCCESS


def assert_view_subcommand_requires_run_path_or_latest_flag() -> None:
    """Assert view requires either a run path or --latest."""

    result = CliRunner().invoke(main, ["view"])

    assert result.exit_code != EXIT_SUCCESS


def assert_ci_subcommand_executes_selected_plan() -> None:
    """Assert ci plans selected suites and runs them through the CI executor."""

    _assert_ci_subcommand_builds_plan_and_executes_with_default_ceilings()


def assert_run_command_appends_format_suffix_to_every_prompt() -> None:
    """Assert run appends the required response-format suffix."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(Path(tmp), cases_jsonl=f"{RUN_CASE_ALPHA}\n")

        harness.runner.invoke(
            main,
            _run_argv(harness),
            obj=harness.runner_context,
        )

        assert len(harness.recorder.transcripts) == 1
        captured_prompt, _ = harness.recorder.transcripts[0]
        assert captured_prompt.endswith(_FORMAT_SUFFIX)
        assert "Case alpha" in captured_prompt


def assert_run_command_filters_cases_by_case_id() -> None:
    """Assert run filters to a requested case id."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(
            Path(tmp),
            cases_jsonl="\n".join((RUN_CASE_ALPHA, RUN_CASE_BETA)),
        )

        result = harness.runner.invoke(
            main,
            _run_argv(harness, "--case-id", "beta"),
            obj=harness.runner_context,
        )

        assert result.exit_code == EXIT_SUCCESS
        assert len(harness.recorder.transcripts) == 1
        captured_prompt, _ = harness.recorder.transcripts[0]
        assert "Case beta" in captured_prompt
        assert "Case alpha" not in captured_prompt


def assert_run_command_rejects_unknown_case_id() -> None:
    """Assert run rejects a case id that is absent from the case file."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(Path(tmp), cases_jsonl=f"{RUN_CASE_ALPHA}\n")

        result = harness.runner.invoke(
            main,
            _run_argv(harness, "--case-id", "missing"),
            obj=harness.runner_context,
        )

        assert result.exit_code == EXIT_GENERAL_ERROR
        assert "missing" in result.output
        assert harness.recorder.transcripts == []


def assert_run_command_filters_repeated_case_ids_in_case_file_order() -> None:
    """Assert repeated case-id selectors are emitted in case-file order."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(
            Path(tmp),
            cases_jsonl="\n".join((RUN_CASE_ALPHA, RUN_CASE_BETA, RUN_CASE_GAMMA)),
        )

        result = harness.runner.invoke(
            main,
            _run_argv(harness, "--case-id", "gamma", "--case-id", "alpha"),
            obj=harness.runner_context,
        )

        assert result.exit_code == EXIT_SUCCESS
        captured_case_ids = [
            prompt.split("Case ", 1)[1].split(":", 1)[0]
            for prompt, _metadata in harness.recorder.transcripts
        ]
        assert captured_case_ids == ["alpha", "gamma"]
        assert all(
            prompt.endswith(_FORMAT_SUFFIX)
            for prompt, _metadata in harness.recorder.transcripts
        )


def assert_run_command_uses_eval_definition_model() -> None:
    """Assert run uses the model declared by the eval definition."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(
            Path(tmp),
            cases_jsonl=f"{RUN_CASE_ALPHA}\n",
            model=RUN_DEFAULT_MODEL,
        )

        result = harness.runner.invoke(
            main,
            _run_argv(harness),
            obj=harness.runner_context,
        )

        assert result.exit_code == EXIT_SUCCESS
        assert harness.models == [RUN_DEFAULT_MODEL]


def assert_run_command_model_option_overrides_eval_definition_model() -> None:
    """Assert --model overrides the model declared by the eval definition."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(
            Path(tmp),
            cases_jsonl=f"{RUN_CASE_ALPHA}\n",
            model=RUN_DEFAULT_MODEL,
        )

        result = harness.runner.invoke(
            main,
            _run_argv(harness, "--model", RUN_OVERRIDE_MODEL),
            obj=harness.runner_context,
        )

        assert result.exit_code == EXIT_SUCCESS
        assert harness.models == [RUN_OVERRIDE_MODEL]


def assert_run_command_records_selected_model_in_artifacts() -> None:
    """Assert run artifacts record the selected model."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(
            Path(tmp),
            cases_jsonl=f"{RUN_CASE_ALPHA}\n",
            model=RUN_DEFAULT_MODEL,
        )

        result = harness.runner.invoke(
            main,
            _run_argv(harness, "--model", RUN_OVERRIDE_MODEL),
            obj=harness.runner_context,
        )

        assert result.exit_code == EXIT_SUCCESS
        runs_dir = harness.eval_toml.parent / "runs"
        result_json = next(runs_dir.glob("*.json"))
        history_row = json.loads(
            (harness.eval_toml.parent / "history.jsonl").read_text(encoding="utf-8")
        )
        assert json.loads(result_json.read_text(encoding="utf-8"))["model"] == (
            RUN_OVERRIDE_MODEL
        )
        assert history_row["model"] == RUN_OVERRIDE_MODEL


def assert_run_command_rejects_inherit_model_option() -> None:
    """Assert run rejects inherit as an explicit model option."""

    with TemporaryDirectory() as tmp:
        harness = build_run_cli_harness(Path(tmp), cases_jsonl=f"{RUN_CASE_ALPHA}\n")

        result = harness.runner.invoke(
            main,
            _run_argv(harness, "--model", "inherit"),
            obj=harness.runner_context,
        )

        assert result.exit_code == EXIT_GENERAL_ERROR
        assert "inherit" in result.output
        assert harness.models == []


def assert_plan_selects_smoke_cases_for_owned_path_change() -> None:
    """Assert PR planning selects smoke cases for an owned-path change."""

    with TemporaryDirectory() as tmp:
        _assert_plan_for_changed_paths(
            Path(tmp),
            changed_paths_text=PLAN_OWNED_PATH_CHANGE,
            expected_case_ids=(PLAN_SMOKE_CASE_ID,),
        )


def assert_plan_selects_smoke_cases_for_renamed_owned_path() -> None:
    """Assert PR planning preserves rename sources for owned-path selection."""

    with TemporaryDirectory() as tmp:
        _assert_plan_for_changed_paths(
            Path(tmp),
            changed_paths_text=PLAN_RENAMED_OWNED_PATH_CHANGE,
            expected_case_ids=(PLAN_SMOKE_CASE_ID,),
        )


def assert_plan_selects_full_suite_when_harness_change_follows_owned_path() -> None:
    """Assert universal harness changes widen owned-path smoke selection."""

    with TemporaryDirectory() as tmp:
        _assert_plan_for_changed_paths(
            Path(tmp),
            changed_paths_text=PLAN_OWNED_AND_HARNESS_PATH_CHANGE,
            expected_case_ids=(),
        )


def assert_plan_selects_full_suite_for_harness_change() -> None:
    """Assert eval-harness implementation changes select full eval suites."""

    with TemporaryDirectory() as tmp:
        _assert_plan_for_changed_paths(
            Path(tmp),
            changed_paths_text=PLAN_HARNESS_PATH_CHANGE,
            expected_case_ids=(),
        )


def assert_plan_selects_full_suite_for_copied_harness_path() -> None:
    """Assert PR planning preserves copy sources for universal path selection."""

    with TemporaryDirectory() as tmp:
        _assert_plan_for_changed_paths(
            Path(tmp),
            changed_paths_text=PLAN_COPIED_HARNESS_PATH_CHANGE,
            expected_case_ids=(),
        )


def assert_plan_selects_full_suite_for_test_harness_change() -> None:
    """Assert shared test-harness changes select full eval suites."""

    with TemporaryDirectory() as tmp:
        _assert_plan_for_changed_paths(
            Path(tmp),
            changed_paths_text=PLAN_TEST_HARNESS_PATH_CHANGE,
            expected_case_ids=(),
        )


def assert_plan_selects_full_suite_for_test_generator_change() -> None:
    """Assert shared test-generator changes select full eval suites."""

    with TemporaryDirectory() as tmp:
        _assert_plan_for_changed_paths(
            Path(tmp),
            changed_paths_text=PLAN_TEST_GENERATOR_PATH_CHANGE,
            expected_case_ids=(),
        )


def assert_plan_selects_full_suite_for_absolute_eval_definition_change() -> None:
    """Assert absolute eval artifact paths select the owning full suite."""

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        eval_toml = _make_plan_eval_dir(root)
        _assert_plan_for_changed_paths(
            root,
            changed_paths_text=f"{eval_toml.parent / 'cases.jsonl'}\n",
            expected_case_ids=(),
        )


def assert_plan_selects_full_suite_for_eval_definition_change() -> None:
    """Assert relative eval artifact paths select the owning full suite."""

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_cwd = Path.cwd()
        try:
            os.chdir(root)
            eval_root = Path(PLAN_RELATIVE_EVAL_ROOT)
            eval_toml = _make_plan_eval_dir(eval_root)
            changed_paths = Path("changed.txt")
            changed_paths.write_text(
                f"{eval_toml.parent.as_posix()}/cases.jsonl\n",
                encoding="utf-8",
            )

            result = CliRunner().invoke(
                main,
                [
                    "plan",
                    str(eval_root),
                    "--mode",
                    "pr",
                    "--changed-paths-file",
                    str(changed_paths),
                ],
            )

            assert result.exit_code == EXIT_SUCCESS
            assert json.loads(result.output) == [
                {
                    "eval_toml": str(eval_toml),
                    "plugin_dir": PLAN_PLUGIN_DIR,
                    "case_ids": [],
                }
            ]
        finally:
            os.chdir(original_cwd)


def assert_plan_full_mode_excludes_manual_evals() -> None:
    """Assert full-mode planning excludes manual eval definitions."""

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        automatic_eval = make_eval_dir(
            root / "evals" / "automatic",
            title="automatic",
            plugin_dir=PLAN_PLUGIN_DIR,
            owned_paths=(PLAN_OWNED_PATH_PATTERN,),
            smoke_case_ids=(PLAN_SMOKE_CASE_ID,),
        )
        make_eval_dir(
            root / "evals" / "manual",
            title="manual",
            plugin_dir=PLAN_PLUGIN_DIR,
            owned_paths=("src/plugins/spec-tree/skills/review-changes/**",),
            smoke_case_ids=(PLAN_MANUAL_CASE_ID,),
            ci_policy="manual",
        )

        result = CliRunner().invoke(
            main,
            [
                "plan",
                str(root),
                "--mode",
                "full",
            ],
        )

        assert result.exit_code == EXIT_SUCCESS
        assert json.loads(result.output) == [
            {
                "eval_toml": str(automatic_eval),
                "plugin_dir": PLAN_PLUGIN_DIR,
                "case_ids": [],
            }
        ]


def assert_plan_skips_unrelated_pr_change() -> None:
    """Assert unrelated PR paths select no eval suites."""

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _make_plan_eval_dir(root)
        changed_paths = root / "changed.txt"
        changed_paths.write_text(PLAN_UNRELATED_PATH_CHANGE, encoding="utf-8")

        result = CliRunner().invoke(
            main,
            [
                "plan",
                str(root),
                "--mode",
                "pr",
                "--changed-paths-file",
                str(changed_paths),
            ],
        )

        assert result.exit_code == EXIT_SUCCESS
        assert json.loads(result.output) == []


def _assert_run_subcommand_rejects_worker_count(workers: int) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        eval_toml = root / EVAL_TOML_FILENAME
        eval_toml.write_text("", encoding="utf-8")
        plugin_dir = root / "plugin"
        plugin_dir.mkdir()

        result = CliRunner().invoke(
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

        assert result.exit_code == EXIT_INVOCATION_ERROR
        assert "workers" in result.output.lower()


def _run_argv(harness: RunCliHarness, *extra_args: str) -> list[str]:
    return [
        "run",
        str(harness.eval_toml),
        "--plugin-dir",
        str(harness.plugin_dir),
        *extra_args,
    ]


def _assert_plan_for_changed_paths(
    tmp_path: Path,
    *,
    changed_paths_text: str,
    expected_case_ids: tuple[str, ...],
) -> None:
    eval_toml = make_eval_dir(
        tmp_path / "evals" / "rule",
        title="rule",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=(PLAN_OWNED_PATH_PATTERN,),
        smoke_case_ids=(PLAN_SMOKE_CASE_ID,),
    )
    changed_paths = tmp_path / "changed.txt"
    changed_paths.write_text(changed_paths_text, encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "plan",
            str(tmp_path),
            "--mode",
            "pr",
            "--changed-paths-file",
            str(changed_paths),
        ],
    )

    assert result.exit_code == EXIT_SUCCESS
    assert json.loads(result.output) == [
        {
            "eval_toml": str(eval_toml),
            "plugin_dir": PLAN_PLUGIN_DIR,
            "case_ids": list(expected_case_ids),
        }
    ]


def _make_plan_eval_dir(root: Path) -> Path:
    return make_eval_dir(
        root / "evals" / "rule",
        title="rule",
        plugin_dir=PLAN_PLUGIN_DIR,
        owned_paths=(PLAN_OWNED_PATH_PATTERN,),
        smoke_case_ids=(PLAN_SMOKE_CASE_ID,),
    )
