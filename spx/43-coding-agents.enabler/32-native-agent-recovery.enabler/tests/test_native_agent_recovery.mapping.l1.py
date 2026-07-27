from outcomeeng_testing.harnesses.native_agent_recovery import (
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
