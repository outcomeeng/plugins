from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_contract_rejects_extra_runtime_artifact,
    audit_contract_rejects_missing_runtime_skill,
    audit_contract_rejects_retired_artifact_in_language_runtime,
    audit_contract_rejects_retired_artifact_in_other_runtime,
    implementation_audit_runtime_contains_only_skill,
)


def test_implementation_audit_runtime_contains_only_skill() -> None:
    assert implementation_audit_runtime_contains_only_skill()


def test_implementation_audit_runtime_rejects_extra_artifact() -> None:
    assert audit_contract_rejects_extra_runtime_artifact()


def test_implementation_audit_runtime_rejects_missing_skill() -> None:
    assert audit_contract_rejects_missing_runtime_skill()


def test_other_audit_runtime_rejects_retired_artifact() -> None:
    assert audit_contract_rejects_retired_artifact_in_other_runtime()


def test_language_audit_runtime_rejects_retired_artifact() -> None:
    assert audit_contract_rejects_retired_artifact_in_language_runtime()
