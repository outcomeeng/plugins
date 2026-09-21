#!/usr/bin/env python3
"""Operate the agent-mail store through a checked, versioned capability."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Mapping, Protocol, TextIO, cast

SCHEMA_VERSION = 1
RECORD_SCHEMA_VERSION = 1
COMMAND_TIMEOUT_SECONDS = 30

# Public command grammar of the store and of the diagnosis that names its project.
AM_COMMAND = "am"
SPX_COMMAND = "spx"
AGENTS_COMMAND = "agents"
REGISTER_COMMAND = "register"
MAIL_COMMAND = "mail"
SEND_COMMAND = "send"
ACK_COMMAND = "ack"
INBOX_COMMAND = "inbox"
DIAGNOSE_COMMAND = "diagnose"
PROJECT_OPTION = "--project"
PROGRAM_OPTION = "--program"
MODEL_OPTION = "--model"
NAME_OPTION = "--name"
TASK_OPTION = "--task"
FROM_OPTION = "--from"
TO_OPTION = "--to"
THREAD_ID_OPTION = "--thread-id"
SUBJECT_OPTION = "--subject"
BODY_OPTION = "--body"
ACK_REQUIRED_OPTION = "--ack-required"
AGENT_OPTION = "--agent"
INCLUDE_BODIES_OPTION = "--include-bodies"
LIMIT_OPTION = "--limit"
JSON_OPTION = "--json"
FORMAT_OPTION = "--format"
JSON_FORMAT = "json"

# Fields of the diagnosis payload the project key is read from.
CHECKS_FIELD = "checks"
NAME_FIELD = "name"
WORKTREE_POOL_CHECK = "worktree-pool"
READINGS_FIELD = "readings"
MAIN_CHECKOUT_PATH_FIELD = "mainCheckoutPath"

# Fields of the store's public responses.
STORE_ID_FIELD = "id"
STORE_NAME_FIELD = "name"
STORE_REGISTRATION_TOKEN_FIELD = "registration_token"
STORE_SUBJECT_FIELD = "subject"
STORE_BODY_FIELD = "body_md"
STORE_FROM_FIELD = "from"
STORE_TO_FIELD = "to"
STORE_THREAD_ID_FIELD = "thread_id"
STORE_ACK_REQUIRED_FIELD = "ack_required"
# The store reads `--to` as a list joined by this separator, so a recipient
# that carries it names several agents and no longer maps back to one record.
STORE_RECIPIENT_SEPARATOR = ","
# The store's parser reads a separate value that begins with `-` as another
# option, so every text-valued option travels attached, `--option=value`.
ATTACHED_OPTION_SEPARATOR = "="

# Fields of the capability's requests and results.
SCHEMA_VERSION_FIELD = "schemaVersion"
OPERATION_FIELD = "operation"
ARGUMENTS_FIELD = "arguments"
STATUS_FIELD = "status"
DETAIL_FIELD = "detail"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
PROJECT_KEY_FIELD = "projectKey"
RESPONSE_FIELD = "response"
DATA_FIELD = "data"
OUTPUT_FIELD = "output"
AGENT_FIELD = "agent"
PROGRAM_FIELD = "program"
MODEL_FIELD = "model"
TASK_FIELD = "task"
RECORD_FIELD = "record"
RECORDS_FIELD = "records"
MESSAGE_ID_FIELD = "messageId"
INCLUDE_BODIES_FIELD = "includeBodies"
LIMIT_FIELD = "limit"

# Fields of a message record.
RECORD_SCHEMA_FIELD = "schema"
RECORD_ID_FIELD = "id"
CORRELATION_FIELD = "correlation"
KIND_FIELD = "kind"
SENDER_FIELD = "sender"
RECIPIENT_FIELD = "recipient"
RECORD_SUBJECT_FIELD = "subject"
BODY_FIELD = "body"
ACK_REQUIRED_FIELD = "ackRequired"
KIND_PREFIX_OPEN = "["
KIND_PREFIX_CLOSE = "] "
TERMINAL_KINDS_LOCATION = "terminal"

REQUEST_FIELDS = frozenset({SCHEMA_VERSION_FIELD, OPERATION_FIELD, ARGUMENTS_FIELD})
SUCCESS_RESULT_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        OPERATION_FIELD,
        STATUS_FIELD,
        COMMAND_EXIT_CODE_FIELD,
        PROJECT_KEY_FIELD,
        RESPONSE_FIELD,
        DATA_FIELD,
    }
)
FAILURE_RESULT_REQUIRED_FIELDS = frozenset(
    {SCHEMA_VERSION_FIELD, OPERATION_FIELD, STATUS_FIELD, DETAIL_FIELD}
)
FAILURE_RESULT_OPTIONAL_FIELDS = frozenset({COMMAND_EXIT_CODE_FIELD})
# The fields a caller supplies on a record it sends; the store assigns `id`.
RECORD_INPUT_FIELDS = frozenset(
    {
        RECORD_SCHEMA_FIELD,
        CORRELATION_FIELD,
        KIND_FIELD,
        SENDER_FIELD,
        RECIPIENT_FIELD,
        RECORD_SUBJECT_FIELD,
        BODY_FIELD,
        ACK_REQUIRED_FIELD,
    }
)
RECORD_FIELDS = RECORD_INPUT_FIELDS | {RECORD_ID_FIELD}
# Text fields a sent record never leaves empty. A row the store returns may
# leave the correlation absent and the subject empty, and its body is empty
# when the read omits bodies.
RECORD_TEXT_FIELDS = (
    CORRELATION_FIELD,
    SENDER_FIELD,
    RECIPIENT_FIELD,
    RECORD_SUBJECT_FIELD,
)


class Operation(StrEnum):
    REGISTER = "register"
    SEND = "send"
    INBOX = "inbox"
    RECEIPT = "receipt"


class RecordKind(StrEnum):
    ORDER = "order"
    FACT = "fact"
    QUESTION = "question"
    ANSWER = "answer"
    DELEGATION_REQUEST = "delegation-request"
    DELEGATION_COMPLETED = "delegation-completed"
    DELEGATION_FAILED = "delegation-failed"
    DELEGATION_REJECTED = "delegation-rejected"
    DELEGATION_UNAVAILABLE = "delegation-unavailable"
    UNCLASSIFIED = "unclassified"


TERMINAL_KINDS = frozenset(
    {
        RecordKind.DELEGATION_COMPLETED,
        RecordKind.DELEGATION_FAILED,
        RecordKind.DELEGATION_REJECTED,
        RecordKind.DELEGATION_UNAVAILABLE,
    }
)
# Kinds a sender writes; the read side derives `unclassified` for a subject
# that carries no kind prefix and never sends it.
SENT_KINDS = frozenset(RecordKind) - {RecordKind.UNCLASSIFIED}


class ExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    COMMAND_FAILED = "command-failed"
    INVALID_SCHEMA = "invalid-schema"
    STORE_UNAVAILABLE = "store-unavailable"
    DIAGNOSIS_UNAVAILABLE = "diagnosis-unavailable"
    OPERATION_UNAVAILABLE = "operation-unavailable"


class CliOperation(StrEnum):
    RUN = "run"
    PROJECT_KEY = "project-key"


@dataclass(frozen=True)
class RequestShape:
    required_fields: frozenset[str] = frozenset()
    optional_fields: frozenset[str] = frozenset()

    def accepts(self, fields: frozenset[str]) -> bool:
        return (
            self.required_fields
            <= fields
            <= (self.required_fields | self.optional_fields)
        )


@dataclass(frozen=True)
class OperationContract:
    request_shapes: tuple[RequestShape, ...]

    @property
    def allowed_fields(self) -> frozenset[str]:
        return frozenset(
            field
            for shape in self.request_shapes
            for field in shape.required_fields | shape.optional_fields
        )


OPERATION_CONTRACTS: Final[Mapping[Operation, OperationContract]] = {
    Operation.REGISTER: OperationContract(
        (
            RequestShape(
                frozenset({AGENT_FIELD, PROGRAM_FIELD, MODEL_FIELD}),
                frozenset({TASK_FIELD}),
            ),
        )
    ),
    Operation.SEND: OperationContract((RequestShape(frozenset({RECORD_FIELD})),)),
    Operation.INBOX: OperationContract(
        (
            RequestShape(
                frozenset({AGENT_FIELD}),
                frozenset({INCLUDE_BODIES_FIELD, LIMIT_FIELD}),
            ),
        )
    ),
    Operation.RECEIPT: OperationContract(
        (RequestShape(frozenset({AGENT_FIELD, MESSAGE_ID_FIELD})),)
    ),
}
PUBLIC_AM_COMMAND_PREFIXES: Final[Mapping[Operation, tuple[str, ...]]] = {
    Operation.REGISTER: (AM_COMMAND, AGENTS_COMMAND, REGISTER_COMMAND),
    Operation.SEND: (AM_COMMAND, MAIL_COMMAND, SEND_COMMAND),
    Operation.INBOX: (AM_COMMAND, MAIL_COMMAND, INBOX_COMMAND),
    Operation.RECEIPT: (AM_COMMAND, MAIL_COMMAND, ACK_COMMAND),
}
# Operations whose public command emits JSON on `--json`; receipt prints text.
JSON_OPERATIONS = frozenset({Operation.REGISTER, Operation.SEND, Operation.INBOX})
PUBLIC_AM_ARGUMENT_OPTIONS: Final[Mapping[str, str]] = {
    AGENT_FIELD: AGENT_OPTION,
    PROGRAM_FIELD: PROGRAM_OPTION,
    MODEL_FIELD: MODEL_OPTION,
    TASK_FIELD: TASK_OPTION,
    INCLUDE_BODIES_FIELD: INCLUDE_BODIES_OPTION,
    LIMIT_FIELD: LIMIT_OPTION,
}
PUBLIC_AM_RECORD_OPTIONS: Final[Mapping[str, str]] = {
    SENDER_FIELD: FROM_OPTION,
    RECIPIENT_FIELD: TO_OPTION,
    CORRELATION_FIELD: THREAD_ID_OPTION,
    RECORD_SUBJECT_FIELD: SUBJECT_OPTION,
    BODY_FIELD: BODY_OPTION,
    ACK_REQUIRED_FIELD: ACK_REQUIRED_OPTION,
}
PUBLIC_SPX_DIAGNOSE_COMMAND: Final[tuple[str, ...]] = (
    SPX_COMMAND,
    DIAGNOSE_COMMAND,
    FORMAT_OPTION,
    JSON_FORMAT,
)
INTEGER_BOUNDS: Final[Mapping[str, tuple[int, int]]] = {
    LIMIT_FIELD: (1, 1_000),
    MESSAGE_ID_FIELD: (1, 1_000_000_000),
}
BOOLEAN_ARGUMENT_FIELDS = frozenset({INCLUDE_BODIES_FIELD})
TEXT_ARGUMENT_FIELDS = frozenset({AGENT_FIELD, PROGRAM_FIELD, MODEL_FIELD, TASK_FIELD})
ARGUMENT_NAMES: Final[Mapping[str, str]] = {
    "agent": AGENT_FIELD,
    "program": PROGRAM_FIELD,
    "agent_model": MODEL_FIELD,
    "task": TASK_FIELD,
    "record": RECORD_FIELD,
    "message_id": MESSAGE_ID_FIELD,
    "include_bodies": INCLUDE_BODIES_FIELD,
    "limit": LIMIT_FIELD,
}
RAW_MAIL_COMMAND_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bAM_COMMAND\b|[\[(]['\"]am['\"]"),
)
GIT_PROJECT_KEY_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"[\[(]['\"]git['\"]\s*,"),
    re.compile(r"['\"]\.git['\"/]"),
    re.compile(r"\bgit\s+(?:rev-parse|worktree|-C)\b"),
)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult: ...


class AgentMailError(RuntimeError):
    def __init__(self, status: ExecutionStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class SubprocessRunner:
    """Run one bounded, reaped command; absence and timeouts propagate as raised."""

    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS

    def run(self, argv: tuple[str, ...], stdin: str | None = None) -> CommandResult:
        completed = subprocess.run(
            argv,
            input=stdin,
            stdin=subprocess.DEVNULL if stdin is None else None,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an object at {location}."
        )
    return cast(dict[str, object], value)


def _array(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an array at {location}."
        )
    return cast(list[object], value)


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected non-empty text at {location}."
        )
    return value


def _string(value: object, location: str) -> str:
    if not isinstance(value, str):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected text at {location}."
        )
    return value


def _boolean(value: object, location: str) -> bool:
    if not isinstance(value, bool):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected a boolean at {location}."
        )
    return value


def _integer(value: object, location: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an integer at {location}."
        )
    if not minimum <= value <= maximum:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Expected an integer between {minimum} and {maximum} at {location}.",
        )
    return value


def _operation(value: object) -> Operation:
    try:
        return Operation(_text(value, OPERATION_FIELD))
    except ValueError as error:
        valid = ", ".join(sorted(operation.value for operation in Operation))
        raise AgentMailError(
            ExecutionStatus.OPERATION_UNAVAILABLE,
            f"Unsupported agent-mail operation: {value!r}. Valid operations: {valid}.",
        ) from error


def _record_kind(value: object, location: str, *, sent: bool) -> RecordKind:
    try:
        kind = RecordKind(_text(value, location))
    except ValueError as error:
        valid = ", ".join(sorted(member.value for member in SENT_KINDS))
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported record kind at {location}. Valid kinds: {valid}.",
        ) from error
    if sent and kind not in SENT_KINDS:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"A {kind.value} record is derived on read and is never sent.",
        )
    return kind


def validate_record(
    record: object,
    *,
    location: str = RECORD_FIELD,
    with_id: bool,
    from_store: bool = False,
) -> dict[str, object]:
    """Return the record with every field checked against the record contract.

    A record read from a store row (`from_store`) admits what another sender
    may have left: an absent correlation and an empty subject. Its id, sender,
    and subject key remain required, because a row without them is not the
    store's inbox shape.
    """
    value = _object(record, location)
    expected = RECORD_FIELDS if with_id else RECORD_INPUT_FIELDS
    unexpected = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Record fields at {location} are invalid ({'; '.join(details)}).",
        )
    if value.get(RECORD_SCHEMA_FIELD) != RECORD_SCHEMA_VERSION:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Record schema at {location} must be {RECORD_SCHEMA_VERSION}.",
        )
    validated: dict[str, object] = {
        RECORD_SCHEMA_FIELD: RECORD_SCHEMA_VERSION,
        KIND_FIELD: _record_kind(
            value.get(KIND_FIELD), f"{location}.{KIND_FIELD}", sent=not with_id
        ),
        ACK_REQUIRED_FIELD: _boolean(
            value.get(ACK_REQUIRED_FIELD), f"{location}.{ACK_REQUIRED_FIELD}"
        ),
    }
    for field_name in RECORD_TEXT_FIELDS:
        raw = value.get(field_name)
        field_location = f"{location}.{field_name}"
        if from_store and field_name == CORRELATION_FIELD and raw is None:
            validated[field_name] = None
        elif from_store and field_name == RECORD_SUBJECT_FIELD:
            validated[field_name] = _string(raw, field_location)
        else:
            validated[field_name] = _text(raw, field_location)
    recipient = cast(str, validated[RECIPIENT_FIELD])
    if STORE_RECIPIENT_SEPARATOR in recipient:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"A record names one recipient; {location}.{RECIPIENT_FIELD} carries "
            f"the store's {STORE_RECIPIENT_SEPARATOR!r} separator: {recipient!r}.",
        )
    validated[BODY_FIELD] = _string(value.get(BODY_FIELD), f"{location}.{BODY_FIELD}")
    if with_id:
        validated[RECORD_ID_FIELD] = _integer(
            value.get(RECORD_ID_FIELD),
            f"{location}.{RECORD_ID_FIELD}",
            minimum=INTEGER_BOUNDS[MESSAGE_ID_FIELD][0],
            maximum=INTEGER_BOUNDS[MESSAGE_ID_FIELD][1],
        )
    return validated


def message_record(
    *,
    kind: RecordKind | str,
    correlation: str,
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    ack_required: bool = False,
) -> dict[str, object]:
    """Build one record a sender supplies; the store assigns its id on delivery."""
    return validate_record(
        {
            RECORD_SCHEMA_FIELD: RECORD_SCHEMA_VERSION,
            KIND_FIELD: str(kind),
            CORRELATION_FIELD: correlation,
            SENDER_FIELD: sender,
            RECIPIENT_FIELD: recipient,
            RECORD_SUBJECT_FIELD: subject,
            BODY_FIELD: body,
            ACK_REQUIRED_FIELD: ack_required,
        },
        with_id=False,
    )


def terminal_handback(
    *,
    kind: RecordKind | str,
    correlation: str,
    sender: str,
    recipient: str,
    subject: str,
    body: str,
) -> dict[str, object]:
    """Build the one terminal handback record for a delegation's coordination reference."""
    record = message_record(
        kind=kind,
        correlation=correlation,
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
    )
    if record[KIND_FIELD] not in TERMINAL_KINDS:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{record[KIND_FIELD]} is not a terminal handback kind.",
        )
    return record


def reduce_terminal(current: object | None, incoming: object) -> dict[str, object]:
    """Reduce a terminal handback onto the current terminal state for its reference."""
    terminal = validate_record(
        incoming, location=TERMINAL_KINDS_LOCATION, with_id=False
    )
    if terminal[KIND_FIELD] not in TERMINAL_KINDS:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{terminal[KIND_FIELD]} is not a terminal handback kind.",
        )
    if current is None:
        return terminal
    existing = validate_record(current, location=TERMINAL_KINDS_LOCATION, with_id=False)
    if existing[CORRELATION_FIELD] != terminal[CORRELATION_FIELD]:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            "A terminal handback names a different coordination reference.",
        )
    if existing == terminal:
        return existing
    raise AgentMailError(
        ExecutionStatus.INVALID_SCHEMA,
        f"Conflicting terminal handbacks for {terminal[CORRELATION_FIELD]}: "
        f"{existing[KIND_FIELD]} then {terminal[KIND_FIELD]}.",
    )


def store_fields_for(record: object) -> dict[str, object]:
    """Map a record onto the store fields the send command writes."""
    validated = validate_record(record, with_id=False)
    kind = cast(RecordKind, validated[KIND_FIELD])
    return {
        STORE_FROM_FIELD: validated[SENDER_FIELD],
        STORE_TO_FIELD: validated[RECIPIENT_FIELD],
        STORE_THREAD_ID_FIELD: validated[CORRELATION_FIELD],
        STORE_SUBJECT_FIELD: (
            f"{KIND_PREFIX_OPEN}{kind.value}{KIND_PREFIX_CLOSE}"
            f"{validated[RECORD_SUBJECT_FIELD]}"
        ),
        STORE_BODY_FIELD: validated[BODY_FIELD],
        STORE_ACK_REQUIRED_FIELD: validated[ACK_REQUIRED_FIELD],
    }


def _split_kind(subject: str) -> tuple[RecordKind, str]:
    if subject.startswith(KIND_PREFIX_OPEN):
        close = subject.find(KIND_PREFIX_CLOSE)
        if close > len(KIND_PREFIX_OPEN):
            candidate = subject[len(KIND_PREFIX_OPEN) : close]
            try:
                kind = RecordKind(candidate)
            except ValueError:
                return RecordKind.UNCLASSIFIED, subject
            remainder = subject[close + len(KIND_PREFIX_CLOSE) :]
            if kind in SENT_KINDS and remainder:
                return kind, remainder
    return RecordKind.UNCLASSIFIED, subject


def record_from_inbox_item(item: object, *, recipient: str) -> dict[str, object]:
    """Map one inbox item of the store back onto a record for its recipient.

    A row another sender wrote reads back rather than failing the read: a row
    without a thread reads as an unclassified record with no correlation and
    its subject verbatim, and only a literal `ack_required: true` reads as
    required. A row without the store's id, sender, or subject key is a
    malformed store response and fails the read.
    """
    value = _object(item, f"{INBOX_COMMAND}[]")
    location = f"{INBOX_COMMAND}[]"
    thread = value.get(STORE_THREAD_ID_FIELD)
    correlation = thread if isinstance(thread, str) and thread else None
    subject_text = _string(
        value.get(STORE_SUBJECT_FIELD), f"{location}.{STORE_SUBJECT_FIELD}"
    )
    if correlation is None:
        kind, subject = RecordKind.UNCLASSIFIED, subject_text
    else:
        kind, subject = _split_kind(subject_text)
    body = value.get(STORE_BODY_FIELD)
    return validate_record(
        {
            RECORD_SCHEMA_FIELD: RECORD_SCHEMA_VERSION,
            RECORD_ID_FIELD: value.get(STORE_ID_FIELD),
            KIND_FIELD: kind.value,
            CORRELATION_FIELD: correlation,
            SENDER_FIELD: value.get(STORE_FROM_FIELD),
            RECIPIENT_FIELD: recipient,
            RECORD_SUBJECT_FIELD: subject,
            BODY_FIELD: body if isinstance(body, str) else "",
            ACK_REQUIRED_FIELD: value.get(STORE_ACK_REQUIRED_FIELD) is True,
        },
        location=location,
        with_id=True,
        from_store=True,
    )


def project_key_from_diagnosis(payload: object) -> str:
    """Return the pool's main checkout path from the worktree-pool record.

    A payload that is not an object, carries no check list, or carries one
    that is not an array holds no worktree-pool record, so it is the
    diagnosis-unavailable result like any diagnosis without that record.
    """
    checks_value = payload.get(CHECKS_FIELD) if isinstance(payload, dict) else None
    if not isinstance(checks_value, list):
        raise AgentMailError(
            ExecutionStatus.DIAGNOSIS_UNAVAILABLE,
            f"The diagnosis carries no {CHECKS_FIELD} array, so no "
            f"{WORKTREE_POOL_CHECK} record can be read.",
        )
    checks = cast(list[object], checks_value)
    records = [
        record
        for record in checks
        if isinstance(record, dict) and record.get(NAME_FIELD) == WORKTREE_POOL_CHECK
    ]
    if len(records) != 1:
        raise AgentMailError(
            ExecutionStatus.DIAGNOSIS_UNAVAILABLE,
            f"The diagnosis carries {len(records)} {WORKTREE_POOL_CHECK} records; one is required.",
        )
    readings = cast(dict[str, object], records[0]).get(READINGS_FIELD)
    path = (
        readings.get(MAIN_CHECKOUT_PATH_FIELD) if isinstance(readings, dict) else None
    )
    if not isinstance(path, str) or not path.startswith("/"):
        raise AgentMailError(
            ExecutionStatus.DIAGNOSIS_UNAVAILABLE,
            f"The {WORKTREE_POOL_CHECK} record reports no absolute {MAIN_CHECKOUT_PATH_FIELD}.",
        )
    return path


def resolve_project_key(runner: CommandRunner) -> str:
    """Run the diagnosis and return the project key, or raise the unavailable result."""
    try:
        result = runner.run(PUBLIC_SPX_DIAGNOSE_COMMAND)
    except FileNotFoundError as error:
        raise AgentMailError(
            ExecutionStatus.DIAGNOSIS_UNAVAILABLE,
            f"{SPX_COMMAND} is unavailable on this machine.",
        ) from error
    except subprocess.TimeoutExpired as error:
        raise AgentMailError(
            ExecutionStatus.DIAGNOSIS_UNAVAILABLE,
            f"{SPX_COMMAND} exceeded its bound: {' '.join(PUBLIC_SPX_DIAGNOSE_COMMAND)}",
        ) from error
    if result.returncode != 0 and not result.stdout.strip():
        detail = result.stderr.strip() or "no command detail"
        raise AgentMailError(
            ExecutionStatus.DIAGNOSIS_UNAVAILABLE,
            f"{SPX_COMMAND} diagnose failed with exit {result.returncode}: {detail}",
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AgentMailError(
            ExecutionStatus.DIAGNOSIS_UNAVAILABLE,
            f"{SPX_COMMAND} diagnose returned invalid JSON: {error.msg}",
        ) from error
    return project_key_from_diagnosis(payload)


def _describe_shapes(contract: OperationContract) -> str:
    return "; ".join(
        f"required {sorted(shape.required_fields)}, optional {sorted(shape.optional_fields)}"
        for shape in contract.request_shapes
    )


def _validated_request(request: object) -> tuple[Operation, dict[str, object]]:
    value = _object(request, "request")
    unexpected = sorted(set(value) - REQUEST_FIELDS)
    missing = sorted(REQUEST_FIELDS - set(value))
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request fields are invalid ({'; '.join(details)}).",
        )
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request schema version must be {SCHEMA_VERSION}.",
        )
    operation = _operation(value.get(OPERATION_FIELD))
    arguments = _object(value.get(ARGUMENTS_FIELD), f"request.{ARGUMENTS_FIELD}")
    contract = OPERATION_CONTRACTS[operation]
    unexpected_arguments = sorted(set(arguments) - contract.allowed_fields)
    if unexpected_arguments:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} contains unsupported arguments: {', '.join(unexpected_arguments)}.",
        )
    if not any(
        shape.accepts(frozenset(arguments)) for shape in contract.request_shapes
    ):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} arguments do not match a source-owned request shape; "
            f"accepted shapes: {_describe_shapes(contract)}.",
        )
    for field_name in TEXT_ARGUMENT_FIELDS:
        if field_name in arguments:
            _text(arguments[field_name], f"request.{ARGUMENTS_FIELD}.{field_name}")
    for field_name in BOOLEAN_ARGUMENT_FIELDS:
        if field_name in arguments:
            _boolean(arguments[field_name], f"request.{ARGUMENTS_FIELD}.{field_name}")
    for field_name, (minimum, maximum) in INTEGER_BOUNDS.items():
        if field_name in arguments:
            _integer(
                arguments[field_name],
                f"request.{ARGUMENTS_FIELD}.{field_name}",
                minimum=minimum,
                maximum=maximum,
            )
    if operation is Operation.SEND:
        arguments = {
            RECORD_FIELD: validate_record(
                arguments[RECORD_FIELD],
                location=f"request.{ARGUMENTS_FIELD}.{RECORD_FIELD}",
                with_id=False,
            )
        }
    return operation, arguments


def operation_request(
    operation: Operation | str, **kwargs: object
) -> dict[str, object]:
    """Build one checked operation request from keyword arguments."""
    operation_value = Operation(operation)
    arguments: dict[str, object] = {}
    for name, value in kwargs.items():
        if name not in ARGUMENT_NAMES:
            valid = ", ".join(sorted(ARGUMENT_NAMES))
            raise AgentMailError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Unsupported operation-request argument {name!r}. Valid arguments: {valid}.",
            )
        if value is not None:
            arguments[ARGUMENT_NAMES[name]] = value
    request: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation_value,
        ARGUMENTS_FIELD: arguments,
    }
    _validated_request(request)
    return request


def attached_option(option: str, value: object) -> str:
    """One free-text option with its value attached, the form the store's
    parser reads whatever character the value begins with."""
    return f"{option}{ATTACHED_OPTION_SEPARATOR}{value}"


def command_for(request: object, project_key: str) -> tuple[str, ...]:
    """Map one checked request onto the exact store argument vector."""
    operation, arguments = _validated_request(request)
    command = [*PUBLIC_AM_COMMAND_PREFIXES[operation], PROJECT_OPTION, project_key]
    if operation is Operation.REGISTER:
        for field_name in (PROGRAM_FIELD, MODEL_FIELD):
            command.append(
                attached_option(
                    PUBLIC_AM_ARGUMENT_OPTIONS[field_name], arguments[field_name]
                )
            )
        command.append(attached_option(NAME_OPTION, arguments[AGENT_FIELD]))
        if TASK_FIELD in arguments:
            command.append(
                attached_option(
                    PUBLIC_AM_ARGUMENT_OPTIONS[TASK_FIELD], arguments[TASK_FIELD]
                )
            )
    elif operation is Operation.SEND:
        fields = store_fields_for(arguments[RECORD_FIELD])
        for record_field, store_field in (
            (SENDER_FIELD, STORE_FROM_FIELD),
            (RECIPIENT_FIELD, STORE_TO_FIELD),
            (CORRELATION_FIELD, STORE_THREAD_ID_FIELD),
            (RECORD_SUBJECT_FIELD, STORE_SUBJECT_FIELD),
            (BODY_FIELD, STORE_BODY_FIELD),
        ):
            command.append(
                attached_option(
                    PUBLIC_AM_RECORD_OPTIONS[record_field], fields[store_field]
                )
            )
        if fields[STORE_ACK_REQUIRED_FIELD] is True:
            command.append(PUBLIC_AM_RECORD_OPTIONS[ACK_REQUIRED_FIELD])
    else:
        command.append(
            attached_option(
                PUBLIC_AM_ARGUMENT_OPTIONS[AGENT_FIELD], arguments[AGENT_FIELD]
            )
        )
        if operation is Operation.INBOX:
            if arguments.get(INCLUDE_BODIES_FIELD) is True:
                command.append(PUBLIC_AM_ARGUMENT_OPTIONS[INCLUDE_BODIES_FIELD])
            if LIMIT_FIELD in arguments:
                command.extend(
                    (
                        PUBLIC_AM_ARGUMENT_OPTIONS[LIMIT_FIELD],
                        str(arguments[LIMIT_FIELD]),
                    )
                )
        else:
            command.append(str(arguments[MESSAGE_ID_FIELD]))
    if operation in JSON_OPERATIONS:
        command.append(JSON_OPTION)
    return tuple(command)


def raw_mail_command_violations(sources: Mapping[str, str]) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in RAW_MAIL_COMMAND_PATTERNS)
    )


def git_project_key_violations(sources: Mapping[str, str]) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in GIT_PROJECT_KEY_PATTERNS)
    )


def validate_operation_result(result: object) -> dict[str, object]:
    """Return a result checked against the source-owned success or failure shape."""
    value = _object(result, "result")
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation result schema version must be {SCHEMA_VERSION}.",
        )
    operation_value = _text(value.get(OPERATION_FIELD), OPERATION_FIELD)
    try:
        status = ExecutionStatus(_text(value.get(STATUS_FIELD), STATUS_FIELD))
    except ValueError as error:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported operation result status: {value.get(STATUS_FIELD)!r}.",
        ) from error
    if status is ExecutionStatus.SUCCEEDED:
        if set(value) != SUCCESS_RESULT_FIELDS:
            raise AgentMailError(
                ExecutionStatus.INVALID_SCHEMA,
                "Successful operation result fields do not match the source-owned schema.",
            )
        try:
            operation = Operation(operation_value)
        except ValueError as error:
            raise AgentMailError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Unsupported operation result operation: {operation_value!r}.",
            ) from error
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            STATUS_FIELD: status,
            COMMAND_EXIT_CODE_FIELD: _integer(
                value.get(COMMAND_EXIT_CODE_FIELD),
                f"result.{COMMAND_EXIT_CODE_FIELD}",
                minimum=-1_000_000,
                maximum=1_000_000,
            ),
            PROJECT_KEY_FIELD: _text(value.get(PROJECT_KEY_FIELD), PROJECT_KEY_FIELD),
            RESPONSE_FIELD: (
                _array(value.get(RESPONSE_FIELD), RESPONSE_FIELD)
                if operation is Operation.INBOX
                else _object(value.get(RESPONSE_FIELD), RESPONSE_FIELD)
            ),
            DATA_FIELD: _object(value.get(DATA_FIELD), DATA_FIELD),
        }
    allowed = FAILURE_RESULT_REQUIRED_FIELDS | FAILURE_RESULT_OPTIONAL_FIELDS
    if not FAILURE_RESULT_REQUIRED_FIELDS <= set(value) or set(value) - allowed:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            "Failed operation result fields do not match the source-owned schema.",
        )
    validated: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation_value,
        STATUS_FIELD: status,
        DETAIL_FIELD: _text(value.get(DETAIL_FIELD), DETAIL_FIELD),
    }
    if COMMAND_EXIT_CODE_FIELD in value:
        validated[COMMAND_EXIT_CODE_FIELD] = _integer(
            value[COMMAND_EXIT_CODE_FIELD],
            f"result.{COMMAND_EXIT_CODE_FIELD}",
            minimum=-1_000_000,
            maximum=1_000_000,
        )
    return validated


def _failure_result(
    operation: str,
    status: ExecutionStatus,
    detail: str,
    command_exit_code: int | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation,
        STATUS_FIELD: status,
        DETAIL_FIELD: detail,
    }
    if command_exit_code is not None:
        result[COMMAND_EXIT_CODE_FIELD] = command_exit_code
    return validate_operation_result(result)


def _scrubbed(payload: object) -> object:
    if not isinstance(payload, dict):
        return payload
    return {
        key: value
        for key, value in payload.items()
        if key != STORE_REGISTRATION_TOKEN_FIELD
    }


def _data_for(
    operation: Operation,
    arguments: dict[str, object],
    response: object,
) -> dict[str, object]:
    if operation is Operation.REGISTER:
        response_object = _object(response, RESPONSE_FIELD)
        return {
            AGENT_FIELD: _text(response_object.get(STORE_NAME_FIELD), STORE_NAME_FIELD),
            RECORD_ID_FIELD: response_object.get(STORE_ID_FIELD),
        }
    if operation is Operation.SEND:
        response_object = _object(response, RESPONSE_FIELD)
        record = validate_record(arguments[RECORD_FIELD], with_id=False)
        return {
            RECORD_FIELD: validate_record(
                {
                    **record,
                    RECORD_ID_FIELD: response_object.get(STORE_ID_FIELD),
                },
                with_id=True,
            )
        }
    if operation is Operation.INBOX:
        recipient = str(arguments[AGENT_FIELD])
        items = _array(response, RESPONSE_FIELD)
        return {
            RECORDS_FIELD: [
                record_from_inbox_item(item, recipient=recipient) for item in items
            ]
        }
    return {
        AGENT_FIELD: arguments[AGENT_FIELD],
        MESSAGE_ID_FIELD: arguments[MESSAGE_ID_FIELD],
    }


def execute(request: object, runner: CommandRunner) -> dict[str, object]:
    """Resolve the project key, run one store command, and return the checked result."""
    operation_value = "unknown"
    try:
        raw = _object(request, "request")
        candidate = raw.get(OPERATION_FIELD)
        if isinstance(candidate, str) and candidate:
            operation_value = candidate
        operation, arguments = _validated_request(request)
        project_key = resolve_project_key(runner)
    except AgentMailError as error:
        return _failure_result(operation_value, error.status, str(error))
    command = command_for(request, project_key)
    try:
        result = runner.run(command)
    except FileNotFoundError:
        return _failure_result(
            operation.value,
            ExecutionStatus.STORE_UNAVAILABLE,
            f"{AM_COMMAND} is unavailable on this machine.",
        )
    except subprocess.TimeoutExpired:
        return _failure_result(
            operation.value,
            ExecutionStatus.COMMAND_FAILED,
            f"{AM_COMMAND} exceeded its bound: {' '.join(command)}",
        )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no command detail"
        return _failure_result(
            operation.value, ExecutionStatus.COMMAND_FAILED, detail, result.returncode
        )
    if operation in JSON_OPERATIONS:
        try:
            decoded = json.loads(result.stdout)
            response = (
                _array(decoded, RESPONSE_FIELD)
                if operation is Operation.INBOX
                else _object(decoded, RESPONSE_FIELD)
            )
        except (json.JSONDecodeError, AgentMailError) as error:
            return _failure_result(
                operation.value,
                ExecutionStatus.INVALID_SCHEMA,
                f"{AM_COMMAND} returned an unexpected response: {error}",
                result.returncode,
            )
    else:
        response = {OUTPUT_FIELD: result.stdout.strip()}
    try:
        data = _data_for(operation, arguments, response)
    except AgentMailError as error:
        return _failure_result(
            operation.value,
            ExecutionStatus.INVALID_SCHEMA,
            str(error),
            result.returncode,
        )
    return validate_operation_result(
        {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            STATUS_FIELD: ExecutionStatus.SUCCEEDED,
            COMMAND_EXIT_CODE_FIELD: result.returncode,
            PROJECT_KEY_FIELD: project_key,
            RESPONSE_FIELD: _scrubbed(response),
            DATA_FIELD: data,
        }
    )


def _json_input(stream: TextIO, location: str) -> dict[str, object]:
    try:
        return _object(json.load(stream), location)
    except json.JSONDecodeError as error:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA, f"{location} is not valid JSON: {error.msg}"
        ) from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent_mail")
    parser.add_argument("cli_operation", choices=[op.value for op in CliOperation])
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    arguments = _parser().parse_args(argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    runner = SubprocessRunner() if runner is None else runner
    cli_operation = CliOperation(arguments.cli_operation)
    if cli_operation is CliOperation.PROJECT_KEY:
        try:
            payload: dict[str, object] = {
                PROJECT_KEY_FIELD: resolve_project_key(runner)
            }
        except AgentMailError as error:
            payload = {STATUS_FIELD: error.status, DETAIL_FIELD: str(error)}
        json.dump(payload, stdout)
        stdout.write("\n")
        return 0 if PROJECT_KEY_FIELD in payload else 1
    try:
        request = _json_input(stdin, "request")
    except AgentMailError as error:
        json.dump({STATUS_FIELD: error.status, DETAIL_FIELD: str(error)}, stdout)
        stdout.write("\n")
        return 2
    result = execute(request, runner)
    json.dump(result, stdout)
    stdout.write("\n")
    return 0 if result[STATUS_FIELD] is ExecutionStatus.SUCCEEDED else 1


if __name__ == "__main__":
    sys.exit(main())
