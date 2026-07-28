from outcomeeng_testing.harnesses.native_agent_recovery import (
    observe_attested_controller_binding,
    observe_attested_controller_rejections,
    observe_wholly_intact_settlement,
    verify_native_agent_recovery_mappings,
)


def test_native_agent_recovery_mappings() -> None:
    assert verify_native_agent_recovery_mappings() == []


def test_wholly_intact_candidate_set_maps_to_recorded_identities() -> None:
    observed = observe_wholly_intact_settlement()
    assert observed.planned_status == observed.reassessment_ready_status
    assert observed.deliveries == []
    assert observed.judged_intact_sessions == observed.pending_sessions
    assert observed.settled_status == observed.reassessment_sent_status
    assert set(observed.judged_intact_sessions) <= set(observed.recorded_sessions)


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
