from types import ModuleType
from typing import cast

import pytest

from outcomeeng_testing.harnesses.agent_mail import (
    ConflictingHandbackCase,
    RecordingRunner,
    TerminalCase,
    argv_option_values,
    run_conflicting_handback_property,
    run_delegation_chain_property,
    run_record_roundtrip_property,
    run_terminal_property,
    store_listing_echo,
    usage_contract_for,
)


def test_message_records_round_trip_through_the_store_fields() -> None:
    def assert_roundtrip(
        module: ModuleType,
        record: dict[str, object],
        message_id: int,
        row_ordinal: int,
        store_rejected: frozenset[str],
    ) -> None:
        send_fields = module.store_fields_for(record)
        thread = cast(str, send_fields[module.STORE_THREAD_ID_FIELD])
        read_back = module.record_from_inbox_item(
            store_listing_echo(module, send_fields, message_id, row_ordinal),
            recipient=cast(str, record[module.RECIPIENT_FIELD]),
        )

        assert read_back == {**record, module.RECORD_ID_FIELD: message_id}
        assert (
            send_fields[module.STORE_ACK_REQUIRED_FIELD]
            is record[module.ACK_REQUIRED_FIELD]
        )
        # Every thread the adapter writes is one the store's alphabet admits, and
        # a correlation the store refused as a thread never reaches it verbatim.
        assert module.THREAD_ID_PATTERN.fullmatch(thread), thread
        if record[module.CORRELATION_FIELD] in store_rejected:
            assert thread != record[module.CORRELATION_FIELD]

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

        # Every record reached the store through this capability's own command,
        # all three under one thread that reads back as the reference.
        contract = usage_contract_for(module, module.Operation.SEND)
        sent = [argv for argv, _ in runner.calls if argv[0] == module.AM_COMMAND]
        assert len(sent) == len(chain)
        threads: set[str | None] = set()
        for record, argv in zip(chain, sent, strict=True):
            bound = argv_option_values(contract, argv)
            threads.update(
                bound[module.PUBLIC_AM_RECORD_OPTIONS[module.CORRELATION_FIELD]]
            )
            assert bound[
                module.PUBLIC_AM_RECORD_OPTIONS[module.RECORD_SUBJECT_FIELD]
            ] == [
                f"{module.KIND_PREFIX_OPEN}{record[module.KIND_FIELD]}"
                f"{module.KIND_PREFIX_CLOSE}{record[module.RECORD_SUBJECT_FIELD]}"
            ]
        assert len(threads) == 1
        (thread,) = threads
        assert thread is not None
        assert module.correlation_for(thread) == reference

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
    def assert_terminal(module: ModuleType, case: TerminalCase) -> None:
        def handback(kind: object, reference: str, content: dict[str, str]) -> object:
            return module.terminal_handback(
                kind=kind,
                correlation=reference,
                sender=content[module.SENDER_FIELD],
                recipient=content[module.RECIPIENT_FIELD],
                subject=content[module.RECORD_SUBJECT_FIELD],
                body=content[module.BODY_FIELD],
            )

        first = cast(
            dict[str, object], handback(case.first_kind, case.reference, case.content)
        )
        rejection = module.TerminalHandbackRejected

        # The first handback is the result; a matching repeat is idempotent.
        assert first[module.CORRELATION_FIELD] == case.reference
        assert module.reduce_terminal(None, first) == first
        assert module.reduce_terminal(first, first) == first

        # Another terminal kind for the reference is a kind conflict.
        if case.second_kind != case.first_kind:
            with pytest.raises(rejection) as conflict:
                module.reduce_terminal(
                    first, {**first, module.KIND_FIELD: case.second_kind}
                )
            assert conflict.value.rejection == module.HandbackRejection.KIND_CONFLICT
            assert conflict.value.status == module.ExecutionStatus.INVALID_SCHEMA
            assert {
                change.name: (change.current, change.incoming)
                for change in conflict.value.differences
            } == {module.KIND_FIELD: (case.first_kind, case.second_kind)}

        # A handback for another reference never reduces onto this one's state.
        elsewhere = handback(case.first_kind, case.other_reference, case.content)
        with pytest.raises(rejection) as mismatch:
            module.reduce_terminal(first, elsewhere)
        assert mismatch.value.rejection == module.HandbackRejection.REFERENCE_MISMATCH

        # A kind that closes no delegation is no terminal handback, whether it
        # arrives or is the state it would reduce onto.
        with pytest.raises(rejection) as built:
            handback(case.non_terminal_kind, case.reference, case.content)
        assert built.value.rejection == module.HandbackRejection.NOT_TERMINAL
        open_record = {**first, module.KIND_FIELD: case.non_terminal_kind}
        with pytest.raises(rejection) as arriving:
            module.reduce_terminal(first, open_record)
        assert arriving.value.rejection == module.HandbackRejection.NOT_TERMINAL
        with pytest.raises(rejection) as current:
            module.reduce_terminal(open_record, first)
        assert current.value.rejection == module.HandbackRejection.NOT_TERMINAL

    run_terminal_property(assert_terminal)


def test_a_same_kind_handback_with_other_content_is_a_conflicting_handback() -> None:
    def assert_conflicting(module: ModuleType, case: ConflictingHandbackCase) -> None:
        def handback(content: dict[str, str]) -> dict[str, object]:
            return cast(
                dict[str, object],
                module.terminal_handback(
                    kind=case.kind,
                    correlation=case.reference,
                    sender=content[module.SENDER_FIELD],
                    recipient=content[module.RECIPIENT_FIELD],
                    subject=content[module.RECORD_SUBJECT_FIELD],
                    body=content[module.BODY_FIELD],
                ),
            )

        first = handback(case.content)
        second = handback(case.other_content)
        # The content difference is read from the two generated contents,
        # never from the records the adapter built from them.
        difference = {
            name: (value, case.other_content[name])
            for name, value in case.content.items()
            if case.other_content[name] != value
        }

        with pytest.raises(module.TerminalHandbackRejected) as conflicting:
            module.reduce_terminal(first, second)
        rejected = conflicting.value

        # Rejected as a conflicting handback, never as a kind conflict.
        assert rejected.rejection == module.HandbackRejection.CONFLICTING_HANDBACK

        # The detail names every changed field with the value it held and the
        # value the second handback carries, and names no unchanged field.
        named = {
            change.name: (change.current, change.incoming)
            for change in rejected.differences
        }
        assert len(named) == len(rejected.differences)
        assert named == difference
        detail = str(rejected)
        for name, (current, incoming) in difference.items():
            assert name in detail
            assert repr(current) in detail
            assert repr(incoming) in detail

    run_conflicting_handback_property(assert_conflicting)
