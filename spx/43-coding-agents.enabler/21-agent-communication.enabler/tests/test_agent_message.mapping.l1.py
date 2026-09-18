import uuid
from typing import cast

from outcomeeng_testing.generators.coding_agents import (
    message_content,
    mutation_observation,
)
from outcomeeng_testing.harnesses.coding_agents import (
    PROWL_REJECTION_DETAIL,
    PROWL_REJECTION_EXIT_CODE,
    fact_envelope,
    observe_send_transport,
    observed_message_participants,
)


def test_agent_message_mappings() -> None:
    prowl, module, _, participants = observed_message_participants()

    sender = participants[0]
    recipient = participants[1]
    active_reference = str(uuid.uuid5(uuid.NAMESPACE_URL, sender[module.PANE_FIELD]))
    initiating_kinds = set(module.MessageKind) - module.RESPONSE_KINDS
    assert {
        module.coordination_reference(kind, active_reference)
        for kind in module.RESPONSE_KINDS
    } == {active_reference}
    minted_references = {
        module.coordination_reference(
            kind,
            None,
            lambda kind=kind: uuid.uuid5(uuid.NAMESPACE_URL, str(kind)),
        )
        for kind in initiating_kinds
    }
    assert len(minted_references) == len(initiating_kinds)
    assert active_reference not in minted_references
    for reference in minted_references:
        assert str(uuid.UUID(reference)) == reference

    sender_target, sender_state = mutation_observation(module, sender)
    recipient_target, recipient_state = mutation_observation(module, recipient)

    observed_states: set[object] = set()
    initiating_references: set[str] = set()
    for ordinal, kind in enumerate(module.MessageKind, start=1):
        content = message_content(kind, ordinal)
        fields: dict[str, object] = {}
        if kind in module.RESPONSE_KINDS:
            fields["active_reference"] = active_reference
        if kind is module.MessageKind.ACKNOWLEDGEMENT:
            fields["accepted"] = True
        elif kind is module.MessageKind.MUTATION_STATE:
            fields["mutation_target"] = sender_target
            fields["observed_state"] = sender_state
        elif kind is module.MessageKind.MUTATION_AUTHORIZATION:
            fields["mutation_target"] = recipient_target
            fields["observed_state"] = recipient_state
        envelope = module.build_envelope(
            kind=kind,
            sender=sender,
            recipient=recipient,
            subject=content.subject,
            facts=list(content.facts),
            request=content.request,
            **fields,
        )
        assert envelope[module.KIND_FIELD] == kind
        assert envelope[module.ACCEPTED_FIELD] is fields.get("accepted")
        if kind in module.RESPONSE_KINDS:
            assert envelope[module.COORDINATION_REFERENCE_FIELD] == active_reference
        else:
            envelope_reference = cast(
                str, envelope[module.COORDINATION_REFERENCE_FIELD]
            )
            assert str(uuid.UUID(envelope_reference)) == envelope_reference
            assert envelope_reference not in initiating_references
            initiating_references.add(envelope_reference)
        assert envelope[module.MESSAGE_STATE_FIELD] not in observed_states
        observed_states.add(envelope[module.MESSAGE_STATE_FIELD])
    assert observed_states == set(module.MessageState)
    assert len(initiating_references) == len(initiating_kinds)

    rejected_content = message_content(module.MessageKind.ACKNOWLEDGEMENT, 7)
    rejected_acknowledgement = module.build_envelope(
        kind=module.MessageKind.ACKNOWLEDGEMENT,
        sender=recipient,
        recipient=sender,
        subject=rejected_content.subject,
        facts=list(rejected_content.facts),
        request=rejected_content.request,
        active_reference=active_reference,
        accepted=False,
    )
    assert rejected_acknowledgement[module.ACCEPTED_FIELD] is False

    envelope = fact_envelope(module, sender, recipient)
    failed = module.delivery_result(
        envelope,
        delivered=False,
        command_exit_code=PROWL_REJECTION_EXIT_CODE,
        detail=PROWL_REJECTION_DETAIL,
    )
    transport = observe_send_transport(recipient[module.PANE_FIELD])
    delivered = module.delivery_result(
        envelope,
        delivered=True,
        command_exit_code=cast(int, transport[prowl.COMMAND_EXIT_CODE_FIELD]),
        transport=transport,
    )
    assert failed[module.STATUS_FIELD] == module.DeliveryStatus.DELIVERY_FAILED
    assert delivered[module.STATUS_FIELD] == module.DeliveryStatus.DELIVERED
