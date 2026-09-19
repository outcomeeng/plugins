from types import ModuleType

from outcomeeng_testing.harnesses.coding_agents import (
    run_doorbell_roundtrip_property,
)


def test_rendered_doorbells_parse_back_to_sender_and_id() -> None:
    def assert_roundtrip(message: ModuleType, sender: str, message_id: int) -> None:
        line = message.doorbell_text(sender, message_id)
        parsed = message.parse_doorbell(line, [sender])

        assert line.count("\n") == 0
        assert parsed[message.SENDER_FIELD] == sender
        assert parsed[message.RECORD_ID_FIELD] == message_id

    run_doorbell_roundtrip_property(assert_roundtrip)
