"""Suite orchestrator: replay cases, run trials, gate on pass rate threshold."""

from __future__ import annotations

import math
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from typing import Any

from outcomeeng_evals.case import Case, load_cases
from outcomeeng_evals.grader import GradeResult, grade, parse_verdict
from outcomeeng_evals.runner import ModelRunner, RunMetadata


PromptBuilder = Callable[[Case], str]


@dataclass(frozen=True)
class TrialResult:
    """Outcome of a single trial of a single case."""

    case_id: str
    trial_index: int
    prompt: str
    response: str
    verdict: Any | None
    grade: GradeResult
    metadata: RunMetadata


@dataclass(frozen=True)
class CaseOutcome:
    """Aggregated result across trials for one case."""

    case: Case
    trials: tuple[TrialResult, ...]
    passed: bool

    @property
    def trial_pass_count(self) -> int:
        return sum(1 for t in self.trials if t.grade.passed)

    @property
    def trial_pass_rate(self) -> float:
        return self.trial_pass_count / len(self.trials) if self.trials else 1.0


@dataclass(frozen=True)
class SuiteResult:
    """Aggregated suite result with pass-rate gating."""

    outcomes: tuple[CaseOutcome, ...]
    pass_rate: float
    threshold: float
    passed: bool


def run_suite(
    cases_path: Path,
    runner: ModelRunner,
    build_prompt: PromptBuilder,
    *,
    trials_per_case: int = 1,
    case_pass_majority: bool = True,
    suite_threshold: float = 0.85,
    workers: int = 1,
) -> SuiteResult:
    """Replay each case through ``runner``, grade trials, return aggregated result.

    ``workers > 1`` parallelizes case execution with a thread pool. Each
    case still runs its ``trials_per_case`` trials sequentially; the pool
    bounds concurrent ``claude`` subprocesses. Output ordering matches the
    case-file order regardless of execution interleaving.
    """
    cases = load_cases(cases_path)
    if workers <= 1:
        outcomes = [
            _run_case(
                case=case,
                runner=runner,
                build_prompt=build_prompt,
                trials=trials_per_case,
                case_pass_majority=case_pass_majority,
            )
            for case in cases
        ]
    else:
        outcomes = _run_cases_parallel(
            cases=cases,
            workers=workers,
            runner=runner,
            build_prompt=build_prompt,
            trials=trials_per_case,
            case_pass_majority=case_pass_majority,
        )
    pass_rate = _pass_rate(outcomes)
    return SuiteResult(
        outcomes=tuple(outcomes),
        pass_rate=pass_rate,
        threshold=suite_threshold,
        passed=pass_rate >= suite_threshold,
    )


def _run_cases_parallel(
    *,
    cases: list[Case],
    workers: int,
    runner: ModelRunner,
    build_prompt: PromptBuilder,
    trials: int,
    case_pass_majority: bool,
) -> list[CaseOutcome]:
    """Run cases concurrently while preserving case-file ordering in outcomes."""
    results: list[CaseOutcome | None] = [None] * len(cases)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _run_case,
                case=case,
                runner=runner,
                build_prompt=build_prompt,
                trials=trials,
                case_pass_majority=case_pass_majority,
            ): index
            for index, case in enumerate(cases)
        }
        for future in futures:
            results[futures[future]] = future.result()
    return [outcome for outcome in results if outcome is not None]


def _run_case(
    *,
    case: Case,
    runner: ModelRunner,
    build_prompt: PromptBuilder,
    trials: int,
    case_pass_majority: bool,
) -> CaseOutcome:
    trial_results: list[TrialResult] = []
    prompt = build_prompt(case)
    for index in range(trials):
        run_result = runner.run(prompt)
        response_text = run_result.text
        trial_results.append(
            TrialResult(
                case_id=case.id,
                trial_index=index,
                prompt=prompt,
                response=response_text,
                verdict=parse_verdict(response_text),
                grade=grade(case, response_text),
                metadata=run_result.metadata,
            )
        )
    passes = sum(1 for t in trial_results if t.grade.passed)
    threshold = math.ceil(trials / 2) if case_pass_majority else trials
    return CaseOutcome(
        case=case,
        trials=tuple(trial_results),
        passed=passes >= threshold,
    )


def _pass_rate(outcomes: list[CaseOutcome]) -> float:
    if not outcomes:
        return 1.0
    passed = sum(1 for o in outcomes if o.passed)
    return passed / len(outcomes)


def format_report(result: SuiteResult) -> str:
    """Format a one-line-per-case report; suitable for CI log capture."""
    lines = [
        f"suite pass_rate={result.pass_rate:.2%} threshold={result.threshold:.2%} "
        f"verdict={'PASS' if result.passed else 'FAIL'}",
    ]
    for outcome in result.outcomes:
        trials_summary = "".join("." if t.grade.passed else "X" for t in outcome.trials)
        case_verdict = "PASS" if outcome.passed else "FAIL"
        lines.append(f"  {outcome.case.id}: [{trials_summary}] {case_verdict}")
        for trial in outcome.trials:
            if not trial.grade.passed:
                for reason in trial.grade.reasons:
                    lines.append(f"      trial {trial.trial_index}: {reason}")
    return "\n".join(lines)
