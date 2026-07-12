"""Assertion entrypoints for JSON-first eval-report evidence.

Data and presentation are separated: ``serialize_result`` and
``write_json_report`` produce the authoritative artifact; ``write_run_reports``
adds a thin viewer that reads the same JSON.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.eval_assertions import (
    run_plain,
    run_with_tmp_path,
)

import json
from pathlib import Path

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
from outcomeeng_testing.evals.factories import (
    make_bimodal_cache_suite_result,
    make_report_suite_result,
    make_stability_outcomes,
)


def _impl_serialize_result_carries_schema_version_and_suite_summary() -> None:
    result = make_report_suite_result(passed=True)
    payload = serialize_result(result, title="my-eval", model="claude-sonnet-4-5")

    assert payload["schema_version"] == JSON_SCHEMA_VERSION
    assert payload["title"] == "my-eval"
    assert payload["model"] == "claude-sonnet-4-5"
    assert payload["suite"] == {
        "passed": True,
        "pass_rate": 1.0,
        "threshold": 0.85,
        "cases_total": 1,
        "cases_passed": 1,
    }


def _impl_serialize_result_defaults_to_concrete_model() -> None:
    payload = serialize_result(make_report_suite_result(passed=True), title="my-eval")

    assert payload["model"] == "sonnet"


def _impl_serialize_result_preserves_case_expectations() -> None:
    payload = serialize_result(make_report_suite_result(passed=True), title="t")
    outcome = payload["outcomes"][0]
    assert outcome["case"]["id"] == "c-1"
    assert outcome["case"]["must_contain"] == [{"findings": [{"rule": "r-1"}]}]
    assert outcome["case"]["must_not_contain"] == []


def _impl_serialize_result_includes_trial_transcripts() -> None:
    payload = serialize_result(
        make_report_suite_result(passed=False, reason="missing rule"), title="t"
    )
    trial = payload["outcomes"][0]["trials"][0]
    assert trial["prompt"] == "prompt body"
    assert json.loads(trial["response"]) == {
        "status": "rejected",
        "findings": [{"rule": "r-1", "present": True}],
    }
    assert trial["verdict"] == {
        "status": "rejected",
        "findings": [{"rule": "r-1", "present": True}],
    }
    assert trial["grade"] == {"passed": False, "reasons": ["missing rule"]}


def _impl_serialize_result_is_json_round_trippable() -> None:
    payload = serialize_result(make_report_suite_result(passed=True), title="t")
    text = json.dumps(payload)
    assert json.loads(text) == payload


def _impl_serialize_result_aggregates_cost_summary_across_trials() -> None:
    payload = serialize_result(make_report_suite_result(passed=True), title="t")
    summary = payload["cost_summary"]
    assert summary["trials_total"] == 1
    assert summary["trials_with_metadata"] == 1
    assert summary["total_cost_usd"] == pytest.approx(0.22)
    assert summary["total_duration_ms"] == pytest.approx(2608.0)
    assert summary["total_input_tokens"] == 5
    assert summary["total_output_tokens"] == 6
    assert summary["total_cache_read_input_tokens"] == 18240
    assert summary["total_cache_creation_input_tokens"] == 33830


def _impl_cost_summary_aggregates_cache_tokens_across_trials() -> None:
    summary = serialize_result(make_bimodal_cache_suite_result(), title="t")[
        "cost_summary"
    ]
    assert summary["trials_total"] == 2
    assert summary["trials_with_metadata"] == 2
    assert summary["total_input_tokens"] == 22
    assert summary["total_output_tokens"] == 12
    assert summary["total_cache_read_input_tokens"] == 49600
    assert summary["total_cache_creation_input_tokens"] == 34000


def _impl_serialize_result_carries_per_trial_metadata() -> None:
    payload = serialize_result(make_report_suite_result(passed=True), title="t")
    trial = payload["outcomes"][0]["trials"][0]
    assert trial["metadata"]["duration_ms"] == pytest.approx(2608.0)
    assert trial["metadata"]["stop_reason"] == "end_turn"
    assert trial["metadata"]["total_cost_usd"] == pytest.approx(0.22)


def _impl_cost_summary_skips_trials_without_metadata() -> None:
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


def _impl_cost_summary_counts_cache_only_metadata_trial() -> None:
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


def _impl_write_json_report_writes_file_and_returns_path(tmp_path: Path) -> None:
    target = tmp_path / "out" / "report.json"
    returned = write_json_report(
        make_report_suite_result(passed=True), target, title="t"
    )
    assert returned == target
    assert target.exists()
    parsed = json.loads(target.read_text(encoding="utf-8"))
    assert parsed["suite"]["passed"] is True


def _impl_write_run_reports_emits_html_and_sidecar_json(tmp_path: Path) -> None:
    target = tmp_path / "report.html"
    returned = write_run_reports(
        make_report_suite_result(passed=True),
        target,
        title="my-title",
        model="sonnet",
    )

    assert returned == target
    assert target.exists(), "the HTML viewer must be written at the given path"
    sidecar = target.with_suffix(".json")
    assert sidecar.exists(), "sidecar JSON must be written alongside the HTML"
    sidecar_payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert sidecar_payload["title"] == "my-title"
    assert sidecar_payload["model"] == "sonnet"


def _impl_write_run_reports_embeds_json_payload_in_script_tag(tmp_path: Path) -> None:
    target = tmp_path / "report.html"
    write_run_reports(
        make_report_suite_result(passed=True), target, title="embedded-test"
    )
    html = target.read_text(encoding="utf-8")

    marker = '<script id="eval-results" type="application/json">'
    assert marker in html, "HTML must embed the JSON payload in a script tag"
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    embedded = html[start:end].replace("<\\/", "</")
    parsed = json.loads(embedded)
    assert parsed["title"] == "embedded-test"


def _impl_write_run_reports_renders_no_closing_script_in_body(tmp_path: Path) -> None:
    """The embedded JSON must never contain a bare </script> sequence."""
    result = make_report_suite_result(
        passed=False, reason="says </script> in the reason text"
    )
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


def _impl_trial_stability_for_k1_reports_zero_or_one_pass_rate_per_case() -> None:
    outcomes = make_stability_outcomes((True,), (True,), (False,))
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


def _impl_trial_stability_for_k_greater_than_1_computes_mean() -> None:
    # Case A: 4/4 = 1.0; Case B: 2/4 = 0.5; mean = 0.75.
    outcomes = make_stability_outcomes(
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


def _impl_trial_stability_stddev_is_none_with_single_case() -> None:
    outcomes = make_stability_outcomes((True,))
    result = SuiteResult(outcomes=outcomes, pass_rate=1.0, threshold=0.85, passed=True)
    stability = serialize_result(result, title="t")["trial_stability"]
    assert stability["stddev_trial_pass_rate"] is None


def _impl_outcome_carries_trial_pass_count_and_rate_in_json() -> None:
    outcomes = make_stability_outcomes((True, True, False, False))
    result = SuiteResult(outcomes=outcomes, pass_rate=0.0, threshold=0.85, passed=False)
    payload = serialize_result(result, title="t")
    outcome_json = payload["outcomes"][0]
    assert outcome_json["trial_count"] == 4
    assert outcome_json["trial_pass_count"] == 2
    assert outcome_json["trial_pass_rate"] == pytest.approx(0.5)


def assert_serialize_result_carries_schema_version_and_suite_summary() -> None:
    run_plain(_impl_serialize_result_carries_schema_version_and_suite_summary)


def assert_serialize_result_defaults_to_concrete_model() -> None:
    run_plain(_impl_serialize_result_defaults_to_concrete_model)


def assert_serialize_result_preserves_case_expectations() -> None:
    run_plain(_impl_serialize_result_preserves_case_expectations)


def assert_serialize_result_includes_trial_transcripts() -> None:
    run_plain(_impl_serialize_result_includes_trial_transcripts)


def assert_serialize_result_is_json_round_trippable() -> None:
    run_plain(_impl_serialize_result_is_json_round_trippable)


def assert_serialize_result_aggregates_cost_summary_across_trials() -> None:
    run_plain(_impl_serialize_result_aggregates_cost_summary_across_trials)


def assert_cost_summary_aggregates_cache_tokens_across_trials() -> None:
    run_plain(_impl_cost_summary_aggregates_cache_tokens_across_trials)


def assert_serialize_result_carries_per_trial_metadata() -> None:
    run_plain(_impl_serialize_result_carries_per_trial_metadata)


def assert_cost_summary_skips_trials_without_metadata() -> None:
    run_plain(_impl_cost_summary_skips_trials_without_metadata)


def assert_cost_summary_counts_cache_only_metadata_trial() -> None:
    run_plain(_impl_cost_summary_counts_cache_only_metadata_trial)


def assert_write_json_report_writes_file_and_returns_path() -> None:
    run_with_tmp_path(_impl_write_json_report_writes_file_and_returns_path)


def assert_write_run_reports_emits_html_and_sidecar_json() -> None:
    run_with_tmp_path(_impl_write_run_reports_emits_html_and_sidecar_json)


def assert_write_run_reports_embeds_json_payload_in_script_tag() -> None:
    run_with_tmp_path(_impl_write_run_reports_embeds_json_payload_in_script_tag)


def assert_write_run_reports_renders_no_closing_script_in_body() -> None:
    run_with_tmp_path(_impl_write_run_reports_renders_no_closing_script_in_body)


def assert_trial_stability_for_k1_reports_zero_or_one_pass_rate_per_case() -> None:
    run_plain(_impl_trial_stability_for_k1_reports_zero_or_one_pass_rate_per_case)


def assert_trial_stability_for_k_greater_than_1_computes_mean() -> None:
    run_plain(_impl_trial_stability_for_k_greater_than_1_computes_mean)


def assert_trial_stability_stddev_is_none_with_single_case() -> None:
    run_plain(_impl_trial_stability_stddev_is_none_with_single_case)


def assert_outcome_carries_trial_pass_count_and_rate_in_json() -> None:
    run_plain(_impl_outcome_carries_trial_pass_count_and_rate_in_json)
