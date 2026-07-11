from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    spx_audit_verification_run_lifecycle_accepts_implementation_payloads,
    spx_floor_provides_verification_run_lifecycle,
)


def test_spx_floor_provides_verification_run_lifecycle() -> None:
    assert spx_floor_provides_verification_run_lifecycle()


def test_spx_verification_run_accepts_implementation_payloads() -> None:
    assert spx_audit_verification_run_lifecycle_accepts_implementation_payloads()
