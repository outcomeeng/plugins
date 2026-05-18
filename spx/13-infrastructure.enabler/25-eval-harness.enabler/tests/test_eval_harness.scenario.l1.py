"""Scenario tests for the eval harness. l1 — no real Claude calls."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from outcomeeng_evals.case import MAX_EXPECTED_LIST_LENGTH, Case, load_cases
from outcomeeng_evals.cli.commands.run import _render_prompt
from outcomeeng_evals.grader import grade, is_subset, parse_verdict
from outcomeeng_evals.suite import run_suite
from outcomeeng_evals.testing.fakes import RaisingModelRunner
from outcomeeng_evals.testing.fakes import StubModelRunner as StubRunner


_RULE = "shared-test-owned-constant-bag"
# Stand-ins for the two exceptions ClaudeCliRunner.run can surface — a
# non-zero ``claude`` exit (RuntimeError) and a per-invocation timeout.
_RUNNER_NONZERO_EXIT = RuntimeError("claude exited 2: boom")
_RUNNER_TIMEOUT = subprocess.TimeoutExpired(cmd="claude", timeout=120.0)
_PASS_VERDICT = json.dumps(
    {"status": "rejected", "findings": [{"rule": _RULE, "present": True}]}
)
_FAIL_VERDICT = json.dumps({"status": "approved", "findings": []})
_INVALID_JSON = "the model returned prose only"


def _write_case(tmp_path: Path, record: dict[str, Any]) -> Path:
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return path


def test_load_cases_parses_jsonl_record_with_must_contain(tmp_path: Path) -> None:
    record = {
        "id": "positive-1",
        "input": {"snippet": "x"},
        "expected_verdict": {
            "must_contain": [{"findings": [{"rule": "r-1"}]}],
            "must_not_contain": [],
        },
    }
    cases = load_cases(_write_case(tmp_path, record))
    assert len(cases) == 1
    case = cases[0]
    assert case.id == "positive-1"
    assert case.input == {"snippet": "x"}
    assert case.must_contain[0] == {"findings": [{"rule": "r-1"}]}


def test_load_cases_rejects_record_missing_id(tmp_path: Path) -> None:
    bad: dict[str, Any] = {"input": {}, "expected_verdict": {}}
    with pytest.raises(ValueError, match="missing required field 'id'"):
        load_cases(_write_case(tmp_path, bad))


def test_load_cases_rejects_blank_id(tmp_path: Path) -> None:
    bad: dict[str, Any] = {"id": "", "input": {}, "expected_verdict": {}}
    with pytest.raises(ValueError, match="'id'"):
        load_cases(_write_case(tmp_path, bad))


def test_load_cases_accepts_expected_list_at_cap(tmp_path: Path) -> None:
    record = {
        "id": "at-cap",
        "input": {},
        "expected_verdict": {
            "must_contain": [
                {
                    "findings": [
                        {"rule": f"r-{i}"} for i in range(MAX_EXPECTED_LIST_LENGTH)
                    ]
                }
            ]
        },
    }
    cases = load_cases(_write_case(tmp_path, record))
    assert len(cases[0].must_contain[0]["findings"]) == MAX_EXPECTED_LIST_LENGTH


def test_load_cases_rejects_oversized_expected_list(tmp_path: Path) -> None:
    record = {
        "id": "over-cap",
        "input": {},
        "expected_verdict": {
            "must_contain": [
                {
                    "findings": [
                        {"rule": f"r-{i}"} for i in range(MAX_EXPECTED_LIST_LENGTH + 1)
                    ]
                }
            ]
        },
    }
    with pytest.raises(ValueError, match="must_contain"):
        load_cases(_write_case(tmp_path, record))


def test_parse_verdict_returns_parsed_json_document() -> None:
    msg = '{"status":"rejected","findings":[{"rule":"x","present":true}]}'
    assert parse_verdict(msg) == {
        "status": "rejected",
        "findings": [{"rule": "x", "present": True}],
    }


def test_parse_verdict_tolerates_surrounding_whitespace() -> None:
    msg = '  \n{"status":"approved"}\n  '
    assert parse_verdict(msg) == {"status": "approved"}


def test_parse_verdict_returns_none_when_response_is_not_json() -> None:
    assert parse_verdict(_INVALID_JSON) is None


def test_is_subset_matches_dict_keys_recursively() -> None:
    assert is_subset({"status": "rejected"}, {"status": "rejected", "findings": []})


def test_is_subset_rejects_when_dict_key_missing() -> None:
    assert not is_subset({"status": "rejected"}, {"findings": []})


def test_is_subset_matches_list_element_via_any_match() -> None:
    expected = {"findings": [{"rule": "x"}]}
    actual = {"findings": [{"rule": "other"}, {"rule": "x", "present": True}]}
    assert is_subset(expected, actual)


def test_is_subset_rejects_when_no_list_element_matches() -> None:
    expected = {"findings": [{"rule": "x"}]}
    actual = {"findings": [{"rule": "other"}]}
    assert not is_subset(expected, actual)


def test_is_subset_list_matching_is_cardinality_aware() -> None:
    # Multiset semantics: two expected occurrences need two distinct
    # actual matches. A single actual element cannot satisfy two
    # expected entries via any-match.
    expected = {"findings": [{"rule": "x"}, {"rule": "x"}]}
    actual_one = {"findings": [{"rule": "x", "present": True}]}
    actual_two = {
        "findings": [{"rule": "x", "present": True}, {"rule": "x", "present": False}]
    }
    assert not is_subset(expected, actual_one)
    assert is_subset(expected, actual_two)


def test_is_subset_string_sentinel_matches_any_string() -> None:
    assert is_subset({"action": "#string"}, {"action": "Add a null check"})
    assert is_subset({"action": "#string"}, {"action": ""})


def test_is_subset_string_sentinel_rejects_non_string() -> None:
    assert not is_subset({"action": "#string"}, {"action": None})
    assert not is_subset({"action": "#string"}, {"action": 42})
    assert not is_subset({"action": "#string"}, {"action": ["a"]})
    assert not is_subset({"action": "#string"}, {"action": {"k": "v"}})
    assert not is_subset({"action": "#string"}, {"action": True})


def test_is_subset_notnull_sentinel_matches_any_non_null() -> None:
    assert is_subset({"action": "#notnull"}, {"action": "x"})
    assert is_subset({"action": "#notnull"}, {"action": ""})
    assert is_subset({"action": "#notnull"}, {"action": 0})
    assert is_subset({"action": "#notnull"}, {"action": False})
    assert is_subset({"action": "#notnull"}, {"action": []})
    assert is_subset({"action": "#notnull"}, {"action": {}})


def test_is_subset_notnull_sentinel_rejects_null() -> None:
    assert not is_subset({"action": "#notnull"}, {"action": None})


def test_is_subset_present_sentinel_matches_any_value_including_null() -> None:
    assert is_subset({"action": "#present"}, {"action": "x"})
    assert is_subset({"action": "#present"}, {"action": None})
    assert is_subset({"action": "#present"}, {"action": 0})
    assert is_subset({"action": "#present"}, {"action": []})


def test_is_subset_present_sentinel_rejects_when_key_missing() -> None:
    # Dict-level "key must exist" check happens BEFORE is_subset is
    # invoked on the value, so a missing key fails regardless of the
    # sentinel that would have matched the value.
    assert not is_subset({"action": "#present"}, {})


def test_is_subset_sentinel_only_applies_at_expected_position() -> None:
    # Sentinels are an expected-side convention. The dispatch keys on
    # `expected`, so a non-sentinel expected string is compared by
    # equality regardless of actual. When expected is `#string` and
    # actual happens to equal the literal `#string`, the sentinel
    # matcher still fires (because actual is a string) — the result is
    # the same as equality would yield, but the path is the matcher.
    assert is_subset({"action": "#string"}, {"action": "#string"})
    assert is_subset({"action": "#string"}, {"action": "other"})


def test_is_subset_sentinel_used_with_coupled_finding_attributes() -> None:
    # The wider eval-harness rule requires every sentinel be paired with
    # a coupled discriminator. Verify the combined shape still works:
    # severity + concern carry the discrimination; action only checks
    # type, not value.
    expected = {
        "findings": [
            {"severity": "blocking", "concern": "consistency", "action": "#string"}
        ]
    }
    actual_match = {
        "findings": [
            {
                "severity": "blocking",
                "concern": "consistency",
                "action": "Add a null check before the dereference",
                "rule": "spx/.../rule:1",
            }
        ]
    }
    actual_no_action = {
        "findings": [
            {"severity": "blocking", "concern": "consistency", "rule": "spx/.../rule:1"}
        ]
    }
    actual_wrong_severity = {
        "findings": [{"severity": "follow_up", "concern": "consistency", "action": "x"}]
    }
    assert is_subset(expected, actual_match)
    assert not is_subset(expected, actual_no_action)
    assert not is_subset(expected, actual_wrong_severity)


def test_grade_passes_when_must_contain_subset_matches() -> None:
    case = _case(
        must_contain=[
            {"status": "rejected", "findings": [{"rule": _RULE, "present": True}]}
        ]
    )
    result = grade(case, _PASS_VERDICT)
    assert result.passed
    assert result.reasons == ()


def test_grade_fails_when_required_structure_missing() -> None:
    case = _case(must_contain=[{"findings": [{"rule": "x"}]}])
    result = grade(case, _FAIL_VERDICT)
    assert not result.passed
    assert any("missing required structure" in r for r in result.reasons)


def test_grade_fails_when_forbidden_structure_present() -> None:
    case = _case(must_not_contain=[{"status": "approved"}])
    result = grade(case, _FAIL_VERDICT)
    assert not result.passed
    assert any("forbidden structure present" in r for r in result.reasons)


def test_grade_fails_when_response_is_not_parseable_json() -> None:
    case = _case(must_contain=[{"status": "rejected"}])
    result = grade(case, _INVALID_JSON)
    assert not result.passed
    assert any("not a parseable JSON document" in r for r in result.reasons)


def test_run_suite_passes_when_canned_verdict_matches(tmp_path: Path) -> None:
    record = {
        "id": "positive-1",
        "input": {"snippet": "x"},
        "expected_verdict": {
            "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
        },
    }
    cases_path = _write_case(tmp_path, record)
    canned = json.dumps(
        {"status": "rejected", "findings": [{"rule": "x", "present": True}]}
    )
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
                "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
            },
        }
        for i in range(4)
    ]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    matching = json.dumps(
        {"status": "rejected", "findings": [{"rule": "x", "present": True}]}
    )
    nonmatching = json.dumps({"status": "approved", "findings": []})

    def responder(prompt: str) -> str:
        return matching if "c-0" in prompt else nonmatching

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
            "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
        },
    }
    cases_path = _write_case(tmp_path, record)
    matching = json.dumps(
        {"status": "rejected", "findings": [{"rule": "x", "present": True}]}
    )
    responses = iter([matching, matching, "no verdict here"])
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
            "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
        },
    }
    cases_path = _write_case(tmp_path, record)
    matching = json.dumps(
        {"status": "rejected", "findings": [{"rule": "x", "present": True}]}
    )
    responses = iter([matching, "fail", matching, "fail"])
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
                "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
            },
        }
        for i in range(6)
    ]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    finish_order: list[str] = []
    lock = threading.Lock()
    matching = json.dumps(
        {"status": "rejected", "findings": [{"rule": "x", "present": True}]}
    )

    def responder(prompt: str) -> str:
        case_id = prompt.split("=", 1)[1]
        index = int(case_id.split("-", 1)[1])
        time.sleep(0.005 * (6 - index))
        with lock:
            finish_order.append(case_id)
        return matching

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
    assert finish_order != case_ids, (
        "test premise: threads should not finish in case order"
    )


def test_render_prompt_warns_on_unrecognized_placeholder(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rendered = _render_prompt("before {input_jsn} after", _case())

    assert "{input_jsn}" in rendered  # passed through as literal text
    err = capsys.readouterr().err
    assert "input_jsn" in err
    assert "unrecognized placeholder" in err


def test_render_prompt_does_not_warn_on_known_placeholder_or_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rendered = _render_prompt(
        'case={case_id} payload={input_json} sample={"k": 1}', _case()
    )

    assert "case=t" in rendered
    assert capsys.readouterr().err == ""


def _trivial_record(case_id: str) -> dict[str, Any]:
    return {
        "id": case_id,
        "input": {},
        "expected_verdict": {"must_contain": [{"status": "rejected"}]},
    }


def test_run_suite_serial_isolates_runner_failure_as_fail_outcome(
    tmp_path: Path,
) -> None:
    cases_path = _write_case(tmp_path, _trivial_record("c-1"))

    result = run_suite(
        cases_path=cases_path,
        runner=RaisingModelRunner(error=_RUNNER_NONZERO_EXIT),
        build_prompt=lambda case: f"case={case.id}",
    )

    assert len(result.outcomes) == 1
    outcome = result.outcomes[0]
    assert outcome.passed is False
    assert result.passed is False
    reasons = outcome.trials[0].grade.reasons
    assert any(str(_RUNNER_NONZERO_EXIT) in reason for reason in reasons), reasons


def test_run_suite_serial_isolates_runner_timeout_as_fail_outcome(
    tmp_path: Path,
) -> None:
    cases_path = _write_case(tmp_path, _trivial_record("c-1"))

    result = run_suite(
        cases_path=cases_path,
        runner=RaisingModelRunner(error=_RUNNER_TIMEOUT),
        build_prompt=lambda case: f"case={case.id}",
    )

    assert len(result.outcomes) == 1
    assert result.outcomes[0].passed is False
    assert result.passed is False


def test_run_suite_parallel_isolates_runner_failure_per_case(tmp_path: Path) -> None:
    records = [_trivial_record("c-1"), _trivial_record("c-2")]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    result = run_suite(
        cases_path=cases_path,
        runner=RaisingModelRunner(error=_RUNNER_NONZERO_EXIT),
        build_prompt=lambda case: f"case={case.id}",
        workers=2,
    )

    assert [o.case.id for o in result.outcomes] == ["c-1", "c-2"]
    assert all(o.passed is False for o in result.outcomes)
    assert result.passed is False


def test_run_suite_rejects_empty_cases_file(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="cases"):
        run_suite(
            cases_path=cases_path,
            runner=StubRunner(response=_PASS_VERDICT),
            build_prompt=lambda case: f"case={case.id}",
        )


def _case(
    *,
    must_contain: list[dict[str, Any]] | None = None,
    must_not_contain: list[dict[str, Any]] | None = None,
) -> Case:
    return Case(
        id="t",
        input={},
        must_contain=tuple(must_contain or ()),
        must_not_contain=tuple(must_not_contain or ()),
    )
