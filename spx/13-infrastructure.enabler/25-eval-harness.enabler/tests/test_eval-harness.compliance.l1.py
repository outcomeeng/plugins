"""Compliance evidence for eval case loading, grading, and suite execution."""

from __future__ import annotations

import json
import subprocess
import time
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from threading import Lock

import pytest

from outcomeeng_evals.case import (
    CASE_ID_FIELD,
    CASE_INPUT_FIELD,
    EXPECTED_VERDICT_FIELD,
    MAX_EXPECTED_LIST_LENGTH,
    MUST_CONTAIN_FIELD,
    MUST_NOT_CONTAIN_FIELD,
    load_cases,
)
from outcomeeng_evals.grader import grade, is_subset, parse_verdict
from outcomeeng_evals.runner import DEFAULT_CLAUDE_BINARY, RunResult
from outcomeeng_evals.settings import DEFAULT_TIMEOUT_SECONDS
from outcomeeng_evals.suite import TIMEOUT_ERROR_PREFIX, run_suite
from outcomeeng_testing.evals.fakes import (
    ConcurrencyTrackingRunner,
    RaisingModelRunner,
    StubModelRunner,
)
from outcomeeng_testing.generators.evals import expected_list_boundary_record
from outcomeeng_testing.harnesses.eval_harness import (
    fixture_json,
    fixture_path,
    fixture_prompt,
    fixture_text,
    render_prompt,
    response_sequences,
    write_jsonl_record,
)


def test_case_loader_matches_complete_fixture() -> None:
    record = fixture_json("eval_case_valid.jsonl")

    cases = load_cases(fixture_path("eval_case_valid.jsonl"))

    assert len(cases) == 1
    case = cases[0]
    assert isinstance(record, dict)
    expected_verdict = record[EXPECTED_VERDICT_FIELD]
    assert case.id == record[CASE_ID_FIELD]
    assert case.input == record[CASE_INPUT_FIELD]
    assert case.must_contain == tuple(expected_verdict[MUST_CONTAIN_FIELD])
    assert case.must_not_contain == tuple(expected_verdict[MUST_NOT_CONTAIN_FIELD])


@pytest.mark.parametrize(
    "fixture_name", ("eval_case_missing_id.jsonl", "eval_case_blank_id.jsonl")
)
def test_case_loader_rejects_invalid_complete_fixtures(fixture_name: str) -> None:
    with pytest.raises(ValueError):
        load_cases(fixture_path(fixture_name))


def test_case_loader_enforces_expected_list_boundary(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    write_jsonl_record(path, expected_list_boundary_record(over_limit=False))
    case = load_cases(path)[0]
    assert len(case.must_contain[0]["findings"]) == MAX_EXPECTED_LIST_LENGTH

    write_jsonl_record(path, expected_list_boundary_record(over_limit=True))
    with pytest.raises(ValueError):
        load_cases(path)


def test_verdict_parser_matches_complete_response_fixtures() -> None:
    expected = fixture_json("verdict_rejected.json")

    assert parse_verdict(fixture_text("verdict_rejected.json")) == expected
    assert parse_verdict(fixture_text("verdict_fenced.md")) == expected
    assert parse_verdict(fixture_text("verdict_fenced_untagged.md")) == expected
    assert parse_verdict(fixture_text("verdict_invalid.txt")) is None


def test_subset_matching_follows_fixture_matrix() -> None:
    cases = fixture_json("subset_cases.json")

    assert isinstance(cases, list)
    for case in cases:
        assert is_subset(case["expected"], case["actual"]) is case["matches"]


def test_grader_uses_fixture_expectations() -> None:
    case = load_cases(fixture_path("eval_case_valid.jsonl"))[0]

    assert grade(case, fixture_text("verdict_rejected.json")).passed
    assert not grade(case, fixture_text("verdict_approved.json")).passed
    assert not grade(case, fixture_text("verdict_invalid.txt")).passed


def test_suite_replays_fixture_cases_and_bounds_trials() -> None:
    case_path = fixture_path("eval_case_valid.jsonl")
    responses = response_sequences()
    majority = iter(responses["majority"])
    result = run_suite(
        cases_path=case_path,
        runner=StubModelRunner(responder=lambda _prompt: next(majority)),
        build_prompt=fixture_prompt,
        trials_per_case=len(responses["majority"]),
    )

    assert result.passed
    assert result.outcomes[0].trial_pass_count == sum(
        parse_verdict(response) is not None for response in responses["majority"]
    )

    below_majority = iter(responses["below_majority"])
    result = run_suite(
        cases_path=case_path,
        runner=StubModelRunner(responder=lambda _prompt: next(below_majority)),
        build_prompt=fixture_prompt,
        trials_per_case=len(responses["below_majority"]),
    )
    assert not result.outcomes[0].passed

    half_passed = iter(responses["half_passed"])
    result = run_suite(
        cases_path=case_path,
        runner=StubModelRunner(responder=lambda _prompt: next(half_passed)),
        build_prompt=fixture_prompt,
        trials_per_case=len(responses["half_passed"]),
    )
    assert result.outcomes[0].trial_pass_rate == pytest.approx(
        sum(
            parse_verdict(response) is not None for response in responses["half_passed"]
        )
        / len(responses["half_passed"])
    )


def test_parallel_suite_preserves_fixture_case_order() -> None:
    cases_path = fixture_path("eval_suite_cases.jsonl")
    cases = load_cases(cases_path)
    response = fixture_text("verdict_rejected.json")
    finish_order: list[str] = []
    lock = Lock()

    def responder(prompt: str) -> str:
        index = json.loads(prompt)["index"]
        time.sleep(0.001 * (len(cases) - index))
        with lock:
            finish_order.append(cases[index].id)
        return response

    result = run_suite(
        cases_path=cases_path,
        runner=StubModelRunner(responder=responder),
        build_prompt=lambda case: json.dumps(case.input),
        workers=len(cases),
    )

    case_order = [case.id for case in cases]
    assert [outcome.case.id for outcome in result.outcomes] == case_order
    assert finish_order != case_order

    parallel_config = fixture_json("parallel_execution.json")
    assert isinstance(parallel_config, dict)
    tracking_runner = ConcurrencyTrackingRunner(
        result=RunResult(text=response),
        delay_seconds=parallel_config["delay_seconds"],
    )
    run_suite(
        cases_path=cases_path,
        runner=tracking_runner,
        build_prompt=fixture_prompt,
        workers=parallel_config["workers"],
    )
    assert tracking_runner.max_active_calls > 1
    assert tracking_runner.max_active_calls <= parallel_config["workers"]


def test_prompt_renderer_reports_fixture_placeholder_drift() -> None:
    case = load_cases(fixture_path("eval_case_valid.jsonl"))[0]
    collision_case = load_cases(fixture_path("eval_case_placeholder_collision.jsonl"))[
        0
    ]

    unknown_stderr = StringIO()
    with redirect_stderr(unknown_stderr):
        unknown_rendered = render_prompt(
            fixture_text("prompt_unknown_placeholder.md"), case
        )
    known_stderr = StringIO()
    with redirect_stderr(known_stderr):
        known_rendered = render_prompt(
            fixture_text("prompt_known_placeholders.md"), collision_case
        )

    assert unknown_rendered == fixture_text("prompt_unknown_rendered.md")
    assert known_rendered == fixture_text("prompt_known_rendered.txt")
    assert unknown_stderr.getvalue()
    assert not known_stderr.getvalue()


def test_suite_isolates_runner_failures() -> None:
    cases_path = fixture_path("eval_suite_cases.jsonl")
    errors = (
        RuntimeError(fixture_text("verdict_invalid.txt").strip()),
        subprocess.TimeoutExpired(
            cmd=DEFAULT_CLAUDE_BINARY,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        ),
    )

    for error in errors:
        for workers in (1, len(load_cases(cases_path))):
            result = run_suite(
                cases_path=cases_path,
                runner=RaisingModelRunner(error=error),
                build_prompt=fixture_prompt,
                workers=workers,
            )
            assert not result.passed
            assert all(not outcome.passed for outcome in result.outcomes)
            reasons = [
                reason
                for outcome in result.outcomes
                for trial in outcome.trials
                for reason in trial.grade.reasons
            ]
            if isinstance(error, subprocess.TimeoutExpired):
                assert all(
                    reason.startswith(TIMEOUT_ERROR_PREFIX) for reason in reasons
                )


def test_suite_rejects_empty_case_file(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.touch()

    with pytest.raises(ValueError):
        run_suite(
            cases_path=path,
            runner=StubModelRunner(),
            build_prompt=fixture_prompt,
        )
