from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    implementation_audit_scripts_are_absent_and_rejected,
    spx_audit_verification_run_lifecycle_accepts_implementation_payloads,
    spx_floor_and_ci_pin_meet_verification_run_minimum,
    spx_floor_rejects_version_below_verification_run_minimum,
)


def test_spx_floor_and_ci_pin_meet_verification_run_minimum() -> None:
    assert spx_floor_and_ci_pin_meet_verification_run_minimum()


def test_spx_floor_rejects_version_below_verification_run_minimum() -> None:
    assert spx_floor_rejects_version_below_verification_run_minimum()


def test_implementation_audit_scripts_are_absent_and_rejected() -> None:
    assert implementation_audit_scripts_are_absent_and_rejected()


def test_spx_verification_run_accepts_implementation_payloads() -> None:
    assert spx_audit_verification_run_lifecycle_accepts_implementation_payloads()
