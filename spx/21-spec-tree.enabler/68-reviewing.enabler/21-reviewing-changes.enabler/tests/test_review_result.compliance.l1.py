"""Compliance evidence for the canonical review-result contract."""

from outcomeeng_testing.harnesses.reviewing_changes import (
    declared_rule_slug_contract_holds,
    review_module_surface_observation,
    review_parse_compliance_observation,
    root_rule_resolves_from_subdirectory,
    rule_citation_observation,
    runtime_skill_rule_resolves,
    versioned_sibling_plugin_resolution_holds,
)


def test_schema_version_is_a_positive_integer() -> None:
    assert review_module_surface_observation().schema_version_is_positive


def test_severity_and_concern_enums_exist_and_no_decision() -> None:
    observation = review_module_surface_observation()

    assert observation.severity_exists
    assert observation.concern_exists
    assert observation.decision_absent


def test_finding_and_review_result_are_frozen_dataclasses() -> None:
    assert review_module_surface_observation().dataclasses_are_frozen


def test_validation_error_subclass_of_exception() -> None:
    assert review_module_surface_observation().validation_error_is_exception


def test_parse_json_returns_review_result_on_conforming_document() -> None:
    observation = review_parse_compliance_observation()

    assert observation.conforming_result_type is observation.expected_result_type


def test_parse_json_accepts_empty_findings() -> None:
    assert not review_parse_compliance_observation().empty_findings


def test_missing_required_key_raises() -> None:
    observation = review_parse_compliance_observation()

    assert observation.missing_document_field in observation.missing_document_error


def test_unknown_severity_raises_with_value_and_allowed_set() -> None:
    observation = review_parse_compliance_observation()

    assert observation.unknown_severity in observation.unknown_severity_error


def test_unknown_concern_raises_with_value_and_allowed_set() -> None:
    observation = review_parse_compliance_observation()

    assert observation.unknown_concern in observation.unknown_concern_error


def test_malformed_json_raises() -> None:
    assert review_parse_compliance_observation().malformed_error


def test_missing_action_field_raises() -> None:
    observation = review_parse_compliance_observation()

    assert observation.missing_finding_field in observation.missing_finding_error


def test_parse_json_accepts_declared_rule_citation_forms() -> None:
    observation = rule_citation_observation()

    assert observation.accepted_rules == observation.expected_rules


def test_parse_json_rejects_free_form_rule_text() -> None:
    observation = rule_citation_observation()

    assert observation.malformed_rule in observation.malformed_error


def test_plugin_skill_rule_can_resolve_absolute_runtime_path() -> None:
    assert runtime_skill_rule_resolves()


def test_plugin_skill_rule_resolves_from_runtime_layout_without_repo_tree() -> None:
    assert versioned_sibling_plugin_resolution_holds()


def test_root_rule_resolves_from_git_root_when_cwd_is_subdirectory() -> None:
    assert root_rule_resolves_from_subdirectory()


def test_rule_slug_discovery_uses_declared_section_identity() -> None:
    assert declared_rule_slug_contract_holds()
