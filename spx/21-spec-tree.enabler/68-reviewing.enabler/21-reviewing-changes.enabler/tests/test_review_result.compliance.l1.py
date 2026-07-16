"""Compliance evidence for the canonical review-result contract."""

from outcomeeng_testing.harnesses.reviewing_changes import (
    declared_rule_slug_contract_holds,
    review_module_surface_contract_holds,
    review_parse_compliance_contract_holds,
    root_rule_resolves_from_subdirectory,
    rule_citation_contract_holds,
    runtime_skill_rule_resolves,
    versioned_sibling_plugin_resolution_holds,
)


def test_review_result_module_surface_contract() -> None:
    assert review_module_surface_contract_holds()


def test_parse_json_returns_review_result_on_conforming_document() -> None:
    assert review_parse_compliance_contract_holds()


def test_parse_json_accepts_declared_rule_citation_forms() -> None:
    assert rule_citation_contract_holds()


def test_plugin_skill_rule_can_resolve_absolute_runtime_path() -> None:
    assert runtime_skill_rule_resolves()


def test_plugin_skill_rule_resolves_from_runtime_layout_without_repo_tree() -> None:
    assert versioned_sibling_plugin_resolution_holds()


def test_root_rule_resolves_from_git_root_when_cwd_is_subdirectory() -> None:
    assert root_rule_resolves_from_subdirectory()


def test_rule_slug_discovery_uses_declared_section_identity() -> None:
    assert declared_rule_slug_contract_holds()
