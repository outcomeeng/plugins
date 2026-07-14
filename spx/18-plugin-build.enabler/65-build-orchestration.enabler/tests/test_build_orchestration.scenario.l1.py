"""Scenario evidence for build orchestration."""

from __future__ import annotations

from outcomeeng_testing.harnesses.build_orchestration import (
    clean_dist_matches_contract,
    dist_drift_with_source_edit_matches_contract,
    dist_drift_without_source_edit_matches_contract,
    failing_formatter_matches_contract,
    failing_formatter_version_probe_matches_contract,
    missing_formatter_matches_contract,
)


def test_reports_expected_precommit_state_when_src_has_matching_edits() -> None:
    assert dist_drift_with_source_edit_matches_contract()


def test_reports_rebuild_remediation_when_src_is_clean() -> None:
    assert dist_drift_without_source_edit_matches_contract()


def test_reports_nothing_when_dist_in_sync() -> None:
    assert clean_dist_matches_contract()


def test_format_dist_reports_missing_formatter_without_running_child() -> None:
    assert missing_formatter_matches_contract()


def test_format_dist_reports_formatter_failure() -> None:
    assert failing_formatter_matches_contract()


def test_format_dist_reports_formatter_version_probe_failure() -> None:
    assert failing_formatter_version_probe_matches_contract()
