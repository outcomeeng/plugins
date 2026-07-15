from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_finding_payload_rejects_empty_subject_paths,
    audited_scope_payload_carries_concern_evidence,
    audited_scope_payload_rejects_empty_subject_paths,
    implementation_audit_scripts_are_absent_and_rejected,
    spx_audit_verification_run_lifecycle_accepts_implementation_payloads,
    spx_floor_and_ci_pin_meet_verification_run_minimum,
    spx_floor_rejects_version_below_verification_run_minimum,
)


def test_audited_scope_payload_carries_concern_evidence() -> None:
    assert audited_scope_payload_carries_concern_evidence()


def test_audited_scope_payload_rejects_empty_subject_paths() -> None:
    assert audited_scope_payload_rejects_empty_subject_paths()


def test_audit_finding_payload_rejects_empty_subject_paths() -> None:
    assert audit_finding_payload_rejects_empty_subject_paths()


def test_spx_floor_and_ci_pin_meet_verification_run_minimum() -> None:
    assert spx_floor_and_ci_pin_meet_verification_run_minimum()


def test_spx_floor_rejects_version_below_verification_run_minimum() -> None:
    assert spx_floor_rejects_version_below_verification_run_minimum()


def test_implementation_audit_scripts_are_absent_and_rejected() -> None:
    assert implementation_audit_scripts_are_absent_and_rejected()


def test_spx_verification_run_accepts_implementation_payloads() -> None:
    assert spx_audit_verification_run_lifecycle_accepts_implementation_payloads()
