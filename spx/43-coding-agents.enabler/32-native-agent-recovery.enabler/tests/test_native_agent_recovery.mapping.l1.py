from outcomeeng_testing.harnesses.native_agent_recovery import (
    NonNativeOccupancyEvidence,
    native_agent_recovery_mapping_evidence,
    run_non_native_occupancy_mapping,
)


def _assert_non_native_occupancy(evidence: NonNativeOccupancyEvidence) -> None:
    assert evidence.status == evidence.expected_status
    assert evidence.occupied_pane_ids == evidence.expected_occupied_pane_ids
    assert evidence.target_field_sets == evidence.expected_target_field_sets
    assert evidence.send_count == 0


def test_native_agent_recovery_mappings() -> None:
    assert (
        native_agent_recovery_mapping_evidence().target_count
        == native_agent_recovery_mapping_evidence().selected_count
    )
    assert (
        native_agent_recovery_mapping_evidence().correlated_statuses
        == native_agent_recovery_mapping_evidence().expected_correlated_statuses
    )
    assert (
        native_agent_recovery_mapping_evidence().unoccupied_statuses
        == native_agent_recovery_mapping_evidence().expected_unoccupied_statuses
    )
    assert (
        native_agent_recovery_mapping_evidence().native_type_statuses
        == native_agent_recovery_mapping_evidence().expected_native_type_statuses
    )
    assert (
        native_agent_recovery_mapping_evidence().unknown_status
        == native_agent_recovery_mapping_evidence().expected_unknown_status
    )
    assert native_agent_recovery_mapping_evidence().unknown_send_count == 0
    assert (
        native_agent_recovery_mapping_evidence().duplicate_status
        == native_agent_recovery_mapping_evidence().expected_duplicate_status
    )
    assert (
        native_agent_recovery_mapping_evidence().multiple_status
        == native_agent_recovery_mapping_evidence().expected_multiple_status
    )
    assert (
        native_agent_recovery_mapping_evidence().multiple_target_field_sets
        == native_agent_recovery_mapping_evidence().expected_multiple_target_field_sets
    )
    assert native_agent_recovery_mapping_evidence().multiple_send_count == 0
    run_non_native_occupancy_mapping(_assert_non_native_occupancy)
