from outcomeeng_testing.harnesses.native_agent_recovery import (
    IdempotentRecovery,
    UnsupportedEvidence,
    drive_idempotent_recovery_property,
    drive_unsupported_evidence_property,
)


def test_repeated_recovery_of_a_correlated_set_emits_nothing() -> None:
    def check(observed: IdempotentRecovery) -> None:
        assert observed.activation_status == observed.ready_status
        assert observed.activations == []
        assert observed.recovery_status == observed.already_current_status
        assert observed.deliveries == []

    drive_idempotent_recovery_property(check)


def test_evidence_outside_the_source_contract_is_rejected() -> None:
    def check(observed: UnsupportedEvidence) -> None:
        assert observed.prepare_status == observed.invalid_schema_status

    drive_unsupported_evidence_property(check)
