import json
import uuid
from io import StringIO
from typing import cast

import pytest

from outcomeeng_testing.generators.coding_agents import (
    message_content,
)
from outcomeeng_testing.harnesses.coding_agents import (
    fact_envelope,
    generated_envelope,
    mutation_observation,
    observe_send_transport,
    production_handback,
    public_message_context,
)


def test_delivery_preserves_complete_public_identities_and_semantic_payload() -> None:
    module, sender, recipient, _ = public_message_context()

    envelope = fact_envelope(module, sender, recipient)
    delivery = module.delivery_request(envelope)
    assert delivery[module.TO_PANE_FIELD] == recipient[module.PANE_FIELD]
    assert json.loads(cast(str, delivery[module.TEXT_FIELD])) == envelope


def test_delivery_requires_complete_checked_transport_evidence() -> None:
    module, sender, recipient, _ = public_message_context()
    envelope = fact_envelope(module, sender, recipient)
    transport = observe_send_transport(recipient[module.PANE_FIELD])

    result = module.delivery_result(
        envelope,
        delivered=True,
        command_exit_code=0,
        transport=transport,
    )
    assert result[module.STATUS_FIELD] == module.DeliveryStatus.DELIVERED

    invalid_transports: list[object] = [None]
    invalid_transports.extend(
        {key: value for key, value in transport.items() if key != omitted_field}
        for omitted_field in module.TRANSPORT_SUCCESS_FIELDS
    )
    invalid_transports.extend(
        (
            {
                **transport,
                module.TRANSPORT_OPERATION_FIELD: (
                    f"not-{module.TRANSPORT_SEND_OPERATION}"
                ),
            },
            {
                **transport,
                module.STATUS_FIELD: f"not-{module.TRANSPORT_SUCCEEDED_STATUS}",
            },
            {**transport, module.COMMAND_EXIT_CODE_FIELD: 1},
            {
                **transport,
                module.TRANSPORT_RESPONSE_FIELD: {
                    module.DATA_FIELD: {
                        module.INPUT_FIELD: {
                            module.TRAILING_ENTER_SENT_FIELD: False,
                        }
                    }
                },
            },
        )
    )
    for invalid_transport in invalid_transports:
        with pytest.raises(module.MessageError) as raised:
            module.delivery_result(
                envelope,
                delivered=True,
                command_exit_code=0,
                transport=invalid_transport,
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_SCHEMA

    with pytest.raises(module.MessageError) as raised:
        module.delivery_result(
            envelope,
            delivered=True,
            command_exit_code=1,
            transport=transport,
        )
    assert raised.value.status == module.DeliveryStatus.INVALID_SCHEMA


def test_transport_success_establishes_no_coordination_state() -> None:
    module, sender, recipient, _ = public_message_context()
    result = module.delivery_result(
        fact_envelope(module, sender, recipient),
        delivered=True,
        command_exit_code=0,
        transport=observe_send_transport(recipient[module.PANE_FIELD]),
    )

    assert result[module.ACKNOWLEDGED_FIELD] is False
    assert result[module.AGREED_FIELD] is False
    assert result[module.OWNERSHIP_ESTABLISHED_FIELD] is False


def test_envelopes_reject_incomplete_participant_identities() -> None:
    module, sender, recipient, _ = public_message_context()

    for label, identity in (
        (module.SENDER_FIELD, sender),
        (module.RECIPIENT_FIELD, recipient),
    ):
        for identity_field in module.IDENTITY_FIELDS:
            invalid = {
                key: value for key, value in identity.items() if key != identity_field
            }
            with pytest.raises(module.MessageError):
                generated_envelope(
                    module,
                    kind=module.MessageKind.FACT,
                    sender=invalid if label == module.SENDER_FIELD else sender,
                    recipient=(
                        invalid if label == module.RECIPIENT_FIELD else recipient
                    ),
                    ordinal=20,
                )

        invalid_run = {**identity, module.RUN_FIELD: ""}
        with pytest.raises(module.MessageError):
            generated_envelope(
                module,
                kind=module.MessageKind.FACT,
                sender=invalid_run if label == module.SENDER_FIELD else sender,
                recipient=(
                    invalid_run if label == module.RECIPIENT_FIELD else recipient
                ),
                ordinal=21,
            )


def test_mutation_messages_require_exact_target_and_observed_state() -> None:
    module, sender, recipient, _ = public_message_context()
    active_reference = str(
        uuid.uuid5(uuid.NAMESPACE_URL, sender[module.WORKTREE_FIELD])
    )
    sender_target, sender_state = mutation_observation(module, sender)
    recipient_target, recipient_state = mutation_observation(module, recipient)
    proposal_content = message_content(
        module.MessageKind.OWNERSHIP_PROPOSAL, 10, request_required=True
    )
    state_content = message_content(module.MessageKind.MUTATION_STATE, 11)
    authorization_content = message_content(
        module.MessageKind.MUTATION_AUTHORIZATION, 12, request_required=True
    )
    mutation_envelopes = (
        module.build_envelope(
            kind=module.MessageKind.OWNERSHIP_PROPOSAL,
            sender=sender,
            recipient=recipient,
            subject=proposal_content.subject,
            facts=list(proposal_content.facts),
            request=proposal_content.request,
            mutation_target=recipient_target,
        ),
        module.build_envelope(
            kind=module.MessageKind.MUTATION_STATE,
            sender=sender,
            recipient=recipient,
            subject=state_content.subject,
            facts=list(state_content.facts),
            request=state_content.request,
            active_reference=active_reference,
            mutation_target=sender_target,
            observed_state=sender_state,
        ),
        module.build_envelope(
            kind=module.MessageKind.MUTATION_AUTHORIZATION,
            sender=sender,
            recipient=recipient,
            subject=authorization_content.subject,
            facts=list(authorization_content.facts),
            request=authorization_content.request,
            active_reference=active_reference,
            mutation_target=recipient_target,
            observed_state=recipient_state,
        ),
    )
    for envelope in mutation_envelopes:
        assert module.validate_envelope(envelope) == envelope

    for identity_field in (
        module.PANE_FIELD,
        module.WORKTREE_FIELD,
        module.BRANCH_FIELD,
        module.REPOSITORY_FIELD,
    ):
        mismatched_value = sender[identity_field]
        if mismatched_value == recipient_target[identity_field]:
            mismatched_value = f"{mismatched_value}-different"
        mismatched = {**recipient_target, identity_field: mismatched_value}
        with pytest.raises(module.MessageError) as raised:
            generated_envelope(
                module,
                kind=module.MessageKind.OWNERSHIP_PROPOSAL,
                sender=sender,
                recipient=recipient,
                ordinal=22,
                request_required=True,
                mutation_target=mismatched,
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_IDENTITY

    for invalid_target in (
        {**recipient_target, module.HEAD_FIELD: "f" * 39},
        {**recipient_target, module.STATUS_FIELD: ""},
    ):
        with pytest.raises(module.MessageError) as raised:
            generated_envelope(
                module,
                kind=module.MessageKind.OWNERSHIP_PROPOSAL,
                sender=sender,
                recipient=recipient,
                ordinal=23,
                request_required=True,
                mutation_target=invalid_target,
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_SCHEMA

    for stale_target in (
        {**recipient_target, module.HEAD_FIELD: "f" * 40},
        {**recipient_target, module.STATUS_FIELD: "dirty"},
    ):
        with pytest.raises(module.MessageError) as raised:
            generated_envelope(
                module,
                kind=module.MessageKind.MUTATION_AUTHORIZATION,
                sender=sender,
                recipient=recipient,
                ordinal=24,
                active_reference=active_reference,
                mutation_target=stale_target,
                observed_state=recipient_state,
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_IDENTITY

    for state_field in module.OBSERVED_STATE_FIELDS:
        if state_field == module.HEAD_FIELD:
            mismatched_value = "f" * 40
        elif state_field == module.STATUS_FIELD:
            mismatched_value = "dirty"
        else:
            candidate = sender.get(state_field, "different")
            mismatched_value = (
                candidate if candidate != recipient_state[state_field] else "different"
            )
        with pytest.raises(module.MessageError) as raised:
            generated_envelope(
                module,
                kind=module.MessageKind.MUTATION_AUTHORIZATION,
                sender=sender,
                recipient=recipient,
                ordinal=25,
                active_reference=active_reference,
                mutation_target=recipient_target,
                observed_state={**recipient_state, state_field: mismatched_value},
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_IDENTITY

    for stale_target in (
        {**sender_target, module.HEAD_FIELD: "f" * 40},
        {**sender_target, module.STATUS_FIELD: "dirty"},
    ):
        with pytest.raises(module.MessageError) as raised:
            generated_envelope(
                module,
                kind=module.MessageKind.MUTATION_STATE,
                sender=sender,
                recipient=recipient,
                ordinal=26,
                active_reference=active_reference,
                mutation_target=stale_target,
                observed_state=sender_state,
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_IDENTITY

    for state_field in module.OBSERVED_STATE_FIELDS:
        if state_field == module.HEAD_FIELD:
            mismatched_value = "f" * 40
        elif state_field == module.STATUS_FIELD:
            mismatched_value = "dirty"
        else:
            candidate = recipient.get(state_field, "different")
            mismatched_value = (
                candidate if candidate != sender_state[state_field] else "different"
            )
        with pytest.raises(module.MessageError) as raised:
            generated_envelope(
                module,
                kind=module.MessageKind.MUTATION_STATE,
                sender=sender,
                recipient=recipient,
                ordinal=27,
                active_reference=active_reference,
                mutation_target=sender_target,
                observed_state={**sender_state, state_field: mismatched_value},
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_IDENTITY


def test_send_request_targets_only_exact_pane_identity() -> None:
    module, sender, recipient, discovery = public_message_context()
    request_content = message_content(module.MessageKind.FACT, 28)
    valid_request = module.build_request(
        to_pane=recipient[module.PANE_FIELD],
        kind=module.MessageKind.FACT,
        subject=request_content.subject,
        facts=list(request_content.facts),
        request=request_content.request,
    )
    built = module.send_request(valid_request, discovery)
    assert (
        built[module.DELIVERY_FIELD][module.TO_PANE_FIELD]
        == recipient[module.PANE_FIELD]
    )

    with pytest.raises(module.MessageError) as raised:
        module.send_request(
            {**valid_request, module.TO_PANE_FIELD: sender[module.PANE_FIELD]},
            {
                **discovery,
                module.TARGETS_FIELD: [
                    sender,
                    *cast(list[object], discovery[module.TARGETS_FIELD]),
                ],
            },
        )
    assert raised.value.status == module.DeliveryStatus.INVALID_IDENTITY

    for invalid_discovery in (
        {**discovery, module.STATUS_FIELD: "identity-unavailable"},
        {**discovery, module.STATUS_FIELD: "identity-ambiguous"},
    ):
        with pytest.raises(module.MessageError) as raised:
            module.send_request(valid_request, invalid_discovery)
        assert raised.value.status == module.DeliveryStatus.INVALID_IDENTITY

    for forbidden_field in module.FORBIDDEN_TARGET_FIELDS:
        with pytest.raises(module.MessageError) as raised:
            module.send_request(
                {**valid_request, forbidden_field: forbidden_field}, discovery
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_SCHEMA

    for executable_field in (
        module.COMMAND_FIELD,
        "handbackCommand",
        "returnPane",
        module.ADAPTER_PATH_FIELD,
    ):
        with pytest.raises(module.MessageError) as raised:
            module.send_request(
                {**valid_request, executable_field: "caller-owned"}, discovery
            )
        assert raised.value.status == module.DeliveryStatus.INVALID_SCHEMA

    handback = production_handback(sender, recipient)
    tampered_handback = {
        **handback,
        module.COMMAND_FIELD: f"{handback[module.COMMAND_FIELD]} .",
    }
    with pytest.raises(module.MessageError) as raised:
        module.send_request(
            {**valid_request, module.HANDBACK_FIELD: tampered_handback}, discovery
        )
    assert raised.value.status == module.DeliveryStatus.INVALID_SCHEMA


def test_message_cli_preserves_source_owned_results() -> None:
    module, sender, recipient, discovery = public_message_context()
    envelope = fact_envelope(module, sender, recipient)
    request_content = message_content(module.MessageKind.FACT, 29)
    valid_request = module.build_request(
        to_pane=recipient[module.PANE_FIELD],
        kind=module.MessageKind.FACT,
        subject=request_content.subject,
        facts=list(request_content.facts),
        request=request_content.request,
    )

    build_stdout = StringIO()
    build_exit = module.main(
        [module.Operation.BUILD],
        stdin=StringIO(
            json.dumps(
                {
                    module.DISCOVERY_FIELD: discovery,
                    module.MESSAGE_REQUEST_FIELD: valid_request,
                }
            )
        ),
        stdout=build_stdout,
    )
    build_output = json.loads(build_stdout.getvalue())
    assert build_exit == 0
    assert (
        build_output[module.DELIVERY_FIELD][module.STATUS_FIELD]
        == module.DeliveryStatus.READY
    )

    result_stdout = StringIO()
    result_exit = module.main(
        [module.Operation.RESULT],
        stdin=StringIO(
            json.dumps(
                {
                    module.ENVELOPE_FIELD: envelope,
                    module.DELIVERED_FIELD: True,
                    module.COMMAND_EXIT_CODE_FIELD: 0,
                    module.TRANSPORT_FIELD: observe_send_transport(
                        recipient[module.PANE_FIELD]
                    ),
                }
            )
        ),
        stdout=result_stdout,
    )
    result_output = json.loads(result_stdout.getvalue())
    assert result_exit == 0
    assert result_output[module.STATUS_FIELD] == module.DeliveryStatus.DELIVERED
