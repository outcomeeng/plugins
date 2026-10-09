from typing import cast

from outcomeeng_testing.generators.coding_agents import (
    mail_record_input,
    unrenderable_labels,
)
from outcomeeng_testing.harnesses.agent_mail import load_agent_mail
from outcomeeng_testing.harnesses.coding_agents import (
    load_agent_message,
    observe_unresolved_repository_mail_send,
    observe_absent_store_mail_send,
    observe_labeled_mail_send,
    observe_mail_send,
    observe_rejected_mail_send,
    observe_unlabeled_field_mail_send,
    observe_unreadable_store_reply_mail_send,
    observe_unsupported_operation_mail_send,
)


def test_every_sender_kind_maps_to_a_record_the_capability_accepts() -> None:
    message = load_agent_message()
    capability = load_agent_mail()

    records: list[dict[str, object]] = []
    for ordinal, kind in enumerate(message.RecordKind, start=1):
        request = mail_record_input(message, ordinal, kind)
        record = message.mail_request({**request})[message.RECORD_FIELD]
        records.append(record)

        assert record[message.KIND_FIELD] == kind
        assert set(record) == capability.RECORD_INPUT_FIELDS
        assert capability.validate_record(record, with_id=False) == record
        assert capability.RecordKind(str(record[message.KIND_FIELD]))
        stored = capability.store_fields_for(record)
        assert stored[capability.STORE_FROM_FIELD] == request[message.SENDER_FIELD]
        assert stored[capability.STORE_TO_FIELD] == request[message.RECIPIENT_FIELD]

    assert len({str(record[message.KIND_FIELD]) for record in records}) == len(
        message.RecordKind
    )


def test_checked_send_results_map_to_delivery_results() -> None:
    message = load_agent_message()
    capability = load_agent_mail()
    request = mail_record_input(message, 1, message.RecordKind.FACT)
    record = message.mail_request({**request})[message.RECORD_FIELD]

    delivered_capability = observe_mail_send(message, record)
    delivered = message.mail_delivery_result(delivered_capability)
    stored_record = cast(
        dict[str, object],
        cast(dict[str, object], delivered_capability[message.DATA_FIELD])[
            message.RECORD_FIELD
        ],
    )
    store_id = stored_record[message.RECORD_ID_FIELD]

    assert delivered[message.STATUS_FIELD] == message.DeliveryStatus.DELIVERED
    assert delivered[message.RECORD_ID_FIELD] == store_id
    assert delivered[message.SENDER_FIELD] == request[message.SENDER_FIELD]
    assert delivered[message.RECIPIENT_FIELD] == request[message.RECIPIENT_FIELD]
    assert (
        delivered[message.RECORD_CORRELATION_FIELD]
        == request[message.RECORD_CORRELATION_FIELD]
    )
    doorbell = cast(dict[str, object], delivered[message.DOORBELL_FIELD])
    resolved = message.parse_doorbell(
        doorbell[message.TEXT_FIELD], [request[message.SENDER_FIELD]]
    )
    assert resolved[message.SENDER_FIELD] == request[message.SENDER_FIELD]
    assert resolved[message.RECORD_ID_FIELD] == store_id
    assert doorbell[message.DOORBELL_SUBMITTED_FIELD] is False
    assert delivered[message.CAPABILITY_FIELD] == delivered_capability

    failed_statuses: set[object] = set()
    for failed_capability in (
        observe_rejected_mail_send(message, record),
        observe_absent_store_mail_send(message, record),
        observe_unresolved_repository_mail_send(message, record),
        observe_unreadable_store_reply_mail_send(message, record),
        observe_unsupported_operation_mail_send(message, record),
    ):
        failed = message.mail_delivery_result(failed_capability)
        assert failed[message.STATUS_FIELD] == message.DeliveryStatus.DELIVERY_FAILED
        assert (
            failed[message.CAPABILITY_STATUS_FIELD]
            == failed_capability[message.STATUS_FIELD]
        )
        assert failed[message.DETAIL_FIELD] == failed_capability[message.DETAIL_FIELD]
        assert failed[message.COMMAND_EXIT_CODE_FIELD] == failed_capability.get(
            message.COMMAND_EXIT_CODE_FIELD
        )
        assert message.RECORD_ID_FIELD not in failed
        assert failed_capability[message.STATUS_FIELD] not in failed_statuses
        failed_statuses.add(failed_capability[message.STATUS_FIELD])
    assert failed_statuses == set(capability.ExecutionStatus) - {
        capability.ExecutionStatus.SUCCEEDED
    }


def test_send_result_label_maps_to_the_doorbell_form() -> None:
    message = load_agent_message()
    capability = load_agent_mail()
    request = mail_record_input(message, 5, message.RecordKind.FACT)
    sender = cast(str, request[message.SENDER_FIELD])
    record = message.mail_request({**request})[message.RECORD_FIELD]

    def doorbell_line(capability_result: dict[str, object]) -> str:
        delivered = message.mail_delivery_result(capability_result)
        doorbell = cast(dict[str, object], delivered[message.DOORBELL_FIELD])
        return cast(str, doorbell[message.TEXT_FIELD])

    # The captured send result carries a renderable sender label.
    captured = observe_mail_send(message, record)
    response = cast(dict[str, object], captured[capability.RESPONSE_FIELD])
    label = response[capability.STORE_SENDER_DISPLAY_NAME_FIELD]
    store_id = response[capability.STORE_ID_FIELD]
    assert isinstance(label, str) and label
    assert doorbell_line(captured) == f"[{label} <{sender}>] mail {store_id}"

    # A null label and a reply carrying no label field are both unlabeled.
    for unlabeled in (
        observe_labeled_mail_send(message, record, None),
        observe_unlabeled_field_mail_send(message, record),
    ):
        assert doorbell_line(unlabeled) == f"[{sender}] mail {store_id}"

    # Every unrenderable label falls back to the unlabeled form while the full
    # label stays in the store metadata the delivery result carries.
    for unrenderable in unrenderable_labels():
        sent = observe_labeled_mail_send(message, record, unrenderable)
        delivered = message.mail_delivery_result(sent)
        kept = cast(
            dict[str, object],
            cast(dict[str, object], delivered[message.CAPABILITY_FIELD])[
                capability.RESPONSE_FIELD
            ],
        )
        assert doorbell_line(sent) == f"[{sender}] mail {store_id}"
        assert kept[capability.STORE_SENDER_DISPLAY_NAME_FIELD] == unrenderable
