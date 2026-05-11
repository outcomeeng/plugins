"""Scenario tests for the eval harness. l1 — no real Claude calls."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from outcomeeng_evals.case import Case, load_cases
from outcomeeng_evals.grader import extract_verdict, grade
from outcomeeng_evals.testing.fakes import StubModelRunner as StubRunner
from outcomeeng_evals.suite import run_suite


def _write_case(tmp_path: Path, record: dict) -> Path:
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return path


def test_load_cases_parses_jsonl_record_with_must_contain(tmp_path: Path) -> None:
    record = {
        "id": "positive-1",
        "input": {"snippet": "x"},
        "expected_verdict": {
            "must_contain": [{"element": "finding", "attributes": {"rule": "r-1"}}],
            "must_not_contain": [],
        },
    }
    cases = load_cases(_write_case(tmp_path, record))
    assert len(cases) == 1
    case = cases[0]
    assert case.id == "positive-1"
    assert case.input == {"snippet": "x"}
    assert case.must_contain[0].element == "finding"
    assert case.must_contain[0].attributes == {"rule": "r-1"}


def test_load_cases_rejects_record_missing_id(tmp_path: Path) -> None:
    bad = {"input": {}, "expected_verdict": {}}
    with pytest.raises(ValueError, match="missing required field 'id'"):
        load_cases(_write_case(tmp_path, bad))


def test_extract_verdict_finds_xml_block_in_prose() -> None:
    msg = 'Some prose first.\n<verdict status="rejected"><finding rule="x"/></verdict>\nMore prose.'
    assert (
        extract_verdict(msg)
        == '<verdict status="rejected"><finding rule="x"/></verdict>'
    )


def test_extract_verdict_returns_none_when_absent() -> None:
    assert extract_verdict("no verdict in here") is None


def test_grade_passes_when_must_contain_element_present() -> None:
    case = _case(must_contain=[("finding", {"rule": "shared-test-owned-constant-bag"})])
    message = '<verdict><finding rule="shared-test-owned-constant-bag"/></verdict>'
    result = grade(case, message)
    assert result.passed
    assert result.reasons == ()


def test_grade_fails_when_required_element_missing() -> None:
    case = _case(must_contain=[("finding", {"rule": "x"})])
    message = '<verdict><finding rule="other"/></verdict>'
    result = grade(case, message)
    assert not result.passed
    assert any("missing required element" in r for r in result.reasons)


def test_grade_fails_when_forbidden_element_present() -> None:
    case = _case(must_not_contain=[("finding", {"rule": "y"})])
    message = '<verdict><finding rule="y"/></verdict>'
    result = grade(case, message)
    assert not result.passed
    assert any("forbidden element present" in r for r in result.reasons)


def test_grade_fails_when_no_verdict_block_in_response() -> None:
    case = _case(must_contain=[("finding", {"rule": "x"})])
    result = grade(case, "the model returned prose only")
    assert not result.passed
    assert any("no <verdict> block" in r for r in result.reasons)


def test_run_suite_passes_when_canned_verdict_matches(tmp_path: Path) -> None:
    record = {
        "id": "positive-1",
        "input": {"snippet": "x"},
        "expected_verdict": {
            "must_contain": [{"element": "finding", "attributes": {"rule": "x"}}]
        },
    }
    cases_path = _write_case(tmp_path, record)
    canned = '<verdict><finding rule="x"/></verdict>'
    result = run_suite(
        cases_path=cases_path,
        runner=StubRunner(response=canned),
        build_prompt=lambda case: "ignored",
    )
    assert result.passed
    assert result.pass_rate == 1.0


def test_run_suite_fails_when_threshold_not_met(tmp_path: Path) -> None:
    records = [
        {
            "id": f"c-{i}",
            "input": {},
            "expected_verdict": {
                "must_contain": [{"element": "finding", "attributes": {"rule": "x"}}]
            },
        }
        for i in range(4)
    ]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    def responder(prompt: str) -> str:
        # Only the prompt that mentions "c-0" gets the matching verdict; rest fail.
        if "c-0" in prompt:
            return '<verdict><finding rule="x"/></verdict>'
        return '<verdict><finding rule="other"/></verdict>'

    result = run_suite(
        cases_path=cases_path,
        runner=StubRunner(responder=responder),
        build_prompt=lambda case: f"case={case.id}",
        suite_threshold=0.85,
    )
    assert not result.passed
    assert result.pass_rate == pytest.approx(0.25)


def test_run_suite_case_passes_under_majority_when_one_trial_fails(
    tmp_path: Path,
) -> None:
    record = {
        "id": "c",
        "input": {},
        "expected_verdict": {
            "must_contain": [{"element": "finding", "attributes": {"rule": "x"}}]
        },
    }
    cases_path = _write_case(tmp_path, record)
    responses = iter(
        [
            '<verdict><finding rule="x"/></verdict>',
            '<verdict><finding rule="x"/></verdict>',
            "no verdict here",
        ]
    )
    runner = StubRunner(responder=lambda _prompt: next(responses))
    result = run_suite(
        cases_path=cases_path,
        runner=runner,
        build_prompt=lambda _case: "p",
        trials_per_case=3,
    )
    assert result.passed
    assert result.outcomes[0].passed


def test_case_outcome_trial_pass_rate_reflects_per_trial_results(
    tmp_path: Path,
) -> None:
    record = {
        "id": "c",
        "input": {},
        "expected_verdict": {
            "must_contain": [{"element": "finding", "attributes": {"rule": "x"}}]
        },
    }
    cases_path = _write_case(tmp_path, record)
    responses = iter(
        [
            '<verdict><finding rule="x"/></verdict>',
            "fail",
            '<verdict><finding rule="x"/></verdict>',
            "fail",
        ]
    )
    runner = StubRunner(responder=lambda _prompt: next(responses))
    result = run_suite(
        cases_path=cases_path,
        runner=runner,
        build_prompt=lambda _case: "p",
        trials_per_case=4,
    )
    outcome = result.outcomes[0]
    assert outcome.trial_pass_count == 2
    assert outcome.trial_pass_rate == pytest.approx(0.5)


def test_run_suite_with_workers_preserves_case_order_when_threads_finish_out_of_order(
    tmp_path: Path,
) -> None:
    import threading
    import time

    records = [
        {
            "id": f"c-{i}",
            "input": {"index": i},
            "expected_verdict": {
                "must_contain": [{"element": "finding", "attributes": {"rule": "x"}}]
            },
        }
        for i in range(6)
    ]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    finish_order: list[str] = []
    lock = threading.Lock()

    def responder(prompt: str) -> str:
        case_id = prompt.split("=", 1)[1]
        # Lower-numbered cases sleep longer so threads finish in reverse order.
        index = int(case_id.split("-", 1)[1])
        time.sleep(0.005 * (6 - index))
        with lock:
            finish_order.append(case_id)
        return '<verdict><finding rule="x"/></verdict>'

    result = run_suite(
        cases_path=cases_path,
        runner=StubRunner(responder=responder),
        build_prompt=lambda case: f"case={case.id}",
        workers=4,
    )
    case_ids = [outcome.case.id for outcome in result.outcomes]
    assert case_ids == [f"c-{i}" for i in range(6)], (
        f"outcomes must follow case-file order; finish_order={finish_order}"
    )
    # Sanity: actual execution order differed from case-file order.
    assert finish_order != case_ids, (
        "test premise: threads should not finish in case order"
    )


def _case(
    *,
    must_contain: list[tuple[str, dict[str, str]]] | None = None,
    must_not_contain: list[tuple[str, dict[str, str]]] | None = None,
) -> Case:
    from outcomeeng_evals.case import ExpectedElement

    def _to(elements: list[tuple[str, dict[str, str]]] | None):
        if not elements:
            return ()
        return tuple(
            ExpectedElement(element=name, attributes=attrs) for name, attrs in elements
        )

    return Case(
        id="t",
        input={},
        must_contain=_to(must_contain),
        must_not_contain=_to(must_not_contain),
    )
