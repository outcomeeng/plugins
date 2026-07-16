"""Scenario evidence for the complete review-changes script chain."""

from __future__ import annotations

from outcomeeng_testing.harnesses.reviewing_changes import (
    clean_review_chain_contract_holds,
    compute_diff_scenario_contract_holds,
    malformed_runner_finding_contract_holds,
    review_chain_with_finding_contract_holds,
    review_journal_command_contract_holds,
    review_journal_start_cursor_contract_holds,
    review_journal_type_contract_holds,
    review_runner_coverage_contract_holds,
    review_runner_finish_output_contract_holds,
    review_runner_lifecycle_contract_holds,
    review_runner_rename_contract_holds,
)


def test_chain_streams_and_renders_review_run() -> None:
    assert review_chain_with_finding_contract_holds()


def test_clean_review_streams_a_zero_count() -> None:
    assert clean_review_chain_contract_holds()


def test_live_skill_returns_only_the_raw_token() -> None:
    assert review_runner_finish_output_contract_holds()


def test_runner_preserves_journal_lifecycle() -> None:
    assert review_runner_lifecycle_contract_holds()


def test_runner_uses_spx_journal_command() -> None:
    assert review_journal_command_contract_holds()


def test_runner_uses_review_journal_namespace() -> None:
    assert review_journal_type_contract_holds()


def test_runner_reads_from_initial_journal_cursor() -> None:
    assert review_journal_start_cursor_contract_holds()


def test_runner_rejects_malformed_finding_before_append() -> None:
    assert malformed_runner_finding_contract_holds()


def test_runner_rejects_incomplete_scope_coverage() -> None:
    assert review_runner_coverage_contract_holds()


def test_runner_requires_rename_source_and_destination() -> None:
    assert review_runner_rename_contract_holds()


def test_compute_diff_scenarios() -> None:
    assert compute_diff_scenario_contract_holds()
