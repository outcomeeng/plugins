from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    spx_audit_verification_run_lifecycle_accepts_implementation_payloads,
)


def test_spx_audit_verification_run_lifecycle_accepts_implementation_payloads() -> None:
    assert spx_audit_verification_run_lifecycle_accepts_implementation_payloads()
