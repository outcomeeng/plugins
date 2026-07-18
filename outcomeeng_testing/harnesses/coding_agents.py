"""Test infrastructure for the shipped coding-agent message adapter."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from io import StringIO
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from outcomeeng_testing.generators.coding_agents import (
    agent_item,
    mutation_target,
    observed_mutation_state,
)

ROOT = Path(__file__).parents[2]
AGENT_MESSAGE_PATH = (
    ROOT / "src/plugins/coding-agents/skills/message-agents/scripts/agent_message.py"
)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load adapter module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class RecordingRunner:
    results: list[Any]
    calls: list[tuple[tuple[str, ...], str | None]] = field(default_factory=list)

    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> Any:
        self.calls.append((argv, stdin))
        if not self.results:
            raise AssertionError(f"Unexpected command: {argv}")
        return self.results.pop(0)


def verify_agent_message_mappings() -> list[str]:
    module = _load("coding_agents_agent_message_mapping", AGENT_MESSAGE_PATH)
    failures: list[str] = []
    agents = [agent_item(module, ordinal=1)]
    pane = cast(dict[str, object], agents[0][module.PANE_FIELD])
    status, matches = module.discover_callers(
        agents,
        {module.PROWL_PANE_ID_ENV: cast(str, pane[module.ID_FIELD])},
    )
    if status != module.CallerStatus.PROWL_PANE or len(matches) != 1:
        failures.append("unique Prowl caller did not map to prowl-pane")
    status, _ = module.discover_callers(agents, {})
    if status != module.CallerStatus.UNSUPPORTED_TERMINAL:
        failures.append("missing Prowl evidence did not map to unsupported-terminal")
    unsupported = module.discover(
        RecordingRunner(
            [
                module.CommandResult(
                    0,
                    json.dumps(
                        {
                            module.OK_FIELD: True,
                            module.DATA_FIELD: {
                                module.AGENTS_FIELD: agents,
                            },
                        }
                    ),
                    "",
                )
            ]
        ),
        {},
    )
    if unsupported.get(module.DETAIL_FIELD) != module.CALLER_STATUS_DETAILS[status]:
        failures.append("unsupported caller result omitted its actionable detail")
    if unsupported.get(module.STATUS_FIELD) != module.CallerStatus.UNSUPPORTED_TERMINAL:
        failures.append("unsupported discovery emitted the wrong caller status")
    if unsupported.get(module.CALLER_FIELD) is not None:
        failures.append("unsupported caller evidence selected a fallback caller")
    ambiguous_roster = [
        *agents,
        agent_item(module, ordinal=2, worktree_ordinal=1),
    ]
    ambiguous_environment = {
        module.PROWL_WORKTREE_PATH_ENV: module.identity_from_agent(agents[0])[
            module.WORKTREE_FIELD
        ]
    }
    status, _ = module.discover_callers(
        ambiguous_roster,
        ambiguous_environment,
    )
    ambiguous = module.discover(
        RecordingRunner(
            [
                module.CommandResult(
                    0,
                    json.dumps(
                        {
                            module.OK_FIELD: True,
                            module.DATA_FIELD: {
                                module.AGENTS_FIELD: ambiguous_roster,
                            },
                        }
                    ),
                    "",
                )
            ]
        ),
        ambiguous_environment,
    )
    if status != module.CallerStatus.CALLER_AMBIGUOUS:
        failures.append("multiple Prowl callers did not map to caller-ambiguous")
    if ambiguous.get(module.STATUS_FIELD) != module.CallerStatus.CALLER_AMBIGUOUS:
        failures.append("ambiguous discovery emitted the wrong caller status")
    if ambiguous.get(module.CALLER_FIELD) is not None:
        failures.append("ambiguous caller evidence selected a fallback caller")

    active = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    response_references = {
        kind: module.coordination_reference(kind, active)
        for kind in module.RESPONSE_KINDS
    }
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
    if any(reference != active for reference in response_references.values()):
        failures.append(
            "a response kind did not preserve the active proposal reference"
        )
    if len({active, proposal_reference, fact_reference}) != 3:
        failures.append(
            "initiating message kinds did not receive distinct new references"
        )
    sender = module.identity_from_agent(agents[0])
    recipient = module.identity_from_agent(agent_item(module, ordinal=3))
    recipient_target = mutation_target(module, recipient, ordinal=3)
    sender_target = mutation_target(module, sender, ordinal=1)
    recipient_state = observed_mutation_state(module, recipient, ordinal=3)
    sender_state = observed_mutation_state(module, sender, ordinal=1)
    message_cases = (
        (module.MessageKind.OWNERSHIP_PROPOSAL, None, None, None),
        (module.MessageKind.FACT, None, None, None),
        (module.MessageKind.ACKNOWLEDGEMENT, active, None, None),
        (module.MessageKind.MUTATION_STATE, active, sender_target, sender_state),
        (
            module.MessageKind.MUTATION_AUTHORIZATION,
            active,
            recipient_target,
            recipient_state,
        ),
    )
    observed_message_states: set[object] = set()
    for (
        kind,
        active_reference,
        target,
        state,
    ), expected_state in zip(message_cases, module.MessageState, strict=True):
        envelope = module.build_envelope(
            kind=kind,
            sender=sender,
            recipient=recipient,
            subject="mapping evidence",
            facts=["source-owned state remains distinct"],
            request=None,
            active_reference=active_reference,
            mutation_target=target,
            observed_state=state,
        )
        if envelope[module.KIND_FIELD] != kind:
            failures.append(f"message kind {kind} collapsed during envelope mapping")
        if envelope[module.MESSAGE_STATE_FIELD] != expected_state:
            failures.append(f"message kind {kind} mapped to the wrong message state")
        observed_message_states.add(envelope[module.MESSAGE_STATE_FIELD])
    if len(observed_message_states) != len(module.MessageKind):
        failures.append("message kinds did not map to distinct source-owned states")
    failure = module.send_envelope(
        module.build_envelope(
            kind=module.MessageKind.FACT,
            sender=sender,
            recipient=recipient,
            subject="delivery failure evidence",
            facts=["transport rejected the envelope"],
            request=None,
        ),
        RecordingRunner([module.CommandResult(7, "", "transport rejected")]),
    )
    if (
        failure[module.STATUS_FIELD] != module.DeliveryStatus.DELIVERY_FAILED
        or failure[module.COMMAND_EXIT_CODE_FIELD] != 7
    ):
        failures.append("delivery failure did not map to its distinct result state")
    for caller_status in module.CallerStatus:
        expected = 0 if caller_status == module.CallerStatus.PROWL_PANE else 2
        actual = module.command_exit_code(
            module.Operation.DISCOVER, {module.STATUS_FIELD: caller_status}
        )
        if actual != expected:
            failures.append(
                f"discover status {caller_status} mapped to exit code {actual}"
            )
    for delivery_status in module.DeliveryStatus:
        expected = 0 if delivery_status == module.DeliveryStatus.DELIVERED else 2
        actual = module.command_exit_code(
            module.Operation.SEND, {module.STATUS_FIELD: delivery_status}
        )
        if actual != expected:
            failures.append(
                f"send status {delivery_status} mapped to exit code {actual}"
            )
    return failures


def verify_agent_message_compliance() -> list[str]:
    module = _load("coding_agents_agent_message_compliance", AGENT_MESSAGE_PATH)
    failures: list[str] = []
    sender = module.identity_from_agent(agent_item(module, ordinal=1))
    recipient = module.identity_from_agent(agent_item(module, ordinal=2))
    envelope = module.build_envelope(
        kind=module.MessageKind.FACT,
        sender=sender,
        recipient=recipient,
        subject="base advanced",
        facts=["origin/main is abcdef"],
        request=None,
        uuid_factory=lambda: uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
    )
    runner = RecordingRunner(
        [
            module.CommandResult(
                0,
                json.dumps(
                    {
                        module.OK_FIELD: True,
                        module.DATA_FIELD: {module.ACCEPTED_FIELD: True},
                    }
                ),
                "",
            )
        ]
    )
    result = module.send_envelope(envelope, runner)
    expected_command = (
        *module.PROWL_SEND_PREFIX,
        module.PANE_OPTION,
        recipient[module.PANE_FIELD],
        module.NO_WAIT_OPTION,
        module.JSON_FLAG,
    )
    if runner.calls != [(expected_command, json.dumps(envelope, sort_keys=True))]:
        failures.append(
            "delivery did not pass the envelope over Prowl subprocess stdin"
        )
    if (
        result[module.STATUS_FIELD] != module.DeliveryStatus.DELIVERED
        or result[module.COMMAND_EXIT_CODE_FIELD] != 0
    ):
        failures.append("checked Prowl result did not map to delivered")
    if result[module.ACKNOWLEDGED_FIELD] or result[module.AGREED_FIELD]:
        failures.append("transport success established acknowledgement or agreement")
    if result[module.OWNERSHIP_ESTABLISHED_FIELD]:
        failures.append("transport success established ownership")
    invalid_prebuilt_envelopes = [
        {
            **envelope,
            module.SENDER_FIELD: {
                key: value
                for key, value in sender.items()
                if key != module.IDENTITY_FIELDS[0]
            },
        },
        {**envelope, module.RECIPIENT_FIELD: {**recipient, module.RUN_FIELD: ""}},
        {**envelope, module.SUBJECT_FIELD: ""},
        {**envelope, module.FACTS_FIELD: []},
        {**envelope, module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION + 1},
    ]
    for invalid_envelope in invalid_prebuilt_envelopes:
        invalid_envelope_runner = RecordingRunner([])
        try:
            module.send_envelope(invalid_envelope, invalid_envelope_runner)
            failures.append("invalid prebuilt envelope reached message transport")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_SCHEMA:
                failures.append(f"invalid prebuilt envelope mapped to {error.status}")
        if invalid_envelope_runner.calls:
            failures.append("invalid prebuilt envelope invoked Prowl")
    protocol_failure_runner = RecordingRunner(
        [
            module.CommandResult(
                0,
                json.dumps(
                    {
                        module.OK_FIELD: False,
                        module.ERROR_FIELD: {
                            module.MESSAGE_FIELD: "transport rejected"
                        },
                    }
                ),
                "",
            )
        ]
    )
    try:
        module.send_envelope(envelope, protocol_failure_runner)
        failures.append("zero-exit public failure payload mapped to delivered")
    except module.MessageError as error:
        if error.status != module.DeliveryStatus.DELIVERY_FAILED:
            failures.append(
                f"zero-exit public failure payload mapped to {error.status}"
            )
        if error.command_exit_code != 0:
            failures.append("zero-exit public failure lost its checked exit code")
    invalid_json_runner = RecordingRunner([module.CommandResult(0, "{", "")])
    try:
        module.send_envelope(envelope, invalid_json_runner)
        failures.append("zero-exit malformed public payload mapped to delivered")
    except module.MessageError as error:
        if error.status != module.DeliveryStatus.INVALID_SCHEMA:
            failures.append(
                f"zero-exit malformed public payload mapped to {error.status}"
            )
        if error.command_exit_code != 0:
            failures.append("zero-exit malformed payload lost its checked exit code")
    for label, identity in (("sender", sender), ("recipient", recipient)):
        for identity_field in module.IDENTITY_FIELDS:
            for invalid_identity in (
                {
                    key: value
                    for key, value in identity.items()
                    if key != identity_field
                },
                {**identity, identity_field: ""},
            ):
                try:
                    module.build_envelope(
                        kind=module.MessageKind.FACT,
                        sender=(invalid_identity if label == "sender" else sender),
                        recipient=(
                            invalid_identity if label == "recipient" else recipient
                        ),
                        subject="subject",
                        facts=["fact"],
                        request=None,
                    )
                    failures.append(
                        f"delivery accepted {label} with invalid {identity_field}"
                    )
                except module.MessageError:
                    pass
        invalid_run = {**identity, module.RUN_FIELD: ""}
        try:
            module.build_envelope(
                kind=module.MessageKind.FACT,
                sender=invalid_run if label == "sender" else sender,
                recipient=invalid_run if label == "recipient" else recipient,
                subject="subject",
                facts=["fact"],
                request=None,
            )
            failures.append(f"delivery accepted {label} with invalid run identity")
        except module.MessageError:
            pass
    if (
        envelope[module.SENDER_FIELD] != sender
        or envelope[module.RECIPIENT_FIELD] != recipient
    ):
        failures.append("delivery did not preserve complete source identities")
    selected = module._target_by_pane([recipient], recipient[module.PANE_FIELD])
    if selected != recipient:
        failures.append("exact pane UUID did not select its complete target identity")
    for targets, pane_id in (
        ([], recipient[module.PANE_FIELD]),
        ([recipient, recipient], recipient[module.PANE_FIELD]),
    ):
        try:
            module._target_by_pane(targets, pane_id)
            failures.append("non-unique pane targeting did not fail explicitly")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_IDENTITY:
                failures.append(f"non-unique pane targeting mapped to {error.status}")
    try:
        module._message_kind("unsupported-kind")
        failures.append("unsupported message kind did not fail")
    except module.MessageError as error:
        if error.status != module.DeliveryStatus.INVALID_SCHEMA:
            failures.append("unsupported message kind mapped to the wrong status")
        if any(kind.value not in str(error) for kind in module.MessageKind):
            failures.append("unsupported message kind omitted the valid choices")
    invalid_optional_values: tuple[object, ...] = (1, [], {})
    for invalid_optional in invalid_optional_values:
        try:
            module._optional_text(invalid_optional, "request.request")
            failures.append("non-string optional message field did not fail")
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_SCHEMA:
                failures.append("non-string optional field mapped to the wrong status")

    public_roster = [
        agent_item(module, ordinal=1),
        agent_item(module, ordinal=2),
    ]
    discovery = module.discover(
        RecordingRunner(
            [
                module.CommandResult(
                    0,
                    json.dumps(
                        {
                            module.OK_FIELD: True,
                            module.DATA_FIELD: {
                                module.AGENTS_FIELD: public_roster,
                            },
                        }
                    ),
                    "",
                )
            ]
        ),
        {module.PROWL_PANE_ID_ENV: sender[module.PANE_FIELD]},
    )
    valid_request = module.build_request(
        to_pane=recipient[module.PANE_FIELD],
        kind=module.MessageKind.FACT,
        subject="exact pane targeting",
        facts=["only the pane UUID selects the recipient"],
        request=None,
    )
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
            subject="delegated mutation target",
            facts=["mutation remains bound to the target worktree"],
            request="report exact pre-mutation state",
            mutation_target=recipient_target,
        ),
        module.build_envelope(
            kind=module.MessageKind.MUTATION_STATE,
            sender=sender,
            recipient=recipient,
            subject="delegated mutation state",
            facts=["pre-mutation state was observed locally"],
            request=None,
            active_reference=active_reference,
            mutation_target=sender_target,
            observed_state=sender_state,
        ),
        module.build_envelope(
            kind=module.MessageKind.MUTATION_AUTHORIZATION,
            sender=sender,
            recipient=recipient,
            subject="delegated mutation authorization",
            facts=["reported state matches the target"],
            request="perform only the authorized mutation",
            active_reference=active_reference,
            mutation_target=recipient_target,
            observed_state=recipient_state,
        ),
    )
    for mutation_envelope in mutation_envelopes:
        if module.validate_envelope(mutation_envelope) != mutation_envelope:
            failures.append(
                "valid delegated-mutation envelope changed during validation"
            )
    for identity_field in (
        module.PANE_FIELD,
        module.WORKTREE_FIELD,
        module.BRANCH_FIELD,
        module.REPOSITORY_FIELD,
    ):
        mismatched_target = {
            **recipient_target,
            identity_field: sender[identity_field],
        }
        invalid_mutation_runner = RecordingRunner([])
        try:
            module.send_request(
                module.build_request(
                    to_pane=recipient[module.PANE_FIELD],
                    kind=module.MessageKind.OWNERSHIP_PROPOSAL,
                    subject="mismatched delegated mutation target",
                    facts=["target identity must match the live recipient"],
                    request="report exact pre-mutation state",
                    mutation_target=mismatched_target,
                ),
                discovery,
                invalid_mutation_runner,
            )
            failures.append(
                f"mismatched mutation target {identity_field!r} reached transport"
            )
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_IDENTITY:
                failures.append(
                    f"mismatched mutation target {identity_field!r} mapped to {error.status}"
                )
        if invalid_mutation_runner.calls:
            failures.append(
                f"mismatched mutation target {identity_field!r} invoked Prowl"
            )
    mismatched_state = {
        **sender_state,
        module.WORKTREE_FIELD: recipient_state[module.WORKTREE_FIELD],
        module.HEAD_FIELD: recipient_state[module.HEAD_FIELD],
    }
    try:
        module.build_envelope(
            kind=module.MessageKind.MUTATION_STATE,
            sender=sender,
            recipient=recipient,
            subject="mismatched delegated mutation state",
            facts=["reported state must match the mutation target"],
            request=None,
            active_reference=active_reference,
            mutation_target=sender_target,
            observed_state=mismatched_state,
        )
        failures.append("mismatched observed mutation state was accepted")
    except module.MessageError as error:
        if error.status != module.DeliveryStatus.INVALID_IDENTITY:
            failures.append(f"mismatched observed state mapped to {error.status}")
    for forbidden_field in module.FORBIDDEN_TARGET_FIELDS:
        invalid_request = {**valid_request, forbidden_field: forbidden_field}
        forbidden_runner = RecordingRunner([])
        try:
            module.send_request(invalid_request, discovery, forbidden_runner)
            failures.append(
                f"forbidden target selector {forbidden_field!r} was accepted"
            )
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_SCHEMA:
                failures.append(
                    f"forbidden selector {forbidden_field!r} mapped to {error.status}"
                )
        if forbidden_runner.calls:
            failures.append(
                f"forbidden selector {forbidden_field!r} reached message transport"
            )
    for unavailable_status in (
        module.CallerStatus.UNSUPPORTED_TERMINAL,
        module.CallerStatus.CALLER_AMBIGUOUS,
    ):
        unavailable_runner = RecordingRunner([])
        try:
            module.send_request(
                {**valid_request},
                {**discovery, module.STATUS_FIELD: unavailable_status},
                unavailable_runner,
            )
            failures.append(
                f"unavailable caller {unavailable_status!r} reached message transport"
            )
        except module.MessageError as error:
            if error.status != module.DeliveryStatus.INVALID_IDENTITY:
                failures.append(
                    f"unavailable caller {unavailable_status!r} mapped to {error.status}"
                )
        if unavailable_runner.calls:
            failures.append(
                f"unavailable caller {unavailable_status!r} sent through a fallback"
            )

    roster_result = module.CommandResult(
        0,
        json.dumps(
            {
                module.OK_FIELD: True,
                module.DATA_FIELD: {module.AGENTS_FIELD: public_roster},
            }
        ),
        "",
    )
    discover_main_runner = RecordingRunner([roster_result])
    discover_stdout = StringIO()
    discover_exit = module.main(
        [module.Operation.DISCOVER],
        runner=discover_main_runner,
        environment={module.PROWL_PANE_ID_ENV: sender[module.PANE_FIELD]},
        stdin=StringIO(),
        stdout=discover_stdout,
    )
    discover_output = json.loads(discover_stdout.getvalue())
    if (
        discover_exit != 0
        or discover_output[module.STATUS_FIELD] != module.CallerStatus.PROWL_PANE
        or discover_main_runner.calls != [(module.PUBLIC_AGENT_COMMAND, None)]
    ):
        failures.append("discover CLI boundary did not dispatch and emit success")

    send_main_runner = RecordingRunner(
        [
            roster_result,
            module.CommandResult(
                0,
                json.dumps(
                    {
                        module.OK_FIELD: True,
                        module.DATA_FIELD: {module.ACCEPTED_FIELD: True},
                    }
                ),
                "",
            ),
        ]
    )
    send_stdout = StringIO()
    send_exit = module.main(
        [module.Operation.SEND],
        runner=send_main_runner,
        environment={module.PROWL_PANE_ID_ENV: sender[module.PANE_FIELD]},
        stdin=StringIO(json.dumps(valid_request)),
        stdout=send_stdout,
    )
    send_output = json.loads(send_stdout.getvalue())
    if (
        send_exit != 0
        or send_output[module.STATUS_FIELD] != module.DeliveryStatus.DELIVERED
        or len(send_main_runner.calls) != 2
        or send_main_runner.calls[1][0] != expected_command
        or send_main_runner.calls[1][1] is None
    ):
        failures.append("send CLI boundary did not decode, dispatch, and emit success")

    invalid_stdin_runner = RecordingRunner([roster_result])
    invalid_stdin_stdout = StringIO()
    invalid_stdin_exit = module.main(
        [module.Operation.SEND],
        runner=invalid_stdin_runner,
        environment={module.PROWL_PANE_ID_ENV: sender[module.PANE_FIELD]},
        stdin=StringIO("{"),
        stdout=invalid_stdin_stdout,
    )
    invalid_stdin_output = json.loads(invalid_stdin_stdout.getvalue())
    if (
        invalid_stdin_exit != 2
        or invalid_stdin_output[module.STATUS_FIELD]
        != module.DeliveryStatus.INVALID_SCHEMA
        or invalid_stdin_runner.calls != [(module.PUBLIC_AGENT_COMMAND, None)]
    ):
        failures.append("send CLI boundary did not reject malformed stdin")
    return failures
