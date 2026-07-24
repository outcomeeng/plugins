from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    spx_verification_run_accepts_implementation_audit_payloads,
    spx_verification_run_counts_one_rule_across_subjects,
    spx_verification_run_rejects_mismatched_terminal_status,
)


def test_spx_verification_run_accepts_implementation_audit_payloads() -> None:
    assert spx_verification_run_accepts_implementation_audit_payloads()


def test_spx_verification_run_rejects_mismatched_terminal_status() -> None:
    assert spx_verification_run_rejects_mismatched_terminal_status()


def test_spx_verification_run_counts_one_rule_across_subjects() -> None:
    assert spx_verification_run_counts_one_rule_across_subjects()
