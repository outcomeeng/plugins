from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    implementation_audit_runtime_contains_only_skill,
)


def test_implementation_audit_runtime_contains_only_skill() -> None:
    assert implementation_audit_runtime_contains_only_skill()
