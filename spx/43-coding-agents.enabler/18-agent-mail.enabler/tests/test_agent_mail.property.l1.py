from types import ModuleType
from typing import cast

from outcomeeng_testing.harnesses.agent_mail import (
    run_record_roundtrip_property,
    run_terminal_property,
    store_inbox_echo,
)


def test_message_records_round_trip_through_the_store_fields() -> None:
    def assert_roundtrip(
        module: ModuleType, record: dict[str, object], message_id: int, row_ordinal: int
    ) -> None:
        send_fields = module.store_fields_for(record)
        subject = cast(str, send_fields[module.STORE_SUBJECT_FIELD])
        read_back = module.record_from_inbox_item(
            store_inbox_echo(module, send_fields, message_id, row_ordinal),
            recipient=cast(str, record[module.RECIPIENT_FIELD]),
        )

        assert read_back == {**record, module.RECORD_ID_FIELD: message_id}
        assert subject.count(module.KIND_PREFIX_CLOSE) >= 1
        assert (
            send_fields[module.STORE_ACK_REQUIRED_FIELD]
            is record[module.ACK_REQUIRED_FIELD]
        )

    run_record_roundtrip_property(assert_roundtrip)


def test_terminal_handbacks_reduce_to_exactly_one_result() -> None:
    def assert_terminal(
        module: ModuleType,
        reference: str,
        first_kind: object,
        second_kind: object,
        content: dict[str, str],
    ) -> None:
        first = module.terminal_handback(
            kind=first_kind,
            correlation=reference,
            sender=content[module.SENDER_FIELD],
            recipient=content[module.RECIPIENT_FIELD],
            subject=content[module.RECORD_SUBJECT_FIELD],
            body=content[module.BODY_FIELD],
        )
        second = {**first, module.KIND_FIELD: second_kind}

        assert first[module.CORRELATION_FIELD] == reference
        assert module.reduce_terminal(None, first) == first
        assert module.reduce_terminal(first, first) == first
        if second_kind == first_kind:
            return
        try:
            module.reduce_terminal(first, second)
        except module.AgentMailError as error:
            assert error.status == module.ExecutionStatus.INVALID_SCHEMA
        else:
            raise AssertionError(
                "conflicting terminal kinds for one reference were accepted"
            )

    run_terminal_property(assert_terminal)
