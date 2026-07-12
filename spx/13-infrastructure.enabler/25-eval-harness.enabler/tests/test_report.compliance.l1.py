"""Compliance wrappers for JSON-first eval reports."""

from outcomeeng_testing.harnesses.eval_report import (
    assert_report_cost_summary_preserves_metadata_absence,
    assert_report_files_match_serialized_payload,
    assert_run_command_writes_eval_local_json_report,
    assert_report_serialization_matches_fixture_contract,
    assert_report_serialization_preserves_configured_ceilings,
    assert_report_trial_stability_matches_fixture_patterns,
)


def test_report_serialization_matches_fixture_contract() -> None:
    assert_report_serialization_matches_fixture_contract()


def test_report_serialization_preserves_configured_ceilings() -> None:
    assert_report_serialization_preserves_configured_ceilings()


def test_report_cost_summary_preserves_metadata_absence() -> None:
    assert_report_cost_summary_preserves_metadata_absence()


def test_report_trial_stability_matches_fixture_patterns() -> None:
    assert_report_trial_stability_matches_fixture_patterns()


def test_report_files_match_serialized_payload() -> None:
    assert_report_files_match_serialized_payload()


def test_run_command_writes_eval_local_json_report() -> None:
    assert_run_command_writes_eval_local_json_report()
