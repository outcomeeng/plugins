from outcomeeng_testing.harnesses.native_agent_recovery import (
    RecoveryIdempotenceEvidence,
    run_native_agent_recovery_idempotence,
)


def _assert_idempotent_recovery(evidence: RecoveryIdempotenceEvidence) -> None:
    assert (
        evidence.result[evidence.module.STATUS_FIELD]
        == evidence.module.ResultStatus.ALREADY_CURRENT
    )
    assert evidence.send_count == 0
    assert evidence.remaining_result_count == 0


def test_native_agent_recovery_idempotence() -> None:
    run_native_agent_recovery_idempotence(_assert_idempotent_recovery)
