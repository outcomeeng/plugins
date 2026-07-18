from outcomeeng_testing.harnesses.coding_agents import verify_agent_message_compliance


def test_agent_message_compliance() -> None:
    assert verify_agent_message_compliance() == []
