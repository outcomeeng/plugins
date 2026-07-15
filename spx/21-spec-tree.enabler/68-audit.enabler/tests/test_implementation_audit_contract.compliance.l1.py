from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_contract_rejects_incomplete_language_trio,
    audit_contract_rejects_language_specific_wrapper,
    implementation_auditor_is_the_only_implementation_wrapper,
    language_concern_skill_trios_exist,
    spx_verification_run_accepts_implementation_audit_payloads,
)


def test_implementation_auditor_is_the_only_implementation_wrapper() -> None:
    assert implementation_auditor_is_the_only_implementation_wrapper()


def test_language_concern_skill_trios_exist() -> None:
    assert language_concern_skill_trios_exist()


def test_spx_accepts_implementation_audit_payloads() -> None:
    assert spx_verification_run_accepts_implementation_audit_payloads()


def test_language_specific_implementation_wrapper_is_rejected() -> None:
    assert audit_contract_rejects_language_specific_wrapper()


def test_incomplete_language_concern_trio_is_rejected() -> None:
    assert audit_contract_rejects_incomplete_language_trio()
