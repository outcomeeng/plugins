from outcomeeng_testing.harnesses.native_agent_recovery import (
    verify_native_agent_recovery_compliance,
)


def test_native_agent_recovery_compliance() -> None:
    assert verify_native_agent_recovery_compliance() == []
