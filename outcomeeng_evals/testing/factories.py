"""Factory helpers for constructing eval-domain objects in tests.

The ``make_*`` helpers accept keyword overrides so a test can build a
``Case``, ``TrialResult``, ``CaseOutcome``, ``SuiteResult``, or a complete
eval directory tree with one call.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from outcomeeng_evals.case import Case
from outcomeeng_evals.grader import GradeResult
from outcomeeng_evals.runner import RunMetadata
from outcomeeng_evals.suite import CaseOutcome, SuiteResult, TrialResult


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
    toml_path = directory / eval_filename
    toml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if with_cases:
        (directory / cases_filename).write_text(cases_content, encoding="utf-8")
    if with_prompt:
        (directory / prompt_filename).write_text(prompt_content, encoding="utf-8")
    return toml_path
