import hashlib
import uuid
from typing import cast

from outcomeeng_testing.generators.coding_agents import message_content
from outcomeeng_testing.generators.prowl_environment import public_agent_item
from outcomeeng_testing.harnesses.coding_agents import (
    fact_envelope,
    observe_send_transport,
    observed_message_participants,
)


def test_agent_message_mappings() -> None:
    prowl, module, agents, participants = observed_message_participants()
    first = agents[0]
    pane = cast(dict[str, object], first[prowl.PANE_FIELD])
    pane_id = cast(str, pane[prowl.ID_FIELD])

    status, matches = module.discover_callers(
        agents, {module.PROWL_PANE_ID_ENV: pane_id}
    )
    assert status == module.CallerStatus.PROWL_PANE
    assert matches == [participants[0]]
    assert (
        module.discover_callers(agents, {})[0]
        == module.CallerStatus.UNSUPPORTED_TERMINAL
    )

    ambiguous_agent = public_agent_item(prowl, 4)
    ambiguous_worktree = cast(dict[str, object], ambiguous_agent[prowl.WORKTREE_FIELD])
    first_worktree = cast(dict[str, object], first[prowl.WORKTREE_FIELD])
    ambiguous_worktree[prowl.PATH_FIELD] = first_worktree[prowl.PATH_FIELD]
    ambiguous_roster = [first, ambiguous_agent]
    assert (
        module.discover_callers(
            ambiguous_roster,
            {module.PROWL_WORKTREE_PATH_ENV: participants[0][prowl.WORKTREE_FIELD]},
        )[0]
        == module.CallerStatus.CALLER_AMBIGUOUS
    )

    sender = participants[0]
    recipient = participants[1]
    active_reference = str(uuid.uuid5(uuid.NAMESPACE_URL, sender[module.PANE_FIELD]))
    assert {
        module.coordination_reference(kind, active_reference)
        for kind in module.RESPONSE_KINDS
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

    sender_head = hashlib.sha1(
        sender[module.PANE_FIELD].encode(), usedforsecurity=False
    ).hexdigest()
    recipient_head = hashlib.sha1(
        recipient[module.PANE_FIELD].encode(), usedforsecurity=False
    ).hexdigest()
    sender_target = {
        module.PANE_FIELD: sender[module.PANE_FIELD],
        module.WORKTREE_FIELD: sender[module.WORKTREE_FIELD],
        module.BRANCH_FIELD: sender[module.BRANCH_FIELD],
        module.REPOSITORY_FIELD: sender[module.REPOSITORY_FIELD],
        module.HEAD_FIELD: sender_head,
        module.STATUS_FIELD: module.CLEAN_STATUS,
    }
    recipient_target = {
        module.PANE_FIELD: recipient[module.PANE_FIELD],
        module.WORKTREE_FIELD: recipient[module.WORKTREE_FIELD],
        module.BRANCH_FIELD: recipient[module.BRANCH_FIELD],
        module.REPOSITORY_FIELD: recipient[module.REPOSITORY_FIELD],
        module.HEAD_FIELD: recipient_head,
        module.STATUS_FIELD: module.CLEAN_STATUS,
    }
    sender_state = {
        field: sender_target[field] for field in module.OBSERVED_STATE_FIELDS
    }
    recipient_state = {
        field: recipient_target[field] for field in module.OBSERVED_STATE_FIELDS
    }

    observed_states: set[object] = set()
    for ordinal, (kind, expected_state) in enumerate(
        zip(module.MessageKind, module.MessageState, strict=True), start=1
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
