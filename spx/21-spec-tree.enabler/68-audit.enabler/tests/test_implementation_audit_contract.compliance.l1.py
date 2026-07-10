from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_skill_ships_no_verdict_toolchain_scripts,
    implementation_auditor_is_the_only_implementation_wrapper,
    language_concern_skill_trios_exist,
    spx_audit_verification_run_lifecycle_accepts_implementation_payloads,
)


def test_implementation_audit_removes_plugin_side_verdict_scripts() -> None:
    assert audit_skill_ships_no_verdict_toolchain_scripts()


def test_implementation_auditor_is_the_only_implementation_wrapper() -> None:
    assert implementation_auditor_is_the_only_implementation_wrapper()


def test_language_concern_skill_trios_exist() -> None:
    assert language_concern_skill_trios_exist()


def test_spx_audit_verification_run_lifecycle_accepts_implementation_payloads() -> None:
    assert spx_audit_verification_run_lifecycle_accepts_implementation_payloads()
