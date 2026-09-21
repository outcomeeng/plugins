from types import ModuleType
from typing import cast

from outcomeeng_testing.harnesses.agent_mail import (
    RecordingRunner,
    run_delegation_chain_property,
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


def test_an_order_its_delegation_request_and_its_handback_are_delivered() -> None:
    def assert_chain(
        module: ModuleType,
        reference: str,
        chain: list[dict[str, object]],
        runner: RecordingRunner,
    ) -> None:
        kinds = [record[module.KIND_FIELD] for record in chain]
        assert kinds[0] == module.RecordKind.ORDER
        assert kinds[1] == module.RecordKind.DELEGATION_REQUEST
        assert kinds[2] in module.TERMINAL_KINDS

        delivered: list[dict[str, object]] = []
        for record in chain:
            assert record[module.CORRELATION_FIELD] == reference
            result = cast(
                dict[str, object],
                module.execute(
                    module.operation_request(module.Operation.SEND, record=record),
                    runner,
                ),
            )
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED, (
                record[module.KIND_FIELD]
            )
            data = cast(dict[str, object], result[module.DATA_FIELD])
            delivered.append(cast(dict[str, object], data[module.RECORD_FIELD]))

        # Every record reached the store through this capability's own command.
        sent = [argv for argv, _ in runner.calls if argv[0] == module.AM_COMMAND]
        assert len(sent) == len(chain)
        for record, argv in zip(chain, sent, strict=True):
            assert (
                module.attached_option(
                    module.PUBLIC_AM_RECORD_OPTIONS[module.CORRELATION_FIELD],
                    reference,
                )
                in argv
            )
            assert (
                module.attached_option(
                    module.PUBLIC_AM_RECORD_OPTIONS[module.RECORD_SUBJECT_FIELD],
                    f"{module.KIND_PREFIX_OPEN}{record[module.KIND_FIELD]}"
                    f"{module.KIND_PREFIX_CLOSE}{record[module.RECORD_SUBJECT_FIELD]}",
                )
                in argv
            )

        # The delivered handback carries the store's id and the reference the
        # order opened; reduction runs over the record the sender wrote, which
        # carries no store id.
        assert module.RECORD_ID_FIELD in delivered[-1]
        assert delivered[-1][module.CORRELATION_FIELD] == reference
        handback = chain[-1]
        reduced = module.reduce_terminal(None, handback)
        assert reduced[module.CORRELATION_FIELD] == reference
        assert module.reduce_terminal(handback, handback) == handback

    run_delegation_chain_property(assert_chain)


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
