from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    minimum_spx_release_accepts_implementation_audit_lifecycle,
)


def test_minimum_spx_release_accepts_implementation_audit_lifecycle() -> None:
    assert minimum_spx_release_accepts_implementation_audit_lifecycle()
