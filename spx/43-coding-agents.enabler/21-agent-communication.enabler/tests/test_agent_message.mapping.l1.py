import uuid
from typing import cast

from outcomeeng_testing.generators.coding_agents import (
    agent_item,
    message_content,
    mutation_target,
    observed_mutation_state,
)
from outcomeeng_testing.harnesses.coding_agents import (
    fact_envelope,
    load_agent_message,
    successful_transport,
)


def test_agent_message_mappings() -> None:
    module = load_agent_message()
    first = agent_item(module, ordinal=1)
    agents = [first]
    pane = cast(dict[str, object], first[module.PANE_FIELD])
    pane_id = cast(str, pane[module.ID_FIELD])

    status, matches = module.discover_callers(
        agents, {module.PROWL_PANE_ID_ENV: pane_id}
    )
    assert status == module.CallerStatus.PROWL_PANE
    assert len(matches) == 1
    assert (
        module.discover_callers(agents, {})[0]
        == module.CallerStatus.UNSUPPORTED_TERMINAL
    )

    ambiguous_roster = [first, agent_item(module, ordinal=2, worktree_ordinal=1)]
    worktree = module.identity_from_agent(first)[module.WORKTREE_FIELD]
    assert (
        module.discover_callers(
            ambiguous_roster, {module.PROWL_WORKTREE_PATH_ENV: worktree}
        )[0]
        == module.CallerStatus.CALLER_AMBIGUOUS
    )

    active = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert {
        module.coordination_reference(kind, active) for kind in module.RESPONSE_KINDS
    } == {active}
    proposal_reference = module.coordination_reference(
        module.MessageKind.OWNERSHIP_PROPOSAL,
        None,
        lambda: uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
    )
    fact_reference = module.coordination_reference(
        module.MessageKind.FACT,
        None,
        lambda: uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
    )
    assert len({active, proposal_reference, fact_reference}) == 3

    sender = module.identity_from_agent(first)
    recipient = module.identity_from_agent(agent_item(module, ordinal=3))
    recipient_target = mutation_target(module, recipient, ordinal=3)
    sender_target = mutation_target(module, sender, ordinal=1)
    recipient_state = observed_mutation_state(module, recipient, ordinal=3)
    sender_state = observed_mutation_state(module, sender, ordinal=1)
    cases = (
        (
            module.MessageKind.OWNERSHIP_PROPOSAL,
            module.MessageState.OWNERSHIP_PROPOSED,
            None,
            None,
            None,
            None,
        ),
        (
            module.MessageKind.FACT,
            module.MessageState.FACT_REPORTED,
            None,
            None,
            None,
            None,
        ),
        (
            module.MessageKind.ACKNOWLEDGEMENT,
            module.MessageState.ACKNOWLEDGED,
            active,
            None,
            None,
            True,
        ),
        (
            module.MessageKind.MUTATION_STATE,
            module.MessageState.MUTATION_STATE_REPORTED,
            active,
            sender_target,
            sender_state,
            None,
        ),
        (
            module.MessageKind.MUTATION_AUTHORIZATION,
            module.MessageState.MUTATION_AUTHORIZED,
            active,
            recipient_target,
            recipient_state,
            None,
        ),
    )
    observed_states: set[object] = set()
    for ordinal, (
        kind,
        expected_state,
        reference,
        target,
        state,
        accepted,
    ) in enumerate(cases, start=2):
        content = message_content(kind, ordinal)
        envelope = module.build_envelope(
            kind=kind,
            sender=sender,
            recipient=recipient,
            subject=content.subject,
            facts=list(content.facts),
            request=content.request,
            active_reference=reference,
            mutation_target=target,
            observed_state=state,
            accepted=accepted,
        )
        assert envelope[module.KIND_FIELD] == kind
        assert envelope[module.MESSAGE_STATE_FIELD] == expected_state
        assert envelope[module.ACCEPTED_FIELD] is accepted
        if kind in module.RESPONSE_KINDS:
            assert envelope[module.COORDINATION_REFERENCE_FIELD] == active
        else:
            assert envelope[module.COORDINATION_REFERENCE_FIELD] != active
        observed_states.add(envelope[module.MESSAGE_STATE_FIELD])
    assert len(observed_states) == len(module.MessageKind)

    rejected_content = message_content(module.MessageKind.ACKNOWLEDGEMENT, 7)
    rejected_acknowledgement = module.build_envelope(
        kind=module.MessageKind.ACKNOWLEDGEMENT,
        sender=recipient,
        recipient=sender,
        subject=rejected_content.subject,
        facts=list(rejected_content.facts),
        request=rejected_content.request,
        active_reference=active,
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
    delivered = module.delivery_result(
        envelope,
        delivered=True,
        command_exit_code=0,
        transport=successful_transport(module),
    )
    assert failed[module.STATUS_FIELD] == module.DeliveryStatus.DELIVERY_FAILED
    assert delivered[module.STATUS_FIELD] == module.DeliveryStatus.DELIVERED
