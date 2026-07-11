"""Mapping evidence for pickup claim verification."""

from outcomeeng_testing.harnesses.verify_session_claims import (
    clean_state_is_confirmed,
    current_session_frontmatter_shape_still_emits_claims,
    dirty_state_is_discrepancy,
    external_id_surfaces_changed_state,
    full_hex_branch_on_origin_confirms,
    git_ref_branch_absent_from_origin_is_discrepancy,
    git_ref_branch_on_origin_confirms,
    git_ref_unreachable_sha_is_discrepancy,
    hex_like_branch_on_origin_confirms,
    missing_injected_path_is_discrepancy,
    node_status_evidence_excludes_child_tree,
    node_status_surfaces_changed_value,
    session_command_unavailable_is_unverifiable,
    session_load_failure_is_unverifiable,
    session_prose_load_failure_is_unverifiable,
    spec_entry_emits_both_path_and_node_status,
    unavailable_external_id_is_unverifiable,
    unavailable_git_ref_is_unverifiable,
    unavailable_git_status_is_unverifiable,
    unavailable_node_status_is_unverifiable,
)


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


def test_git_ref_unreachable_sha_is_discrepancy() -> None:
    assert git_ref_unreachable_sha_is_discrepancy()


def test_current_session_frontmatter_shape_still_emits_claims() -> None:
    assert current_session_frontmatter_shape_still_emits_claims()


def test_session_load_failure_is_unverifiable() -> None:
    assert session_load_failure_is_unverifiable()


def test_session_command_unavailable_is_unverifiable() -> None:
    assert session_command_unavailable_is_unverifiable()


def test_session_prose_load_failure_is_unverifiable() -> None:
    assert session_prose_load_failure_is_unverifiable()


def test_missing_injected_path_is_discrepancy() -> None:
    assert missing_injected_path_is_discrepancy()


def test_unavailable_node_status_is_unverifiable() -> None:
    assert unavailable_node_status_is_unverifiable()


def test_dirty_state_is_discrepancy() -> None:
    assert dirty_state_is_discrepancy()


def test_clean_state_is_confirmed() -> None:
    assert clean_state_is_confirmed()


def test_unavailable_git_ref_is_unverifiable() -> None:
    assert unavailable_git_ref_is_unverifiable()


def test_unavailable_git_status_is_unverifiable() -> None:
    assert unavailable_git_status_is_unverifiable()


def test_unavailable_external_id_is_unverifiable() -> None:
    assert unavailable_external_id_is_unverifiable()
