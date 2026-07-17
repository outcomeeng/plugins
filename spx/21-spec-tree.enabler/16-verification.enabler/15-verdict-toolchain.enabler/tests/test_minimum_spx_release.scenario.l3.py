from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    spx_verification_run_accepts_implementation_audit_payloads,
)


def test_minimum_spx_release_accepts_implementation_audit_lifecycle() -> None:
    assert spx_verification_run_accepts_implementation_audit_payloads()
