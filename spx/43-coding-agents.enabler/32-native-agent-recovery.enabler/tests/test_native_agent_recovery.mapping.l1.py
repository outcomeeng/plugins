from outcomeeng_testing.harnesses.native_agent_recovery import (
    verify_native_agent_recovery_mappings,
)


def test_native_agent_recovery_mappings() -> None:
    assert verify_native_agent_recovery_mappings() == []
