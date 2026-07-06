"""Mapping evidence for pickup claim verification."""

from outcomeeng_testing.harnesses.verify_session_claims import (
    all_claim_mapping_cases_map_to_verdict,
    current_session_frontmatter_shape_still_emits_claims,
    external_id_surfaces_changed_state,
    full_hex_branch_on_origin_confirms,
    git_ref_branch_absent_from_origin_is_discrepancy,
    git_ref_branch_on_origin_confirms,
    hex_like_branch_on_origin_confirms,
    node_status_evidence_excludes_child_tree,
    node_status_surfaces_changed_value,
    session_load_failure_is_unverifiable,
    spec_entry_emits_both_path_and_node_status,
)


def test_claim_maps_to_verdict() -> None:
    assert all_claim_mapping_cases_map_to_verdict()


def test_node_status_surfaces_changed_value() -> None:
    assert node_status_surfaces_changed_value()


def test_node_status_evidence_excludes_child_tree() -> None:
    assert node_status_evidence_excludes_child_tree()


def test_external_id_surfaces_changed_state() -> None:
    assert external_id_surfaces_changed_state()


def test_spec_entry_emits_both_path_and_node_status() -> None:
    assert spec_entry_emits_both_path_and_node_status()


def test_git_ref_branch_on_origin_confirms() -> None:
    assert git_ref_branch_on_origin_confirms()


def test_hex_like_branch_on_origin_confirms() -> None:
    assert hex_like_branch_on_origin_confirms()


def test_full_hex_branch_on_origin_confirms() -> None:
    assert full_hex_branch_on_origin_confirms()


def test_git_ref_branch_absent_from_origin_is_discrepancy() -> None:
    assert git_ref_branch_absent_from_origin_is_discrepancy()


def test_current_session_frontmatter_shape_still_emits_claims() -> None:
    assert current_session_frontmatter_shape_still_emits_claims()


def test_session_load_failure_is_unverifiable() -> None:
    assert session_load_failure_is_unverifiable()
