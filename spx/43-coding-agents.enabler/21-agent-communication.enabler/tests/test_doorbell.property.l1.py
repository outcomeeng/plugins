from types import ModuleType

from outcomeeng_testing.harnesses.coding_agents import (
    run_doorbell_label_property,
    run_doorbell_roundtrip_property,
)


def test_rendered_doorbells_parse_back_to_sender_and_id() -> None:
    def assert_roundtrip(
        message: ModuleType, sender: str, message_id: int, label: str | None
    ) -> None:
        line = message.doorbell_text(sender, message_id, label)
        parsed = message.parse_doorbell(line, [sender])

        assert line.count("\n") == 0
        assert parsed[message.SENDER_FIELD] == sender
        assert parsed[message.RECORD_ID_FIELD] == message_id

    run_doorbell_roundtrip_property(assert_roundtrip)


def test_a_label_renders_labeled_only_when_it_prints_and_holds_no_delimiter() -> None:
    def assert_label(
        message: ModuleType,
        sender: str,
        message_id: int,
        label: str,
        renderable: bool,
    ) -> None:
        line = message.doorbell_text(sender, message_id, label)

        if renderable:
            assert line == f"[{label} <{sender}>] mail {message_id}"
            parsed = message.parse_doorbell(line, [sender])
            assert parsed[message.SENDER_FIELD] == sender
            assert parsed[message.RECORD_ID_FIELD] == message_id
        else:
            assert line == f"[{sender}] mail {message_id}"

    run_doorbell_label_property(assert_label)
