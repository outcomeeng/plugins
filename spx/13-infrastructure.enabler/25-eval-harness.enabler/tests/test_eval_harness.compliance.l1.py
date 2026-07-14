"""Compliance wrappers for eval parsing, grading, and suite execution."""

from outcomeeng_testing.harnesses.eval_harness import (
    assert_case_loader_enforces_expected_list_boundary,
    assert_case_loader_matches_complete_fixture,
    assert_case_loader_rejects_invalid_complete_fixtures,
    assert_grader_uses_fixture_expectations,
    assert_parallel_suite_preserves_fixture_case_order,
    assert_prompt_renderer_reports_fixture_placeholder_drift,
    assert_subset_matching_follows_fixture_matrix,
    assert_suite_isolates_runner_failures,
    assert_suite_rejects_empty_case_file,
    assert_suite_replays_fixture_cases_and_bounds_trials,
    assert_verdict_parser_matches_complete_response_fixtures,
)


def test_case_loader_matches_complete_fixture() -> None:
    assert_case_loader_matches_complete_fixture()


def test_case_loader_rejects_invalid_complete_fixtures() -> None:
    assert_case_loader_rejects_invalid_complete_fixtures()


def test_case_loader_enforces_expected_list_boundary() -> None:
    assert_case_loader_enforces_expected_list_boundary()


def test_verdict_parser_matches_complete_response_fixtures() -> None:
    assert_verdict_parser_matches_complete_response_fixtures()


def test_subset_matching_follows_fixture_matrix() -> None:
    assert_subset_matching_follows_fixture_matrix()


def test_grader_uses_fixture_expectations() -> None:
    assert_grader_uses_fixture_expectations()


def test_suite_replays_fixture_cases_and_bounds_trials() -> None:
    assert_suite_replays_fixture_cases_and_bounds_trials()


def test_parallel_suite_preserves_fixture_case_order() -> None:
    assert_parallel_suite_preserves_fixture_case_order()


def test_prompt_renderer_reports_fixture_placeholder_drift() -> None:
    assert_prompt_renderer_reports_fixture_placeholder_drift()


def test_suite_isolates_runner_failures() -> None:
    assert_suite_isolates_runner_failures()


def test_suite_rejects_empty_case_file() -> None:
    assert_suite_rejects_empty_case_file()
