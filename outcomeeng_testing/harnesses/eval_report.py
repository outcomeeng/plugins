"""Evidence harness for JSON-first eval reports."""

from __future__ import annotations

import json
import statistics
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from outcomeeng_evals.report import (
    EMBEDDED_RESULTS_SCRIPT_ID,
    EMBEDDED_RESULTS_SCRIPT_TYPE,
    JSON_REPORT_SUFFIX,
    serialize_result,
    write_json_report,
    write_run_reports,
)
from outcomeeng_evals.definition import RUNS_DIRNAME
from outcomeeng_evals.settings import DEFAULT_MAX_BUDGET_USD, DEFAULT_TIMEOUT_SECONDS
from outcomeeng_evals.testing.factories import (
    ReportFixture,
    load_report_fixture,
    make_cache_only_report_suite_result,
    make_metadata_free_report_suite_result,
    make_report_suite_result,
    make_stability_suite_result,
)
from outcomeeng_testing.harnesses.eval_run_exit import (
    configured_ceiling_run,
    configured_threshold_run,
)

_FIXTURE_PATH = Path(__file__).parents[1] / "fixtures/evals/report_suite.json"


class _EmbeddedResultsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_results = False
        self.payload_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self._inside_results = (
            tag == "script"
            and attributes.get("id") == EMBEDDED_RESULTS_SCRIPT_ID
            and attributes.get("type") == EMBEDDED_RESULTS_SCRIPT_TYPE
        )

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._inside_results = False

    def handle_data(self, data: str) -> None:
        if self._inside_results:
            self.payload_parts.append(data)


def assert_report_serialization_matches_fixture_contract() -> None:
    fixture = _fixture()
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
    assert (
        payload["outcomes"][0]["trials"][0]["response"] == (fixture.trial["response"])
    )
    assert payload["outcomes"][0]["trials"][0]["verdict"] == (fixture.trial["verdict"])
    outcome_payload = payload["outcomes"][0]
    outcome = result.outcomes[0]
    assert outcome_payload["trial_pass_count"] == outcome.trial_pass_count
    assert outcome_payload["trial_count"] == len(outcome.trials)
    assert outcome_payload["trial_pass_rate"] == pytest.approx(outcome.trial_pass_rate)
    assert json.loads(json.dumps(payload)) == payload


def assert_report_serialization_preserves_configured_ceilings() -> None:
    fixture = _fixture()

    payload = serialize_result(
        make_report_suite_result(fixture),
        title=fixture.title,
        max_budget_usd=fixture.configured_max_budget_usd,
        timeout_seconds=fixture.configured_timeout_seconds,
    )

    assert payload["max_budget_usd"] == pytest.approx(fixture.configured_max_budget_usd)
    assert payload["timeout_seconds"] == fixture.configured_timeout_seconds


def assert_report_cost_summary_preserves_metadata_absence() -> None:
    fixture = _fixture()

    without_metadata = serialize_result(
        make_metadata_free_report_suite_result(fixture), fixture.title
    )["cost_summary"]
    cache_only = serialize_result(
        make_cache_only_report_suite_result(fixture), fixture.title
    )["cost_summary"]

    assert without_metadata == fixture.expected_without_metadata
    assert cache_only == fixture.expected_cache_only


def assert_report_trial_stability_matches_fixture_patterns() -> None:
    fixture = _fixture()

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


def assert_report_files_match_serialized_payload() -> None:
    fixture = _fixture()

    for assertion in (
        _assert_json_report_file,
        _assert_html_report_and_sidecar,
        _assert_embedded_payload,
        _assert_embedded_payload_escapes_script_close,
    ):
        _run_in_temporary_directory(assertion, fixture)


def assert_run_command_writes_eval_local_json_report() -> None:
    """Drive the run entrypoint and verify its authoritative artifact placement."""

    with configured_threshold_run() as eval_dir:
        runs_dir = eval_dir / RUNS_DIRNAME
        json_reports = tuple(runs_dir.glob(f"*{JSON_REPORT_SUFFIX}"))
        assert len(json_reports) == 1
        assert json_reports[0].parent == runs_dir


def assert_run_command_report_preserves_configured_ceilings() -> None:
    """Drive explicit CLI ceilings through the persisted JSON report."""

    with configured_ceiling_run() as run:
        reports = tuple((run.eval_dir / RUNS_DIRNAME).glob(f"*{JSON_REPORT_SUFFIX}"))
        assert len(reports) == 1
        with reports[0].open(encoding="utf-8") as report_file:
            payload = json.load(report_file)
        assert payload["max_budget_usd"] == pytest.approx(run.max_budget_usd)
        assert payload["timeout_seconds"] == run.timeout_seconds


def _assert_json_report_file(tmp_path: Path, fixture: ReportFixture) -> None:
    target = tmp_path / "reports" / "report.json"
    returned = write_json_report(
        make_report_suite_result(fixture), target, title=fixture.title
    )

    assert returned == target
    with target.open(encoding="utf-8") as report_file:
        payload = json.load(report_file)
    assert payload["title"] == fixture.title


def _assert_html_report_and_sidecar(tmp_path: Path, fixture: ReportFixture) -> None:
    target = tmp_path / "report.html"
    returned = write_run_reports(
        make_report_suite_result(fixture),
        target,
        title=fixture.title,
        model=fixture.model,
    )

    assert returned == target
    assert target.exists()
    sidecar = target.with_suffix(JSON_REPORT_SUFFIX)
    with sidecar.open(encoding="utf-8") as sidecar_file:
        payload = json.load(sidecar_file)
    assert payload["title"] == fixture.title
    assert payload["model"] == fixture.model


def _assert_embedded_payload(tmp_path: Path, fixture: ReportFixture) -> None:
    target = tmp_path / "report.html"
    write_run_reports(make_report_suite_result(fixture), target, title=fixture.title)

    embedded = _embedded_payload(target)
    with target.with_suffix(JSON_REPORT_SUFFIX).open(encoding="utf-8") as sidecar_file:
        sidecar = json.load(sidecar_file)

    assert embedded == sidecar


def _assert_embedded_payload_escapes_script_close(
    tmp_path: Path, fixture: ReportFixture
) -> None:
    target = tmp_path / "report.html"
    write_run_reports(
        make_report_suite_result(fixture, passed=False),
        target,
        title=fixture.title,
    )

    embedded = _embedded_payload(target)

    outcomes = embedded["outcomes"]
    assert isinstance(outcomes, list)
    outcome = outcomes[0]
    assert isinstance(outcome, dict)
    trials = outcome["trials"]
    assert isinstance(trials, list)
    trial = trials[0]
    assert isinstance(trial, dict)
    grade = trial["grade"]
    assert isinstance(grade, dict)
    assert grade["reasons"] == [fixture.failing_reason]


def _embedded_payload(path: Path) -> dict[str, object]:
    parser = _EmbeddedResultsParser()
    with path.open(encoding="utf-8") as html_file:
        parser.feed(html_file.read())
    return json.loads("".join(parser.payload_parts))


def _fixture() -> ReportFixture:
    return load_report_fixture(_FIXTURE_PATH)


def _run_in_temporary_directory(
    assertion: Callable[[Path, ReportFixture], None], fixture: ReportFixture
) -> None:
    with TemporaryDirectory() as tmp:
        assertion(Path(tmp), fixture)
