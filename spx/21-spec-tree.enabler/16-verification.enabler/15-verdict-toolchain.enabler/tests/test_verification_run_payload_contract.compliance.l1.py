from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_contract_rejects_below_verification_run_floor,
    audit_contract_rejects_retired_artifact_in_language_runtime,
    audit_contract_rejects_retired_artifact_in_other_runtime,
    audit_runtime_trees_exclude_retired_artifacts,
    minimum_release_runner_supports_npx_fallback,
    spx_floor_provides_verification_run_lifecycle,
)


def test_spx_floor_provides_verification_run_lifecycle() -> None:
    assert spx_floor_provides_verification_run_lifecycle()


def test_below_verification_run_floor_is_rejected() -> None:
    assert audit_contract_rejects_below_verification_run_floor()


def test_minimum_release_runner_supports_npx_fallback() -> None:
    assert minimum_release_runner_supports_npx_fallback()


def test_audit_runtimes_exclude_retired_artifacts() -> None:
    assert audit_runtime_trees_exclude_retired_artifacts()


def test_other_audit_runtime_rejects_retired_artifact() -> None:
    assert audit_contract_rejects_retired_artifact_in_other_runtime()


def test_language_audit_runtime_rejects_retired_artifact() -> None:
    assert audit_contract_rejects_retired_artifact_in_language_runtime()
