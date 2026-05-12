"""Suite orchestrator: replay cases, run trials, gate on pass rate threshold."""

from __future__ import annotations

import math
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        # Mirror ``_pass_rate``: an empty trial set is a misconfiguration,
        # not a passing case. Return 0.0 so an empty CaseOutcome cannot
        # silently report 100%. (The previous 1.0 fallback was optimistic
        # and asymmetric with ``_pass_rate`` raising ValueError.)
        if not self.trials:
            return 0.0
        return self.trial_pass_count / len(self.trials)


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
    suite_threshold: float = 0.85,
    workers: int = 1,
) -> SuiteResult:
    """Replay each case through ``runner``, grade trials, return aggregated result.

    ``workers > 1`` parallelizes case execution with a thread pool. Each
    case still runs its ``trials_per_case`` trials sequentially; the pool
    bounds concurrent ``claude`` subprocesses. Output ordering matches the
    case-file order regardless of execution interleaving.

    ``workers`` is not capped here — the ``run`` CLI clamps it to 16 to
    prevent fork bursts against the Claude API; direct callers are
    responsible for keeping it within sane bounds.

    Per-case pass policy is majority-of-trials (``ceil(trials_per_case / 2)``).
    """
    cases = load_cases(cases_path)
    if workers <= 1:
        outcomes = [
            _safe_run_case(
                case=case,
                runner=runner,
                build_prompt=build_prompt,
                trials=trials_per_case,
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
        )
    pass_rate = _pass_rate(outcomes)
    return SuiteResult(
        outcomes=tuple(outcomes),
        pass_rate=pass_rate,
        threshold=suite_threshold,
        passed=pass_rate >= suite_threshold,
    )


def _safe_run_case(
    *,
    case: Case,
    runner: ModelRunner,
    build_prompt: PromptBuilder,
    trials: int,
) -> CaseOutcome:
    """Run one case, converting any runner failure into a failing outcome.

    Both the serial and the parallel execution path route through here, so
    a ``claude`` non-zero exit or a ``subprocess.TimeoutExpired`` produces
    one FAIL trial and the suite continues — the same fault-isolation
    guarantee regardless of ``workers``. Without this, a single runner
    exception on ``workers <= 1`` aborts the whole run and writes nothing
    to ``history.jsonl``, while the same exception on ``workers >= 2`` is
    already caught here.
    """
    try:
        return _run_case(
            case=case, runner=runner, build_prompt=build_prompt, trials=trials
        )
    except Exception as exc:  # noqa: BLE001 — convert any runner failure into a failing outcome
        return _error_outcome(case=case, error=exc)


def _run_cases_parallel(
    *,
    cases: list[Case],
    workers: int,
    runner: ModelRunner,
    build_prompt: PromptBuilder,
    trials: int,
) -> list[CaseOutcome]:
    """Run cases concurrently while preserving case-file ordering in outcomes."""
    results: list[CaseOutcome | None] = [None] * len(cases)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _safe_run_case,
                case=case,
                runner=runner,
                build_prompt=build_prompt,
                trials=trials,
            ): index
            for index, case in enumerate(cases)
        }
        # Drain completions as they arrive so a slow case at submission-
        # order index 0 does not block reads from faster cases that
        # finished behind it. Outcome order is still preserved by writing
        # to ``results[index]`` rather than appending.
        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:  # noqa: BLE001 — runner failures are already converted by _safe_run_case; this catches an executor-level failure (e.g. a broken thread pool)
                results[index] = _error_outcome(case=cases[index], error=exc)
    # Every future writes its slot (via ``future.result()`` or
    # ``_error_outcome``), so an unfilled slot is unreachable. Fail loudly
    # rather than silently returning fewer outcomes than cases — a dropped
    # ``None`` would look like a missing case with no traceable cause.
    unfilled = [index for index, outcome in enumerate(results) if outcome is None]
    if unfilled:
        msg = (
            f"parallel runner left case indices {unfilled} unfilled — unreachable: "
            "every future writes its slot via future.result() or _error_outcome()"
        )
        raise AssertionError(msg)
    return [outcome for outcome in results if outcome is not None]


def _error_outcome(*, case: Case, error: BaseException) -> CaseOutcome:
    """Convert a runner exception into a single failing trial result.

    Preserves the case in outcome order so neither execution path unwinds
    the entire suite when one case's runner raises. The error message
    appears in the trial's response field and as the grade reason; downstream
    consumers (JSON report, HTML viewer, history row) see one FAIL trial.

    Tags timeout errors with a ``[timeout]`` prefix so the report can
    distinguish a slow-runner failure from a substantive grading failure
    at a glance — same trial schema, recognizable reason prefix.
    """
    tag = "[timeout] " if isinstance(error, subprocess.TimeoutExpired) else ""
    error_text = f"{tag}{type(error).__name__}: {error}"
    failing_trial = TrialResult(
        case_id=case.id,
        trial_index=0,
        prompt="",
        response=error_text,
        verdict=None,
        grade=GradeResult(passed=False, reasons=(error_text,)),
        metadata=RunMetadata(),
    )
    return CaseOutcome(case=case, trials=(failing_trial,), passed=False)


def _run_case(
    *,
    case: Case,
    runner: ModelRunner,
    build_prompt: PromptBuilder,
    trials: int,
) -> CaseOutcome:
    trial_results: list[TrialResult] = []
    # One rendered prompt for the whole case: every trial of a case sends
    # the same prompt. ("One prompt per trial" would also be defensible —
    # e.g. for templates injecting a timestamp — but the eval contract is a
    # deterministic prompt per case, so pass@k measures model variance, not
    # prompt variance.)
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
    threshold = math.ceil(trials / 2)
    return CaseOutcome(
        case=case,
        trials=tuple(trial_results),
        passed=passes >= threshold,
    )


def _pass_rate(outcomes: list[CaseOutcome]) -> float:
    if not outcomes:
        raise ValueError(
            "no outcomes produced; cases.jsonl may be empty or misconfigured"
        )
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
