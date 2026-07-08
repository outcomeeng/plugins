"""Factory helpers for constructing eval-domain objects in tests.

The ``make_*`` helpers accept keyword overrides so a test can build a
``Case``, ``TrialResult``, ``CaseOutcome``, ``SuiteResult``, or a complete
eval directory tree with one call.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from outcomeeng_evals.case import Case
from outcomeeng_evals.ci_execution import (
    CiRunSettings,
    DEFAULT_CI_MAX_BUDGET_USD,
    DEFAULT_CI_TIMEOUT_SECONDS,
    DEFAULT_CI_WORKERS,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    UV_RUN_EVALS_ARGV_PREFIX,
    command_for_plan_item,
    execute_ci_plan,
)
from outcomeeng_evals.ci_plan import EvalPlanItem
from outcomeeng_evals.ci_plan import read_changed_paths_file
from outcomeeng_evals.grader import GradeResult
from outcomeeng_evals.runner import RunMetadata
from outcomeeng_evals.suite import CaseOutcome, SuiteResult, TrialResult
from outcomeeng_evals.testing.fakes import (
    RecordingCommandRunner,
    RecordingUvExecutable,
    make_recording_uv_executable,
)


_DEFAULT_CASE_ID = "test-case"
_DEFAULT_INPUT: dict[str, Any] = {}
_DEFAULT_PROMPT = "prompt"
_DEFAULT_VERDICT: dict[str, Any] = {
    "status": "rejected",
    "findings": [{"rule": "x", "present": True}],
}
_DEFAULT_RESPONSE = json.dumps(_DEFAULT_VERDICT)
_DEFAULT_THRESHOLD = 0.85
_DEFAULT_EVAL_TITLE = "test-eval"
_DEFAULT_CASES_FILENAME = "cases.jsonl"
_DEFAULT_PROMPT_FILENAME = "prompt.md"
_DEFAULT_EVAL_FILENAME = "eval.toml"
_DEFAULT_EVAL_RULE = "rule"
_DEFAULT_PLUGIN_DIR = Path("dist/claude/spec-tree")
DEFAULT_PLAN_CASE_IDS = ("alpha", "beta")
DEFAULT_CI_OWNED_PATH = "src/plugins/spec-tree/skills/manage-pr/**"
DEFAULT_CI_CHANGED_PATH = "src/plugins/spec-tree/skills/manage-pr/SKILL.md"
DEFAULT_CI_CHANGED_PATH_STATUS = "M"
DEFAULT_CI_RENAMED_PATH = "docs/manage-pr.md"
DEFAULT_CI_COPIED_PATH = "docs/copied-suite.py"
DEFAULT_CI_HARNESS_PATH = "outcomeeng_evals/suite.py"
DEFAULT_CI_WHITESPACE_PATH = " docs/has edge spaces.md "


@dataclass(frozen=True)
class EvalPlanCommandCase:
    """Harness-owned CI plan item with its expected command contract."""

    item: EvalPlanItem
    expected_command: tuple[str, ...]


@dataclass(frozen=True)
class DefaultCiCommandHarness:
    """Harness-owned CI command setup with expected command evidence."""

    eval_root: Path
    changed_paths_file: Path
    fake_uv: RecordingUvExecutable
    expected_command: tuple[str, ...]


@dataclass(frozen=True)
class ChangedPathsFileCase:
    """Harness-owned changed-path file case and expected parser output."""

    content: str
    expected_paths: tuple[str, ...]


def make_case(
    *,
    case_id: str = _DEFAULT_CASE_ID,
    case_input: dict[str, Any] | None = None,
    must_contain: tuple[dict[str, Any], ...] = (),
    must_not_contain: tuple[dict[str, Any], ...] = (),
) -> Case:
    return Case(
        id=case_id,
        input=dict(case_input) if case_input is not None else dict(_DEFAULT_INPUT),
        must_contain=must_contain,
        must_not_contain=must_not_contain,
    )


def make_trial_result(
    *,
    case_id: str = _DEFAULT_CASE_ID,
    trial_index: int = 0,
    prompt: str = _DEFAULT_PROMPT,
    response: str = _DEFAULT_RESPONSE,
    verdict: Any | None = None,
    passed: bool = True,
    reasons: tuple[str, ...] = (),
    metadata: RunMetadata | None = None,
) -> TrialResult:
    return TrialResult(
        case_id=case_id,
        trial_index=trial_index,
        prompt=prompt,
        response=response,
        verdict=verdict if verdict is not None else dict(_DEFAULT_VERDICT),
        grade=GradeResult(passed=passed, reasons=reasons),
        metadata=metadata if metadata is not None else RunMetadata(),
    )


def make_case_outcome(
    *,
    case: Case | None = None,
    trials: tuple[TrialResult, ...] | None = None,
    passed: bool = True,
) -> CaseOutcome:
    case_value = case if case is not None else make_case()
    trial_values = (
        trials
        if trials is not None
        else (make_trial_result(case_id=case_value.id, passed=passed),)
    )
    return CaseOutcome(case=case_value, trials=trial_values, passed=passed)


def make_suite_result(
    *,
    outcomes: tuple[CaseOutcome, ...] | None = None,
    pass_rate: float = 1.0,
    threshold: float = _DEFAULT_THRESHOLD,
    passed: bool = True,
) -> SuiteResult:
    return SuiteResult(
        outcomes=outcomes if outcomes is not None else (make_case_outcome(),),
        pass_rate=pass_rate,
        threshold=threshold,
        passed=passed,
    )


def make_eval_plan_item(
    *,
    rule: str = _DEFAULT_EVAL_RULE,
    plugin_dir: Path = _DEFAULT_PLUGIN_DIR,
    case_ids: tuple[str, ...] = (),
) -> EvalPlanItem:
    return EvalPlanItem(
        eval_toml=Path("spx/node/evals") / rule / _DEFAULT_EVAL_FILENAME,
        plugin_dir=plugin_dir,
        case_ids=case_ids,
    )


def make_eval_plan_item_command_cases() -> tuple[EvalPlanItem, ...]:
    return (
        make_eval_plan_item(rule="full-suite"),
        make_eval_plan_item(
            rule="single-case",
            case_ids=DEFAULT_PLAN_CASE_IDS[:1],
        ),
        make_eval_plan_item(
            rule="multi-case",
            plugin_dir=Path("dist/claude/python"),
            case_ids=DEFAULT_PLAN_CASE_IDS,
        ),
    )


def make_eval_plan_command_cases(
    settings: CiRunSettings | None = None,
) -> tuple[EvalPlanCommandCase, ...]:
    effective_settings = settings or CiRunSettings()
    return tuple(
        EvalPlanCommandCase(
            item=item,
            expected_command=expected_command_for_plan_item(
                item,
                settings=effective_settings,
            ),
        )
        for item in make_eval_plan_item_command_cases()
    )


def expected_command_for_plan_item(
    item: EvalPlanItem,
    *,
    settings: CiRunSettings,
) -> tuple[str, ...]:
    command: list[str] = [
        *UV_RUN_EVALS_ARGV_PREFIX,
        str(item.eval_toml),
        "--plugin-dir",
        str(item.plugin_dir),
        "--workers",
        settings.workers,
        "--max-budget-usd",
        settings.max_budget_usd,
        "--timeout-seconds",
        settings.timeout_seconds,
    ]
    for case_id in item.case_ids:
        command.extend(("--case-id", case_id))
    return tuple(command)


def expected_default_ci_command(eval_toml: Path) -> tuple[str, ...]:
    return (
        *UV_RUN_EVALS_ARGV_PREFIX[1:],
        str(eval_toml),
        "--plugin-dir",
        str(_DEFAULT_PLUGIN_DIR),
        "--workers",
        DEFAULT_CI_WORKERS,
        "--max-budget-usd",
        DEFAULT_CI_MAX_BUDGET_USD,
        "--timeout-seconds",
        DEFAULT_CI_TIMEOUT_SECONDS,
        "--case-id",
        *DEFAULT_PLAN_CASE_IDS[:1],
        "--case-id",
        *DEFAULT_PLAN_CASE_IDS[1:],
    )


def write_default_ci_changed_paths_file(tmp_path: Path) -> Path:
    changed_paths_file = tmp_path / "changed-paths.txt"
    changed_paths_file.write_text(
        f"{DEFAULT_CI_CHANGED_PATH_STATUS}\t{DEFAULT_CI_CHANGED_PATH}\n",
        encoding="utf-8",
    )
    return changed_paths_file


def make_changed_paths_file_cases() -> tuple[ChangedPathsFileCase, ...]:
    return (
        ChangedPathsFileCase(
            content=f"{DEFAULT_CI_CHANGED_PATH_STATUS}\t{DEFAULT_CI_CHANGED_PATH}\n",
            expected_paths=(DEFAULT_CI_CHANGED_PATH,),
        ),
        ChangedPathsFileCase(
            content=f"R100\t{DEFAULT_CI_CHANGED_PATH}\t{DEFAULT_CI_RENAMED_PATH}\n",
            expected_paths=(DEFAULT_CI_CHANGED_PATH, DEFAULT_CI_RENAMED_PATH),
        ),
        ChangedPathsFileCase(
            content=f"C100\t{DEFAULT_CI_HARNESS_PATH}\t{DEFAULT_CI_COPIED_PATH}\n",
            expected_paths=(DEFAULT_CI_HARNESS_PATH, DEFAULT_CI_COPIED_PATH),
        ),
        ChangedPathsFileCase(
            content=f"{DEFAULT_CI_CHANGED_PATH_STATUS}\t{DEFAULT_CI_WHITESPACE_PATH}\n",
            expected_paths=(DEFAULT_CI_WHITESPACE_PATH,),
        ),
        ChangedPathsFileCase(
            content=DEFAULT_CI_WHITESPACE_PATH + "\n",
            expected_paths=(DEFAULT_CI_WHITESPACE_PATH,),
        ),
    )


def assert_changed_paths_file_reads_git_name_status_rows() -> None:
    with TemporaryDirectory() as tmp:
        for index, case in enumerate(make_changed_paths_file_cases()):
            changed_paths_file = Path(tmp) / f"changed-paths-{index}.txt"
            changed_paths_file.write_text(case.content, encoding="utf-8")

            assert read_changed_paths_file(changed_paths_file) == case.expected_paths


def assert_plan_items_map_to_run_commands_with_settings_and_case_selectors() -> None:
    for case in make_eval_plan_command_cases():
        assert command_for_plan_item(case.item, settings=CiRunSettings()) == (
            case.expected_command
        )


def assert_multi_case_plan_item_preserves_case_selector_order() -> None:
    assert command_for_plan_item(
        make_eval_plan_item(case_ids=DEFAULT_PLAN_CASE_IDS),
        settings=CiRunSettings(),
    )[-4:] == (
        "--case-id",
        *DEFAULT_PLAN_CASE_IDS[:1],
        "--case-id",
        *DEFAULT_PLAN_CASE_IDS[1:],
    )


def assert_empty_plan_exits_successfully_without_commands() -> None:
    runner = RecordingCommandRunner()

    result = execute_ci_plan(
        (),
        settings=CiRunSettings(),
        runner=runner,
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.attempted == 0
    assert runner.calls == []


def assert_failing_suite_fails_aggregate_after_attempting_every_suite() -> None:
    first = make_eval_plan_item(rule="first")
    second = make_eval_plan_item(rule="second")
    runner = RecordingCommandRunner(exit_codes=(EXIT_FAILURE, EXIT_SUCCESS))

    result = execute_ci_plan((first, second), settings=CiRunSettings(), runner=runner)

    assert result.exit_code == EXIT_FAILURE
    assert result.attempted == 2
    assert result.failed == (first,)
    assert len(runner.calls) == 2


def make_default_ci_command_harness(tmp_path: Path) -> DefaultCiCommandHarness:
    eval_root = tmp_path / "evals"
    eval_toml = make_eval_dir(
        eval_root / "rule",
        plugin_dir="dist/claude/spec-tree",
        owned_paths=(DEFAULT_CI_OWNED_PATH,),
        smoke_case_ids=DEFAULT_PLAN_CASE_IDS,
    )
    changed_paths_file = write_default_ci_changed_paths_file(tmp_path)
    fake_uv = make_recording_uv_executable(tmp_path)
    return DefaultCiCommandHarness(
        eval_root=eval_root,
        changed_paths_file=changed_paths_file,
        fake_uv=fake_uv,
        expected_command=expected_default_ci_command(eval_toml),
    )


def assert_main_group_exposes_ci_subcommand() -> None:
    from click.testing import CliRunner

    from outcomeeng_evals.cli import main

    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == os.EX_OK
    assert "ci" in result.output


def assert_ci_subcommand_builds_plan_and_executes_with_default_ceilings() -> None:
    from click.testing import CliRunner

    from outcomeeng_evals.cli import main

    with TemporaryDirectory() as tmp:
        harness = make_default_ci_command_harness(Path(tmp))

        result = CliRunner().invoke(
            main,
            [
                "ci",
                str(harness.eval_root),
                "--mode",
                "pr",
                "--changed-paths-file",
                str(harness.changed_paths_file),
            ],
            env=harness.fake_uv.env,
        )

        assert result.exit_code == os.EX_OK
        assert harness.fake_uv.commands() == (harness.expected_command,)


def make_bimodal_cache_suite_result() -> SuiteResult:
    """A two-trial suite: one cold-write trial, then one warm-read trial.

    The bimodal prompt-cache shape — the first trial paying a cache-creation
    write, the second served from a warm cache read — exercises token
    aggregation across more than one trial, which a single-trial fixture
    cannot. Aggregate sums across the two trials: input 22, output 12,
    cache-read 49600, cache-creation 34000.
    """
    trials = (
        make_trial_result(
            trial_index=0,
            metadata=RunMetadata(
                duration_ms=2000.0,
                total_cost_usd=0.42,
                input_tokens=10,
                output_tokens=5,
                cache_read_input_tokens=0,
                cache_creation_input_tokens=34000,
            ),
        ),
        make_trial_result(
            trial_index=1,
            metadata=RunMetadata(
                duration_ms=1000.0,
                total_cost_usd=0.09,
                input_tokens=12,
                output_tokens=7,
                cache_read_input_tokens=49600,
                cache_creation_input_tokens=0,
            ),
        ),
    )
    return make_suite_result(outcomes=(make_case_outcome(trials=trials),))


def make_eval_dir(
    directory: Path,
    *,
    title: str = _DEFAULT_EVAL_TITLE,
    cases_filename: str = _DEFAULT_CASES_FILENAME,
    prompt_filename: str = _DEFAULT_PROMPT_FILENAME,
    eval_filename: str = _DEFAULT_EVAL_FILENAME,
    threshold: float | None = None,
    trials: int | None = None,
    cases_content: str = "",
    prompt_content: str = "",
    with_cases: bool = True,
    with_prompt: bool = True,
    plugin_dir: str | None = None,
    owned_paths: tuple[str, ...] = (),
    smoke_case_ids: tuple[str, ...] = (),
    ci_policy: str | None = None,
) -> Path:
    """Build a complete per-eval directory under ``directory`` and return the eval.toml path.

    ``with_cases=False`` and ``with_prompt=False`` flags skip writing the
    respective files so tests can verify the loader's existence checks.
    """
    directory.mkdir(parents=True, exist_ok=True)
    lines = [
        f'title = "{title}"',
        f'cases = "{cases_filename}"',
        f'prompt = "{prompt_filename}"',
    ]
    if threshold is not None:
        lines.append(f"threshold = {threshold}")
    if trials is not None:
        lines.append(f"trials = {trials}")
    if plugin_dir is not None:
        lines.append(f'plugin_dir = "{plugin_dir}"')
    if owned_paths:
        rendered_owned_paths = ", ".join(f'"{path}"' for path in owned_paths)
        lines.append(f"owned_paths = [{rendered_owned_paths}]")
    if smoke_case_ids:
        rendered_smoke_cases = ", ".join(f'"{case_id}"' for case_id in smoke_case_ids)
        lines.append(f"smoke_cases = [{rendered_smoke_cases}]")
    if ci_policy is not None:
        lines.append(f'ci_policy = "{ci_policy}"')
    toml_path = directory / eval_filename
    toml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if with_cases:
        (directory / cases_filename).write_text(cases_content, encoding="utf-8")
    if with_prompt:
        (directory / prompt_filename).write_text(prompt_content, encoding="utf-8")
    return toml_path
