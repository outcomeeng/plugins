#!/usr/bin/env python3
"""Operate the agent-mail store through a checked, versioned capability."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Mapping, Protocol, TextIO, cast

SCHEMA_VERSION = 1
RECORD_SCHEMA_VERSION = 1
COMMAND_TIMEOUT_SECONDS = 30
# A wait lists the requester's records at this interval until a record arrives
# or its timeout passes, and each listing reads at most this many records.
WAIT_POLL_INTERVAL_SECONDS = 2
WAIT_LISTING_LIMIT = 1_000
WAIT_TIMEOUT_MAXIMUM_SECONDS = 3_600

# Public command grammar of the store and of the repository lookup that names
# its project.
AM_COMMAND = "am"
GIT_COMMAND = "git"
AGENTS_COMMAND = "agents"
REGISTER_COMMAND = "register"
MAIL_COMMAND = "mail"
SEND_COMMAND = "send"
ACK_COMMAND = "ack"
READ_COMMAND = "read"
ROBOT_COMMAND = "robot"
INBOX_COMMAND = "inbox"
REV_PARSE_COMMAND = "rev-parse"
PROJECT_OPTION = "--project"
PROGRAM_OPTION = "--program"
MODEL_OPTION = "--model"
NAME_OPTION = "--name"
TASK_OPTION = "--task"
DISPLAY_NAME_OPTION = "--display-name"
FROM_OPTION = "--from"
TO_OPTION = "--to"
THREAD_ID_OPTION = "--thread-id"
SUBJECT_OPTION = "--subject"
BODY_OPTION = "--body"
ACK_REQUIRED_OPTION = "--ack-required"
AGENT_OPTION = "--agent"
UNREAD_OPTION = "--unread"
ALL_OPTION = "--all"
INCLUDE_BODIES_OPTION = "--include-bodies"
LIMIT_OPTION = "--limit"
JSON_OPTION = "--json"
PATH_FORMAT_ABSOLUTE_OPTION = "--path-format=absolute"
GIT_COMMON_DIR_OPTION = "--git-common-dir"

# Every variable that can make Git answer the location question from something
# other than the invoking working directory. Git exports GIT_DIR into every hook
# and into the commands it runs itself, so an inherited value would name a
# repository the adapter's working directory does not belong to; a caller
# carrying a ceiling above that directory instead hides the repository it does
# belong to. Those are two known mechanisms, not an exhaustive pair: membership
# is decided by the effect — the answer stops coming from the working directory
# — so a variable producing it some other way belongs here too.
#
# A variable that only widens the search toward the repository genuinely there
# is outside the class and stays: removing it could not prevent a wrong answer,
# only a right one.
GIT_LOCATION_VARIABLES: Final[tuple[str, ...]] = (
    "GIT_DIR",
    "GIT_COMMON_DIR",
    "GIT_WORK_TREE",
    "GIT_CEILING_DIRECTORIES",
)

# The separator the project key's absolute path is written with.
PATH_SEPARATOR = "/"

# Fields of the store's public responses.
STORE_ID_FIELD = "id"
STORE_NAME_FIELD = "name"
STORE_REGISTRATION_TOKEN_FIELD = "registration_token"
STORE_SUBJECT_FIELD = "subject"
STORE_BODY_FIELD = "body_md"
STORE_FROM_FIELD = "from"
STORE_TO_FIELD = "to"
STORE_THREAD_ID_FIELD = "thread_id"
STORE_THREAD_FIELD = "thread"
# Labels the store reports beside the stable names; they pass through verbatim.
STORE_DISPLAY_NAME_FIELD = "display_name"
STORE_SENDER_DISPLAY_NAME_FIELD = "sender_display_name"
STORE_TO_DISPLAY_NAMES_FIELD = "to_display_names"
STORE_ACK_REQUIRED_FIELD = "ack_required"
STORE_ACK_STATUS_FIELD = "ack_status"
# The three states of a required acknowledgement on the store's inbox surface:
# required (sent, not yet judged), pending (read, not acknowledged), and acked;
# every other status the store reports reads as no acknowledgement required.
STORE_ACK_STATUS_REQUIRED = "required"
STORE_ACK_STATUS_PENDING = "pending"
STORE_ACK_STATUS_ACKED = "acked"
STORE_ACK_REQUIRED_STATUSES = frozenset(
    {
        STORE_ACK_STATUS_REQUIRED,
        STORE_ACK_STATUS_PENDING,
        STORE_ACK_STATUS_ACKED,
    }
)
STORE_INBOX_FIELD = "inbox"
# The store's thread alphabet: an alphanumeric first character, then letters,
# digits, `.`, `_`, or `-`, at most this many characters in all. A correlation
# outside it, or beginning with the escape prefix, is written as the prefix
# followed by its UTF-8 bytes, each byte outside letters, digits, `.`, and `-`
# spelled as `_` and two lowercase hex digits.
THREAD_ID_MAXIMUM_LENGTH = 128
THREAD_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]{0,%d}" % (THREAD_ID_MAXIMUM_LENGTH - 1)
)
CORRELATION_ESCAPE_PREFIX = "xc-"
CORRELATION_UNESCAPED_BYTES = frozenset(
    b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
)
CORRELATION_ESCAPE_MARK = "_"
NUL_CHARACTER = "\x00"
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
DISPLAY_NAME_FIELD = "displayName"
RECORD_FIELD = "record"
RECORDS_FIELD = "records"
MESSAGE_ID_FIELD = "messageId"
AFTER_ID_FIELD = "afterId"
TIMEOUT_SECONDS_FIELD = "timeoutSeconds"
OUTCOME_FIELD = "outcome"
ALL_RECORDS_FIELD = "allRecords"
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
    LIST = "list"
    READ = "read"
    ACKNOWLEDGE = "acknowledge"
    WAIT = "wait"


class WaitOutcome(StrEnum):
    RECEIVED = "received"
    TIMEOUT = "timeout"
    UNREACHABLE = "unreachable"


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
    REPOSITORY_UNRESOLVED = "repository-unresolved"
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
                frozenset({TASK_FIELD, DISPLAY_NAME_FIELD}),
            ),
        )
    ),
    Operation.SEND: OperationContract((RequestShape(frozenset({RECORD_FIELD})),)),
    Operation.LIST: OperationContract(
        (
            RequestShape(
                frozenset({AGENT_FIELD}),
                frozenset({ALL_RECORDS_FIELD, INCLUDE_BODIES_FIELD, LIMIT_FIELD}),
            ),
        )
    ),
    Operation.READ: OperationContract(
        (RequestShape(frozenset({AGENT_FIELD, MESSAGE_ID_FIELD})),)
    ),
    Operation.ACKNOWLEDGE: OperationContract(
        (RequestShape(frozenset({AGENT_FIELD, MESSAGE_ID_FIELD})),)
    ),
    Operation.WAIT: OperationContract(
        (RequestShape(frozenset({AGENT_FIELD, AFTER_ID_FIELD, TIMEOUT_SECONDS_FIELD})),)
    ),
}
PUBLIC_AM_COMMAND_PREFIXES: Final[Mapping[Operation, tuple[str, ...]]] = {
    Operation.REGISTER: (AM_COMMAND, AGENTS_COMMAND, REGISTER_COMMAND),
    Operation.SEND: (AM_COMMAND, MAIL_COMMAND, SEND_COMMAND),
    Operation.LIST: (AM_COMMAND, ROBOT_COMMAND, INBOX_COMMAND),
    Operation.READ: (AM_COMMAND, MAIL_COMMAND, READ_COMMAND),
    Operation.ACKNOWLEDGE: (AM_COMMAND, MAIL_COMMAND, ACK_COMMAND),
    Operation.WAIT: (AM_COMMAND, ROBOT_COMMAND, INBOX_COMMAND),
}
# Operations whose public command emits JSON on `--json`; read and acknowledge
# print text.
JSON_OPERATIONS = frozenset(
    {Operation.REGISTER, Operation.SEND, Operation.LIST, Operation.WAIT}
)
PUBLIC_AM_ARGUMENT_OPTIONS: Final[Mapping[str, str]] = {
    AGENT_FIELD: AGENT_OPTION,
    PROGRAM_FIELD: PROGRAM_OPTION,
    MODEL_FIELD: MODEL_OPTION,
    TASK_FIELD: TASK_OPTION,
    DISPLAY_NAME_FIELD: DISPLAY_NAME_OPTION,
    ALL_RECORDS_FIELD: ALL_OPTION,
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
PUBLIC_GIT_COMMON_DIR_COMMAND: Final[tuple[str, ...]] = (
    GIT_COMMAND,
    REV_PARSE_COMMAND,
    PATH_FORMAT_ABSOLUTE_OPTION,
    GIT_COMMON_DIR_OPTION,
)
INTEGER_BOUNDS: Final[Mapping[str, tuple[int, int]]] = {
    LIMIT_FIELD: (1, 1_000),
    MESSAGE_ID_FIELD: (1, 1_000_000_000),
    AFTER_ID_FIELD: (0, 1_000_000_000),
    TIMEOUT_SECONDS_FIELD: (1, WAIT_TIMEOUT_MAXIMUM_SECONDS),
}
BOOLEAN_ARGUMENT_FIELDS = frozenset({ALL_RECORDS_FIELD, INCLUDE_BODIES_FIELD})
TEXT_ARGUMENT_FIELDS = frozenset(
    {AGENT_FIELD, PROGRAM_FIELD, MODEL_FIELD, TASK_FIELD, DISPLAY_NAME_FIELD}
)
ARGUMENT_NAMES: Final[Mapping[str, str]] = {
    "agent": AGENT_FIELD,
    "program": PROGRAM_FIELD,
    "agent_model": MODEL_FIELD,
    "task": TASK_FIELD,
    "display_name": DISPLAY_NAME_FIELD,
    "record": RECORD_FIELD,
    "message_id": MESSAGE_ID_FIELD,
    "after_id": AFTER_ID_FIELD,
    "timeout_seconds": TIMEOUT_SECONDS_FIELD,
    "all_records": ALL_RECORDS_FIELD,
    "include_bodies": INCLUDE_BODIES_FIELD,
    "limit": LIMIT_FIELD,
}
# The argument-vector form of a raw `am` command, and its shell-string form: the
# executable followed by one of the store's command groups inside a string.
RAW_MAIL_COMMAND_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bAM_COMMAND\b|[\[(]['\"]am['\"]"),
    re.compile(r"(?<![\w./-])am\s+(?:mail|agents|robot)\b"),
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
    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        env: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandResult: ...


class Clock(Protocol):
    def now(self) -> float: ...

    def sleep(self, seconds: float) -> None: ...


@dataclass(frozen=True)
class MonotonicClock:
    """The wall-clock implementation of the wait's time source."""

    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


def failure_detail(command: str, cause: BaseException | str, check: str) -> str:
    """Return the one failure text: the failing command, its cause, and what to check.

    An exception cause is written as its class name and message. Every part must
    be non-blank, so no failure text exists without a cause and a fix.
    """
    cause_text = (
        f"{type(cause).__name__}: {cause}"
        if isinstance(cause, BaseException)
        else cause
    ).strip()
    for part_name, part in (
        ("command", command),
        ("cause", cause_text),
        ("check", check),
    ):
        if not part.strip():
            raise ValueError(f"A failure detail needs a non-blank {part_name}.")
    return f"{command} failed: {cause_text.rstrip('. ')}. {check}"


class AgentMailError(RuntimeError):
    """A failure whose message is always built by `failure_detail`."""

    def __init__(
        self,
        status: ExecutionStatus,
        command: str,
        cause: BaseException | str,
        check: str,
    ) -> None:
        super().__init__(failure_detail(command, cause, check))
        self.status = status


@dataclass(frozen=True)
class SubprocessRunner:
    """Run one bounded, reaped command; absence and timeouts propagate as raised."""

    timeout_seconds: int = COMMAND_TIMEOUT_SECONDS

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        env: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandResult:
        completed = subprocess.run(
            argv,
            input=stdin,
            stdin=subprocess.DEVNULL if stdin is None else None,
            capture_output=True,
            text=True,
            timeout=(
                self.timeout_seconds
                if timeout_seconds is None
                else min(self.timeout_seconds, timeout_seconds)
            ),
            check=False,
            env=None if env is None else dict(env),
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"expected an object, received {type(value).__name__}",
            "Supply a JSON object there.",
        )
    return cast(dict[str, object], value)


def _array(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"expected an array, received {type(value).__name__}",
            "Supply a JSON array there.",
        )
    return cast(list[object], value)


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"expected non-empty text, received {value!r}",
            "Supply a non-empty string there.",
        )
    return value


def _string(value: object, location: str) -> str:
    if not isinstance(value, str):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"expected text, received {type(value).__name__}",
            "Supply a string there.",
        )
    return value


def _boolean(value: object, location: str) -> bool:
    if not isinstance(value, bool):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"expected a boolean, received {value!r}",
            "Supply true or false there.",
        )
    return value


def _integer(value: object, location: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"expected an integer, received {value!r}",
            "Supply a whole number there.",
        )
    if not minimum <= value <= maximum:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"expected an integer between {minimum} and {maximum}, received {value}",
            "Supply a value inside that range.",
        )
    return value


def _operation(value: object) -> Operation:
    try:
        return Operation(_text(value, OPERATION_FIELD))
    except ValueError as error:
        valid = ", ".join(sorted(operation.value for operation in Operation))
        raise AgentMailError(
            ExecutionStatus.OPERATION_UNAVAILABLE,
            f"Selecting the agent-mail operation {value!r}",
            error,
            f"Use one of: {valid}.",
        ) from error


def _record_kind(value: object, location: str, *, sent: bool) -> RecordKind:
    try:
        kind = RecordKind(_text(value, location))
    except ValueError as error:
        valid = ", ".join(sorted(member.value for member in SENT_KINDS))
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            error,
            f"Use one of the kinds: {valid}.",
        ) from error
    if sent and kind not in SENT_KINDS:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reading {location}",
            f"a {kind.value} record is derived on read and is never sent",
            f"Send a record of kind {', '.join(sorted(m.value for m in SENT_KINDS))}.",
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
            f"Checking the record at {location}",
            f"its fields are invalid ({'; '.join(details)})",
            "Supply exactly the fields of the record contract.",
        )
    if value.get(RECORD_SCHEMA_FIELD) != RECORD_SCHEMA_VERSION:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Checking the record at {location}",
            f"its schema is {value.get(RECORD_SCHEMA_FIELD)!r}, not {RECORD_SCHEMA_VERSION}",
            "Set the schema field to that value.",
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
            f"Checking {location}.{RECIPIENT_FIELD}",
            f"a record names one recipient, but {recipient!r} carries the store's "
            f"{STORE_RECIPIENT_SEPARATOR!r} separator",
            "Name one recipient and send one record per recipient.",
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
    """Build one record a caller sends; the store assigns its id on delivery."""
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
            "Building a terminal handback",
            f"{record[KIND_FIELD]} is not a terminal handback kind",
            f"Use one of: {', '.join(sorted(kind.value for kind in TERMINAL_KINDS))}.",
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
            "Reducing a terminal handback",
            f"{terminal[KIND_FIELD]} is not a terminal handback kind",
            f"Use one of: {', '.join(sorted(kind.value for kind in TERMINAL_KINDS))}.",
        )
    if current is None:
        return terminal
    existing = validate_record(current, location=TERMINAL_KINDS_LOCATION, with_id=False)
    if existing[CORRELATION_FIELD] != terminal[CORRELATION_FIELD]:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            "Reducing a terminal handback",
            f"it names coordination reference {terminal[CORRELATION_FIELD]!r}, "
            f"not the current {existing[CORRELATION_FIELD]!r}",
            "Reduce only handbacks that share one reference.",
        )
    if existing == terminal:
        return existing
    if existing[KIND_FIELD] == terminal[KIND_FIELD]:
        differing = sorted(
            field_name
            for field_name in existing
            if existing[field_name] != terminal[field_name]
        )
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Reducing the handbacks for {terminal[CORRELATION_FIELD]}",
            f"the {terminal[KIND_FIELD]} handbacks differ in {', '.join(differing)}",
            "Keep the first handback, or send the second under a new reference.",
        )
    raise AgentMailError(
        ExecutionStatus.INVALID_SCHEMA,
        f"Reducing the handbacks for {terminal[CORRELATION_FIELD]}",
        f"a {existing[KIND_FIELD]} handback and then a {terminal[KIND_FIELD]} handback conflict",
        "Send one terminal kind per reference.",
    )


def encode_correlation(correlation: str) -> str:
    """Return the thread id the store receives for a correlation.

    A correlation inside the store's thread alphabet that does not begin with the
    escape prefix is written unchanged; every other correlation is written as the
    prefix and its escaped UTF-8 bytes. The written form lies inside the alphabet
    or exceeds its length, and an over-long form is refused before any command.
    """
    if THREAD_ID_PATTERN.fullmatch(correlation) and not correlation.startswith(
        CORRELATION_ESCAPE_PREFIX
    ):
        return correlation
    spelled = "".join(
        chr(byte)
        if byte in CORRELATION_UNESCAPED_BYTES
        else f"{CORRELATION_ESCAPE_MARK}{byte:02x}"
        for byte in correlation.encode("utf-8", errors="surrogatepass")
    )
    thread_id = f"{CORRELATION_ESCAPE_PREFIX}{spelled}"
    if len(thread_id) > THREAD_ID_MAXIMUM_LENGTH:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Writing the {CORRELATION_FIELD} field",
            f"it encodes to a {len(thread_id)}-character thread id, over the "
            f"store's {THREAD_ID_MAXIMUM_LENGTH}-character limit",
            f"Shorten the {CORRELATION_FIELD} so its written form fits.",
        )
    return thread_id


def decode_correlation(thread_id: str) -> str:
    """Return the correlation a thread id encodes, or the thread id verbatim.

    Only a form `encode_correlation` writes decodes; any other thread id, the
    escape prefix included, reads back unchanged.
    """
    if not thread_id.startswith(CORRELATION_ESCAPE_PREFIX):
        return thread_id
    spelled = thread_id[len(CORRELATION_ESCAPE_PREFIX) :]
    raw = bytearray()
    index = 0
    while index < len(spelled):
        character = spelled[index]
        if character == CORRELATION_ESCAPE_MARK:
            digits = spelled[index + 1 : index + 3]
            if len(digits) != 2 or not re.fullmatch(r"[0-9a-f]{2}", digits):
                return thread_id
            raw.append(int(digits, 16))
            index += 3
        elif ord(character) < 128 and ord(character) in CORRELATION_UNESCAPED_BYTES:
            raw.append(ord(character))
            index += 1
        else:
            return thread_id
    try:
        correlation = raw.decode("utf-8", errors="surrogatepass")
        if encode_correlation(correlation) != thread_id:
            return thread_id
    except (UnicodeDecodeError, AgentMailError):
        return thread_id
    return correlation


def store_fields_for(record: object) -> dict[str, object]:
    """Map a record onto the store fields the send command writes."""
    validated = validate_record(record, with_id=False)
    kind = cast(RecordKind, validated[KIND_FIELD])
    return {
        STORE_FROM_FIELD: validated[SENDER_FIELD],
        STORE_TO_FIELD: validated[RECIPIENT_FIELD],
        STORE_THREAD_ID_FIELD: encode_correlation(
            cast(str, validated[CORRELATION_FIELD])
        ),
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
    its subject verbatim, and an acknowledgement status outside the ones that
    require an acknowledgement reads as not required. A row without the store's id,
    sender, or subject key is a malformed store response and fails the read.
    """
    value = _object(item, STORE_INBOX_FIELD)
    location = f"{STORE_INBOX_FIELD}[]"
    thread = value.get(STORE_THREAD_FIELD)
    correlation = (
        decode_correlation(thread) if isinstance(thread, str) and thread else None
    )
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
            ACK_REQUIRED_FIELD: (
                value.get(STORE_ACK_STATUS_FIELD) in STORE_ACK_REQUIRED_STATUSES
            ),
        },
        location=location,
        with_id=True,
        from_store=True,
    )


def project_key_from_common_dir(text: str) -> str:
    """Return the project key the repository's common Git directory names.

    The directory is the identity every checkout of one repository shares, so a
    linked worktree, the pool's bare repository, and the pool's main checkout
    resolve one key and no checkout's deletion removes it. The key is the
    normalized absolute path: no `.` or `..` segment, no repeated separator, and
    no trailing separator. Text naming no absolute directory resolves no
    repository.
    """
    candidate = text.strip()
    if not candidate.startswith(PATH_SEPARATOR):
        raise AgentMailError(
            ExecutionStatus.REPOSITORY_UNRESOLVED,
            "Resolving the repository's common Git directory",
            f"the repository reports no absolute directory, received {text!r}",
            "Run the operation from a directory inside a Git repository.",
        )
    normalized = os.path.normpath(candidate)
    return PATH_SEPARATOR + normalized.lstrip(PATH_SEPARATOR)


def repository_lookup_environment() -> dict[str, str]:
    """Return the environment the repository lookup runs in.

    Every variable in `GIT_LOCATION_VARIABLES` is removed, so the lookup
    answers from its own working directory and no value the caller inherited
    moves that answer. Without the removal the key would follow whatever the
    caller carried: a mail operation invoked from a hook would key the store to
    the repository that ran the hook, and one invoked under a ceiling above its
    own working directory would resolve no repository at all. Every other `GIT_`
    variable is carried through, so a caller whose repository is reachable only
    because of one still resolves it.
    """
    return {
        name: value
        for name, value in os.environ.items()
        if name not in GIT_LOCATION_VARIABLES
    }


def resolve_project_key(runner: CommandRunner) -> str:
    """Return the invoking working directory's repository key, or raise."""
    try:
        result = runner.run(
            PUBLIC_GIT_COMMON_DIR_COMMAND, env=repository_lookup_environment()
        )
    except FileNotFoundError as error:
        raise AgentMailError(
            ExecutionStatus.REPOSITORY_UNRESOLVED,
            " ".join(PUBLIC_GIT_COMMON_DIR_COMMAND),
            error,
            f"Install {GIT_COMMAND} and put it on PATH.",
        ) from error
    except subprocess.TimeoutExpired as error:
        raise AgentMailError(
            ExecutionStatus.REPOSITORY_UNRESOLVED,
            " ".join(PUBLIC_GIT_COMMON_DIR_COMMAND),
            error,
            f"Check that {GIT_COMMAND} answers within its bound, then retry.",
        ) from error
    except Exception as error:
        raise AgentMailError(
            ExecutionStatus.REPOSITORY_UNRESOLVED,
            " ".join(PUBLIC_GIT_COMMON_DIR_COMMAND),
            error,
            f"Check that {GIT_COMMAND} is executable by this user and that the "
            f"working directory is readable, then retry.",
        ) from error
    if result.returncode != 0:
        raise AgentMailError(
            ExecutionStatus.REPOSITORY_UNRESOLVED,
            " ".join(PUBLIC_GIT_COMMON_DIR_COMMAND),
            result.stderr.strip() or f"exit code {result.returncode} with no output",
            "Run from inside a Git repository or one of its worktrees.",
        )
    return project_key_from_common_dir(result.stdout)


def _describe_shapes(contract: OperationContract) -> str:
    return "; ".join(
        f"required {sorted(shape.required_fields)}, optional {sorted(shape.optional_fields)}"
        for shape in contract.request_shapes
    )


def _reject_nul(value: object, location: str) -> None:
    """Refuse a NUL byte in any text of the request, key or value."""
    if isinstance(value, str):
        if NUL_CHARACTER in value:
            raise AgentMailError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Reading {location}",
                f"text {value!r} carries a NUL byte, which cannot cross a process boundary",
                "Remove the NUL byte from that text.",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_nul(key, location)
            _reject_nul(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_nul(item, f"{location}[{index}]")


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
            "Checking the operation request",
            f"its fields are invalid ({'; '.join(details)})",
            "Supply exactly the request fields.",
        )
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            "Checking the operation request",
            f"its schema version is {value.get(SCHEMA_VERSION_FIELD)!r}, not {SCHEMA_VERSION}",
            "Set the schema version field to that value.",
        )
    operation = _operation(value.get(OPERATION_FIELD))
    arguments = _object(value.get(ARGUMENTS_FIELD), f"request.{ARGUMENTS_FIELD}")
    _reject_nul(arguments, f"request.{ARGUMENTS_FIELD}")
    contract = OPERATION_CONTRACTS[operation]
    unexpected_arguments = sorted(set(arguments) - contract.allowed_fields)
    if unexpected_arguments:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Checking the {operation.value} arguments",
            f"unsupported arguments: {', '.join(unexpected_arguments)}",
            f"Remove them; allowed arguments: {', '.join(sorted(contract.allowed_fields))}.",
        )
    if not any(
        shape.accepts(frozenset(arguments)) for shape in contract.request_shapes
    ):
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Checking the {operation.value} arguments",
            "they do not match a source-owned request shape",
            f"Supply one accepted shape: {_describe_shapes(contract)}.",
        )
    for field_name in TEXT_ARGUMENT_FIELDS:
        if field_name in arguments:
            location = f"request.{ARGUMENTS_FIELD}.{field_name}"
            if field_name == DISPLAY_NAME_FIELD:
                _string(arguments[field_name], location)
            else:
                _text(arguments[field_name], location)
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
        store_fields_for(arguments[RECORD_FIELD])
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
                "Building the operation request",
                f"unsupported argument {name!r}",
                f"Use one of: {valid}.",
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
        for field_name in (TASK_FIELD, DISPLAY_NAME_FIELD):
            if field_name in arguments:
                command.append(
                    attached_option(
                        PUBLIC_AM_ARGUMENT_OPTIONS[field_name], arguments[field_name]
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
        if operation is Operation.WAIT:
            command.extend(
                (
                    ALL_OPTION,
                    PUBLIC_AM_ARGUMENT_OPTIONS[INCLUDE_BODIES_FIELD],
                    PUBLIC_AM_ARGUMENT_OPTIONS[LIMIT_FIELD],
                    str(WAIT_LISTING_LIMIT),
                )
            )
        elif operation is Operation.LIST:
            command.append(
                ALL_OPTION
                if arguments.get(ALL_RECORDS_FIELD) is True
                else UNREAD_OPTION
            )
            if arguments.get(INCLUDE_BODIES_FIELD) is True:
                command.append(INCLUDE_BODIES_OPTION)
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
            "Checking the operation result",
            f"its schema version is {value.get(SCHEMA_VERSION_FIELD)!r}, not {SCHEMA_VERSION}",
            "Regenerate the result with this script.",
        )
    operation_value = _text(value.get(OPERATION_FIELD), OPERATION_FIELD)
    try:
        status = ExecutionStatus(_text(value.get(STATUS_FIELD), STATUS_FIELD))
    except ValueError as error:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            "Checking the operation result",
            error,
            f"Use one of the statuses: {', '.join(sorted(m.value for m in ExecutionStatus))}.",
        ) from error
    if status is ExecutionStatus.SUCCEEDED:
        if set(value) != SUCCESS_RESULT_FIELDS:
            raise AgentMailError(
                ExecutionStatus.INVALID_SCHEMA,
                "Checking the successful operation result",
                f"its fields {sorted(value)} do not match the source-owned schema "
                f"{sorted(SUCCESS_RESULT_FIELDS)}",
                "Emit exactly those fields.",
            )
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: Operation(operation_value),
            STATUS_FIELD: status,
            COMMAND_EXIT_CODE_FIELD: _integer(
                value.get(COMMAND_EXIT_CODE_FIELD),
                f"result.{COMMAND_EXIT_CODE_FIELD}",
                minimum=-1_000_000,
                maximum=1_000_000,
            ),
            PROJECT_KEY_FIELD: _text(value.get(PROJECT_KEY_FIELD), PROJECT_KEY_FIELD),
            RESPONSE_FIELD: _object(value.get(RESPONSE_FIELD), RESPONSE_FIELD),
            DATA_FIELD: _object(value.get(DATA_FIELD), DATA_FIELD),
        }
    allowed = FAILURE_RESULT_REQUIRED_FIELDS | FAILURE_RESULT_OPTIONAL_FIELDS
    if not FAILURE_RESULT_REQUIRED_FIELDS <= set(value) or set(value) - allowed:
        raise AgentMailError(
            ExecutionStatus.INVALID_SCHEMA,
            "Checking the failed operation result",
            f"its fields {sorted(value)} do not match the source-owned schema "
            f"(required {sorted(FAILURE_RESULT_REQUIRED_FIELDS)}, "
            f"optional {sorted(FAILURE_RESULT_OPTIONAL_FIELDS)})",
            "Emit only those fields.",
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


def _store_failure_detail(command: tuple[str, ...], result: CommandResult) -> str:
    """Return the store's own message verbatim, or the failure detail when it said nothing."""
    return (
        result.stderr.strip()
        or result.stdout.strip()
        or failure_detail(
            " ".join(command),
            f"exit code {result.returncode} with no output",
            f"Check that {AM_COMMAND} runs for this project, then retry.",
        )
    )


def _run_error_detail(command: tuple[str, ...], error: Exception) -> str:
    return failure_detail(
        " ".join(command),
        error,
        f"Check that {AM_COMMAND} is installed, on PATH, and executable by this "
        f"user, and that its working directory is readable, then retry.",
    )


def _response_error_detail(command: tuple[str, ...], error: Exception) -> str:
    return failure_detail(
        " ".join(command),
        error,
        f"Check that the installed {AM_COMMAND} is a version this skill supports "
        f"and that its output is the JSON the operation expects, then retry.",
    )


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


def _scrubbed(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key != STORE_REGISTRATION_TOKEN_FIELD
    }


def _data_for(
    operation: Operation,
    arguments: dict[str, object],
    response: dict[str, object],
) -> dict[str, object]:
    if operation is Operation.REGISTER:
        return {
            AGENT_FIELD: _text(response.get(STORE_NAME_FIELD), STORE_NAME_FIELD),
            RECORD_ID_FIELD: response.get(STORE_ID_FIELD),
        }
    if operation is Operation.SEND:
        record = validate_record(arguments[RECORD_FIELD], with_id=False)
        return {
            RECORD_FIELD: validate_record(
                {**record, RECORD_ID_FIELD: response.get(STORE_ID_FIELD)},
                with_id=True,
            )
        }
    if operation is Operation.LIST:
        recipient = str(arguments[AGENT_FIELD])
        items = _array(response.get(STORE_INBOX_FIELD), STORE_INBOX_FIELD)
        return {
            RECORDS_FIELD: [
                record_from_inbox_item(item, recipient=recipient) for item in items
            ]
        }
    return {
        AGENT_FIELD: arguments[AGENT_FIELD],
        MESSAGE_ID_FIELD: arguments[MESSAGE_ID_FIELD],
    }


def _wait_selection(
    items: list[object], after_id: int, recipient: str
) -> tuple[dict[str, object] | None, bool]:
    """Pick the first record past `after_id` from one inbox listing.

    Returns that record, or None, with whether the listing reaches back to
    `after_id`. A listing reaches back when it holds a record at or below the
    id, or when it is shorter than the limit and so holds every record the
    requester has. A full listing whose records all lie past the id may have
    cut off older records between the id and its oldest record, so the first
    record past the id is unknown.
    """
    records = [record_from_inbox_item(item, recipient=recipient) for item in items]
    ids = [cast(int, record[RECORD_ID_FIELD]) for record in records]
    reaches = len(items) < WAIT_LISTING_LIMIT or any(
        record_id <= after_id for record_id in ids
    )
    later = [
        record for record in records if cast(int, record[RECORD_ID_FIELD]) > after_id
    ]
    if not reaches:
        return None, False
    if not later:
        return None, True
    return min(later, key=lambda record: cast(int, record[RECORD_ID_FIELD])), True


def _execute_wait(
    arguments: dict[str, object],
    project_key: str,
    runner: CommandRunner,
    clock: Clock,
) -> dict[str, object]:
    """Poll the requester's inbox until a later record arrives or the timeout passes.

    The wait holds no cursor, state file, or lock, and neither reads nor
    acknowledges a record: it only lists. Every listing is bounded by the time
    that remains.
    """
    operation = Operation.WAIT.value
    recipient = str(arguments[AGENT_FIELD])
    after_id = cast(int, arguments[AFTER_ID_FIELD])
    started = clock.now()
    deadline = started + cast(int, arguments[TIMEOUT_SECONDS_FIELD])
    command = command_for(
        {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            ARGUMENTS_FIELD: arguments,
        },
        project_key,
    )
    response: dict[str, object] = {}
    while True:
        remaining = deadline - clock.now()
        if remaining <= 0:
            return _wait_result(WaitOutcome.TIMEOUT, project_key, response, {})
        try:
            result = runner.run(command, timeout_seconds=remaining)
        except OSError as error:
            return _failure_result(
                operation,
                ExecutionStatus.STORE_UNAVAILABLE,
                _run_error_detail(command, error),
            )
        except subprocess.TimeoutExpired as error:
            if deadline - clock.now() <= 0:
                return _wait_result(WaitOutcome.TIMEOUT, project_key, response, {})
            return _failure_result(
                operation,
                ExecutionStatus.COMMAND_FAILED,
                _run_error_detail(command, error),
            )
        except Exception as error:
            return _failure_result(
                operation,
                ExecutionStatus.COMMAND_FAILED,
                _run_error_detail(command, error),
            )
        if result.returncode != 0:
            return _failure_result(
                operation,
                ExecutionStatus.COMMAND_FAILED,
                _store_failure_detail(command, result),
                result.returncode,
            )
        try:
            response = _object(json.loads(result.stdout), RESPONSE_FIELD)
            items = _array(response.get(STORE_INBOX_FIELD), STORE_INBOX_FIELD)
            record, reaches = _wait_selection(items, after_id, recipient)
        except (json.JSONDecodeError, AgentMailError) as error:
            return _failure_result(
                operation,
                ExecutionStatus.INVALID_SCHEMA,
                _response_error_detail(command, error),
                result.returncode,
            )
        if not reaches:
            return _wait_result(WaitOutcome.UNREACHABLE, project_key, response, {})
        if record is not None:
            return _wait_result(
                WaitOutcome.RECEIVED, project_key, response, {RECORD_FIELD: record}
            )
        remaining = deadline - clock.now()
        if remaining <= 0:
            return _wait_result(WaitOutcome.TIMEOUT, project_key, response, {})
        clock.sleep(min(WAIT_POLL_INTERVAL_SECONDS, remaining))


def _wait_result(
    outcome: WaitOutcome,
    project_key: str,
    response: dict[str, object],
    data: dict[str, object],
) -> dict[str, object]:
    return validate_operation_result(
        {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: Operation.WAIT,
            STATUS_FIELD: ExecutionStatus.SUCCEEDED,
            COMMAND_EXIT_CODE_FIELD: 0,
            PROJECT_KEY_FIELD: project_key,
            RESPONSE_FIELD: _scrubbed(response),
            DATA_FIELD: {OUTCOME_FIELD: outcome.value, **data},
        }
    )


def execute(
    request: object, runner: CommandRunner, clock: Clock | None = None
) -> dict[str, object]:
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
    if operation is Operation.WAIT:
        return _execute_wait(
            arguments, project_key, runner, MonotonicClock() if clock is None else clock
        )
    command = command_for(request, project_key)
    try:
        result = runner.run(command)
    except OSError as error:
        return _failure_result(
            operation.value,
            ExecutionStatus.STORE_UNAVAILABLE,
            _run_error_detail(command, error),
        )
    except subprocess.TimeoutExpired as error:
        return _failure_result(
            operation.value,
            ExecutionStatus.COMMAND_FAILED,
            _run_error_detail(command, error),
        )
    except Exception as error:
        return _failure_result(
            operation.value,
            ExecutionStatus.COMMAND_FAILED,
            _run_error_detail(command, error),
        )
    if result.returncode != 0:
        return _failure_result(
            operation.value,
            ExecutionStatus.COMMAND_FAILED,
            _store_failure_detail(command, result),
            result.returncode,
        )
    if operation in JSON_OPERATIONS:
        try:
            response = _object(json.loads(result.stdout), RESPONSE_FIELD)
        except (json.JSONDecodeError, AgentMailError) as error:
            return _failure_result(
                operation.value,
                ExecutionStatus.INVALID_SCHEMA,
                _response_error_detail(command, error),
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
            ExecutionStatus.INVALID_SCHEMA,
            f"Parsing {location} from stdin",
            error,
            "Supply one complete JSON object on stdin.",
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
    clock: Clock | None = None,
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
        json.dump(_failure_result("unknown", error.status, str(error)), stdout)
        stdout.write("\n")
        return 2
    result = execute(request, runner, clock)
    json.dump(result, stdout)
    stdout.write("\n")
    return 0 if result[STATUS_FIELD] is ExecutionStatus.SUCCEEDED else 1


if __name__ == "__main__":
    sys.exit(main())
