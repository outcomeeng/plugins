#!/usr/bin/env python3
"""Validate source-owned coordination envelopes and environment deliveries."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import uuid
from enum import StrEnum
from pathlib import Path
from types import ModuleType
from typing import Callable, TextIO, cast

SCHEMA_VERSION = 4
SCHEMA_VERSION_FIELD = "schemaVersion"
STATUS_FIELD = "status"
DETAIL_FIELD = "detail"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
TRANSPORT_FIELD = "transport"
ACKNOWLEDGED_FIELD = "acknowledged"
AGREED_FIELD = "agreed"
OWNERSHIP_ESTABLISHED_FIELD = "ownershipEstablished"
CALLER_FIELD = "caller"
TARGETS_FIELD = "targets"
DISCOVERY_FIELD = "discovery"
MESSAGE_REQUEST_FIELD = "messageRequest"
ENVELOPE_FIELD = "envelope"
DELIVERY_FIELD = "delivery"
DELIVERED_FIELD = "delivered"
TEXT_FIELD = "text"
DISCOVERY_READY_STATUS = "prowl-pane"
TO_PANE_FIELD = "toPane"
KIND_FIELD = "kind"
SUBJECT_FIELD = "subject"
FACTS_FIELD = "facts"
REQUEST_FIELD = "request"
HANDBACK_FIELD = "handback"
COMPLETION_TEXT_FIELD = "completionText"
ADAPTER_PATH_FIELD = "adapterPath"
COMMAND_FIELD = "command"
SUCCESS_CRITERIA_FIELD = "successCriteria"
RETRY_POLICY_FIELD = "retryPolicy"
SOCKET_FIELD = "socket"
EXPECTED_PANES_FIELD = "expectedPanes"
COORDINATION_REFERENCE_FIELD = "coordinationReference"
MUTATION_TARGET_FIELD = "mutationTarget"
OBSERVED_STATE_FIELD = "observedState"
ACCEPTED_FIELD = "accepted"
HEAD_FIELD = "head"
REPOSITORY_FIELD = "repository"
MESSAGE_STATE_FIELD = "messageState"
SENDER_FIELD = "sender"
RECIPIENT_FIELD = "recipient"
PANE_FIELD = "pane"
WORKTREE_FIELD = "worktree"
RUN_FIELD = "run"
BRANCH_FIELD = "branch"
CLEAN_STATUS = "clean"
FULL_HEAD_PATTERN = re.compile(r"[0-9a-f]{40}")
TRANSPORT_SCHEMA_VERSION = 1
TRANSPORT_OPERATION_FIELD = "operation"
TRANSPORT_RESPONSE_FIELD = "response"
DATA_FIELD = "data"
INPUT_FIELD = "input"
TRAILING_ENTER_SENT_FIELD = "trailing_enter_sent"
TRANSPORT_SEND_OPERATION = "send"
TRANSPORT_SUCCEEDED_STATUS = "succeeded"
HANDBACK_SCHEMA_VERSION = 1
HANDBACK_RETRY_POLICY = "never-after-trailing-enter"
DEFAULT_SOCKET = "default"
TRANSPORT_SUCCESS_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        TRANSPORT_OPERATION_FIELD,
        STATUS_FIELD,
        COMMAND_EXIT_CODE_FIELD,
        TRANSPORT_RESPONSE_FIELD,
    }
)

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
        HANDBACK_FIELD,
        MUTATION_TARGET_FIELD,
        OBSERVED_STATE_FIELD,
        ACCEPTED_FIELD,
    }
)
REQUEST_INPUT_FIELDS = frozenset(
    {
        TO_PANE_FIELD,
        KIND_FIELD,
        SUBJECT_FIELD,
        FACTS_FIELD,
        REQUEST_FIELD,
        HANDBACK_FIELD,
        COORDINATION_REFERENCE_FIELD,
        MUTATION_TARGET_FIELD,
        OBSERVED_STATE_FIELD,
        ACCEPTED_FIELD,
    }
)
HANDBACK_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        COMPLETION_TEXT_FIELD,
        ADAPTER_PATH_FIELD,
        COMMAND_FIELD,
        SUCCESS_CRITERIA_FIELD,
        RETRY_POLICY_FIELD,
        SOCKET_FIELD,
        EXPECTED_PANES_FIELD,
    }
)
HANDBACK_SUCCESS_FIELDS = frozenset(
    {STATUS_FIELD, COMMAND_EXIT_CODE_FIELD, TRAILING_ENTER_SENT_FIELD}
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
FORBIDDEN_EXECUTABLE_FIELDS = frozenset(
    {COMMAND_FIELD, "handbackCommand", "returnPane", ADAPTER_PATH_FIELD}
)
IDENTITY_FIELDS = ("agent", "pane", "worktree", "branch", "repository")
IDENTITY_INPUT_FIELDS = frozenset((*IDENTITY_FIELDS, RUN_FIELD))
PROWL_ENVIRONMENT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "operate-prowl"
    / "scripts"
    / "prowl_environment.py"
)
PROWL_ENVIRONMENT_MODULE = "coding_agents_prowl_environment"


class Operation(StrEnum):
    BUILD = "build"
    RESULT = "result"


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
    READY = "ready"
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery-failed"
    INVALID_IDENTITY = "invalid-identity"
    ENVIRONMENT_UNAVAILABLE = "environment-unavailable"
    INVALID_SCHEMA = "invalid-schema"


class MessageError(RuntimeError):
    def __init__(self, status: DeliveryStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


def _load_prowl_environment() -> ModuleType:
    resolved_path = PROWL_ENVIRONMENT_PATH.resolve()
    cached = sys.modules.get(PROWL_ENVIRONMENT_MODULE)
    if cached is not None:
        module_path = getattr(cached, "__file__", None)
        if isinstance(module_path, str) and Path(module_path).resolve() == resolved_path:
            return cached
    spec = importlib.util.spec_from_file_location(
        PROWL_ENVIRONMENT_MODULE,
        resolved_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load Prowl environment command contract from {resolved_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PROWL_ENVIRONMENT_MODULE] = module
    spec.loader.exec_module(module)
    return module


def _expected_handback_command(
    *, pane: str, completion_text: str, adapter_path: str
) -> str:
    command_builder = cast(
        Callable[..., str],
        getattr(_load_prowl_environment(), "_handback_command"),
    )
    return command_builder(
        pane=pane,
        completion_text=completion_text,
        adapter_path=adapter_path,
    )


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


def validate_identity(identity: object, label: str) -> dict[str, str]:
    value = _object(identity, label)
    unexpected = sorted(set(value) - IDENTITY_INPUT_FIELDS)
    missing = sorted(set(IDENTITY_FIELDS) - set(value))
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"{label.title()} identity fields are invalid ({'; '.join(details)}).",
        )
    validated = {
        field: _text(value.get(field), f"{label}.{field}") for field in IDENTITY_FIELDS
    }
    for field in (WORKTREE_FIELD, REPOSITORY_FIELD):
        if not os.path.isabs(validated[field]):
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                f"Expected an absolute path at {label}.{field}.",
            )
    if value.get(RUN_FIELD) is not None:
        validated[RUN_FIELD] = _text(value.get(RUN_FIELD), f"{label}.{RUN_FIELD}")
    return validated


def _validated_handback(
    value: object,
    *,
    sender: dict[str, str],
    recipient: dict[str, str],
) -> dict[str, object] | None:
    if value is None:
        return None
    handback = _object(value, HANDBACK_FIELD)
    unexpected = sorted(set(handback) - HANDBACK_FIELDS)
    missing = sorted(HANDBACK_FIELDS - set(handback))
    if unexpected or missing:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Handback must contain exactly the environment-owned fields.",
        )
    if handback.get(SCHEMA_VERSION_FIELD) != HANDBACK_SCHEMA_VERSION:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Handback schema version must be {HANDBACK_SCHEMA_VERSION}.",
        )
    completion_text = _text(
        handback.get(COMPLETION_TEXT_FIELD),
        f"{HANDBACK_FIELD}.{COMPLETION_TEXT_FIELD}",
    )
    adapter_path = _text(
        handback.get(ADAPTER_PATH_FIELD),
        f"{HANDBACK_FIELD}.{ADAPTER_PATH_FIELD}",
    )
    if not Path(adapter_path).is_absolute():
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Handback adapterPath must be absolute.",
        )
    command = _text(handback.get(COMMAND_FIELD), f"{HANDBACK_FIELD}.{COMMAND_FIELD}")
    expected_command = _expected_handback_command(
        pane=sender[PANE_FIELD],
        completion_text=completion_text,
        adapter_path=adapter_path,
    )
    if command != expected_command:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Handback command does not match its semantic completion data.",
        )
    success = _object(
        handback.get(SUCCESS_CRITERIA_FIELD),
        f"{HANDBACK_FIELD}.{SUCCESS_CRITERIA_FIELD}",
    )
    command_exit_code = success.get(COMMAND_EXIT_CODE_FIELD)
    if (
        set(success) != HANDBACK_SUCCESS_FIELDS
        or success.get(STATUS_FIELD) != TRANSPORT_SUCCEEDED_STATUS
        or not isinstance(command_exit_code, int)
        or isinstance(command_exit_code, bool)
        or command_exit_code != 0
        or success.get(TRAILING_ENTER_SENT_FIELD) is not True
    ):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Handback success criteria must require checked turn submission.",
        )
    if handback.get(RETRY_POLICY_FIELD) != HANDBACK_RETRY_POLICY:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Handback retryPolicy must be {HANDBACK_RETRY_POLICY}.",
        )
    if handback.get(SOCKET_FIELD) != DEFAULT_SOCKET:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Handback socket must be {DEFAULT_SOCKET}.",
        )
    expected_panes = [sender[PANE_FIELD], recipient[PANE_FIELD]]
    if handback.get(EXPECTED_PANES_FIELD) != expected_panes:
        raise MessageError(
            DeliveryStatus.INVALID_IDENTITY,
            "Handback expectedPanes do not match the message participants.",
        )
    return {
        SCHEMA_VERSION_FIELD: HANDBACK_SCHEMA_VERSION,
        COMPLETION_TEXT_FIELD: completion_text,
        ADAPTER_PATH_FIELD: adapter_path,
        COMMAND_FIELD: command,
        SUCCESS_CRITERIA_FIELD: success,
        RETRY_POLICY_FIELD: HANDBACK_RETRY_POLICY,
        SOCKET_FIELD: DEFAULT_SOCKET,
        EXPECTED_PANES_FIELD: expected_panes,
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
                f"Response coordination reference is not a UUID: {active_reference}",
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
    handback: object = None,
    coordination_reference: str | None = None,
    mutation_target: object = None,
    observed_state: object = None,
    accepted: bool | None = None,
) -> dict[str, object]:
    return {
        TO_PANE_FIELD: _text(to_pane, f"request.{TO_PANE_FIELD}"),
        KIND_FIELD: kind,
        SUBJECT_FIELD: _text(subject, f"request.{SUBJECT_FIELD}"),
        FACTS_FIELD: facts,
        REQUEST_FIELD: _optional_text(request, f"request.{REQUEST_FIELD}"),
        HANDBACK_FIELD: handback,
        COORDINATION_REFERENCE_FIELD: _optional_text(
            coordination_reference, f"request.{COORDINATION_REFERENCE_FIELD}"
        ),
        MUTATION_TARGET_FIELD: mutation_target,
        OBSERVED_STATE_FIELD: observed_state,
        ACCEPTED_FIELD: accepted,
    }


def _validated_fields(
    value: object,
    label: str,
    fields: frozenset[str],
) -> dict[str, str]:
    item = _object(value, label)
    unexpected = sorted(set(item) - fields)
    missing = sorted(fields - set(item))
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"{label} fields are invalid ({'; '.join(details)}).",
        )
    validated = {field: _text(item.get(field), f"{label}.{field}") for field in fields}
    if (
        HEAD_FIELD in validated
        and FULL_HEAD_PATTERN.fullmatch(validated[HEAD_FIELD]) is None
    ):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Expected a complete lowercase hexadecimal HEAD at {label}.{HEAD_FIELD}.",
        )
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
            DeliveryStatus.INVALID_SCHEMA, "observedState requires mutationTarget."
        )
    target = _validated_fields(
        mutation_target,
        MUTATION_TARGET_FIELD,
        MUTATION_TARGET_FIELDS,
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
        )
    elif kind is MessageKind.MUTATION_AUTHORIZATION:
        expected_identity = recipient
        state = _validated_fields(
            observed_state,
            OBSERVED_STATE_FIELD,
            OBSERVED_STATE_FIELDS,
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
    handback: object = None,
    active_reference: str | None = None,
    uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4,
    mutation_target: object = None,
    observed_state: object = None,
    accepted: bool | None = None,
) -> dict[str, object]:
    if not facts or any(not isinstance(fact, str) or not fact for fact in facts):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Message facts must be a non-empty array of non-empty strings.",
        )
    validated_sender = validate_identity(sender, SENDER_FIELD)
    validated_recipient = validate_identity(recipient, RECIPIENT_FIELD)
    if kind is MessageKind.ACKNOWLEDGEMENT:
        if not isinstance(accepted, bool):
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                "An acknowledgement requires boolean accepted state.",
            )
    elif accepted is not None:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"{kind.value} cannot carry accepted state.",
        )
    validated_target, validated_state = _mutation_contract(
        kind,
        validated_sender,
        validated_recipient,
        mutation_target,
        observed_state,
    )
    validated_handback = _validated_handback(
        handback,
        sender=validated_sender,
        recipient=validated_recipient,
    )
    if validated_handback is not None and kind is not MessageKind.FACT:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Only a fact production request may carry a handback.",
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
        SUBJECT_FIELD: _text(subject, SUBJECT_FIELD),
        FACTS_FIELD: facts,
        REQUEST_FIELD: _optional_text(request, REQUEST_FIELD),
        HANDBACK_FIELD: validated_handback,
        MUTATION_TARGET_FIELD: validated_target,
        OBSERVED_STATE_FIELD: validated_state,
        ACCEPTED_FIELD: accepted,
    }


def validate_envelope(envelope: object) -> dict[str, object]:
    value = _object(envelope, ENVELOPE_FIELD)
    unexpected = sorted(set(value) - ENVELOPE_FIELDS)
    missing = sorted(ENVELOPE_FIELDS - set(value))
    if unexpected or missing:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Envelope must contain exactly the source-owned fields.",
        )
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Envelope schema version must be {SCHEMA_VERSION}.",
        )
    kind = _message_kind(value.get(KIND_FIELD), f"envelope.{KIND_FIELD}")
    accepted = value.get(ACCEPTED_FIELD)
    if kind is MessageKind.ACKNOWLEDGEMENT:
        if not isinstance(accepted, bool):
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                "An acknowledgement requires boolean accepted state.",
            )
    elif accepted is not None:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"{kind.value} cannot carry accepted state.",
        )
    expected_state = MESSAGE_STATE_BY_KIND[kind]
    if value.get(MESSAGE_STATE_FIELD) != expected_state:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Envelope message state must be {expected_state} for kind {kind}.",
        )
    reference = (
        coordination_reference(
            kind, cast(str | None, value.get(COORDINATION_REFERENCE_FIELD))
        )
        if kind in RESPONSE_KINDS
        else _text(
            value.get(COORDINATION_REFERENCE_FIELD), COORDINATION_REFERENCE_FIELD
        )
    )
    if kind not in RESPONSE_KINDS:
        try:
            reference = str(uuid.UUID(reference))
        except ValueError as error:
            raise MessageError(
                DeliveryStatus.INVALID_SCHEMA,
                f"Envelope coordination reference is not a UUID: {reference}",
            ) from error
    sender = validate_identity(value.get(SENDER_FIELD), SENDER_FIELD)
    recipient = validate_identity(value.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    handback = _validated_handback(
        value.get(HANDBACK_FIELD),
        sender=sender,
        recipient=recipient,
    )
    if handback is not None and kind is not MessageKind.FACT:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Only a fact production request may carry a handback.",
        )
    target, state = _mutation_contract(
        kind,
        sender,
        recipient,
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
        COORDINATION_REFERENCE_FIELD: reference,
        KIND_FIELD: kind,
        MESSAGE_STATE_FIELD: expected_state,
        SENDER_FIELD: sender,
        RECIPIENT_FIELD: recipient,
        SUBJECT_FIELD: _text(value.get(SUBJECT_FIELD), SUBJECT_FIELD),
        FACTS_FIELD: facts,
        REQUEST_FIELD: _optional_text(value.get(REQUEST_FIELD), REQUEST_FIELD),
        HANDBACK_FIELD: handback,
        MUTATION_TARGET_FIELD: target,
        OBSERVED_STATE_FIELD: state,
        ACCEPTED_FIELD: accepted,
    }


def _target_by_pane(targets: object, pane_id: str) -> dict[str, str]:
    if not isinstance(targets, list):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA, "Expected discovered targets to be an array."
        )
    matches = [
        validate_identity(item, "target")
        for item in targets
        if _object(item, "target").get(PANE_FIELD) == pane_id
    ]
    if len(matches) != 1:
        raise MessageError(
            DeliveryStatus.INVALID_IDENTITY,
            f"Expected exactly one target with pane UUID {pane_id}; found {len(matches)}.",
        )
    return matches[0]


def delivery_request(envelope: object) -> dict[str, object]:
    value = validate_envelope(envelope)
    recipient = validate_identity(value.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: DeliveryStatus.READY,
        COORDINATION_REFERENCE_FIELD: value[COORDINATION_REFERENCE_FIELD],
        TO_PANE_FIELD: recipient[PANE_FIELD],
        TEXT_FIELD: json.dumps(value, sort_keys=True),
    }


def send_request(request: object, discovery: object) -> dict[str, object]:
    value = _object(request, MESSAGE_REQUEST_FIELD)
    unexpected = sorted(set(value) - REQUEST_INPUT_FIELDS)
    if unexpected:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Message request contains unsupported fields: {', '.join(unexpected)}.",
        )
    discovered = _object(discovery, DISCOVERY_FIELD)
    if discovered.get(STATUS_FIELD) != DISCOVERY_READY_STATUS:
        raise MessageError(
            DeliveryStatus.INVALID_IDENTITY,
            f"Cannot send because caller status is {discovered.get(STATUS_FIELD)}.",
        )
    caller = validate_identity(discovered.get(CALLER_FIELD), CALLER_FIELD)
    to_pane = _text(value.get(TO_PANE_FIELD), f"request.{TO_PANE_FIELD}")
    if to_pane == caller[PANE_FIELD]:
        raise MessageError(
            DeliveryStatus.INVALID_IDENTITY,
            "Cannot send a message to the caller pane.",
        )
    facts = value.get(FACTS_FIELD)
    if not isinstance(facts, list) or not all(isinstance(fact, str) for fact in facts):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "Expected an array of strings at request.facts.",
        )
    envelope = build_envelope(
        kind=_message_kind(value.get(KIND_FIELD)),
        sender=caller,
        recipient=_target_by_pane(
            discovered.get(TARGETS_FIELD),
            to_pane,
        ),
        subject=_text(value.get(SUBJECT_FIELD), f"request.{SUBJECT_FIELD}"),
        facts=facts,
        request=_optional_text(value.get(REQUEST_FIELD), f"request.{REQUEST_FIELD}"),
        handback=value.get(HANDBACK_FIELD),
        active_reference=_optional_text(
            value.get(COORDINATION_REFERENCE_FIELD),
            f"request.{COORDINATION_REFERENCE_FIELD}",
        ),
        mutation_target=value.get(MUTATION_TARGET_FIELD),
        observed_state=value.get(OBSERVED_STATE_FIELD),
        accepted=cast(bool | None, value.get(ACCEPTED_FIELD)),
    )
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        ENVELOPE_FIELD: envelope,
        DELIVERY_FIELD: delivery_request(envelope),
    }


def _checked_success_transport(
    transport: object, command_exit_code: int | None
) -> dict[str, object]:
    value = _object(transport, TRANSPORT_FIELD)
    if set(value) != TRANSPORT_SUCCESS_FIELDS:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "A delivered result requires the complete checked transport fields.",
        )
    if value.get(SCHEMA_VERSION_FIELD) != TRANSPORT_SCHEMA_VERSION:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Transport schema version must be {TRANSPORT_SCHEMA_VERSION}.",
        )
    if value.get(TRANSPORT_OPERATION_FIELD) != TRANSPORT_SEND_OPERATION:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "A delivered result requires a checked send transport operation.",
        )
    if value.get(STATUS_FIELD) != TRANSPORT_SUCCEEDED_STATUS:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "A delivered result requires succeeded transport status.",
        )
    transport_exit_code = value.get(COMMAND_EXIT_CODE_FIELD)
    if (
        not isinstance(transport_exit_code, int)
        or isinstance(transport_exit_code, bool)
        or transport_exit_code != 0
        or command_exit_code != transport_exit_code
    ):
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "A delivered result requires matching zero command exit codes.",
        )
    response = _object(
        value.get(TRANSPORT_RESPONSE_FIELD), f"{TRANSPORT_FIELD}.response"
    )
    data = _object(response.get(DATA_FIELD), f"{TRANSPORT_FIELD}.response.data")
    input_record = _object(
        data.get(INPUT_FIELD), f"{TRANSPORT_FIELD}.response.data.input"
    )
    if input_record.get(TRAILING_ENTER_SENT_FIELD) is not True:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            "A delivered result requires trailing_enter_sent: true submission evidence.",
        )
    return value


def delivery_result(
    envelope: object,
    *,
    delivered: bool,
    command_exit_code: int | None,
    transport: object = None,
    detail: str | None = None,
) -> dict[str, object]:
    value = validate_envelope(envelope)
    checked_transport = (
        _checked_success_transport(transport, command_exit_code)
        if delivered
        else transport
    )
    result: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: (
            DeliveryStatus.DELIVERED if delivered else DeliveryStatus.DELIVERY_FAILED
        ),
        COORDINATION_REFERENCE_FIELD: value[COORDINATION_REFERENCE_FIELD],
        COMMAND_EXIT_CODE_FIELD: command_exit_code,
        TRANSPORT_FIELD: checked_transport,
        ACKNOWLEDGED_FIELD: False,
        AGREED_FIELD: False,
        OWNERSHIP_ESTABLISHED_FIELD: False,
    }
    if not delivered:
        result[DETAIL_FIELD] = _optional_text(detail, DETAIL_FIELD) or (
            "The environment capability did not deliver the envelope."
        )
    return result


def command_exit_code(operation: Operation, result: object) -> int:
    value = _object(result, "result")
    status = value.get(STATUS_FIELD)
    if operation is Operation.BUILD:
        delivery = value.get(DELIVERY_FIELD)
        return (
            0
            if isinstance(delivery, dict)
            and delivery.get(STATUS_FIELD) == DeliveryStatus.READY
            else 2
        )
    return 0 if status == DeliveryStatus.DELIVERED else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in Operation:
        subparsers.add_parser(operation.value)
    return parser


def _json_input(stream: TextIO) -> dict[str, object]:
    try:
        return _object(json.load(stream), "stdin")
    except json.JSONDecodeError as error:
        raise MessageError(
            DeliveryStatus.INVALID_SCHEMA,
            f"Message input on stdin is invalid JSON: {error.msg}",
        ) from error


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    args = _parser().parse_args(argv)
    operation = Operation(args.operation)
    input_stream = stdin if stdin is not None else sys.stdin
    output_stream = stdout if stdout is not None else sys.stdout
    try:
        value = _json_input(input_stream)
        if operation is Operation.BUILD:
            result = send_request(
                value.get(MESSAGE_REQUEST_FIELD), value.get(DISCOVERY_FIELD)
            )
        else:
            result = delivery_result(
                value.get(ENVELOPE_FIELD),
                delivered=value.get(DELIVERED_FIELD) is True,
                command_exit_code=cast(int | None, value.get(COMMAND_EXIT_CODE_FIELD)),
                transport=value.get(TRANSPORT_FIELD),
                detail=cast(str | None, value.get(DETAIL_FIELD)),
            )
        print(json.dumps(result, sort_keys=True), file=output_stream)
        return command_exit_code(operation, result)
    except MessageError as error:
        print(
            json.dumps(
                {
                    SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
                    STATUS_FIELD: error.status,
                    DETAIL_FIELD: str(error),
                },
                sort_keys=True,
            ),
            file=output_stream,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
