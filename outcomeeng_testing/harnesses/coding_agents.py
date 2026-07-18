"""Test infrastructure for the shipped coding-agent message protocol."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.coding_agents import (
    agent_item,
    mutation_target,
    observed_mutation_state,
)

ROOT = Path(__file__).parents[2]
AGENT_MESSAGE_PATH = (
    ROOT / "src/plugins/coding-agents/skills/message-agents/scripts/agent_message.py"
)


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, AGENT_MESSAGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load message module: {AGENT_MESSAGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _discovery(
    module: ModuleType,
    roster: list[dict[str, object]],
    pane_id: str,
) -> dict[str, object]:
    return cast(
        dict[str, object],
        module.discover(roster, {module.PROWL_PANE_ID_ENV: pane_id}),
    )


def _fact_envelope(
    module: ModuleType,
    sender: dict[str, str],
    recipient: dict[str, str],
) -> dict[str, object]:
    return cast(
        dict[str, object],
        module.build_envelope(
            kind=module.MessageKind.FACT,
            sender=sender,
            recipient=recipient,
            subject="checked fact",
            facts=["the checked source value is preserved"],
            request=None,
            uuid_factory=lambda: uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
        ),
    )


def verify_agent_message_mappings() -> list[str]:
    module = _load("coding_agents_agent_message_mapping")
    failures: list[str] = []
    first = agent_item(module, ordinal=1)
    agents = [first]
    pane = cast(dict[str, object], first[module.PANE_FIELD])
    pane_id = cast(str, pane[module.ID_FIELD])
    status, matches = module.discover_callers(
        agents, {module.PROWL_PANE_ID_ENV: pane_id}
    )
    if status != module.CallerStatus.PROWL_PANE or len(matches) != 1:
        failures.append("unique public caller did not map to prowl-pane")
    unsupported = module.discover_callers(agents, {})[0]
    if unsupported != module.CallerStatus.UNSUPPORTED_TERMINAL:
        failures.append("missing caller evidence did not map to unsupported-terminal")
    ambiguous_roster = [first, agent_item(module, ordinal=2, worktree_ordinal=1)]
    worktree = module.identity_from_agent(first)[module.WORKTREE_FIELD]
    ambiguous = module.discover_callers(
        ambiguous_roster, {module.PROWL_WORKTREE_PATH_ENV: worktree}
    )[0]
    if ambiguous != module.CallerStatus.CALLER_AMBIGUOUS:
        failures.append("ambiguous caller evidence did not map to caller-ambiguous")

    active = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    response_references = {
        module.coordination_reference(kind, active) for kind in module.RESPONSE_KINDS
    }
    if response_references != {active}:
        failures.append("response messages did not preserve the active reference")
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
    if len({active, proposal_reference, fact_reference}) != 3:
        failures.append("initiating message kinds did not map to distinct references")

    sender = module.identity_from_agent(first)
    recipient = module.identity_from_agent(agent_item(module, ordinal=3))
    recipient_target = mutation_target(module, recipient, ordinal=3)
    sender_target = mutation_target(module, sender, ordinal=1)
    recipient_state = observed_mutation_state(module, recipient, ordinal=3)
    sender_state = observed_mutation_state(module, sender, ordinal=1)
    cases = (
        (module.MessageKind.OWNERSHIP_PROPOSAL, None, None, None, None),
        (module.MessageKind.FACT, None, None, None, None),
        (module.MessageKind.ACKNOWLEDGEMENT, active, None, None, True),
        (module.MessageKind.MUTATION_STATE, active, sender_target, sender_state, None),
        (
            module.MessageKind.MUTATION_AUTHORIZATION,
            active,
            recipient_target,
            recipient_state,
            None,
        ),
    )
    observed_states: set[object] = set()
    for (kind, reference, target, state, accepted), expected_state in zip(
        cases, module.MessageState, strict=True
    ):
        envelope = module.build_envelope(
            kind=kind,
            sender=sender,
            recipient=recipient,
            subject="mapping evidence",
            facts=["source-owned state remains distinct"],
            request=None,
            active_reference=reference,
            mutation_target=target,
            observed_state=state,
            accepted=accepted,
        )
        if envelope[module.KIND_FIELD] != kind:
            failures.append(f"message kind {kind} collapsed during mapping")
        if envelope[module.MESSAGE_STATE_FIELD] != expected_state:
            failures.append(f"message kind {kind} mapped to the wrong state")
        if envelope[module.ACCEPTED_FIELD] is not accepted:
            failures.append(f"message kind {kind} mapped accepted state incorrectly")
        observed_states.add(envelope[module.MESSAGE_STATE_FIELD])
    if len(observed_states) != len(module.MessageKind):
        failures.append("message kinds did not map to distinct states")
    rejected_acknowledgement = module.build_envelope(
        kind=module.MessageKind.ACKNOWLEDGEMENT,
        sender=recipient,
        recipient=sender,
        subject="ownership response",
        facts=["the ownership proposal was rejected"],
        request=None,
        active_reference=active,
        accepted=False,
    )
    if rejected_acknowledgement[module.ACCEPTED_FIELD] is not False:
        failures.append("rejected acknowledgement did not preserve accepted false")

    envelope = _fact_envelope(module, sender, recipient)
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
        transport={module.STATUS_FIELD: "source-preserved"},
    )
    if failed[module.STATUS_FIELD] != module.DeliveryStatus.DELIVERY_FAILED:
        failures.append("delivery failure did not map to its distinct state")
    if delivered[module.STATUS_FIELD] != module.DeliveryStatus.DELIVERED:
        failures.append("delivery success did not map to its distinct state")
    return failures


def verify_agent_message_compliance() -> list[str]:
    module = _load("coding_agents_agent_message_compliance")
    failures: list[str] = []
    public_roster = [agent_item(module, ordinal=1), agent_item(module, ordinal=2)]
    sender = module.identity_from_agent(public_roster[0])
    recipient = module.identity_from_agent(public_roster[1])
    discovery = _discovery(module, public_roster, sender[module.PANE_FIELD])
    if (
        sender[module.RUN_FIELD]
        != cast(dict[str, object], public_roster[0][module.RUN_FIELD])[module.ID_FIELD]
    ):
        failures.append("sender run identity was not preserved from public evidence")
    if (
        recipient[module.RUN_FIELD]
        != cast(dict[str, object], public_roster[1][module.RUN_FIELD])[module.ID_FIELD]
    ):
        failures.append("recipient run identity was not preserved from public evidence")
    envelope = _fact_envelope(module, sender, recipient)
    delivery = module.delivery_request(envelope)
    if delivery[module.TO_PANE_FIELD] != recipient[module.PANE_FIELD]:
        failures.append("semantic delivery targeted the wrong complete pane UUID")
    if json.loads(cast(str, delivery[module.TEXT_FIELD])) != envelope:
        failures.append("semantic delivery rewrote the source-owned envelope")

    result = module.delivery_result(
        envelope,
        delivered=True,
        command_exit_code=0,
        transport={module.STATUS_FIELD: "checked-environment-result"},
    )
    if result[module.ACKNOWLEDGED_FIELD] or result[module.AGREED_FIELD]:
        failures.append("transport success established acknowledgement or agreement")
    if result[module.OWNERSHIP_ESTABLISHED_FIELD]:
        failures.append("transport success established ownership")

    for label, identity in (
        (module.SENDER_FIELD, sender),
        (module.RECIPIENT_FIELD, recipient),
    ):
        for identity_field in module.IDENTITY_FIELDS:
            invalid = {
                key: value for key, value in identity.items() if key != identity_field
            }
            try:
                module.build_envelope(
                    kind=module.MessageKind.FACT,
                    sender=invalid if label == module.SENDER_FIELD else sender,
                    recipient=invalid if label == module.RECIPIENT_FIELD else recipient,
                    subject="invalid identity",
                    facts=["identity is incomplete"],
                    request=None,
                )
                failures.append(f"message accepted {label} without {identity_field}")
            except module.MessageError:
                pass
        invalid_run = {**identity, module.RUN_FIELD: ""}
        try:
            module.build_envelope(
                kind=module.MessageKind.FACT,
                sender=invalid_run if label == module.SENDER_FIELD else sender,
                recipient=invalid_run if label == module.RECIPIENT_FIELD else recipient,
                subject="invalid run identity",
                facts=["run identity must be complete when present"],
                request=None,
            )
            failures.append(f"message accepted malformed {label} run identity")
        except module.MessageError:
            pass

    active_reference = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    recipient_target = mutation_target(module, recipient, ordinal=2)
    sender_target = mutation_target(module, sender, ordinal=1)
    recipient_state = observed_mutation_state(module, recipient, ordinal=2)
    sender_state = observed_mutation_state(module, sender, ordinal=1)
    mutation_envelopes = (
        module.build_envelope(
            kind=module.MessageKind.OWNERSHIP_PROPOSAL,
            sender=sender,
            recipient=recipient,
            subject="mutation target",
            facts=["target identity is checked"],
            request="report exact state",
            mutation_target=recipient_target,
        ),
        module.build_envelope(
            kind=module.MessageKind.MUTATION_STATE,
            sender=sender,
            recipient=recipient,
            subject="mutation state",
            facts=["state is checked"],
            request=None,
            active_reference=active_reference,
            mutation_target=sender_target,
            observed_state=sender_state,
        ),
        module.build_envelope(
            kind=module.MessageKind.MUTATION_AUTHORIZATION,
            sender=sender,
            recipient=recipient,
            subject="mutation authorization",
            facts=["target and state match"],
            request="perform only the authorized mutation",
            active_reference=active_reference,
            mutation_target=recipient_target,
            observed_state=recipient_state,
        ),
    )
    for mutation_envelope in mutation_envelopes:
        if module.validate_envelope(mutation_envelope) != mutation_envelope:
            failures.append("valid mutation envelope changed during validation")

    for identity_field in (
        module.PANE_FIELD,
        module.WORKTREE_FIELD,
        module.BRANCH_FIELD,
        module.REPOSITORY_FIELD,
    ):
        mismatched = {
            **recipient_target,
            identity_field: sender[identity_field],
        }
        try:
            module.build_envelope(
                kind=module.MessageKind.OWNERSHIP_PROPOSAL,
                sender=sender,
                recipient=recipient,
                subject="mismatched target",
                facts=["target must match"],
                request="report state",
                mutation_target=mismatched,
            )
            failures.append(f"mismatched mutation target {identity_field} was accepted")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_IDENTITY:
                failures.append(f"mismatched target mapped to {error.status}")

    invalid_proposal_targets = (
        {**recipient_target, module.HEAD_FIELD: "f" * 39},
        {**recipient_target, module.STATUS_FIELD: ""},
    )
    for invalid_target in invalid_proposal_targets:
        try:
            module.build_envelope(
                kind=module.MessageKind.OWNERSHIP_PROPOSAL,
                sender=sender,
                recipient=recipient,
                subject="stale target state",
                facts=["target HEAD and status must be complete"],
                request="report exact state",
                mutation_target=invalid_target,
            )
            failures.append("proposal accepted stale target HEAD or status")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_SCHEMA:
                failures.append(f"stale proposal target mapped to {error.status}")

    stale_authorization_targets = (
        {**recipient_target, module.HEAD_FIELD: "f" * 40},
        {**recipient_target, module.STATUS_FIELD: "dirty"},
    )
    for stale_target in stale_authorization_targets:
        try:
            module.build_envelope(
                kind=module.MessageKind.MUTATION_AUTHORIZATION,
                sender=sender,
                recipient=recipient,
                subject="stale authorization target",
                facts=["target must match the reported state"],
                request=None,
                active_reference=active_reference,
                mutation_target=stale_target,
                observed_state=recipient_state,
            )
            failures.append("authorization accepted stale target HEAD or status")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_IDENTITY:
                failures.append(f"stale authorization target mapped to {error.status}")

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
        mismatched_state = {
            **recipient_state,
            state_field: mismatched_value,
        }
        try:
            module.build_envelope(
                kind=module.MessageKind.MUTATION_AUTHORIZATION,
                sender=sender,
                recipient=recipient,
                subject="mismatched state",
                facts=["state must match target"],
                request=None,
                active_reference=active_reference,
                mutation_target=recipient_target,
                observed_state=mismatched_state,
            )
            failures.append(f"mismatched observed {state_field} was accepted")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_IDENTITY:
                failures.append(f"mismatched state mapped to {error.status}")

    valid_request = module.build_request(
        to_pane=recipient[module.PANE_FIELD],
        kind=module.MessageKind.FACT,
        subject="exact targeting",
        facts=["pane UUID selects the recipient"],
        request=None,
    )
    built = module.send_request(valid_request, discovery)
    if (
        built[module.DELIVERY_FIELD][module.TO_PANE_FIELD]
        != recipient[module.PANE_FIELD]
    ):
        failures.append("message build did not preserve exact pane targeting")
    for forbidden_field in module.FORBIDDEN_TARGET_FIELDS:
        try:
            module.send_request(
                {**valid_request, forbidden_field: forbidden_field}, discovery
            )
            failures.append(f"forbidden selector {forbidden_field} was accepted")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_SCHEMA:
                failures.append(f"forbidden selector mapped to {error.status}")

    discover_stdout = StringIO()
    discover_exit = module.main(
        [module.Operation.DISCOVER],
        environment={module.PROWL_PANE_ID_ENV: sender[module.PANE_FIELD]},
        stdin=StringIO(json.dumps({module.AGENTS_FIELD: public_roster})),
        stdout=discover_stdout,
    )
    discover_output = json.loads(discover_stdout.getvalue())
    if (
        discover_exit != 0
        or discover_output[module.STATUS_FIELD] != module.CallerStatus.PROWL_PANE
    ):
        failures.append("discover CLI did not emit the source-owned success result")

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
    if (
        build_exit != 0
        or build_output[module.DELIVERY_FIELD][module.STATUS_FIELD]
        != module.DeliveryStatus.READY
    ):
        failures.append("build CLI did not emit one ready semantic delivery")

    result_stdout = StringIO()
    result_exit = module.main(
        [module.Operation.RESULT],
        stdin=StringIO(
            json.dumps(
                {
                    module.ENVELOPE_FIELD: envelope,
                    module.DELIVERED_FIELD: True,
                    module.COMMAND_EXIT_CODE_FIELD: 0,
                    module.TRANSPORT_FIELD: {module.STATUS_FIELD: "checked"},
                }
            )
        ),
        stdout=result_stdout,
    )
    result_output = json.loads(result_stdout.getvalue())
    if (
        result_exit != 0
        or result_output[module.STATUS_FIELD] != module.DeliveryStatus.DELIVERED
    ):
        failures.append("result CLI did not preserve checked transport success")
    return failures
