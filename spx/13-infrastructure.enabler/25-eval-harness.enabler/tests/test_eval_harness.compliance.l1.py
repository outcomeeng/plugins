"""Binding-free compliance wrappers for the eval harness."""

from outcomeeng_testing.evals.assert_eval_harness import (
    assert_load_cases_parses_jsonl_record_with_must_contain,
    assert_load_cases_rejects_record_missing_id,
    assert_load_cases_rejects_blank_id,
    assert_load_cases_accepts_expected_list_at_cap,
    assert_load_cases_rejects_oversized_expected_list,
    assert_parse_verdict_returns_parsed_json_document,
    assert_parse_verdict_tolerates_surrounding_whitespace,
    assert_parse_verdict_returns_none_when_response_is_not_json,
    assert_parse_verdict_strips_backtick_fence_without_language,
    assert_parse_verdict_strips_backtick_fence_with_json_language,
    assert_parse_verdict_strips_fence_with_surrounding_whitespace,
    assert_parse_verdict_returns_none_for_fence_with_invalid_json,
    assert_is_subset_matches_dict_keys_recursively,
    assert_is_subset_rejects_when_dict_key_missing,
    assert_is_subset_matches_list_element_via_any_match,
    assert_is_subset_rejects_when_no_list_element_matches,
    assert_is_subset_list_matching_is_cardinality_aware,
    assert_is_subset_string_sentinel_matches_any_string,
    assert_is_subset_string_sentinel_rejects_non_string,
    assert_is_subset_notnull_sentinel_matches_any_non_null,
    assert_is_subset_notnull_sentinel_rejects_null,
    assert_is_subset_present_sentinel_matches_any_value_including_null,
    assert_is_subset_present_sentinel_rejects_when_key_missing,
    assert_is_subset_sentinel_only_applies_at_expected_position,
    assert_is_subset_sentinel_used_with_coupled_finding_attributes,
    assert_grade_passes_when_must_contain_subset_matches,
    assert_grade_fails_when_required_structure_missing,
    assert_grade_fails_when_forbidden_structure_present,
    assert_grade_fails_when_response_is_not_parseable_json,
    assert_run_suite_passes_when_canned_verdict_matches,
    assert_run_suite_fails_when_threshold_not_met,
    assert_run_suite_case_passes_under_majority_when_one_trial_fails,
    assert_case_outcome_trial_pass_rate_reflects_per_trial_results,
    assert_run_suite_with_workers_preserves_case_order_when_threads_finish_out_of_order,
    assert_render_prompt_warns_on_unrecognized_placeholder,
    assert_render_prompt_does_not_warn_on_known_placeholder_or_json,
    assert_run_suite_serial_isolates_runner_failure_as_fail_outcome,
    assert_run_suite_serial_isolates_runner_timeout_as_fail_outcome,
    assert_run_suite_parallel_isolates_runner_failure_per_case,
    assert_run_suite_rejects_empty_cases_file,
)


def test_load_cases_parses_jsonl_record_with_must_contain() -> None:
    assert_load_cases_parses_jsonl_record_with_must_contain()


def test_load_cases_rejects_record_missing_id() -> None:
    assert_load_cases_rejects_record_missing_id()


def test_load_cases_rejects_blank_id() -> None:
    assert_load_cases_rejects_blank_id()


def test_load_cases_accepts_expected_list_at_cap() -> None:
    assert_load_cases_accepts_expected_list_at_cap()


def test_load_cases_rejects_oversized_expected_list() -> None:
    assert_load_cases_rejects_oversized_expected_list()


def test_parse_verdict_returns_parsed_json_document() -> None:
    assert_parse_verdict_returns_parsed_json_document()


def test_parse_verdict_tolerates_surrounding_whitespace() -> None:
    assert_parse_verdict_tolerates_surrounding_whitespace()


def test_parse_verdict_returns_none_when_response_is_not_json() -> None:
    assert_parse_verdict_returns_none_when_response_is_not_json()


def test_parse_verdict_strips_backtick_fence_without_language() -> None:
    assert_parse_verdict_strips_backtick_fence_without_language()


def test_parse_verdict_strips_backtick_fence_with_json_language() -> None:
    assert_parse_verdict_strips_backtick_fence_with_json_language()


def test_parse_verdict_strips_fence_with_surrounding_whitespace() -> None:
    assert_parse_verdict_strips_fence_with_surrounding_whitespace()


def test_parse_verdict_returns_none_for_fence_with_invalid_json() -> None:
    assert_parse_verdict_returns_none_for_fence_with_invalid_json()


def test_is_subset_matches_dict_keys_recursively() -> None:
    assert_is_subset_matches_dict_keys_recursively()


def test_is_subset_rejects_when_dict_key_missing() -> None:
    assert_is_subset_rejects_when_dict_key_missing()


def test_is_subset_matches_list_element_via_any_match() -> None:
    assert_is_subset_matches_list_element_via_any_match()


def test_is_subset_rejects_when_no_list_element_matches() -> None:
    assert_is_subset_rejects_when_no_list_element_matches()


def test_is_subset_list_matching_is_cardinality_aware() -> None:
    assert_is_subset_list_matching_is_cardinality_aware()


def test_is_subset_string_sentinel_matches_any_string() -> None:
    assert_is_subset_string_sentinel_matches_any_string()


def test_is_subset_string_sentinel_rejects_non_string() -> None:
    assert_is_subset_string_sentinel_rejects_non_string()


def test_is_subset_notnull_sentinel_matches_any_non_null() -> None:
    assert_is_subset_notnull_sentinel_matches_any_non_null()


def test_is_subset_notnull_sentinel_rejects_null() -> None:
    assert_is_subset_notnull_sentinel_rejects_null()


def test_is_subset_present_sentinel_matches_any_value_including_null() -> None:
    assert_is_subset_present_sentinel_matches_any_value_including_null()


def test_is_subset_present_sentinel_rejects_when_key_missing() -> None:
    assert_is_subset_present_sentinel_rejects_when_key_missing()


def test_is_subset_sentinel_only_applies_at_expected_position() -> None:
    assert_is_subset_sentinel_only_applies_at_expected_position()


def test_is_subset_sentinel_used_with_coupled_finding_attributes() -> None:
    assert_is_subset_sentinel_used_with_coupled_finding_attributes()


def test_grade_passes_when_must_contain_subset_matches() -> None:
    assert_grade_passes_when_must_contain_subset_matches()


def test_grade_fails_when_required_structure_missing() -> None:
    assert_grade_fails_when_required_structure_missing()


def test_grade_fails_when_forbidden_structure_present() -> None:
    assert_grade_fails_when_forbidden_structure_present()


def test_grade_fails_when_response_is_not_parseable_json() -> None:
    assert_grade_fails_when_response_is_not_parseable_json()


def test_run_suite_passes_when_canned_verdict_matches() -> None:
    assert_run_suite_passes_when_canned_verdict_matches()


def test_run_suite_fails_when_threshold_not_met() -> None:
    assert_run_suite_fails_when_threshold_not_met()


def test_run_suite_case_passes_under_majority_when_one_trial_fails() -> None:
    assert_run_suite_case_passes_under_majority_when_one_trial_fails()


def test_case_outcome_trial_pass_rate_reflects_per_trial_results() -> None:
    assert_case_outcome_trial_pass_rate_reflects_per_trial_results()


def test_run_suite_with_workers_preserves_case_order_when_threads_finish_out_of_order() -> (
    None
):
    assert_run_suite_with_workers_preserves_case_order_when_threads_finish_out_of_order()


def test_render_prompt_warns_on_unrecognized_placeholder() -> None:
    assert_render_prompt_warns_on_unrecognized_placeholder()


def test_render_prompt_does_not_warn_on_known_placeholder_or_json() -> None:
    assert_render_prompt_does_not_warn_on_known_placeholder_or_json()


def test_run_suite_serial_isolates_runner_failure_as_fail_outcome() -> None:
    assert_run_suite_serial_isolates_runner_failure_as_fail_outcome()


def test_run_suite_serial_isolates_runner_timeout_as_fail_outcome() -> None:
    assert_run_suite_serial_isolates_runner_timeout_as_fail_outcome()


def test_run_suite_parallel_isolates_runner_failure_per_case() -> None:
    assert_run_suite_parallel_isolates_runner_failure_per_case()


def test_run_suite_rejects_empty_cases_file() -> None:
    assert_run_suite_rejects_empty_cases_file()
