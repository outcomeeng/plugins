from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_skill_ships_no_verdict_toolchain_scripts,
    spx_audit_verification_run_lifecycle_accepts_implementation_payloads,
)


def test_spx_verification_run_accepts_implementation_payloads() -> None:
    assert spx_audit_verification_run_lifecycle_accepts_implementation_payloads()


def test_audit_skill_ships_no_verdict_toolchain_scripts() -> None:
    assert audit_skill_ships_no_verdict_toolchain_scripts()
