from outcomeeng_testing.harnesses.native_agent_recovery import (
    verify_native_agent_recovery_properties,
)


def test_native_agent_recovery_idempotence() -> None:
    assert verify_native_agent_recovery_properties() == []
