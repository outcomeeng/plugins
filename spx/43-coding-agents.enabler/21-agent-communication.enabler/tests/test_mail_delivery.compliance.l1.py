from typing import cast

import pytest

from outcomeeng_testing.generators.coding_agents import (
    delegation_authority,
    mail_record_input,
)
from outcomeeng_testing.harnesses.coding_agents import (
    load_agent_message,
    observe_doorbell_transport,
    observe_mail_send,
    public_message_context,
)


def test_doorbell_sender_resolves_only_in_the_live_inventory() -> None:
    message = load_agent_message()
    request = mail_record_input(message, 1, message.RecordKind.FACT)
    record = message.mail_request({**request})[message.RECORD_FIELD]
    delivered = message.mail_delivery_result(observe_mail_send(message, record))
    doorbell = cast(dict[str, object], delivered[message.DOORBELL_FIELD])
    line = cast(str, doorbell[message.TEXT_FIELD])
    sender = cast(str, delivered[message.SENDER_FIELD])
    recipient = cast(str, delivered[message.RECIPIENT_FIELD])

    resolved = message.parse_doorbell(line, [recipient, sender])
    assert resolved[message.SENDER_FIELD] == sender

    with pytest.raises(message.MessageError) as raised:
        message.parse_doorbell(line, [recipient])
    assert raised.value.status == message.DeliveryStatus.INVALID_IDENTITY

    for malformed in (f"{line}\n{line}", f"{line} and more", f"note {line}"):
        with pytest.raises(message.MessageError) as raised:
            message.parse_doorbell(malformed, [sender])
        assert raised.value.status == message.DeliveryStatus.INVALID_SCHEMA


def test_mail_delivery_requires_the_checked_capability_result() -> None:
    message = load_agent_message()
    _, _, recipient_pane, _ = public_message_context()
    request = mail_record_input(message, 2, message.RecordKind.ORDER)
    record = message.mail_request({**request})[message.RECORD_FIELD]
    capability = observe_mail_send(message, record)

    delivered = message.mail_delivery_result(capability)
    assert delivered[message.STATUS_FIELD] == message.DeliveryStatus.DELIVERED

    for omitted_field in message.MAIL_SUCCESS_FIELDS - {message.STATUS_FIELD}:
        incomplete = {
            key: value for key, value in capability.items() if key != omitted_field
        }
        with pytest.raises(message.MessageError) as raised:
            message.mail_delivery_result(incomplete)
        assert raised.value.status == message.DeliveryStatus.INVALID_SCHEMA

    with pytest.raises(message.MessageError) as raised:
        message.mail_delivery_result({**capability, message.COMMAND_EXIT_CODE_FIELD: 1})
    assert raised.value.status == message.DeliveryStatus.INVALID_SCHEMA

    data = cast(dict[str, object], capability[message.DATA_FIELD])
    stored = cast(dict[str, object], data[message.RECORD_FIELD])
    without_id = {
        **capability,
        message.DATA_FIELD: {
            message.RECORD_FIELD: {
                key: value
                for key, value in stored.items()
                if key != message.RECORD_ID_FIELD
            }
        },
    }
    with pytest.raises(message.MessageError) as raised:
        message.mail_delivery_result(without_id)
    assert raised.value.status == message.DeliveryStatus.INVALID_SCHEMA

    submitted = observe_doorbell_transport(
        recipient_pane[message.PANE_FIELD], trailing_enter_sent=True
    )
    unsubmitted = observe_doorbell_transport(
        recipient_pane[message.PANE_FIELD], trailing_enter_sent=False
    )
    with_submitted = message.mail_delivery_result(
        capability, doorbell_transport=submitted
    )
    with_unsubmitted = message.mail_delivery_result(
        capability, doorbell_transport=unsubmitted
    )
    without_transport = message.mail_delivery_result(capability)
    for result in (with_submitted, with_unsubmitted, without_transport):
        assert result[message.STATUS_FIELD] == message.DeliveryStatus.DELIVERED
    assert (
        cast(dict[str, object], with_submitted[message.DOORBELL_FIELD])[
            message.DOORBELL_SUBMITTED_FIELD
        ]
        is True
    )
    assert (
        cast(dict[str, object], with_unsubmitted[message.DOORBELL_FIELD])[
            message.DOORBELL_SUBMITTED_FIELD
        ]
        is False
    )
    assert (
        cast(dict[str, object], without_transport[message.DOORBELL_FIELD])[
            message.DOORBELL_SUBMITTED_FIELD
        ]
        is False
    )


def test_same_worktree_delegation_requires_complete_authority() -> None:
    message = load_agent_message()
    request = mail_record_input(message, 3, message.RecordKind.DELEGATION_REQUEST)
    sender = cast(str, request[message.SENDER_FIELD])
    authority = delegation_authority(message, sender, 3)

    record = message.mail_request({**request, message.AUTHORITY_FIELD: authority})[
        message.RECORD_FIELD
    ]
    assert cast(str, record[message.BODY_FIELD]).startswith(
        message.render_authority(authority)
    )
    assert cast(str, record[message.BODY_FIELD]).endswith(
        cast(str, request[message.BODY_FIELD])
    )

    for violating, status in (
        (
            {
                **authority,
                message.OWNER_FIELD: cast(str, request[message.RECIPIENT_FIELD]),
            },
            message.DeliveryStatus.INVALID_IDENTITY,
        ),
        (
            {**authority, message.WRITE_SCOPE_FIELD: []},
            message.DeliveryStatus.INVALID_SCHEMA,
        ),
        (
            {**authority, message.GIT_MUTATION_FIELD: True},
            message.DeliveryStatus.INVALID_SCHEMA,
        ),
        *(
            (
                {key: value for key, value in authority.items() if key != omitted},
                message.DeliveryStatus.INVALID_SCHEMA,
            )
            for omitted in message.AUTHORITY_FIELDS
        ),
    ):
        with pytest.raises(message.MessageError) as raised:
            message.mail_request({**request, message.AUTHORITY_FIELD: violating})
        assert raised.value.status == status

    fact = mail_record_input(message, 4, message.RecordKind.FACT)
    with pytest.raises(message.MessageError) as raised:
        message.mail_request({**fact, message.AUTHORITY_FIELD: authority})
    assert raised.value.status == message.DeliveryStatus.INVALID_SCHEMA
