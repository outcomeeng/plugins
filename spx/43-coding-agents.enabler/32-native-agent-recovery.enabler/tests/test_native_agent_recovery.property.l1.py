from outcomeeng_testing.harnesses.native_agent_recovery import (
    AdvisoryStatusEligibility,
    IdempotentRecovery,
    UnsupportedEvidence,
    drive_advisory_status_property,
    drive_idempotent_recovery_property,
    drive_unsupported_evidence_property,
)


def test_repeated_recovery_of_a_correlated_set_emits_nothing() -> None:
    def check(observed: IdempotentRecovery) -> None:
        assert observed.activation_status == observed.ready_status
        assert observed.activations == []
        assert observed.recovery_status == observed.already_current_status
        assert observed.deliveries == []
        assert observed.repeated_reassessment_status == observed.already_current_status
        assert observed.repeated_reassessment_deliveries == []

    drive_idempotent_recovery_property(check)


def test_evidence_outside_the_source_contract_is_rejected() -> None:
    def check(observed: UnsupportedEvidence) -> None:
        assert observed.prepare_status == observed.invalid_schema_status
        assert observed.verify_status == observed.invalid_schema_status

    drive_unsupported_evidence_property(check)


def test_any_prowl_status_leaves_eligibility_unchanged() -> None:
    def check(observed: AdvisoryStatusEligibility) -> None:
        assert observed.observed_status == observed.prepared_status

    drive_advisory_status_property(check)
