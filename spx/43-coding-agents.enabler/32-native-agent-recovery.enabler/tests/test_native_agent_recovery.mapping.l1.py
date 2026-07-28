from outcomeeng_testing.harnesses.native_agent_recovery import (
    observe_activation_binding_mapping,
    observe_activation_request_mapping,
    observe_attested_controller_binding,
    observe_attested_controller_rejections,
    observe_bound_pane_occupancy,
    observe_bound_resolution_mapping,
    observe_prepared_manifest_mapping,
    observe_reassessment_planning_mapping,
    observe_wholly_intact_settlement,
    observe_worktree_role_mapping,
)


def test_exact_pre_restart_identity_maps_to_one_durable_candidate() -> None:
    observed = observe_prepared_manifest_mapping()
    assert observed.exact_status == observed.prepared_status
    assert observed.candidate_count == observed.expected_candidate_count
    assert observed.resume_locators == observed.expected_resume_locators
    assert observed.candidates_missing_native_home == []
    assert observed.non_public_hint_status == observed.prepared_status


def test_incomplete_or_duplicate_evidence_maps_to_non_mutating_failure() -> None:
    observed = observe_prepared_manifest_mapping()
    assert observed.conflicting_public_session_status == observed.invalid_target_status
    assert observed.duplicate_session_status == observed.invalid_target_status
    assert observed.lone_secondary_status == observed.invalid_target_status
    assert observed.duplicate_controller_status == observed.invalid_target_status


def test_absent_worktrees_map_to_exact_root_activation_requests() -> None:
    observed = observe_activation_request_mapping()
    assert observed.binding_count == observed.expected_binding_count
    assert observed.activation_count == observed.expected_activation_count
    assert observed.activation_operations == observed.expected_activation_operations


def test_only_an_exact_root_activation_result_binds_its_prepared_target() -> None:
    observed = observe_activation_binding_mapping()
    assert observed.bound_count == observed.expected_bound_count
    assert observed.existing_target_status == observed.ready_status
    assert observed.new_root_status == observed.invalid_target_status
    assert observed.mixed_status == observed.command_failed_status
    assert observed.mixed_result_count == observed.expected_mixed_result_count
    assert observed.mixed_binding_count == observed.expected_mixed_binding_count


def test_attested_controller_pane_maps_to_its_own_candidate_binding() -> None:
    observed = observe_attested_controller_binding()
    assert observed.unattested_activation_status == observed.pane_occupied_status
    assert observed.attested_activation_status == observed.ready_status
    assert observed.attested_bound_pane_ids == [observed.attested_pane_id]
    assert observed.attested_controller_resolutions == [
        observed.already_correlated_status
    ]


def test_unidentifying_attestation_maps_to_non_mutating_failure() -> None:
    observed = observe_attested_controller_rejections()
    assert observed.absent_current_session_status == observed.invalid_target_status
    assert observed.absent_pane_status == observed.invalid_target_status
    assert observed.foreign_worktree_status == observed.invalid_target_status
    assert observed.multiple_agents_status == observed.invalid_target_status
    assert observed.foreign_agent_type_status == observed.invalid_target_status
    assert observed.foreign_session_status == observed.invalid_target_status


def test_each_bound_candidate_maps_to_its_occupancy_resolution() -> None:
    observed = observe_bound_resolution_mapping()
    assert observed.occupied_resolutions == (
        [observed.already_correlated_status] * observed.correlated_count
    )
    assert observed.unoccupied_resolutions == (
        [observed.resumed_status] * observed.unoccupied_count
    )
    assert observed.mismatched_occupant_status == observed.pane_occupied_status


def test_a_bound_pane_another_session_holds_maps_to_non_mutating_failure() -> None:
    observed = observe_bound_pane_occupancy()
    assert observed.matching_status == observed.resumed_status
    assert observed.mismatched_session_status == observed.pane_occupied_status
    assert observed.mismatched_type_status == observed.pane_occupied_status
    assert observed.duplicate_agent_status == observed.pane_occupied_status
    assert observed.mismatched_session_targets == []
    assert observed.mismatched_session_deliveries == []
    assert observed.occupied_pane_ids == observed.held_pane_ids


def test_one_worktree_admits_one_primary_and_authorized_secondaries() -> None:
    observed = observe_worktree_role_mapping()
    assert observed.two_primaries_status == observed.invalid_target_status
    assert (
        observed.authorized_secondary_operations
        == observed.expected_secondary_operations
    )


def test_the_read_barrier_and_destroyed_facts_map_to_reassessment_planning() -> None:
    observed = observe_reassessment_planning_mapping()
    assert observed.incomplete_barrier_status == observed.invalid_schema_status
    assert observed.failed_read_status == observed.command_failed_status
    assert observed.failed_read_deliveries == []
    assert observed.delivery_count == observed.supplied_fact_count
    assert observed.judged_intact_sessions == observed.expected_judged_intact_sessions
    assert observed.deliveries_to_judged_intact == []


def test_wholly_intact_candidate_set_maps_to_recorded_identities() -> None:
    observed = observe_wholly_intact_settlement()
    assert observed.planned_status == observed.reassessment_ready_status
    assert observed.deliveries == []
    assert observed.judged_intact_sessions == observed.pending_sessions
    assert observed.settled_status == observed.reassessment_sent_status
    assert set(observed.judged_intact_sessions) <= set(observed.recorded_sessions)
