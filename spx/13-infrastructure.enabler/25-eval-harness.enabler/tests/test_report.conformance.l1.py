"""Conformance tests for the JSON-first eval report.

Data and presentation are separated: ``serialize_result`` and
``write_json_report`` produce the authoritative artifact; ``write_run_reports``
adds a thin viewer that reads the same JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from outcomeeng_evals.case import Case
from outcomeeng_evals.grader import GradeResult
from outcomeeng_evals.report import (
    JSON_SCHEMA_VERSION,
    serialize_result,
    write_run_reports,
    write_json_report,
)
from outcomeeng_evals.runner import RunMetadata
from outcomeeng_evals.suite import CaseOutcome, SuiteResult, TrialResult
from outcomeeng_evals.testing.factories import make_bimodal_cache_suite_result


_RULE = "r-1"
_VERDICT = {"status": "rejected", "findings": [{"rule": _RULE, "present": True}]}
_RESPONSE = json.dumps(_VERDICT)


def _suite_result(*, passed: bool, reason: str | None = None) -> SuiteResult:
    case = Case(
        id="c-1",
        input={"path": "foo.ts", "content": "stub"},
        must_contain=({"findings": [{"rule": _RULE}]},),
        must_not_contain=(),
    )
    trial = TrialResult(
        case_id=case.id,
        trial_index=0,
        prompt="prompt body",
        response=_RESPONSE,
        verdict=_VERDICT,
        grade=GradeResult(passed=passed, reasons=(reason,) if reason else ()),
        metadata=RunMetadata(
            duration_ms=2608.0,
            total_cost_usd=0.22,
            input_tokens=5,
            output_tokens=6,
            cache_read_input_tokens=18240,
            cache_creation_input_tokens=33830,
            num_turns=1,
            stop_reason="end_turn",
        ),
    )
    outcome = CaseOutcome(case=case, trials=(trial,), passed=passed)
    return SuiteResult(
        outcomes=(outcome,),
        pass_rate=1.0 if passed else 0.0,
        threshold=0.85,
        passed=passed,
    )


def test_serialize_result_carries_schema_version_and_suite_summary() -> None:
    result = _suite_result(passed=True)
    payload = serialize_result(result, title="my-eval")

    assert payload["schema_version"] == JSON_SCHEMA_VERSION
    assert payload["title"] == "my-eval"
    assert payload["suite"] == {
        "passed": True,
        "pass_rate": 1.0,
        "threshold": 0.85,
        "cases_total": 1,
        "cases_passed": 1,
    }


def test_serialize_result_preserves_case_expectations() -> None:
    payload = serialize_result(_suite_result(passed=True), title="t")
    outcome = payload["outcomes"][0]
    assert outcome["case"]["id"] == "c-1"
    assert outcome["case"]["must_contain"] == [{"findings": [{"rule": _RULE}]}]
    assert outcome["case"]["must_not_contain"] == []


def test_serialize_result_includes_trial_transcripts() -> None:
    payload = serialize_result(
        _suite_result(passed=False, reason="missing rule"), title="t"
    )
    trial = payload["outcomes"][0]["trials"][0]
    assert trial["prompt"] == "prompt body"
    assert json.loads(trial["response"]) == _VERDICT
    assert trial["verdict"] == _VERDICT
    assert trial["grade"] == {"passed": False, "reasons": ["missing rule"]}


def test_serialize_result_is_json_round_trippable() -> None:
    payload = serialize_result(_suite_result(passed=True), title="t")
    text = json.dumps(payload)
    assert json.loads(text) == payload


def test_serialize_result_aggregates_cost_summary_across_trials() -> None:
    payload = serialize_result(_suite_result(passed=True), title="t")
    summary = payload["cost_summary"]
    assert summary["trials_total"] == 1
    assert summary["trials_with_metadata"] == 1
    assert summary["total_cost_usd"] == pytest.approx(0.22)
    assert summary["total_duration_ms"] == pytest.approx(2608.0)
    assert summary["total_input_tokens"] == 5
    assert summary["total_output_tokens"] == 6
    assert summary["total_cache_read_input_tokens"] == 18240
    assert summary["total_cache_creation_input_tokens"] == 33830


def test_cost_summary_aggregates_cache_tokens_across_trials() -> None:
    summary = serialize_result(make_bimodal_cache_suite_result(), title="t")[
        "cost_summary"
    ]
    assert summary["trials_total"] == 2
    assert summary["trials_with_metadata"] == 2
    assert summary["total_input_tokens"] == 22
    assert summary["total_output_tokens"] == 12
    assert summary["total_cache_read_input_tokens"] == 49600
    assert summary["total_cache_creation_input_tokens"] == 34000


def test_serialize_result_carries_per_trial_metadata() -> None:
    payload = serialize_result(_suite_result(passed=True), title="t")
    trial = payload["outcomes"][0]["trials"][0]
    assert trial["metadata"]["duration_ms"] == pytest.approx(2608.0)
    assert trial["metadata"]["stop_reason"] == "end_turn"
    assert trial["metadata"]["total_cost_usd"] == pytest.approx(0.22)


def test_cost_summary_skips_trials_without_metadata() -> None:
    case = Case(
        id="c",
        input={},
        must_contain=({"status": "rejected"},),
        must_not_contain=(),
    )
    bare_trial = TrialResult(
        case_id="c",
        trial_index=0,
        prompt="p",
        response="r",
        verdict=None,
        grade=GradeResult(passed=True, reasons=()),
        metadata=RunMetadata(),
    )
    outcome = CaseOutcome(case=case, trials=(bare_trial,), passed=True)
    result = SuiteResult(
        outcomes=(outcome,), pass_rate=1.0, threshold=0.85, passed=True
    )

    payload = serialize_result(result, title="t")
    summary = payload["cost_summary"]
    assert summary["trials_total"] == 1
    assert summary["trials_with_metadata"] == 0
    assert summary["total_cost_usd"] is None
    assert summary["total_duration_ms"] is None
    assert summary["total_input_tokens"] is None
    assert summary["total_output_tokens"] is None
    assert summary["total_cache_read_input_tokens"] is None
    assert summary["total_cache_creation_input_tokens"] is None


def test_cost_summary_counts_cache_only_metadata_trial() -> None:
    # A trial carrying only cache tokens — every other metadata field None —
    # must count as having metadata: the skip-guard includes the cache
    # fields, so dropping them from the guard (the boundary this test pins)
    # would wrongly skip a cache-only trial.
    case = Case(
        id="c",
        input={},
        must_contain=({"status": "rejected"},),
        must_not_contain=(),
    )
    cache_only_trial = TrialResult(
        case_id="c",
        trial_index=0,
        prompt="p",
        response="r",
        verdict=None,
        grade=GradeResult(passed=True, reasons=()),
        metadata=RunMetadata(cache_read_input_tokens=49600),
    )
    outcome = CaseOutcome(case=case, trials=(cache_only_trial,), passed=True)
    result = SuiteResult(
        outcomes=(outcome,), pass_rate=1.0, threshold=0.85, passed=True
    )

    summary = serialize_result(result, title="t")["cost_summary"]
    assert summary["trials_with_metadata"] == 1
    assert summary["total_cache_read_input_tokens"] == 49600
    assert summary["total_cost_usd"] is None
    assert summary["total_input_tokens"] is None


def test_write_json_report_writes_file_and_returns_path(tmp_path: Path) -> None:
    target = tmp_path / "out" / "report.json"
    returned = write_json_report(_suite_result(passed=True), target, title="t")
    assert returned == target
    assert target.exists()
    parsed = json.loads(target.read_text(encoding="utf-8"))
    assert parsed["suite"]["passed"] is True


def test_write_run_reports_emits_html_and_sidecar_json(tmp_path: Path) -> None:
    target = tmp_path / "report.html"
    returned = write_run_reports(_suite_result(passed=True), target, title="my-title")

    assert returned == target
    assert target.exists(), "the HTML viewer must be written at the given path"
    sidecar = target.with_suffix(".json")
    assert sidecar.exists(), "sidecar JSON must be written alongside the HTML"
    assert json.loads(sidecar.read_text(encoding="utf-8"))["title"] == "my-title"


def test_write_run_reports_embeds_json_payload_in_script_tag(tmp_path: Path) -> None:
    target = tmp_path / "report.html"
    write_run_reports(_suite_result(passed=True), target, title="embedded-test")
    html = target.read_text(encoding="utf-8")

    marker = '<script id="eval-results" type="application/json">'
    assert marker in html, "HTML must embed the JSON payload in a script tag"
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    embedded = html[start:end].replace("<\\/", "</")
    parsed = json.loads(embedded)
    assert parsed["title"] == "embedded-test"


def test_write_run_reports_renders_no_closing_script_in_body(tmp_path: Path) -> None:
    """The embedded JSON must never contain a bare </script> sequence."""
    result = _suite_result(passed=False, reason="says </script> in the reason text")
    target = tmp_path / "report.html"
    write_run_reports(result, target, title="t")
    html = target.read_text(encoding="utf-8")

    head_end = html.index('<script id="eval-results"')
    body_start = html.index(">", head_end) + 1
    body_end = html.index("</script>", body_start)
    embedded_body = html[body_start:body_end]
    assert "</script>" not in embedded_body, (
        "embedded JSON must escape closing script tags"
    )


def _stability_outcomes(*pass_patterns: tuple[bool, ...]) -> tuple[CaseOutcome, ...]:
    """Build a tuple of CaseOutcomes from per-case pass/fail patterns."""
    case = Case(
        id="c",
        input={},
        must_contain=({"status": "rejected"},),
        must_not_contain=(),
    )
    outcomes: list[CaseOutcome] = []
    for case_index, pattern in enumerate(pass_patterns):
        trials = tuple(
            TrialResult(
                case_id=f"c-{case_index}",
                trial_index=i,
                prompt="p",
                response="r",
                verdict=None,
                grade=GradeResult(passed=p, reasons=()),
                metadata=RunMetadata(),
            )
            for i, p in enumerate(pattern)
        )
        passes = sum(1 for p in pattern if p)
        outcome_passed = passes > len(pattern) / 2
        outcomes.append(CaseOutcome(case=case, trials=trials, passed=outcome_passed))
    return tuple(outcomes)


def test_trial_stability_for_k1_reports_zero_or_one_pass_rate_per_case() -> None:
    outcomes = _stability_outcomes((True,), (True,), (False,))
    result = SuiteResult(
        outcomes=outcomes, pass_rate=2 / 3, threshold=0.85, passed=False
    )
    stability = serialize_result(result, title="t")["trial_stability"]
    assert stability["max_trials_per_case"] == 1
    assert stability["min_trials_per_case"] == 1
    assert stability["mean_trial_pass_rate"] == pytest.approx(2 / 3)
    assert stability["min_trial_pass_rate"] == pytest.approx(0.0)
    assert stability["max_trial_pass_rate"] == pytest.approx(1.0)
    assert stability["stddev_trial_pass_rate"] is not None


def test_trial_stability_for_k_greater_than_1_computes_mean() -> None:
    # Case A: 4/4 = 1.0; Case B: 2/4 = 0.5; mean = 0.75.
    outcomes = _stability_outcomes(
        (True, True, True, True),
        (True, True, False, False),
    )
    result = SuiteResult(outcomes=outcomes, pass_rate=0.5, threshold=0.85, passed=False)
    stability = serialize_result(result, title="t")["trial_stability"]
    assert stability["max_trials_per_case"] == 4
    assert stability["min_trials_per_case"] == 4
    assert stability["mean_trial_pass_rate"] == pytest.approx(0.75)
    assert stability["min_trial_pass_rate"] == pytest.approx(0.5)
    assert stability["max_trial_pass_rate"] == pytest.approx(1.0)


def test_trial_stability_stddev_is_none_with_single_case() -> None:
    outcomes = _stability_outcomes((True,))
    result = SuiteResult(outcomes=outcomes, pass_rate=1.0, threshold=0.85, passed=True)
    stability = serialize_result(result, title="t")["trial_stability"]
    assert stability["stddev_trial_pass_rate"] is None


def test_outcome_carries_trial_pass_count_and_rate_in_json() -> None:
    outcomes = _stability_outcomes((True, True, False, False))
    result = SuiteResult(outcomes=outcomes, pass_rate=0.0, threshold=0.85, passed=False)
    payload = serialize_result(result, title="t")
    outcome_json = payload["outcomes"][0]
    assert outcome_json["trial_count"] == 4
    assert outcome_json["trial_pass_count"] == 2
    assert outcome_json["trial_pass_rate"] == pytest.approx(0.5)


# Unused imports kept off for ruff cleanliness; Any is referenced for clarity.
_ = Any
