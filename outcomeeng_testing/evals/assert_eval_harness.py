"""Assertion entrypoints for eval-harness compliance evidence."""

from __future__ import annotations

from outcomeeng_testing.harnesses.eval_assertions import (
    CapturedStderr,
    run_plain,
    run_with_captured_stderr,
    run_with_tmp_path,
)

import json
from pathlib import Path
from typing import Any

import pytest

from outcomeeng_evals.case import MAX_EXPECTED_LIST_LENGTH, load_cases
from outcomeeng_evals.cli.commands.run import _render_prompt
from outcomeeng_evals.grader import grade, is_subset, parse_verdict
from outcomeeng_evals.suite import run_suite
from outcomeeng_testing.evals.factories import (
    make_case,
    make_case_record,
    write_cases_file,
)
from outcomeeng_testing.evals.fakes import (
    RaisingModelRunner,
    approved_verdict,
    invalid_verdict_response,
    rejected_verdict,
    runner_nonzero_error,
    runner_timeout_error,
)
from outcomeeng_testing.evals.fakes import StubModelRunner as StubRunner


def _impl_load_cases_parses_jsonl_record_with_must_contain(tmp_path: Path) -> None:
    record = {
        "id": "positive-1",
        "input": {"snippet": "x"},
        "expected_verdict": {
            "must_contain": [{"findings": [{"rule": "r-1"}]}],
            "must_not_contain": [],
        },
    }
    cases = load_cases(write_cases_file(tmp_path, record))
    assert len(cases) == 1
    case = cases[0]
    assert case.id == "positive-1"
    assert case.input == {"snippet": "x"}
    assert case.must_contain[0] == {"findings": [{"rule": "r-1"}]}


def _impl_load_cases_rejects_record_missing_id(tmp_path: Path) -> None:
    bad: dict[str, Any] = {"input": {}, "expected_verdict": {}}
    with pytest.raises(ValueError, match="missing required field 'id'"):
        load_cases(write_cases_file(tmp_path, bad))


def _impl_load_cases_rejects_blank_id(tmp_path: Path) -> None:
    bad: dict[str, Any] = {"id": "", "input": {}, "expected_verdict": {}}
    with pytest.raises(ValueError, match="'id'"):
        load_cases(write_cases_file(tmp_path, bad))


def _impl_load_cases_accepts_expected_list_at_cap(tmp_path: Path) -> None:
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
    cases = load_cases(write_cases_file(tmp_path, record))
    assert len(cases[0].must_contain[0]["findings"]) == MAX_EXPECTED_LIST_LENGTH


def _impl_load_cases_rejects_oversized_expected_list(tmp_path: Path) -> None:
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
        load_cases(write_cases_file(tmp_path, record))


def _impl_parse_verdict_returns_parsed_json_document() -> None:
    msg = '{"status":"rejected","findings":[{"rule":"x","present":true}]}'
    assert parse_verdict(msg) == {
        "status": "rejected",
        "findings": [{"rule": "x", "present": True}],
    }


def _impl_parse_verdict_tolerates_surrounding_whitespace() -> None:
    msg = '  \n{"status":"approved"}\n  '
    assert parse_verdict(msg) == {"status": "approved"}


def _impl_parse_verdict_returns_none_when_response_is_not_json() -> None:
    assert parse_verdict(invalid_verdict_response()) is None


def _impl_parse_verdict_strips_backtick_fence_without_language() -> None:
    msg = '```\n{"terminal_green": true}\n```'
    assert parse_verdict(msg) == {"terminal_green": True}


def _impl_parse_verdict_strips_backtick_fence_with_json_language() -> None:
    msg = '```json\n{"status": "approved"}\n```'
    assert parse_verdict(msg) == {"status": "approved"}


def _impl_parse_verdict_strips_fence_with_surrounding_whitespace() -> None:
    msg = '  \n```json\n{"x": 1}\n```\n  '
    assert parse_verdict(msg) == {"x": 1}


def _impl_parse_verdict_returns_none_for_fence_with_invalid_json() -> None:
    msg = "```json\nnot valid json\n```"
    assert parse_verdict(msg) is None


def _impl_is_subset_matches_dict_keys_recursively() -> None:
    assert is_subset({"status": "rejected"}, {"status": "rejected", "findings": []})


def _impl_is_subset_rejects_when_dict_key_missing() -> None:
    assert not is_subset({"status": "rejected"}, {"findings": []})


def _impl_is_subset_matches_list_element_via_any_match() -> None:
    expected = {"findings": [{"rule": "x"}]}
    actual = {"findings": [{"rule": "other"}, {"rule": "x", "present": True}]}
    assert is_subset(expected, actual)


def _impl_is_subset_rejects_when_no_list_element_matches() -> None:
    expected = {"findings": [{"rule": "x"}]}
    actual = {"findings": [{"rule": "other"}]}
    assert not is_subset(expected, actual)


def _impl_is_subset_list_matching_is_cardinality_aware() -> None:
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


def _impl_is_subset_string_sentinel_matches_any_string() -> None:
    assert is_subset({"action": "#string"}, {"action": "Add a null check"})
    assert is_subset({"action": "#string"}, {"action": ""})


def _impl_is_subset_string_sentinel_rejects_non_string() -> None:
    assert not is_subset({"action": "#string"}, {"action": None})
    assert not is_subset({"action": "#string"}, {"action": 42})
    assert not is_subset({"action": "#string"}, {"action": ["a"]})
    assert not is_subset({"action": "#string"}, {"action": {"k": "v"}})
    assert not is_subset({"action": "#string"}, {"action": True})


def _impl_is_subset_notnull_sentinel_matches_any_non_null() -> None:
    assert is_subset({"action": "#notnull"}, {"action": "x"})
    assert is_subset({"action": "#notnull"}, {"action": ""})
    assert is_subset({"action": "#notnull"}, {"action": 0})
    assert is_subset({"action": "#notnull"}, {"action": False})
    assert is_subset({"action": "#notnull"}, {"action": []})
    assert is_subset({"action": "#notnull"}, {"action": {}})


def _impl_is_subset_notnull_sentinel_rejects_null() -> None:
    assert not is_subset({"action": "#notnull"}, {"action": None})


def _impl_is_subset_present_sentinel_matches_any_value_including_null() -> None:
    assert is_subset({"action": "#present"}, {"action": "x"})
    assert is_subset({"action": "#present"}, {"action": None})
    assert is_subset({"action": "#present"}, {"action": 0})
    assert is_subset({"action": "#present"}, {"action": []})


def _impl_is_subset_present_sentinel_rejects_when_key_missing() -> None:
    # Dict-level "key must exist" check happens BEFORE is_subset is
    # invoked on the value, so a missing key fails regardless of the
    # sentinel that would have matched the value.
    assert not is_subset({"action": "#present"}, {})


def _impl_is_subset_sentinel_only_applies_at_expected_position() -> None:
    # Sentinels are an expected-side convention. The dispatch keys on
    # `expected`, so a non-sentinel expected string is compared by
    # equality regardless of actual. When expected is `#string` and
    # actual happens to equal the literal `#string`, the sentinel
    # matcher still fires (because actual is a string) — the result is
    # the same as equality would yield, but the path is the matcher.
    assert is_subset({"action": "#string"}, {"action": "#string"})
    assert is_subset({"action": "#string"}, {"action": "other"})


def _impl_is_subset_sentinel_used_with_coupled_finding_attributes() -> None:
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


def _impl_grade_passes_when_must_contain_subset_matches() -> None:
    case = make_case(
        case_id="t",
        must_contain=(
            {
                "status": "rejected",
                "findings": [
                    {"rule": "shared-test-owned-constant-bag", "present": True}
                ],
            },
        ),
    )
    result = grade(case, rejected_verdict("shared-test-owned-constant-bag"))
    assert result.passed
    assert result.reasons == ()


def _impl_grade_fails_when_required_structure_missing() -> None:
    case = make_case(case_id="t", must_contain=({"findings": [{"rule": "x"}]},))
    result = grade(case, approved_verdict())
    assert not result.passed
    assert any("missing required structure" in r for r in result.reasons)


def _impl_grade_fails_when_forbidden_structure_present() -> None:
    case = make_case(case_id="t", must_not_contain=({"status": "approved"},))
    result = grade(case, approved_verdict())
    assert not result.passed
    assert any("forbidden structure present" in r for r in result.reasons)


def _impl_grade_fails_when_response_is_not_parseable_json() -> None:
    case = make_case(case_id="t", must_contain=({"status": "rejected"},))
    result = grade(case, invalid_verdict_response())
    assert not result.passed
    assert any("not a parseable JSON document" in r for r in result.reasons)


def _impl_run_suite_passes_when_canned_verdict_matches(tmp_path: Path) -> None:
    record = {
        "id": "positive-1",
        "input": {"snippet": "x"},
        "expected_verdict": {
            "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
        },
    }
    cases_path = write_cases_file(tmp_path, record)
    canned = json.dumps(
        {"status": "rejected", "findings": [{"rule": "x", "present": True}]}
    )
    result = run_suite(
        cases_path=cases_path,
        runner=StubRunner(response=canned),
        build_prompt=lambda case: "ignored",
    )
    assert result.passed
    assert result.pass_rate == pytest.approx(1.0)


def _impl_run_suite_fails_when_threshold_not_met(tmp_path: Path) -> None:
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


def _impl_run_suite_case_passes_under_majority_when_one_trial_fails(
    tmp_path: Path,
) -> None:
    record = {
        "id": "c",
        "input": {},
        "expected_verdict": {
            "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
        },
    }
    cases_path = write_cases_file(tmp_path, record)
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


def _impl_case_outcome_trial_pass_rate_reflects_per_trial_results(
    tmp_path: Path,
) -> None:
    record = {
        "id": "c",
        "input": {},
        "expected_verdict": {
            "must_contain": [{"findings": [{"rule": "x", "present": True}]}]
        },
    }
    cases_path = write_cases_file(tmp_path, record)
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


def _impl_run_suite_with_workers_preserves_case_order_when_threads_finish_out_of_order(
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


def _impl_render_prompt_warns_on_unrecognized_placeholder(
    capsys: CapturedStderr,
) -> None:
    rendered = _render_prompt("before {input_jsn} after", make_case(case_id="t"))

    assert "{input_jsn}" in rendered  # passed through as literal text
    err = capsys.readouterr().err
    assert "input_jsn" in err
    assert "unrecognized placeholder" in err


def _impl_render_prompt_does_not_warn_on_known_placeholder_or_json(
    capsys: CapturedStderr,
) -> None:
    rendered = _render_prompt(
        'case={case_id} payload={input_json} sample={"k": 1}', make_case(case_id="t")
    )

    assert "case=t" in rendered
    assert capsys.readouterr().err == ""


def _impl_run_suite_serial_isolates_runner_failure_as_fail_outcome(
    tmp_path: Path,
) -> None:
    cases_path = write_cases_file(tmp_path, make_case_record("c-1"))

    result = run_suite(
        cases_path=cases_path,
        runner=RaisingModelRunner(error=runner_nonzero_error()),
        build_prompt=lambda case: f"case={case.id}",
    )

    assert len(result.outcomes) == 1
    outcome = result.outcomes[0]
    assert outcome.passed is False
    assert result.passed is False
    reasons = outcome.trials[0].grade.reasons
    assert any(str(runner_nonzero_error()) in reason for reason in reasons), reasons


def _impl_run_suite_serial_isolates_runner_timeout_as_fail_outcome(
    tmp_path: Path,
) -> None:
    cases_path = write_cases_file(tmp_path, make_case_record("c-1"))

    result = run_suite(
        cases_path=cases_path,
        runner=RaisingModelRunner(error=runner_timeout_error()),
        build_prompt=lambda case: f"case={case.id}",
    )

    assert len(result.outcomes) == 1
    assert result.outcomes[0].passed is False
    assert result.passed is False


def _impl_run_suite_parallel_isolates_runner_failure_per_case(tmp_path: Path) -> None:
    records = [make_case_record("c-1"), make_case_record("c-2")]
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    result = run_suite(
        cases_path=cases_path,
        runner=RaisingModelRunner(error=runner_nonzero_error()),
        build_prompt=lambda case: f"case={case.id}",
        workers=2,
    )

    assert [o.case.id for o in result.outcomes] == ["c-1", "c-2"]
    assert all(o.passed is False for o in result.outcomes)
    assert result.passed is False


def _impl_run_suite_rejects_empty_cases_file(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.jsonl"
    cases_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="cases"):
        run_suite(
            cases_path=cases_path,
            runner=StubRunner(
                response=rejected_verdict("shared-test-owned-constant-bag")
            ),
            build_prompt=lambda case: f"case={case.id}",
        )


def assert_load_cases_parses_jsonl_record_with_must_contain() -> None:
    run_with_tmp_path(_impl_load_cases_parses_jsonl_record_with_must_contain)


def assert_load_cases_rejects_record_missing_id() -> None:
    run_with_tmp_path(_impl_load_cases_rejects_record_missing_id)


def assert_load_cases_rejects_blank_id() -> None:
    run_with_tmp_path(_impl_load_cases_rejects_blank_id)


def assert_load_cases_accepts_expected_list_at_cap() -> None:
    run_with_tmp_path(_impl_load_cases_accepts_expected_list_at_cap)


def assert_load_cases_rejects_oversized_expected_list() -> None:
    run_with_tmp_path(_impl_load_cases_rejects_oversized_expected_list)


def assert_parse_verdict_returns_parsed_json_document() -> None:
    run_plain(_impl_parse_verdict_returns_parsed_json_document)


def assert_parse_verdict_tolerates_surrounding_whitespace() -> None:
    run_plain(_impl_parse_verdict_tolerates_surrounding_whitespace)


def assert_parse_verdict_returns_none_when_response_is_not_json() -> None:
    run_plain(_impl_parse_verdict_returns_none_when_response_is_not_json)


def assert_parse_verdict_strips_backtick_fence_without_language() -> None:
    run_plain(_impl_parse_verdict_strips_backtick_fence_without_language)


def assert_parse_verdict_strips_backtick_fence_with_json_language() -> None:
    run_plain(_impl_parse_verdict_strips_backtick_fence_with_json_language)


def assert_parse_verdict_strips_fence_with_surrounding_whitespace() -> None:
    run_plain(_impl_parse_verdict_strips_fence_with_surrounding_whitespace)


def assert_parse_verdict_returns_none_for_fence_with_invalid_json() -> None:
    run_plain(_impl_parse_verdict_returns_none_for_fence_with_invalid_json)


def assert_is_subset_matches_dict_keys_recursively() -> None:
    run_plain(_impl_is_subset_matches_dict_keys_recursively)


def assert_is_subset_rejects_when_dict_key_missing() -> None:
    run_plain(_impl_is_subset_rejects_when_dict_key_missing)


def assert_is_subset_matches_list_element_via_any_match() -> None:
    run_plain(_impl_is_subset_matches_list_element_via_any_match)


def assert_is_subset_rejects_when_no_list_element_matches() -> None:
    run_plain(_impl_is_subset_rejects_when_no_list_element_matches)


def assert_is_subset_list_matching_is_cardinality_aware() -> None:
    run_plain(_impl_is_subset_list_matching_is_cardinality_aware)


def assert_is_subset_string_sentinel_matches_any_string() -> None:
    run_plain(_impl_is_subset_string_sentinel_matches_any_string)


def assert_is_subset_string_sentinel_rejects_non_string() -> None:
    run_plain(_impl_is_subset_string_sentinel_rejects_non_string)


def assert_is_subset_notnull_sentinel_matches_any_non_null() -> None:
    run_plain(_impl_is_subset_notnull_sentinel_matches_any_non_null)


def assert_is_subset_notnull_sentinel_rejects_null() -> None:
    run_plain(_impl_is_subset_notnull_sentinel_rejects_null)


def assert_is_subset_present_sentinel_matches_any_value_including_null() -> None:
    run_plain(_impl_is_subset_present_sentinel_matches_any_value_including_null)


def assert_is_subset_present_sentinel_rejects_when_key_missing() -> None:
    run_plain(_impl_is_subset_present_sentinel_rejects_when_key_missing)


def assert_is_subset_sentinel_only_applies_at_expected_position() -> None:
    run_plain(_impl_is_subset_sentinel_only_applies_at_expected_position)


def assert_is_subset_sentinel_used_with_coupled_finding_attributes() -> None:
    run_plain(_impl_is_subset_sentinel_used_with_coupled_finding_attributes)


def assert_grade_passes_when_must_contain_subset_matches() -> None:
    run_plain(_impl_grade_passes_when_must_contain_subset_matches)


def assert_grade_fails_when_required_structure_missing() -> None:
    run_plain(_impl_grade_fails_when_required_structure_missing)


def assert_grade_fails_when_forbidden_structure_present() -> None:
    run_plain(_impl_grade_fails_when_forbidden_structure_present)


def assert_grade_fails_when_response_is_not_parseable_json() -> None:
    run_plain(_impl_grade_fails_when_response_is_not_parseable_json)


def assert_run_suite_passes_when_canned_verdict_matches() -> None:
    run_with_tmp_path(_impl_run_suite_passes_when_canned_verdict_matches)


def assert_run_suite_fails_when_threshold_not_met() -> None:
    run_with_tmp_path(_impl_run_suite_fails_when_threshold_not_met)


def assert_run_suite_case_passes_under_majority_when_one_trial_fails() -> None:
    run_with_tmp_path(_impl_run_suite_case_passes_under_majority_when_one_trial_fails)


def assert_case_outcome_trial_pass_rate_reflects_per_trial_results() -> None:
    run_with_tmp_path(_impl_case_outcome_trial_pass_rate_reflects_per_trial_results)


def assert_run_suite_with_workers_preserves_case_order_when_threads_finish_out_of_order() -> (
    None
):
    run_with_tmp_path(
        _impl_run_suite_with_workers_preserves_case_order_when_threads_finish_out_of_order
    )


def assert_render_prompt_warns_on_unrecognized_placeholder() -> None:
    run_with_captured_stderr(_impl_render_prompt_warns_on_unrecognized_placeholder)


def assert_render_prompt_does_not_warn_on_known_placeholder_or_json() -> None:
    run_with_captured_stderr(
        _impl_render_prompt_does_not_warn_on_known_placeholder_or_json
    )


def assert_run_suite_serial_isolates_runner_failure_as_fail_outcome() -> None:
    run_with_tmp_path(_impl_run_suite_serial_isolates_runner_failure_as_fail_outcome)


def assert_run_suite_serial_isolates_runner_timeout_as_fail_outcome() -> None:
    run_with_tmp_path(_impl_run_suite_serial_isolates_runner_timeout_as_fail_outcome)


def assert_run_suite_parallel_isolates_runner_failure_per_case() -> None:
    run_with_tmp_path(_impl_run_suite_parallel_isolates_runner_failure_per_case)


def assert_run_suite_rejects_empty_cases_file() -> None:
    run_with_tmp_path(_impl_run_suite_rejects_empty_cases_file)
