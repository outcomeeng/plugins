"""Factory helpers for constructing eval-domain objects in tests.

The ``make_*`` helpers accept keyword overrides so a test can build a
``Case``, ``TrialResult``, ``CaseOutcome``, ``SuiteResult``, or a complete
eval directory tree with one call.
"""

from __future__ import annotations

import glob
import json
import math
import os
from string import printable
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from outcomeeng_evals.case import Case
from outcomeeng_evals.ci_execution import (
    CiRunSettings,
    DEFAULT_CI_MAX_BUDGET_USD,
    DEFAULT_CI_TIMEOUT_SECONDS,
    DEFAULT_CI_WORKERS,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    UV_RUN_EVALS_ARGV_PREFIX,
    execute_ci_plan,
)
from outcomeeng_evals.ci_plan import (
    ROOT_INSTRUCTION_PATHS,
    CiMode,
    EvalPlanItem,
    build_ci_plan,
    read_changed_paths_file,
)
from outcomeeng_evals.definition import (
    CiPolicy,
    DEFAULT_MODEL,
    DEFAULT_SUITE_THRESHOLD,
    DEFAULT_TRIALS_PER_CASE,
    MAX_TRIALS_PER_CASE,
    OWNED_PATH_ALPHABET,
    OWNED_PATH_RECURSIVE_SUFFIX,
    EvalDefinition,
    load_definition,
)
from outcomeeng_evals.grader import GradeResult
from outcomeeng_evals.history import HistoryRow
from outcomeeng_evals.runner import ModelProcessResult, RunMetadata
from outcomeeng_evals.suite import CaseOutcome, SuiteResult, TrialResult
from outcomeeng_testing.evals.fakes import (
    RecordingCommandRunner,
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
_DEFAULT_EVAL_TITLE = "test-eval"
_DEFAULT_CASES_FILENAME = "cases.jsonl"
_DEFAULT_PROMPT_FILENAME = "prompt.md"
_DEFAULT_EVAL_FILENAME = "eval.toml"
_DEFAULT_EVAL_RULE = "rule"
_DEFAULT_PLUGIN_DIR = Path("dist/claude/spec-tree")
DEFAULT_DEFINITION_THRESHOLD = 0.95
DEFAULT_DEFINITION_TRIALS = 3
DEFAULT_PLAN_CASE_IDS = ("alpha", "beta")
DEFAULT_CI_OWNED_PATH = "src/plugins/spec-tree/skills/manage-pr/**"
DEFAULT_CI_CHANGED_PATH = "src/plugins/spec-tree/skills/manage-pr/SKILL.md"
DEFAULT_CI_CHANGED_PATH_STATUS = "M"
DEFAULT_CI_RENAMED_PATH = "docs/manage-pr.md"
DEFAULT_CI_COPIED_PATH = "docs/copied-suite.py"
DEFAULT_CI_HARNESS_PATH = "outcomeeng_evals/suite.py"
DEFAULT_CI_WHITESPACE_PATH = " docs/has edge spaces.md "
DEFAULT_CI_TABBED_PATH = "docs/plain\tpath.md"
DEFAULT_CI_MALFORMED_STATUS_ROW = "M\tdocs/plain\tpath.md"
DEFAULT_CI_EXPLICIT_MODEL = "claude-sonnet-4-5"


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


@dataclass(frozen=True)
class ChangedPathsFileErrorCase:
    """Harness-owned changed-path file case that must be rejected."""

    content: str


@dataclass(frozen=True)
class CiMetadataDefinitionCase:
    """Harness-owned eval definition case for optional CI metadata."""

    eval_toml: Path
    plugin_dir: Path
    model: str
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
    explicit_model: str
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
        explicit_model=payload["explicit_model"],
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
    plugin_dir: Path = _DEFAULT_PLUGIN_DIR,
    case_ids: tuple[str, ...] = (),
) -> EvalPlanItem:
    return EvalPlanItem(
        eval_toml=Path("spx/node/evals") / rule / _DEFAULT_EVAL_FILENAME,
        plugin_dir=plugin_dir,
        case_ids=case_ids,
    )


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


def assert_changed_paths_file_reads_git_name_status_rows() -> None:
    with TemporaryDirectory() as tmp:
        for index, case in enumerate(make_changed_paths_file_cases()):
            changed_paths_file = Path(tmp) / f"changed-paths-{index}.txt"
            changed_paths_file.write_text(case.content, encoding="utf-8")

            assert read_changed_paths_file(changed_paths_file) == case.expected_paths
        for index, error_case in enumerate(make_changed_paths_file_error_cases()):
            changed_paths_file = Path(tmp) / f"changed-paths-error-{index}.txt"
            changed_paths_file.write_text(error_case.content, encoding="utf-8")

            try:
                read_changed_paths_file(changed_paths_file)
            except ValueError:
                continue
            raise AssertionError(
                f"changed paths file accepted ambiguous input: {error_case.content!r}"
            )


def make_ci_metadata_definition_case(tmp_path: Path) -> CiMetadataDefinitionCase:
    eval_toml = make_eval_dir(
        tmp_path / "eval",
        plugin_dir=str(_DEFAULT_PLUGIN_DIR),
        model=DEFAULT_CI_EXPLICIT_MODEL,
        owned_paths=(DEFAULT_CI_OWNED_PATH,),
        smoke_case_ids=DEFAULT_PLAN_CASE_IDS[:1],
        ci_policy=CiPolicy.MANUAL.value,
    )
    return CiMetadataDefinitionCase(
        eval_toml=eval_toml,
        plugin_dir=_DEFAULT_PLUGIN_DIR,
        model=DEFAULT_CI_EXPLICIT_MODEL,
        owned_paths=(DEFAULT_CI_OWNED_PATH,),
        smoke_case_ids=DEFAULT_PLAN_CASE_IDS[:1],
        ci_policy=CiPolicy.MANUAL,
    )


def _required_eval_lines() -> tuple[str, ...]:
    return (
        f'title = "{_DEFAULT_EVAL_TITLE}"',
        f'cases = "{_DEFAULT_CASES_FILENAME}"',
        f'prompt = "{_DEFAULT_PROMPT_FILENAME}"',
    )


def _write_eval_definition(
    tmp_path: Path,
    *,
    lines: tuple[str, ...] = (),
    with_cases: bool = True,
    with_prompt: bool = True,
) -> Path:
    directory = tmp_path / "eval"
    directory.mkdir(parents=True)
    toml_path = directory / _DEFAULT_EVAL_FILENAME
    toml_path.write_text(
        "\n".join((*_required_eval_lines(), *lines)) + "\n",
        encoding="utf-8",
    )
    if with_cases:
        (directory / _DEFAULT_CASES_FILENAME).write_text("", encoding="utf-8")
    if with_prompt:
        (directory / _DEFAULT_PROMPT_FILENAME).write_text("", encoding="utf-8")
    return toml_path


def _assert_definition_raises(
    *,
    lines: tuple[str, ...],
    match: str,
    with_cases: bool = True,
    with_prompt: bool = True,
) -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(
            Path(tmp),
            lines=lines,
            with_cases=with_cases,
            with_prompt=with_prompt,
        )
        try:
            load_definition(toml_path)
        except (FileNotFoundError, KeyError, ValueError) as exc:
            if match not in str(exc):
                raise AssertionError(
                    f"expected error containing {match!r}, got {exc!r}"
                ) from exc
            return
        raise AssertionError(f"expected load_definition to reject {toml_path}")


def assert_definition_loads_required_fields() -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(Path(tmp))

        definition = load_definition(toml_path)

        assert isinstance(definition, EvalDefinition)
        assert definition.title == _DEFAULT_EVAL_TITLE


def assert_definition_resolves_cases_path_relative_to_toml_directory() -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(Path(tmp))

        definition = load_definition(toml_path)

        assert (
            definition.cases_path
            == (toml_path.parent / _DEFAULT_CASES_FILENAME).resolve()
        )


def assert_definition_resolves_prompt_path_relative_to_toml_directory() -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(Path(tmp))

        definition = load_definition(toml_path)

        assert (
            definition.prompt_template_path
            == (toml_path.parent / _DEFAULT_PROMPT_FILENAME).resolve()
        )


def assert_definition_applies_default_threshold_when_omitted() -> None:
    with TemporaryDirectory() as tmp:
        definition = load_definition(_write_eval_definition(Path(tmp)))

        assert definition.threshold == DEFAULT_SUITE_THRESHOLD


def assert_definition_applies_default_trials_when_omitted() -> None:
    with TemporaryDirectory() as tmp:
        definition = load_definition(_write_eval_definition(Path(tmp)))

        assert definition.trials == DEFAULT_TRIALS_PER_CASE


def assert_definition_applies_default_model_when_omitted() -> None:
    with TemporaryDirectory() as tmp:
        definition = load_definition(_write_eval_definition(Path(tmp)))

        assert definition.model == DEFAULT_MODEL


def assert_definition_uses_explicit_threshold_when_set() -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(
            Path(tmp),
            lines=(f"threshold = {DEFAULT_DEFINITION_THRESHOLD}",),
        )

        definition = load_definition(toml_path)

        assert math.isclose(definition.threshold, DEFAULT_DEFINITION_THRESHOLD)


def assert_definition_uses_explicit_trials_when_set() -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(
            Path(tmp),
            lines=(f"trials = {DEFAULT_DEFINITION_TRIALS}",),
        )

        definition = load_definition(toml_path)

        assert definition.trials == DEFAULT_DEFINITION_TRIALS


def assert_definition_loads_optional_ci_metadata() -> None:
    with TemporaryDirectory() as tmp:
        case = make_ci_metadata_definition_case(Path(tmp))

        definition = load_definition(case.eval_toml)

        assert definition.plugin_dir == case.plugin_dir
        assert definition.model == case.model
        assert definition.owned_paths == case.owned_paths
        assert definition.smoke_case_ids == case.smoke_case_ids
        assert definition.ci_policy is case.ci_policy


def assert_definition_uses_explicit_model_when_set() -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(
            Path(tmp),
            lines=(f'model = "{DEFAULT_CI_EXPLICIT_MODEL}"',),
        )

        definition = load_definition(toml_path)

        assert definition.model == DEFAULT_CI_EXPLICIT_MODEL


def assert_definition_rejects_inherit_model() -> None:
    _assert_definition_raises(lines=('model = "inherit"',), match="model")


def assert_definition_rejects_non_string_model() -> None:
    _assert_definition_raises(lines=("model = 1",), match="model")


def assert_definition_accepts_owned_path_shapes_ci_matches_identically() -> None:
    """Assert an exact path and a trailing recursive glob both load.

    Both shapes are built from the source-owned alphabet and recursive suffix,
    so narrowing either contract reaches this evidence rather than passing
    beside it.
    """

    exact = "AGENTS.md"
    recursive = f"src/plugins/spec-tree/skills/merge{OWNED_PATH_RECURSIVE_SUFFIX}"
    assert OWNED_PATH_ALPHABET.fullmatch(exact)
    assert OWNED_PATH_ALPHABET.fullmatch(
        recursive.removesuffix(OWNED_PATH_RECURSIVE_SUFFIX)
    )

    accepted = (exact, recursive)
    with TemporaryDirectory() as tmp:
        entries = ", ".join(f'"{path}"' for path in accepted)
        toml_path = _write_eval_definition(
            Path(tmp),
            lines=(f"owned_paths = [{entries}]",),
        )

        definition = load_definition(toml_path)

        assert definition.owned_paths == accepted


def assert_owned_path_alphabet_excludes_every_glob_magic_character() -> None:
    """Assert the alphabet excludes every character the stdlib calls glob magic.

    The property evidence proves the loader honors whatever the alphabet says.
    It cannot prove the alphabet says the right thing -- a widened alphabet also
    widens the domain that evidence searches. `glob.has_magic` is an oracle
    outside this module's control, so it pins the contract the alphabet must
    keep: a path carrying a glob character is matched differently by `fnmatch`
    and by the CI provider's engine, and must never reach either.
    """

    magic = tuple(character for character in printable if glob.has_magic(character))
    assert magic

    for character in magic:
        assert OWNED_PATH_ALPHABET.fullmatch(character) is None
        _assert_definition_raises(
            lines=(f'owned_paths = ["src{character}nested"]',),
            match="owned_paths",
        )


def assert_definition_accepts_trials_at_cap() -> None:
    with TemporaryDirectory() as tmp:
        toml_path = _write_eval_definition(
            Path(tmp),
            lines=(f"trials = {MAX_TRIALS_PER_CASE}",),
        )

        definition = load_definition(toml_path)

        assert definition.trials == MAX_TRIALS_PER_CASE


def assert_definition_rejects_trials_above_cap() -> None:
    _assert_definition_raises(
        lines=(f"trials = {MAX_TRIALS_PER_CASE + 1}",),
        match="trials",
    )


def assert_definition_rejects_trials_below_one() -> None:
    _assert_definition_raises(lines=("trials = 0",), match="trials")


def assert_definition_rejects_missing_title() -> None:
    with TemporaryDirectory() as tmp:
        directory = Path(tmp) / "eval"
        directory.mkdir(parents=True)
        toml_path = directory / _DEFAULT_EVAL_FILENAME
        toml_path.write_text(
            (
                f'cases = "{_DEFAULT_CASES_FILENAME}"\n'
                f'prompt = "{_DEFAULT_PROMPT_FILENAME}"\n'
            ),
            encoding="utf-8",
        )
        (directory / _DEFAULT_CASES_FILENAME).write_text("", encoding="utf-8")
        (directory / _DEFAULT_PROMPT_FILENAME).write_text("", encoding="utf-8")

        try:
            load_definition(toml_path)
        except (KeyError, ValueError) as exc:
            if "title" not in str(exc):
                raise AssertionError(f"expected title error, got {exc!r}") from exc
            return
        raise AssertionError(f"expected load_definition to reject {toml_path}")


def assert_definition_rejects_missing_cases() -> None:
    with TemporaryDirectory() as tmp:
        directory = Path(tmp) / "eval"
        directory.mkdir(parents=True)
        toml_path = directory / _DEFAULT_EVAL_FILENAME
        toml_path.write_text(
            (
                f'title = "{_DEFAULT_EVAL_TITLE}"\n'
                f'prompt = "{_DEFAULT_PROMPT_FILENAME}"\n'
            ),
            encoding="utf-8",
        )
        (directory / _DEFAULT_PROMPT_FILENAME).write_text("", encoding="utf-8")

        try:
            load_definition(toml_path)
        except (KeyError, ValueError) as exc:
            if "cases" not in str(exc):
                raise AssertionError(f"expected cases error, got {exc!r}") from exc
            return
        raise AssertionError(f"expected load_definition to reject {toml_path}")


def assert_definition_rejects_missing_prompt() -> None:
    with TemporaryDirectory() as tmp:
        directory = Path(tmp) / "eval"
        directory.mkdir(parents=True)
        toml_path = directory / _DEFAULT_EVAL_FILENAME
        toml_path.write_text(
            (f'title = "{_DEFAULT_EVAL_TITLE}"\ncases = "{_DEFAULT_CASES_FILENAME}"\n'),
            encoding="utf-8",
        )
        (directory / _DEFAULT_CASES_FILENAME).write_text("", encoding="utf-8")

        try:
            load_definition(toml_path)
        except (KeyError, ValueError) as exc:
            if "prompt" not in str(exc):
                raise AssertionError(f"expected prompt error, got {exc!r}") from exc
            return
        raise AssertionError(f"expected load_definition to reject {toml_path}")


def assert_definition_rejects_nonexistent_cases_file() -> None:
    _assert_definition_raises(lines=(), match="cases", with_cases=False)


def assert_definition_rejects_nonexistent_prompt_file() -> None:
    _assert_definition_raises(lines=(), match="prompt", with_prompt=False)


def assert_root_instruction_changes_select_full_suites() -> None:
    with TemporaryDirectory() as tmp:
        eval_toml = make_eval_dir(
            Path(tmp) / "evals" / "rule",
            plugin_dir="dist/claude/spec-tree",
            owned_paths=(DEFAULT_CI_OWNED_PATH,),
            smoke_case_ids=DEFAULT_PLAN_CASE_IDS,
        )

        for root_instruction_path in ROOT_INSTRUCTION_PATHS:
            plan = build_ci_plan(
                eval_toml.parent.parent,
                mode=CiMode.PR,
                changed_paths=(root_instruction_path,),
            )

            assert plan == [
                EvalPlanItem(
                    eval_toml=eval_toml,
                    plugin_dir=_DEFAULT_PLUGIN_DIR,
                    case_ids=(),
                )
            ]


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
    model: str | None = None,
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
    if model is not None:
        lines.append(f'model = "{model}"')
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
