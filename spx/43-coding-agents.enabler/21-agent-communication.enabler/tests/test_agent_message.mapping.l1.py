import uuid
from typing import cast

from outcomeeng_testing.generators.coding_agents import message_content
from outcomeeng_testing.harnesses.coding_agents import (
    fact_envelope,
    mutation_observation,
    observe_send_transport,
    observed_message_participants,
)


def test_agent_message_mappings() -> None:
    prowl, module, _, participants = observed_message_participants()

    sender = participants[0]
    recipient = participants[1]
    active_reference = str(uuid.uuid5(uuid.NAMESPACE_URL, sender[module.PANE_FIELD]))
    assert module.RESPONSE_KINDS == frozenset(
        {
            module.MessageKind.ACKNOWLEDGEMENT,
            module.MessageKind.MUTATION_STATE,
            module.MessageKind.MUTATION_AUTHORIZATION,
        }
    )
    assert {
        module.coordination_reference(kind, active_reference)
        for kind in (
            module.MessageKind.ACKNOWLEDGEMENT,
            module.MessageKind.MUTATION_STATE,
            module.MessageKind.MUTATION_AUTHORIZATION,
        )
    } == {active_reference}
    proposal_reference = module.coordination_reference(
        module.MessageKind.OWNERSHIP_PROPOSAL,
        None,
        lambda: uuid.uuid5(uuid.NAMESPACE_URL, sender[module.WORKTREE_FIELD]),
    )
    fact_reference = module.coordination_reference(
        module.MessageKind.FACT,
        None,
        lambda: uuid.uuid5(uuid.NAMESPACE_URL, recipient[module.WORKTREE_FIELD]),
    )
    assert len({active_reference, proposal_reference, fact_reference}) == 3

    sender_target, sender_state = mutation_observation(module, sender)
    recipient_target, recipient_state = mutation_observation(module, recipient)

    observed_states: set[object] = set()
    for ordinal, (kind, expected_state) in enumerate(
        (
            (
                module.MessageKind.OWNERSHIP_PROPOSAL,
                module.MessageState.OWNERSHIP_PROPOSED,
            ),
            (module.MessageKind.FACT, module.MessageState.FACT_REPORTED),
            (
                module.MessageKind.ACKNOWLEDGEMENT,
                module.MessageState.ACKNOWLEDGED,
            ),
            (
                module.MessageKind.MUTATION_STATE,
                module.MessageState.MUTATION_STATE_REPORTED,
            ),
            (
                module.MessageKind.MUTATION_AUTHORIZATION,
                module.MessageState.MUTATION_AUTHORIZED,
            ),
        ),
        start=1,
    ):
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
        assert envelope[module.MESSAGE_STATE_FIELD] == expected_state
        assert envelope[module.ACCEPTED_FIELD] is fields.get("accepted")
        if kind in module.RESPONSE_KINDS:
            assert envelope[module.COORDINATION_REFERENCE_FIELD] == active_reference
        else:
            assert envelope[module.COORDINATION_REFERENCE_FIELD] != active_reference
        observed_states.add(envelope[module.MESSAGE_STATE_FIELD])
    assert observed_states == set(module.MessageState)

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
        command_exit_code=7,
        detail="transport rejected",
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
