#!/usr/bin/env python3
"""Validate and deliver source-owned coordination envelopes through Prowl."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Mapping, Protocol, TextIO

SCHEMA_VERSION = 1
SCHEMA_VERSION_FIELD = "schemaVersion"
COMMAND_TIMEOUT_SECONDS = 15
PROWL_COMMAND = "prowl"
JSON_FLAG = "--json"
PUBLIC_AGENT_COMMAND = (PROWL_COMMAND, "agents", JSON_FLAG)
PROWL_SEND_PREFIX = (PROWL_COMMAND, "send")
PANE_OPTION = "--pane"
NO_WAIT_OPTION = "--no-wait"
OK_FIELD = "ok"
DATA_FIELD = "data"
AGENTS_FIELD = "agents"
ACCEPTED_FIELD = "accepted"
ERROR_FIELD = "error"
MESSAGE_FIELD = "message"
ID_FIELD = "id"
PANE_FIELD = "pane"
WORKTREE_FIELD = "worktree"
PROJECT_FIELD = "project"
RUN_FIELD = "run"
PATH_FIELD = "path"
ROOT_PATH_FIELD = "root_path"
BRANCH_FIELD = "branch"
STATUS_FIELD = "status"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
ACKNOWLEDGED_FIELD = "acknowledged"
AGREED_FIELD = "agreed"
OWNERSHIP_ESTABLISHED_FIELD = "ownershipEstablished"
TRANSPORT_FIELD = "transport"
DETAIL_FIELD = "detail"
CALLER_FIELD = "caller"
TARGETS_FIELD = "targets"
PROWL_PANE_ID_ENV = "PROWL_PANE_ID"
PROWL_WORKTREE_PATH_ENV = "PROWL_WORKTREE_PATH"
TO_PANE_FIELD = "toPane"
KIND_FIELD = "kind"
SUBJECT_FIELD = "subject"
FACTS_FIELD = "facts"
REQUEST_FIELD = "request"
COORDINATION_REFERENCE_FIELD = "coordinationReference"
MUTATION_TARGET_FIELD = "mutationTarget"
OBSERVED_STATE_FIELD = "observedState"
HEAD_FIELD = "head"
REPOSITORY_FIELD = "repository"
MESSAGE_STATE_FIELD = "messageState"
SENDER_FIELD = "sender"
RECIPIENT_FIELD = "recipient"
ENVELOPE_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        COORDINATION_REFERENCE_FIELD,
        KIND_FIELD,
        MESSAGE_STATE_FIELD,
        SENDER_FIELD,
        RECIPIENT_FIELD,
        SUBJECT_FIELD,
        FACTS_FIELD,
        REQUEST_FIELD,
        MUTATION_TARGET_FIELD,
        OBSERVED_STATE_FIELD,
    }
)
REQUEST_INPUT_FIELDS = frozenset(
    {
        TO_PANE_FIELD,
        KIND_FIELD,
        SUBJECT_FIELD,
        FACTS_FIELD,
        REQUEST_FIELD,
        COORDINATION_REFERENCE_FIELD,
        MUTATION_TARGET_FIELD,
        OBSERVED_STATE_FIELD,
    }
)
MUTATION_TARGET_FIELDS = frozenset(
    {
        PANE_FIELD,
        WORKTREE_FIELD,
        BRANCH_FIELD,
        REPOSITORY_FIELD,
        HEAD_FIELD,
        STATUS_FIELD,
    }
)
OBSERVED_STATE_FIELDS = frozenset(
    {WORKTREE_FIELD, BRANCH_FIELD, REPOSITORY_FIELD, HEAD_FIELD, STATUS_FIELD}
)
FORBIDDEN_TARGET_FIELDS = frozenset({"title", "focus", "position", "prose", "channel"})
IDENTITY_FIELDS = ("agent", "pane", "worktree", "branch", "repository")
IDENTITY_INPUT_FIELDS = frozenset((*IDENTITY_FIELDS, RUN_FIELD))


class Operation(StrEnum):
    DISCOVER = "discover"
    SEND = "send"


class CallerStatus(StrEnum):
    PROWL_PANE = "prowl-pane"
    UNSUPPORTED_TERMINAL = "unsupported-terminal"
    CALLER_AMBIGUOUS = "caller-ambiguous"


CALLER_STATUS_DETAILS = {
    CallerStatus.UNSUPPORTED_TERMINAL: (
        "Prowl caller evidence is unavailable. Run inside a Prowl pane with an exact "
        "pane or worktree identity."
    ),
    CallerStatus.CALLER_AMBIGUOUS: (
        "Prowl caller evidence matches more than one detected agent. Supply an exact "
        "PROWL_PANE_ID before sending."
    ),
}


class MessageKind(StrEnum):
    OWNERSHIP_PROPOSAL = "ownership-proposal"
    FACT = "fact"
    ACKNOWLEDGEMENT = "acknowledgement"
    MUTATION_STATE = "mutation-state"
    MUTATION_AUTHORIZATION = "mutation-authorization"


class MessageState(StrEnum):
    OWNERSHIP_PROPOSED = "ownership-proposed"
    FACT_REPORTED = "fact-reported"
    ACKNOWLEDGED = "acknowledged"
    MUTATION_STATE_REPORTED = "mutation-state-reported"
    MUTATION_AUTHORIZED = "mutation-authorized"


MESSAGE_STATE_BY_KIND = {
    MessageKind.OWNERSHIP_PROPOSAL: MessageState.OWNERSHIP_PROPOSED,
    MessageKind.FACT: MessageState.FACT_REPORTED,
    MessageKind.ACKNOWLEDGEMENT: MessageState.ACKNOWLEDGED,
    MessageKind.MUTATION_STATE: MessageState.MUTATION_STATE_REPORTED,
    MessageKind.MUTATION_AUTHORIZATION: MessageState.MUTATION_AUTHORIZED,
}
RESPONSE_KINDS = frozenset(
    {
        MessageKind.ACKNOWLEDGEMENT,
        MessageKind.MUTATION_STATE,
        MessageKind.MUTATION_AUTHORIZATION,
    }
)


class DeliveryStatus(StrEnum):
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery-failed"
    INVALID_IDENTITY = "invalid-identity"
    PROWL_UNAVAILABLE = "prowl-unavailable"
    INVALID_SCHEMA = "invalid-schema"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult: ...


@dataclass(frozen=True)
class SubprocessRunner:
    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS

    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult:
        try:
            completed = subprocess.run(
                argv,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as error:
            raise MessageError(
                DeliveryStatus.PROWL_UNAVAILABLE,
                "Prowl CLI is unavailable. Install `prowl` or run this skill inside Prowl.",
            ) from error
        except subprocess.TimeoutExpired as error:
            raise MessageError(
                DeliveryStatus.DELIVERY_FAILED,
                f"Prowl command exceeded the {self.timeout_seconds}-second bound: {' '.join(argv)}",
            ) from error
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class MessageError(RuntimeError):
    def __init__(
        self,
        status: DeliveryStatus,
        message: str,
        command_exit_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.command_exit_code = command_exit_code


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA, f"Expected an object at {location}."
        )
    return value


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA, f"Expected a non-empty string at {location}."
        )
    return value


def _optional_text(value: object, location: str) -> str | None:
    if value is None:
        return None
    return _text(value, location)


def _message_kind(value: object, location: str = "request.kind") -> MessageKind:
    raw = _text(value, location)
    try:
        return MessageKind(raw)
    except ValueError as error:
        valid = ", ".join(kind.value for kind in MessageKind)
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Unsupported message kind {raw!r}. Valid kinds: {valid}.",
        ) from error


def _decode(result: CommandResult, command: tuple[str, ...]) -> dict[str, object]:
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no command detail"
        raise MessageError(
            DeliveryStatus.DELIVERY_FAILED,
            f"Prowl command failed ({result.returncode}): {' '.join(command)}: {detail}",
            result.returncode,
        )
    try:
        payload = _object(json.loads(result.stdout), "response")
    except json.JSONDecodeError as error:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Prowl returned invalid JSON for {' '.join(command)}: {error.msg}",
            result.returncode,
        ) from error
    if payload.get(OK_FIELD) is not True:
        error_payload = payload.get(ERROR_FIELD)
        detail = "public response reported failure"
        if isinstance(error_payload, dict):
            message = error_payload.get(MESSAGE_FIELD)
            if isinstance(message, str) and message:
                detail = message
        raise MessageError(
            DeliveryStatus.DELIVERY_FAILED,
            f"Prowl command was not accepted: {' '.join(command)}: {detail}",
            result.returncode,
        )
    return payload


def _agents(payload: dict[str, object]) -> list[dict[str, object]]:
    data = _object(payload.get(DATA_FIELD), f"response.{DATA_FIELD}")
    agents = data.get(AGENTS_FIELD)
    if not isinstance(agents, list):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Expected an array at response.{DATA_FIELD}.{AGENTS_FIELD}.",
        )
    return [
        _object(item, f"response.data.agents[{index}]")
        for index, item in enumerate(agents)
    ]


def identity_from_agent(item: dict[str, object]) -> dict[str, str]:
    pane = _object(item.get(PANE_FIELD), f"agent.{PANE_FIELD}")
    worktree = _object(item.get(WORKTREE_FIELD), f"agent.{WORKTREE_FIELD}")
    project = _object(item.get(PROJECT_FIELD), f"agent.{PROJECT_FIELD}")
    identity = {
        "agent": _text(item.get(ID_FIELD), f"agent.{ID_FIELD}"),
        "pane": _text(pane.get(ID_FIELD), f"agent.{PANE_FIELD}.{ID_FIELD}"),
        "worktree": _text(
            worktree.get(PATH_FIELD), f"agent.{WORKTREE_FIELD}.{PATH_FIELD}"
        ),
        "branch": _text(
            project.get(BRANCH_FIELD), f"agent.{PROJECT_FIELD}.{BRANCH_FIELD}"
        ),
        "repository": _text(
            worktree.get(ROOT_PATH_FIELD),
            f"agent.{WORKTREE_FIELD}.{ROOT_PATH_FIELD}",
        ),
    }
    run = item.get(RUN_FIELD)
    if run is not None:
        identity["run"] = _text(
            _object(run, f"agent.{RUN_FIELD}").get(ID_FIELD),
            f"agent.{RUN_FIELD}.{ID_FIELD}",
        )
    return identity


def validate_identity(identity: object, label: str) -> dict[str, str]:
    value = _object(identity, label)
    unexpected = sorted(set(value) - IDENTITY_INPUT_FIELDS)
    if unexpected:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"{label.title()} contains unsupported fields: {', '.join(unexpected)}.",
        )
    validated = {
        field: _text(value.get(field), f"{label}.{field}") for field in IDENTITY_FIELDS
    }
    if value.get("run") is not None:
        validated["run"] = _text(value.get("run"), f"{label}.run")
    return validated


def discover_callers(
    roster: list[dict[str, object]], environment: Mapping[str, str]
) -> tuple[CallerStatus, list[dict[str, str]]]:
    pane_id = environment.get(PROWL_PANE_ID_ENV)
    worktree_path = environment.get(PROWL_WORKTREE_PATH_ENV)
    if not pane_id and not worktree_path:
        return CallerStatus.UNSUPPORTED_TERMINAL, []
    identities = [identity_from_agent(item) for item in roster]
    matches = [
        identity
        for identity in identities
        if (pane_id is None or identity["pane"] == pane_id)
        and (worktree_path is None or identity["worktree"] == worktree_path)
    ]
    if len(matches) == 1:
        return CallerStatus.PROWL_PANE, matches
    return CallerStatus.CALLER_AMBIGUOUS, matches


def discover(
    runner: CommandRunner, environment: Mapping[str, str]
) -> dict[str, object]:
    payload = _decode(runner.run(PUBLIC_AGENT_COMMAND), PUBLIC_AGENT_COMMAND)
    roster = _agents(payload)
    status, matches = discover_callers(roster, environment)
    return {
        "schemaVersion": SCHEMA_VERSION,
        STATUS_FIELD: status,
        DETAIL_FIELD: CALLER_STATUS_DETAILS.get(status),
        CALLER_FIELD: matches[0] if status == CallerStatus.PROWL_PANE else None,
        TARGETS_FIELD: [identity_from_agent(item) for item in roster],
    }


def coordination_reference(
    kind: MessageKind,
    active_reference: str | None,
    uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4,
) -> str:
    if kind in RESPONSE_KINDS:
        if active_reference is None:
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                f"{kind.value} requires the active coordination reference.",
            )
        try:
            return str(uuid.UUID(active_reference))
        except ValueError as error:
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                f"Acknowledgement coordination reference is not a UUID: {active_reference}",
            ) from error
    if active_reference is not None:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Only response messages may reuse an active coordination reference.",
        )
    return str(uuid_factory())


def build_request(
    *,
    to_pane: str,
    kind: MessageKind,
    subject: str,
    facts: list[str],
    request: str | None,
    coordination_reference: str | None = None,
    mutation_target: object = None,
    observed_state: object = None,
) -> dict[str, object]:
    return {
        TO_PANE_FIELD: _text(to_pane, f"request.{TO_PANE_FIELD}"),
        KIND_FIELD: kind,
        SUBJECT_FIELD: _text(subject, f"request.{SUBJECT_FIELD}"),
        FACTS_FIELD: facts,
        REQUEST_FIELD: _optional_text(request, f"request.{REQUEST_FIELD}"),
        COORDINATION_REFERENCE_FIELD: _optional_text(
            coordination_reference, f"request.{COORDINATION_REFERENCE_FIELD}"
        ),
        MUTATION_TARGET_FIELD: mutation_target,
        OBSERVED_STATE_FIELD: observed_state,
    }


def _validated_fields(
    value: object,
    label: str,
    fields: frozenset[str],
    *,
    allow_empty: frozenset[str] = frozenset(),
) -> dict[str, str]:
    item = _object(value, label)
    unexpected = sorted(set(item) - fields)
    missing = sorted(fields - set(item))
    if unexpected or missing:
        details = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"{label} fields are invalid ({'; '.join(details)}).",
        )
    validated: dict[str, str] = {}
    for field in fields:
        raw = item.get(field)
        if field in allow_empty:
            if not isinstance(raw, str):
                raise MessageError(
                    DeliveryStatus.INVALID_SCHEMA,
                    f"Expected a string at {label}.{field}.",
                )
            validated[field] = raw
        else:
            validated[field] = _text(raw, f"{label}.{field}")
    return validated


def _mutation_contract(
    kind: MessageKind,
    sender: dict[str, str],
    recipient: dict[str, str],
    mutation_target: object,
    observed_state: object,
) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    if mutation_target is None and observed_state is None:
        if kind in {MessageKind.MUTATION_STATE, MessageKind.MUTATION_AUTHORIZATION}:
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                f"{kind.value} requires mutationTarget and observedState.",
            )
        return None, None
    if mutation_target is None:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "observedState requires mutationTarget.",
        )
    target = _validated_fields(
        mutation_target,
        MUTATION_TARGET_FIELD,
        MUTATION_TARGET_FIELDS,
        allow_empty=frozenset({STATUS_FIELD}),
    )
    if kind is MessageKind.OWNERSHIP_PROPOSAL:
        if observed_state is not None:
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                "An ownership proposal cannot report observed mutation state.",
            )
        expected_identity = recipient
        state = None
    elif kind is MessageKind.MUTATION_STATE:
        expected_identity = sender
        state = _validated_fields(
            observed_state,
            OBSERVED_STATE_FIELD,
            OBSERVED_STATE_FIELDS,
            allow_empty=frozenset({STATUS_FIELD}),
        )
    elif kind is MessageKind.MUTATION_AUTHORIZATION:
        expected_identity = recipient
        state = _validated_fields(
            observed_state,
            OBSERVED_STATE_FIELD,
            OBSERVED_STATE_FIELDS,
            allow_empty=frozenset({STATUS_FIELD}),
        )
    else:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"{kind.value} cannot carry a mutation target.",
        )
    for field in {PANE_FIELD, WORKTREE_FIELD, BRANCH_FIELD, REPOSITORY_FIELD}:
        if target[field] != expected_identity[field]:
            raise MessageError(
                DeliveryStatus.INVALID_IDENTITY,
                f"{kind.value} target {field} does not match the live message identity.",
            )
    if state is not None:
        for field in OBSERVED_STATE_FIELDS:
            if state[field] != target[field]:
                raise MessageError(
                    DeliveryStatus.INVALID_IDENTITY,
                    f"Observed {field} does not match the mutation target.",
                )
    return target, state


def build_envelope(
    *,
    kind: MessageKind,
    sender: object,
    recipient: object,
    subject: str,
    facts: list[str],
    request: str | None,
    active_reference: str | None = None,
    uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4,
    mutation_target: object = None,
    observed_state: object = None,
) -> dict[str, object]:
    if not subject:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA, "Message subject must not be empty."
        )
    if not facts:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "At least one authoritative fact is required.",
        )
    if any(not fact for fact in facts):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA, "Message facts must be non-empty strings."
        )
    validated_sender = validate_identity(sender, SENDER_FIELD)
    validated_recipient = validate_identity(recipient, RECIPIENT_FIELD)
    validated_target, validated_state = _mutation_contract(
        kind,
        validated_sender,
        validated_recipient,
        mutation_target,
        observed_state,
    )
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        COORDINATION_REFERENCE_FIELD: coordination_reference(
            kind, active_reference, uuid_factory
        ),
        KIND_FIELD: kind,
        MESSAGE_STATE_FIELD: MESSAGE_STATE_BY_KIND[kind],
        SENDER_FIELD: validated_sender,
        RECIPIENT_FIELD: validated_recipient,
        SUBJECT_FIELD: subject,
        FACTS_FIELD: facts,
        REQUEST_FIELD: request,
        MUTATION_TARGET_FIELD: validated_target,
        OBSERVED_STATE_FIELD: validated_state,
    }


def validate_envelope(envelope: object) -> dict[str, object]:
    value = _object(envelope, "envelope")
    unexpected = sorted(set(value) - ENVELOPE_FIELDS)
    missing = sorted(ENVELOPE_FIELDS - set(value))
    if unexpected or missing:
        details = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Envelope fields are invalid ({'; '.join(details)}).",
        )
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Envelope schema version must be {SCHEMA_VERSION}.",
        )
    kind = _message_kind(value.get(KIND_FIELD), f"envelope.{KIND_FIELD}")
    expected_state = MESSAGE_STATE_BY_KIND[kind]
    if value.get(MESSAGE_STATE_FIELD) != expected_state:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Envelope message state must be {expected_state} for kind {kind}.",
        )
    reference = _text(
        value.get(COORDINATION_REFERENCE_FIELD),
        f"envelope.{COORDINATION_REFERENCE_FIELD}",
    )
    try:
        canonical_reference = str(uuid.UUID(reference))
    except ValueError as error:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Envelope coordination reference is not a UUID: {reference}",
        ) from error
    validated_sender = validate_identity(value.get(SENDER_FIELD), SENDER_FIELD)
    validated_recipient = validate_identity(value.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    validated_target, validated_state = _mutation_contract(
        kind,
        validated_sender,
        validated_recipient,
        value.get(MUTATION_TARGET_FIELD),
        value.get(OBSERVED_STATE_FIELD),
    )
    facts = value.get(FACTS_FIELD)
    if (
        not isinstance(facts, list)
        or not facts
        or not all(isinstance(fact, str) and fact for fact in facts)
    ):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Envelope facts must be a non-empty array of non-empty strings.",
        )
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        COORDINATION_REFERENCE_FIELD: canonical_reference,
        KIND_FIELD: kind,
        MESSAGE_STATE_FIELD: expected_state,
        SENDER_FIELD: validated_sender,
        RECIPIENT_FIELD: validated_recipient,
        SUBJECT_FIELD: _text(value.get(SUBJECT_FIELD), f"envelope.{SUBJECT_FIELD}"),
        FACTS_FIELD: facts,
        REQUEST_FIELD: _optional_text(
            value.get(REQUEST_FIELD), f"envelope.{REQUEST_FIELD}"
        ),
        MUTATION_TARGET_FIELD: validated_target,
        OBSERVED_STATE_FIELD: validated_state,
    }


def delivery_command(pane_id: str) -> tuple[str, ...]:
    return (
        *PROWL_SEND_PREFIX,
        PANE_OPTION,
        pane_id,
        NO_WAIT_OPTION,
        JSON_FLAG,
    )


def send_envelope(envelope: object, runner: CommandRunner) -> dict[str, object]:
    value = validate_envelope(envelope)
    recipient = validate_identity(value.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    rendered = json.dumps(value, sort_keys=True)
    command = delivery_command(recipient["pane"])
    result = runner.run(command, rendered)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no command detail"
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: DeliveryStatus.DELIVERY_FAILED,
            COORDINATION_REFERENCE_FIELD: value.get(COORDINATION_REFERENCE_FIELD),
            COMMAND_EXIT_CODE_FIELD: result.returncode,
            DETAIL_FIELD: detail,
        }
    payload = _decode(result, command)
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: DeliveryStatus.DELIVERED,
        COORDINATION_REFERENCE_FIELD: value.get(COORDINATION_REFERENCE_FIELD),
        COMMAND_EXIT_CODE_FIELD: result.returncode,
        TRANSPORT_FIELD: payload,
        ACKNOWLEDGED_FIELD: False,
        AGREED_FIELD: False,
        OWNERSHIP_ESTABLISHED_FIELD: False,
    }


def send_request(
    request: object, discovery: dict[str, object], runner: CommandRunner
) -> dict[str, object]:
    value = _object(request, "request")
    unexpected = sorted(set(value) - REQUEST_INPUT_FIELDS)
    if unexpected:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Message request contains unsupported fields: {', '.join(unexpected)}.",
        )
    if discovery.get(STATUS_FIELD) != CallerStatus.PROWL_PANE:
        raise MessageError(
            DeliveryStatus.INVALID_IDENTITY,
            f"Cannot send because caller status is {discovery.get(STATUS_FIELD)}.",
        )
    facts = value.get(FACTS_FIELD)
    if not isinstance(facts, list) or not all(isinstance(fact, str) for fact in facts):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Expected an array of strings at request.facts.",
        )
    envelope = build_envelope(
        kind=_message_kind(value.get(KIND_FIELD)),
        sender=discovery.get(CALLER_FIELD),
        recipient=_target_by_pane(
            discovery.get(TARGETS_FIELD),
            _text(value.get(TO_PANE_FIELD), f"request.{TO_PANE_FIELD}"),
        ),
        subject=_text(value.get(SUBJECT_FIELD), f"request.{SUBJECT_FIELD}"),
        facts=facts,
        request=_optional_text(value.get(REQUEST_FIELD), f"request.{REQUEST_FIELD}"),
        active_reference=_optional_text(
            value.get(COORDINATION_REFERENCE_FIELD),
            f"request.{COORDINATION_REFERENCE_FIELD}",
        ),
        mutation_target=value.get(MUTATION_TARGET_FIELD),
        observed_state=value.get(OBSERVED_STATE_FIELD),
    )
    return send_envelope(envelope, runner)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in Operation:
        subparsers.add_parser(operation)
    return parser


def command_exit_code(operation: Operation, result: object) -> int:
    status = _object(result, "result").get(STATUS_FIELD)
    if operation is Operation.DISCOVER:
        return 0 if status == CallerStatus.PROWL_PANE else 2
    return 0 if status == DeliveryStatus.DELIVERED else 2


def _target_by_pane(targets: object, pane_id: str) -> dict[str, str]:
    if not isinstance(targets, list):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA, "Expected discovered targets to be an array."
        )
    matches = [
        validate_identity(item, "target")
        for item in targets
        if _object(item, "target").get("pane") == pane_id
    ]
    if len(matches) != 1:
        raise MessageError(
            DeliveryStatus.INVALID_IDENTITY,
            f"Expected exactly one target with pane UUID {pane_id}; found {len(matches)}.",
        )
    return matches[0]


def main(
    argv: list[str] | None = None,
    *,
    runner: CommandRunner | None = None,
    environment: Mapping[str, str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    args = _parser().parse_args(argv)
    operation = Operation(args.operation)
    command_runner = runner if runner is not None else SubprocessRunner()
    active_environment = environment if environment is not None else os.environ
    input_stream = stdin if stdin is not None else sys.stdin
    output_stream = stdout if stdout is not None else sys.stdout
    try:
        discovery = discover(command_runner, active_environment)
        if operation is Operation.DISCOVER:
            result: object = discovery
        else:
            try:
                request = json.load(input_stream)
            except json.JSONDecodeError as error:
                raise MessageError(
                    DeliveryStatus.INVALID_SCHEMA,
                    f"Message request on stdin is invalid JSON: {error.msg}",
                ) from error
            result = send_request(request, discovery, command_runner)
        print(json.dumps(result, sort_keys=True), file=output_stream)
        return command_exit_code(operation, result)
    except MessageError as error:
        failure: dict[str, object] = {
            "schemaVersion": SCHEMA_VERSION,
            STATUS_FIELD: error.status,
            DETAIL_FIELD: str(error),
        }
        if error.command_exit_code is not None:
            failure[COMMAND_EXIT_CODE_FIELD] = error.command_exit_code
        print(json.dumps(failure, sort_keys=True), file=output_stream)
        return 2


if __name__ == "__main__":
    sys.exit(main())
