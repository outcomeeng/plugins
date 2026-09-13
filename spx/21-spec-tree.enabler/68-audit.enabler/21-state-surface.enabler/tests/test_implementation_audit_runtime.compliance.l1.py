from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    implementation_audit_runtime_errors,
    runtime_errors_with_extra_artifact,
    runtime_errors_with_extra_directory,
    runtime_errors_with_retired_artifact_in_language_skill,
    runtime_errors_with_retired_artifact_in_other_skill,
    runtime_errors_without_scope_entrypoint,
    runtime_errors_without_skill,
)


def test_implementation_audit_runtime_contains_declared_artifacts() -> None:
    assert implementation_audit_runtime_errors() == []


def test_implementation_audit_runtime_rejects_extra_artifact() -> None:
    assert runtime_errors_with_extra_artifact()


def test_implementation_audit_runtime_rejects_missing_skill() -> None:
    assert runtime_errors_without_skill()


def test_implementation_audit_runtime_rejects_missing_scope_entrypoint() -> None:
    assert runtime_errors_without_scope_entrypoint()


def test_implementation_audit_runtime_rejects_extra_directory() -> None:
    assert runtime_errors_with_extra_directory()


def test_other_audit_runtime_rejects_retired_artifact() -> None:
    assert runtime_errors_with_retired_artifact_in_other_skill()


def test_language_audit_runtime_rejects_retired_artifact() -> None:
    assert runtime_errors_with_retired_artifact_in_language_skill()
