from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    audit_contract_rejects_incomplete_language_trio,
    audit_contract_rejects_missing_generated_audit_host,
    audit_contract_rejects_missing_generated_language,
    audit_contract_rejects_missing_generated_surface,
    audit_contract_rejects_missing_single_surface_audit_host,
    audit_contract_rejects_language_specific_wrapper,
    audit_contract_rejects_language_wrapper_under_spec_tree,
    audit_contract_rejects_retired_language_audit_skill,
    audit_contract_rejects_retired_implementation_wrappers,
    audit_contract_rejects_retired_wrappers_in_language_plugins,
    audit_contract_rejects_unrecognized_language_specific_wrapper,
    implementation_auditor_is_the_only_implementation_wrapper,
    implementation_audit_payloads_reject_empty_subject,
    implementation_audit_unit_ids_are_subject_specific,
    language_concern_skill_trios_exist,
)


def test_implementation_auditor_is_the_only_implementation_wrapper() -> None:
    assert implementation_auditor_is_the_only_implementation_wrapper()


def test_language_concern_skill_trios_exist() -> None:
    assert language_concern_skill_trios_exist()


def test_language_specific_implementation_wrapper_is_rejected() -> None:
    assert audit_contract_rejects_language_specific_wrapper()


def test_language_wrapper_under_spec_tree_is_rejected() -> None:
    assert audit_contract_rejects_language_wrapper_under_spec_tree()


def test_unrecognized_language_specific_wrapper_is_rejected() -> None:
    assert audit_contract_rejects_unrecognized_language_specific_wrapper()


def test_implementation_audit_unit_ids_are_subject_specific() -> None:
    assert implementation_audit_unit_ids_are_subject_specific()


def test_implementation_audit_payloads_reject_empty_subject() -> None:
    assert implementation_audit_payloads_reject_empty_subject()


def test_retired_implementation_wrappers_are_rejected() -> None:
    assert audit_contract_rejects_retired_implementation_wrappers()


def test_retired_wrappers_in_language_plugins_are_rejected() -> None:
    assert audit_contract_rejects_retired_wrappers_in_language_plugins()


def test_incomplete_language_concern_trio_is_rejected() -> None:
    assert audit_contract_rejects_incomplete_language_trio()


def test_missing_generated_surface_is_rejected() -> None:
    assert audit_contract_rejects_missing_generated_surface()


def test_missing_generated_audit_host_is_rejected() -> None:
    assert audit_contract_rejects_missing_generated_audit_host()


def test_missing_single_surface_audit_host_is_rejected() -> None:
    assert audit_contract_rejects_missing_single_surface_audit_host()


def test_missing_generated_language_is_rejected() -> None:
    assert audit_contract_rejects_missing_generated_language()


def test_retired_language_audit_skill_is_rejected() -> None:
    assert audit_contract_rejects_retired_language_audit_skill()
