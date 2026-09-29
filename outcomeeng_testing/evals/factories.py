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
from typing import Any, cast

from click.testing import CliRunner, Result

from outcomeeng_evals.case import Case
from outcomeeng_evals.ci_execution import (
    CASE_ID_FLAG,
    DEFAULT_CI_MAX_BUDGET_USD,
    DEFAULT_CI_TIMEOUT_SECONDS,
    DEFAULT_CI_WORKERS,
    PLUGIN_DIR_FLAG,
    UV_RUN_EVALS_ARGV_PREFIX,
)
from outcomeeng_evals.ci_plan import CiMode, EvalPlanItem
from outcomeeng_evals.cli import main
from outcomeeng_evals.cli.commands.ci import ci_command
from outcomeeng_evals.cli.commands.run import (
    MAX_BUDGET_USD_OPTION,
    TIMEOUT_SECONDS_OPTION,
)
from outcomeeng.models import AgentProfile
from outcomeeng_evals.definition import (
    CASES_FIELD,
    CI_POLICY_FIELD,
    CiPolicy,
    DEFAULT_PROFILE,
    EVAL_TOML_FILENAME,
    OWNED_PATHS_FIELD,
    PLUGIN_DIR_FIELD,
    PROFILE_FIELD,
    PROMPT_FIELD,
    SMOKE_CASES_FIELD,
    THRESHOLD_FIELD,
    TITLE_FIELD,
    TRIALS_FIELD,
)
from outcomeeng_evals.grader import GradeResult
from outcomeeng_evals.history import HistoryRow
from outcomeeng_evals.runner import ModelProcessResult, RunMetadata
from outcomeeng_evals.suite import CaseOutcome, SuiteResult, TrialResult
from outcomeeng_testing.evals.fakes import (
    RecordingModelProcessLauncher,
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
EVAL_DEFINITION_TITLE = "test-eval"
EVAL_CASES_FILENAME = "cases.jsonl"
EVAL_PROMPT_FILENAME = "prompt.md"
_DEFAULT_EVAL_RULE = "rule"
DEFAULT_CI_PLUGIN_DIR = Path("dist/claude/spec-tree")
DEFAULT_DEFINITION_THRESHOLD = 0.95
DEFAULT_DEFINITION_TRIALS = 3
DEFAULT_PLAN_CASE_IDS = ("alpha", "beta")
DEFAULT_PLAN_RULES = ("first", "second")
DEFAULT_CI_OWNED_PATH = "src/plugins/spec-tree/skills/manage-pr/**"
DEFAULT_CI_CHANGED_PATH = "src/plugins/spec-tree/skills/manage-pr/SKILL.md"
DEFAULT_CI_CHANGED_PATH_STATUS = "M"
DEFAULT_CI_RENAMED_PATH = "docs/manage-pr.md"
DEFAULT_CI_COPIED_PATH = "docs/copied-suite.py"
DEFAULT_CI_HARNESS_PATH = "outcomeeng_evals/suite.py"
DEFAULT_CI_WHITESPACE_PATH = " docs/has edge spaces.md "
DEFAULT_CI_TABBED_PATH = "docs/plain\tpath.md"
DEFAULT_CI_MALFORMED_STATUS_ROW = "M\tdocs/plain\tpath.md"
DEFAULT_CI_EXPLICIT_PROFILE = next(
    profile for profile in AgentProfile if profile is not DEFAULT_PROFILE
)


@dataclass(frozen=True)
class DefaultCiCommandHarness:
    """Harness-owned CI command setup with expected command evidence."""

    eval_root: Path
    changed_paths_file: Path
    fake_uv: RecordingUvExecutable
    expected_command: tuple[str, ...]


@dataclass(frozen=True)
class DefaultCiCommandRun:
    """Observations from one ``ci`` subcommand run over the default CI suite."""

    result: Result
    commands: tuple[tuple[str, ...], ...]
    expected_command: tuple[str, ...]


@dataclass(frozen=True)
class ChangedPathsFileCase:
    """Harness-owned changed-path file case and expected parser output."""

    content: str
    expected_paths: tuple[str, ...]


@dataclass(frozen=True)
class ChangedPathsFileErrorCase:
    """Harness-owned changed-path file case that must be rejected."""

    content: str


@dataclass(frozen=True)
class CiMetadataDefinitionCase:
    """Harness-owned eval definition case for optional CI metadata."""

    eval_toml: Path
    plugin_dir: Path
    profile: AgentProfile
    owned_paths: tuple[str, ...]
    smoke_case_ids: tuple[str, ...]
    ci_policy: CiPolicy


@dataclass(frozen=True)
class ModelAuthCase:
    """One fixture-provided model-process authentication case."""

    name: str
    environment: dict[str, str]
    bare_override: bool | None
    expected_bare: bool


@dataclass(frozen=True)
class ModelProcessFixture:
    """A captured model-process envelope and its independent expectations."""

    prompt: str
    envelope: dict[str, Any]
    expected_text: str
    expected_metadata: RunMetadata
    auth_cases: tuple[ModelAuthCase, ...]


@dataclass(frozen=True)
class ReportFixture:
    """A complete inert suite payload used by report serialization evidence."""

    title: str
    model: str
    configured_max_budget_usd: float
    configured_timeout_seconds: int
    case: Case
    trial: dict[str, Any]
    threshold: float
    failing_reason: str
    expected_report: dict[str, Any]
    expected_without_metadata: dict[str, Any]
    expected_cache_only: dict[str, Any]
    stability: dict[str, tuple[tuple[bool, ...], ...]]


def load_model_process_fixture(path: Path) -> ModelProcessFixture:
    """Decode one inert model-process contract fixture."""

    with path.open(encoding="utf-8") as fixture_file:
        payload = json.load(fixture_file)
    expected = payload["expected"]
    return ModelProcessFixture(
        prompt=payload["prompt"],
        envelope=payload["envelope"],
        expected_text=expected["text"],
        expected_metadata=RunMetadata(
            duration_ms=expected["duration_ms"],
            total_cost_usd=expected["total_cost_usd"],
            input_tokens=expected["input_tokens"],
            output_tokens=expected["output_tokens"],
            cache_read_input_tokens=expected["cache_read_input_tokens"],
            cache_creation_input_tokens=expected["cache_creation_input_tokens"],
            num_turns=expected["num_turns"],
            stop_reason=expected["stop_reason"],
        ),
        auth_cases=tuple(
            ModelAuthCase(
                name=case["name"],
                environment=case["environment"],
                bare_override=case["bare_override"],
                expected_bare=case["expected_bare"],
            )
            for case in payload["auth_cases"]
        ),
    )


def load_history_rows_fixture(path: Path) -> tuple[HistoryRow, ...]:
    """Decode complete inert history rows for append-writer evidence."""

    with path.open(encoding="utf-8") as fixture_file:
        payload = json.load(fixture_file)
    if not isinstance(payload, list) or not all(
        isinstance(row, dict) for row in payload
    ):
        raise ValueError("history-row fixture must be a JSON array of objects")
    return tuple(cast(HistoryRow, row) for row in payload)


def load_report_fixture(path: Path) -> ReportFixture:
    """Decode one complete inert report-suite payload."""

    with path.open(encoding="utf-8") as fixture_file:
        payload = json.load(fixture_file)
    case_payload = payload["case"]
    return ReportFixture(
        title=payload["title"],
        model=payload["model"],
        configured_max_budget_usd=payload["configured_max_budget_usd"],
        configured_timeout_seconds=payload["configured_timeout_seconds"],
        case=Case(
            id=case_payload["id"],
            input=case_payload["input"],
            must_contain=tuple(case_payload["must_contain"]),
            must_not_contain=tuple(case_payload["must_not_contain"]),
        ),
        trial=payload["trial"],
        threshold=payload["threshold"],
        failing_reason=payload["failing_reason"],
        expected_report=payload["expected_report"],
        expected_without_metadata=payload["expected_without_metadata"],
        expected_cache_only=payload["expected_cache_only"],
        stability={
            name: tuple(tuple(pattern) for pattern in patterns)
            for name, patterns in payload["stability"].items()
        },
    )


def make_report_suite_result(
    fixture: ReportFixture,
    *,
    passed: bool = True,
) -> SuiteResult:
    """Construct a suite result from a complete inert report fixture."""

    trial = fixture.trial
    metadata = trial["metadata"]
    trial_result = TrialResult(
        case_id=fixture.case.id,
        trial_index=trial["trial_index"],
        prompt=trial["prompt"],
        response=trial["response"],
        verdict=trial["verdict"],
        grade=GradeResult(
            passed=passed,
            reasons=() if passed else (fixture.failing_reason,),
        ),
        metadata=RunMetadata(**metadata),
    )
    return SuiteResult(
        outcomes=(
            CaseOutcome(case=fixture.case, trials=(trial_result,), passed=passed),
        ),
        pass_rate=float(passed),
        threshold=fixture.threshold,
        passed=passed,
    )


def make_metadata_free_report_suite_result(fixture: ReportFixture) -> SuiteResult:
    """Construct the fixture suite with an explicitly absent metadata payload."""

    trial = make_trial_result(case_id=fixture.case.id, metadata=RunMetadata())
    return make_suite_result(
        outcomes=(make_case_outcome(case=fixture.case, trials=(trial,)),),
        threshold=fixture.threshold,
    )


def make_cache_only_report_suite_result(fixture: ReportFixture) -> SuiteResult:
    """Construct the fixture suite with only cache-read observability present."""

    cache_read = fixture.trial["metadata"]["cache_read_input_tokens"]
    trial = make_trial_result(
        case_id=fixture.case.id,
        metadata=RunMetadata(cache_read_input_tokens=cache_read),
    )
    return make_suite_result(
        outcomes=(make_case_outcome(case=fixture.case, trials=(trial,)),),
        threshold=fixture.threshold,
    )


def make_stability_suite_result(
    fixture: ReportFixture,
    patterns: tuple[tuple[bool, ...], ...],
) -> SuiteResult:
    """Construct per-case trial outcomes from fixture-owned pass patterns."""

    outcomes = []
    for case_index, pattern in enumerate(patterns):
        trials = tuple(
            make_trial_result(
                case_id=f"{fixture.case.id}-{case_index}",
                trial_index=trial_index,
                passed=passed,
            )
            for trial_index, passed in enumerate(pattern)
        )
        pass_count = sum(pattern)
        outcomes.append(
            make_case_outcome(
                case=fixture.case,
                trials=trials,
                passed=pass_count > len(pattern) / 2,
            )
        )
    passed_count = sum(outcome.passed for outcome in outcomes)
    pass_rate = passed_count / len(outcomes)
    return make_suite_result(
        outcomes=tuple(outcomes),
        pass_rate=pass_rate,
        threshold=fixture.threshold,
        passed=pass_rate >= fixture.threshold,
    )


def make_recording_model_process_launcher(
    fixture: ModelProcessFixture,
    *,
    returncode: int = os.EX_OK,
) -> RecordingModelProcessLauncher:
    """Return a recording boundary that replays an inert CLI envelope."""

    return RecordingModelProcessLauncher(
        result=ModelProcessResult(
            returncode=returncode,
            stdout=json.dumps(fixture.envelope) if returncode == os.EX_OK else "",
            stderr="" if returncode == os.EX_OK else "model process failed",
        )
    )


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
    plugin_dir: Path = DEFAULT_CI_PLUGIN_DIR,
    case_ids: tuple[str, ...] = (),
) -> EvalPlanItem:
    return EvalPlanItem(
        eval_toml=Path("spx/node/evals") / rule / EVAL_TOML_FILENAME,
        plugin_dir=plugin_dir,
        case_ids=case_ids,
    )


def expected_default_ci_command(eval_toml: Path) -> tuple[str, ...]:
    return (
        *UV_RUN_EVALS_ARGV_PREFIX[1:],
        str(eval_toml),
        PLUGIN_DIR_FLAG,
        str(DEFAULT_CI_PLUGIN_DIR),
        "--workers",
        DEFAULT_CI_WORKERS,
        MAX_BUDGET_USD_OPTION,
        DEFAULT_CI_MAX_BUDGET_USD,
        TIMEOUT_SECONDS_OPTION,
        DEFAULT_CI_TIMEOUT_SECONDS,
        CASE_ID_FLAG,
        *DEFAULT_PLAN_CASE_IDS[:1],
        CASE_ID_FLAG,
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


def make_changed_paths_file_error_cases() -> tuple[ChangedPathsFileErrorCase, ...]:
    return (
        ChangedPathsFileErrorCase(content=DEFAULT_CI_TABBED_PATH + "\n"),
        ChangedPathsFileErrorCase(content=DEFAULT_CI_MALFORMED_STATUS_ROW + "\n"),
        ChangedPathsFileErrorCase(
            content=(
                f"{DEFAULT_CI_CHANGED_PATH_STATUS}\t{DEFAULT_CI_CHANGED_PATH}\n"
                f"{DEFAULT_CI_RENAMED_PATH}\n"
            ),
        ),
    )


def make_ci_metadata_definition_case(tmp_path: Path) -> CiMetadataDefinitionCase:
    eval_toml = make_eval_dir(
        tmp_path / "eval",
        plugin_dir=str(DEFAULT_CI_PLUGIN_DIR),
        profile=DEFAULT_CI_EXPLICIT_PROFILE,
        owned_paths=(DEFAULT_CI_OWNED_PATH,),
        smoke_case_ids=DEFAULT_PLAN_CASE_IDS[:1],
        ci_policy=CiPolicy.MANUAL.value,
    )
    return CiMetadataDefinitionCase(
        eval_toml=eval_toml,
        plugin_dir=DEFAULT_CI_PLUGIN_DIR,
        profile=DEFAULT_CI_EXPLICIT_PROFILE,
        owned_paths=(DEFAULT_CI_OWNED_PATH,),
        smoke_case_ids=DEFAULT_PLAN_CASE_IDS[:1],
        ci_policy=CiPolicy.MANUAL,
    )


EvalDefinitionValue = str | int | float | tuple[str, ...]


def _toml_value(value: EvalDefinitionValue) -> str:
    """Render one TOML value: strings as basic strings, arrays of strings, numbers."""

    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, tuple):
        return "[" + ", ".join(json.dumps(item) for item in value) + "]"
    return str(value)


def write_eval_definition(
    tmp_path: Path,
    *,
    fields: dict[str, EvalDefinitionValue] | None = None,
    omit: tuple[str, ...] = (),
    with_cases: bool = True,
    with_prompt: bool = True,
) -> Path:
    """Write an eval definition under ``tmp_path`` and return its ``eval.toml``.

    The required title, case-file, and prompt-file keys are written unless
    named in ``omit``; each entry of ``fields`` adds one top-level key. The
    case and prompt files exist unless ``with_cases`` or ``with_prompt`` is
    false.
    """

    required = {
        TITLE_FIELD: EVAL_DEFINITION_TITLE,
        CASES_FIELD: EVAL_CASES_FILENAME,
        PROMPT_FIELD: EVAL_PROMPT_FILENAME,
    }
    entries = {
        **{key: value for key, value in required.items() if key not in omit},
        **(fields or {}),
    }
    directory = tmp_path / "eval"
    directory.mkdir(parents=True)
    toml_path = directory / EVAL_TOML_FILENAME
    toml_path.write_text(
        "".join(f"{key} = {_toml_value(value)}\n" for key, value in entries.items()),
        encoding="utf-8",
    )
    if with_cases:
        (directory / EVAL_CASES_FILENAME).write_text("", encoding="utf-8")
    if with_prompt:
        (directory / EVAL_PROMPT_FILENAME).write_text("", encoding="utf-8")
    return toml_path


def make_default_ci_command_harness(tmp_path: Path) -> DefaultCiCommandHarness:
    eval_root = tmp_path / "evals"
    eval_toml = make_eval_dir(
        eval_root / "rule",
        plugin_dir=str(DEFAULT_CI_PLUGIN_DIR),
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


def run_default_ci_subcommand(tmp_path: Path) -> DefaultCiCommandRun:
    """Run ``ci`` in PR mode over the default suite and record its suite commands."""

    harness = make_default_ci_command_harness(tmp_path)
    result = CliRunner().invoke(
        main,
        [
            str(ci_command.name),
            str(harness.eval_root),
            "--mode",
            CiMode.PR.value,
            "--changed-paths-file",
            str(harness.changed_paths_file),
        ],
        env=harness.fake_uv.env,
    )
    return DefaultCiCommandRun(
        result=result,
        commands=harness.fake_uv.commands(),
        expected_command=harness.expected_command,
    )


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
    title: str = EVAL_DEFINITION_TITLE,
    cases_filename: str = EVAL_CASES_FILENAME,
    prompt_filename: str = EVAL_PROMPT_FILENAME,
    eval_filename: str = EVAL_TOML_FILENAME,
    threshold: float | None = None,
    trials: int | None = None,
    cases_content: str = "",
    prompt_content: str = "",
    with_cases: bool = True,
    with_prompt: bool = True,
    plugin_dir: str | None = None,
    profile: str | None = None,
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
        f'{TITLE_FIELD} = "{title}"',
        f'{CASES_FIELD} = "{cases_filename}"',
        f'{PROMPT_FIELD} = "{prompt_filename}"',
    ]
    if threshold is not None:
        lines.append(f"{THRESHOLD_FIELD} = {threshold}")
    if trials is not None:
        lines.append(f"{TRIALS_FIELD} = {trials}")
    if plugin_dir is not None:
        lines.append(f'{PLUGIN_DIR_FIELD} = "{plugin_dir}"')
    if profile is not None:
        lines.append(f'{PROFILE_FIELD} = "{profile}"')
    if owned_paths:
        rendered_owned_paths = ", ".join(f'"{path}"' for path in owned_paths)
        lines.append(f"{OWNED_PATHS_FIELD} = [{rendered_owned_paths}]")
    if smoke_case_ids:
        rendered_smoke_cases = ", ".join(f'"{case_id}"' for case_id in smoke_case_ids)
        lines.append(f"{SMOKE_CASES_FIELD} = [{rendered_smoke_cases}]")
    if ci_policy is not None:
        lines.append(f'{CI_POLICY_FIELD} = "{ci_policy}"')
    toml_path = directory / eval_filename
    toml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if with_cases:
        (directory / cases_filename).write_text(cases_content, encoding="utf-8")
    if with_prompt:
        (directory / prompt_filename).write_text(prompt_content, encoding="utf-8")
    return toml_path
