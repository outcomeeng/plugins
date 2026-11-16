"""Compliance evidence for JSON-first eval reports."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest

from outcomeeng_evals.definition import RUNS_DIRNAME
from outcomeeng_evals.report import (
    JSON_REPORT_SUFFIX,
    serialize_result,
    write_json_report,
    write_run_reports,
)
from outcomeeng_evals.settings import DEFAULT_MAX_BUDGET_USD, DEFAULT_TIMEOUT_SECONDS
from outcomeeng_testing.evals.factories import (
    make_cache_only_report_suite_result,
    make_metadata_free_report_suite_result,
    make_report_suite_result,
    make_stability_suite_result,
)
from outcomeeng_testing.harnesses.eval_report import (
    embedded_payload,
    read_json_object,
    report_fixture,
)
from outcomeeng_testing.harnesses.eval_run_exit import (
    configured_ceiling_run,
    configured_threshold_run,
)


def test_report_serialization_matches_fixture_contract() -> None:
    fixture = report_fixture()
    result = make_report_suite_result(fixture)

    payload = serialize_result(result, title=fixture.title, model=fixture.model)

    assert payload["title"] == fixture.title
    assert payload["model"] == fixture.model
    assert payload["max_budget_usd"] == pytest.approx(DEFAULT_MAX_BUDGET_USD)
    assert payload["timeout_seconds"] == DEFAULT_TIMEOUT_SECONDS
    for field, expected in fixture.expected_report.items():
        assert payload[field] == expected
    assert payload["outcomes"][0]["case"] == {
        "id": fixture.case.id,
        "input": fixture.case.input,
        "must_contain": list(fixture.case.must_contain),
        "must_not_contain": list(fixture.case.must_not_contain),
    }
    assert payload["outcomes"][0]["trials"][0]["response"] == fixture.trial["response"]
    assert payload["outcomes"][0]["trials"][0]["verdict"] == fixture.trial["verdict"]
    outcome_payload = payload["outcomes"][0]
    outcome = result.outcomes[0]
    assert outcome_payload["trial_pass_count"] == outcome.trial_pass_count
    assert outcome_payload["trial_count"] == len(outcome.trials)
    assert outcome_payload["trial_pass_rate"] == pytest.approx(outcome.trial_pass_rate)
    assert json.loads(json.dumps(payload)) == payload


def test_report_serialization_preserves_configured_ceilings() -> None:
    fixture = report_fixture()

    payload = serialize_result(
        make_report_suite_result(fixture),
        title=fixture.title,
        max_budget_usd=fixture.configured_max_budget_usd,
        timeout_seconds=fixture.configured_timeout_seconds,
    )

    assert payload["max_budget_usd"] == pytest.approx(fixture.configured_max_budget_usd)
    assert payload["timeout_seconds"] == fixture.configured_timeout_seconds


def test_report_cost_summary_preserves_metadata_absence() -> None:
    fixture = report_fixture()

    without_metadata = serialize_result(
        make_metadata_free_report_suite_result(fixture), fixture.title
    )["cost_summary"]
    cache_only = serialize_result(
        make_cache_only_report_suite_result(fixture), fixture.title
    )["cost_summary"]

    assert without_metadata == fixture.expected_without_metadata
    assert cache_only == fixture.expected_cache_only


def test_report_trial_stability_matches_fixture_patterns() -> None:
    fixture = report_fixture()

    for patterns in fixture.stability.values():
        result = make_stability_suite_result(fixture, patterns)
        stability = serialize_result(result, fixture.title)["trial_stability"]
        rates = [sum(pattern) / len(pattern) for pattern in patterns]

        assert stability["max_trials_per_case"] == max(map(len, patterns))
        assert stability["min_trials_per_case"] == min(map(len, patterns))
        assert stability["mean_trial_pass_rate"] == pytest.approx(
            statistics.fmean(rates)
        )
        assert stability["min_trial_pass_rate"] == pytest.approx(min(rates))
        assert stability["max_trial_pass_rate"] == pytest.approx(max(rates))
        expected_stddev = statistics.stdev(rates) if len(rates) > 1 else None
        if expected_stddev is None:
            assert stability["stddev_trial_pass_rate"] is None
        else:
            assert stability["stddev_trial_pass_rate"] == pytest.approx(expected_stddev)


def test_json_report_file_carries_the_serialized_payload(tmp_path: Path) -> None:
    fixture = report_fixture()
    target = tmp_path / "reports" / "report.json"

    returned = write_json_report(
        make_report_suite_result(fixture), target, title=fixture.title
    )

    assert returned == target
    assert read_json_object(target)["title"] == fixture.title


def test_html_report_writes_a_json_sidecar(tmp_path: Path) -> None:
    fixture = report_fixture()
    target = tmp_path / "report.html"

    returned = write_run_reports(
        make_report_suite_result(fixture),
        target,
        title=fixture.title,
        model=fixture.model,
    )

    assert returned == target
    assert target.exists()
    payload = read_json_object(target.with_suffix(JSON_REPORT_SUFFIX))
    assert payload["title"] == fixture.title
    assert payload["model"] == fixture.model


def test_html_embedded_payload_equals_the_json_sidecar(tmp_path: Path) -> None:
    fixture = report_fixture()
    target = tmp_path / "report.html"
    write_run_reports(make_report_suite_result(fixture), target, title=fixture.title)

    assert embedded_payload(target) == read_json_object(
        target.with_suffix(JSON_REPORT_SUFFIX)
    )


def test_html_embedded_payload_survives_script_close_in_a_grade_reason(
    tmp_path: Path,
) -> None:
    fixture = report_fixture()
    target = tmp_path / "report.html"
    write_run_reports(
        make_report_suite_result(fixture, passed=False),
        target,
        title=fixture.title,
    )

    outcomes = embedded_payload(target)["outcomes"]

    assert isinstance(outcomes, list)
    trial = outcomes[0]["trials"][0]
    assert trial["grade"]["reasons"] == [fixture.failing_reason]


def test_run_command_writes_the_json_report_in_the_eval_runs_directory() -> None:
    with configured_threshold_run() as eval_dir:
        runs_dir = eval_dir / RUNS_DIRNAME
        json_reports = tuple(runs_dir.glob(f"*{JSON_REPORT_SUFFIX}"))

        assert len(json_reports) == 1
        assert json_reports[0].parent == runs_dir


def test_run_command_report_records_the_configured_ceilings() -> None:
    with configured_ceiling_run() as run:
        reports = tuple((run.eval_dir / RUNS_DIRNAME).glob(f"*{JSON_REPORT_SUFFIX}"))

        assert len(reports) == 1
        payload = read_json_object(reports[0])
        assert payload["max_budget_usd"] == pytest.approx(run.max_budget_usd)
        assert payload["timeout_seconds"] == run.timeout_seconds
