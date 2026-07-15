from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_contract_rejects_extra_runtime_artifact,
    audit_contract_rejects_missing_runtime_skill,
    audit_contract_rejects_retired_artifact_in_other_runtime,
    audit_runtime_trees_exclude_retired_artifacts,
    spx_floor_provides_verification_run_lifecycle,
    verification_run_floor_rejects_pre_capability_version,
)


def test_spx_floor_provides_verification_run_lifecycle() -> None:
    assert spx_floor_provides_verification_run_lifecycle()


def test_verification_run_floor_rejects_pre_capability_version() -> None:
    assert verification_run_floor_rejects_pre_capability_version()


def test_audit_runtimes_exclude_retired_artifacts() -> None:
    assert audit_runtime_trees_exclude_retired_artifacts()


def test_verdict_runtime_rejects_extra_artifacts() -> None:
    assert audit_contract_rejects_extra_runtime_artifact()


def test_verdict_runtime_rejects_missing_skill() -> None:
    assert audit_contract_rejects_missing_runtime_skill()


def test_other_audit_runtime_rejects_retired_artifact() -> None:
    assert audit_contract_rejects_retired_artifact_in_other_runtime()
