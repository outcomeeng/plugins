#!/usr/bin/env python3
"""Operate Prowl through a checked, versioned environment contract."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Mapping, Protocol, TextIO, cast
from urllib.parse import urlparse

SCHEMA_VERSION = 1
DELEGATION_SCHEMA_VERSION = 2
HANDBACK_SCHEMA_VERSION = 1
COMMAND_TIMEOUT_SECONDS = 30
MAX_RESULT_PROJECTION_CHARACTERS = 4_000
PROWL_COMMAND = "prowl"
LIST_COMMAND = "list"
AGENTS_COMMAND = "agents"
READ_COMMAND = "read"
SEND_COMMAND = "send"
KEY_COMMAND = "key"
FOCUS_COMMAND = "focus"
TAB_COMMAND = "tab"
PANE_COMMAND = "pane"
OPEN_COMMAND = "open"
CREATE_COMMAND = "create"
CLOSE_COMMAND = "close"
JSON_OPTION = "--json"
HELP_OPTION = "--help"
TARGET_OPTION = "--target"
WORKTREE_OPTION = "--worktree"
TAB_OPTION = "--tab"
PANE_OPTION = "--pane"
LAST_OPTION = "--last"
WAIT_STABLE_OPTION = "--wait-stable"
STABLE_INTERVAL_OPTION = "--stable-interval"
STABLE_PERIOD_OPTION = "--stable-period"
WAIT_TIMEOUT_OPTION = "--wait-timeout"
NO_ENTER_OPTION = "--no-enter"
NO_WAIT_OPTION = "--no-wait"
CAPTURE_OPTION = "--capture"
TIMEOUT_OPTION = "--timeout"
REPEAT_OPTION = "--repeat"
PATH_OPTION = "--path"
FORCE_OPTION = "--force"

SCHEMA_VERSION_FIELD = "schemaVersion"
SCHEMA_VERSION_SNAKE_FIELD = "schema_version"
OPERATION_FIELD = "operation"
ARGUMENTS_FIELD = "arguments"
STATUS_FIELD = "status"
DETAIL_FIELD = "detail"
COMMAND_FIELD = "command"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
RESPONSE_FIELD = "response"
OK_FIELD = "ok"
DATA_FIELD = "data"
ERROR_FIELD = "error"
MESSAGE_FIELD = "message"
ITEMS_FIELD = "items"
AGENTS_FIELD = "agents"
ID_FIELD = "id"
AGENT_FIELD = "agent"
PANE_FIELD = "pane"
WORKTREE_FIELD = "worktree"
TAB_FIELD = "tab"
TARGET_FIELD = "target"
PROJECT_FIELD = "project"
RUN_FIELD = "run"
PATH_FIELD = "path"
ROOT_PATH_FIELD = "root_path"
BRANCH_FIELD = "branch"
REPOSITORY_FIELD = "repository"
LAST_FIELD = "last"
WAIT_STABLE_FIELD = "waitStable"
STABLE_INTERVAL_FIELD = "stableInterval"
STABLE_PERIOD_FIELD = "stablePeriod"
WAIT_TIMEOUT_FIELD = "waitTimeout"
TEXT_FIELD = "text"
NO_ENTER_FIELD = "noEnter"
NO_WAIT_FIELD = "noWait"
CAPTURE_FIELD = "capture"
TIMEOUT_FIELD = "timeout"
KEY_FIELD = "key"
REPEAT_FIELD = "repeat"
FORCE_FIELD = "force"
MUTATION_AUTHORIZED_FIELD = "mutationAuthorized"
KIND_FIELD = "kind"
SENDER_FIELD = "sender"
RECIPIENT_FIELD = "recipient"
SUBJECT_FIELD = "subject"
INSTRUCTION_FIELD = "instruction"
COMPLETION_TEXT_FIELD = "completionText"
COORDINATION_REFERENCE_FIELD = "coordinationReference"
INLINE_RESULT_FIELD = "inlineResult"
RESULT_REFERENCE_FIELD = "resultReference"
PROJECTION_FIELD = "projection"
DELEGATION_FIELD = "delegation"
TERMINAL_FIELD = "terminal"
HANDBACK_FIELD = "handback"
ADAPTER_PATH_FIELD = "adapterPath"
SUCCESS_CRITERIA_FIELD = "successCriteria"
RETRY_POLICY_FIELD = "retryPolicy"
SOCKET_FIELD = "socket"
EXPECTED_PANES_FIELD = "expectedPanes"
CONCLUSION_FIELD = "conclusion"
PARTICIPANTS_FIELD = "participants"
PARTICIPANT_FIELD = "participant"
CALLER_FIELD = "caller"
CANDIDATES_FIELD = "candidates"
INVENTORY_FIELD = "inventory"
SEND_REQUEST_TEMPLATE_FIELD = "sendRequestTemplate"
INPUT_FIELD = "input"
TRAILING_ENTER_SENT_FIELD = "trailing_enter_sent"
RESOLUTION_FIELD = "resolution"
CREATED_TAB_FIELD = "created_tab"
PROWL_PANE_ID_ENV = "PROWL_PANE_ID"
PROWL_WORKTREE_PATH_ENV = "PROWL_WORKTREE_PATH"
CALLER_IDENTITY_ENV_FIELDS = (PROWL_PANE_ID_ENV, PROWL_WORKTREE_PATH_ENV)
HANDBACK_RETRY_POLICY = "never-after-trailing-enter"
DEFAULT_SOCKET = "default"

REQUEST_FIELDS = frozenset({SCHEMA_VERSION_FIELD, OPERATION_FIELD, ARGUMENTS_FIELD})
SUCCESS_RESULT_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        OPERATION_FIELD,
        STATUS_FIELD,
        COMMAND_EXIT_CODE_FIELD,
        RESPONSE_FIELD,
    }
)
FAILURE_RESULT_REQUIRED_FIELDS = frozenset(
    {SCHEMA_VERSION_FIELD, OPERATION_FIELD, STATUS_FIELD, DETAIL_FIELD}
)
FAILURE_RESULT_OPTIONAL_FIELDS = frozenset({COMMAND_EXIT_CODE_FIELD})
SELECTOR_FIELDS = (TARGET_FIELD, WORKTREE_FIELD, TAB_FIELD, PANE_FIELD)
IDENTITY_FIELDS = (
    AGENT_FIELD,
    PANE_FIELD,
    WORKTREE_FIELD,
    BRANCH_FIELD,
    REPOSITORY_FIELD,
)
IDENTITY_INPUT_FIELDS = frozenset((*IDENTITY_FIELDS, RUN_FIELD))
# The keys a delegation request may carry over stdin. `schemaVersion` and `kind`
# are owned by the envelope builder, so a caller never supplies them.
DELEGATION_CLI_FIELDS = frozenset(
    {
        SENDER_FIELD,
        RECIPIENT_FIELD,
        SUBJECT_FIELD,
        INSTRUCTION_FIELD,
        COMPLETION_TEXT_FIELD,
        COORDINATION_REFERENCE_FIELD,
    }
)
DELEGATION_REQUEST_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        KIND_FIELD,
        COORDINATION_REFERENCE_FIELD,
        SENDER_FIELD,
        RECIPIENT_FIELD,
        SUBJECT_FIELD,
        INSTRUCTION_FIELD,
        HANDBACK_FIELD,
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
HANDBACK_PLAN_CLI_FIELDS = frozenset(
    {SENDER_FIELD, RECIPIENT_FIELD, COMPLETION_TEXT_FIELD}
)
TERMINAL_HANDBACK_FIELDS = frozenset(
    {
        SCHEMA_VERSION_FIELD,
        KIND_FIELD,
        COORDINATION_REFERENCE_FIELD,
        SENDER_FIELD,
        RECIPIENT_FIELD,
        INLINE_RESULT_FIELD,
        RESULT_REFERENCE_FIELD,
        PROJECTION_FIELD,
    }
)


class Operation(StrEnum):
    LIST = "list"
    AGENTS = "agents"
    READ = "read"
    SEND = "send"
    KEY = "key"
    FOCUS = "focus"
    TAB_CREATE = "tab-create"
    TAB_CLOSE = "tab-close"
    PANE_CLOSE = "pane-close"
    OPEN = "open"


MUTATING_OPERATIONS = frozenset(
    {
        Operation.KEY,
        Operation.FOCUS,
        Operation.TAB_CREATE,
        Operation.TAB_CLOSE,
        Operation.PANE_CLOSE,
        Operation.OPEN,
    }
)


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


def _selector_shapes(
    required_fields: frozenset[str], optional_fields: frozenset[str] = frozenset()
) -> tuple[RequestShape, ...]:
    return tuple(
        RequestShape(required_fields | {selector}, optional_fields)
        for selector in SELECTOR_FIELDS
    )


def _send_shapes() -> tuple[RequestShape, ...]:
    shapes: list[RequestShape] = []
    for selector in SELECTOR_FIELDS:
        base = frozenset({selector, TEXT_FIELD})
        shapes.extend(
            (
                RequestShape(base, frozenset({NO_ENTER_FIELD, TIMEOUT_FIELD})),
                RequestShape(base | {NO_WAIT_FIELD}, frozenset({NO_ENTER_FIELD})),
                RequestShape(base | {CAPTURE_FIELD}, frozenset({TIMEOUT_FIELD})),
            )
        )
    return tuple(shapes)


PUBLIC_PROWL_COMMAND_PREFIXES: Final[Mapping[Operation, tuple[str, ...]]] = {
    Operation.LIST: ("prowl", "list"),
    Operation.AGENTS: ("prowl", "agents"),
    Operation.READ: ("prowl", "read"),
    Operation.SEND: ("prowl", "send"),
    Operation.KEY: ("prowl", "key"),
    Operation.FOCUS: ("prowl", "focus"),
    Operation.TAB_CREATE: ("prowl", "tab", "create"),
    Operation.TAB_CLOSE: ("prowl", "tab", "close"),
    Operation.PANE_CLOSE: ("prowl", "pane", "close"),
    Operation.OPEN: ("prowl", "open"),
}
PUBLIC_PROWL_SELECTOR_OPTIONS: Final[Mapping[str, str]] = {
    TARGET_FIELD: "--target",
    WORKTREE_FIELD: "--worktree",
    TAB_FIELD: "--tab",
    PANE_FIELD: "--pane",
}
PUBLIC_PROWL_ARGUMENT_OPTIONS: Final[Mapping[str, str]] = {
    LAST_FIELD: "--last",
    WAIT_STABLE_FIELD: "--wait-stable",
    STABLE_INTERVAL_FIELD: "--stable-interval",
    STABLE_PERIOD_FIELD: "--stable-period",
    WAIT_TIMEOUT_FIELD: "--wait-timeout",
    NO_ENTER_FIELD: "--no-enter",
    NO_WAIT_FIELD: "--no-wait",
    CAPTURE_FIELD: "--capture",
    TIMEOUT_FIELD: "--timeout",
    REPEAT_FIELD: "--repeat",
    PATH_FIELD: "--path",
    FORCE_FIELD: "--force",
}
PUBLIC_PROWL_JSON_OPTION = "--json"

OPERATION_CONTRACTS: Final[Mapping[Operation, OperationContract]] = {
    Operation.LIST: OperationContract((RequestShape(),)),
    Operation.AGENTS: OperationContract((RequestShape(),)),
    Operation.READ: OperationContract(
        _selector_shapes(
            frozenset(),
            frozenset(
                {
                    LAST_FIELD,
                    WAIT_STABLE_FIELD,
                    STABLE_INTERVAL_FIELD,
                    STABLE_PERIOD_FIELD,
                    WAIT_TIMEOUT_FIELD,
                }
            ),
        )
    ),
    Operation.SEND: OperationContract(_send_shapes()),
    Operation.KEY: OperationContract(
        _selector_shapes(
            frozenset({KEY_FIELD, MUTATION_AUTHORIZED_FIELD}),
            frozenset({REPEAT_FIELD}),
        )
    ),
    Operation.FOCUS: OperationContract(
        _selector_shapes(frozenset({MUTATION_AUTHORIZED_FIELD}))
    ),
    Operation.TAB_CREATE: OperationContract(
        (
            RequestShape(
                frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({PATH_FIELD})
            ),
            *_selector_shapes(
                frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({PATH_FIELD})
            ),
        )
    ),
    Operation.TAB_CLOSE: OperationContract(
        _selector_shapes(
            frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({FORCE_FIELD})
        )
    ),
    Operation.PANE_CLOSE: OperationContract(
        _selector_shapes(
            frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({FORCE_FIELD})
        )
    ),
    Operation.OPEN: OperationContract(
        (RequestShape(frozenset({MUTATION_AUTHORIZED_FIELD}), frozenset({PATH_FIELD})),)
    ),
}
INTEGER_BOUNDS: Final[Mapping[str, tuple[int, int]]] = {
    LAST_FIELD: (1, 1_000_000),
    STABLE_INTERVAL_FIELD: (50, 5_000),
    STABLE_PERIOD_FIELD: (100, 60_000),
    WAIT_TIMEOUT_FIELD: (1, 300),
    TIMEOUT_FIELD: (1, 300),
    REPEAT_FIELD: (1, 100),
}
BOOLEAN_ARGUMENT_FIELDS = frozenset(
    {
        WAIT_STABLE_FIELD,
        NO_ENTER_FIELD,
        NO_WAIT_FIELD,
        CAPTURE_FIELD,
        FORCE_FIELD,
        MUTATION_AUTHORIZED_FIELD,
    }
)
TEXT_ARGUMENT_FIELDS = frozenset({TEXT_FIELD, KEY_FIELD})
ARGUMENT_NAMES: Final[Mapping[str, str]] = {
    "target": TARGET_FIELD,
    "worktree": WORKTREE_FIELD,
    "tab": TAB_FIELD,
    "pane": PANE_FIELD,
    "last": LAST_FIELD,
    "wait_stable": WAIT_STABLE_FIELD,
    "stable_interval": STABLE_INTERVAL_FIELD,
    "stable_period": STABLE_PERIOD_FIELD,
    "wait_timeout": WAIT_TIMEOUT_FIELD,
    "text": TEXT_FIELD,
    "no_enter": NO_ENTER_FIELD,
    "no_wait": NO_WAIT_FIELD,
    "capture": CAPTURE_FIELD,
    "timeout": TIMEOUT_FIELD,
    "key": KEY_FIELD,
    "repeat": REPEAT_FIELD,
    "path": PATH_FIELD,
    "force": FORCE_FIELD,
    "mutation_authorized": MUTATION_AUTHORIZED_FIELD,
}
RAW_PROWL_COMMAND_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"PROWL_COMMAND|[\[(]['\"]prowl['\"]"),
    re.compile(r"\bHELP_OPTION\b"),
)
LOCAL_WORKTREE_ENUMERATION_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"['\"]git['\"]\s*,\s*['\"]worktree['\"]\s*,\s*['\"]list['\"]"),
    re.compile(r"['\"]\.git[/\\\\]worktrees(?:[/\\\\]|['\"])"),
    re.compile(r"\bos\.(?:listdir|scandir|walk)\s*\("),
    re.compile(r"\.(?:iterdir|glob|rglob)\s*\("),
)


class ExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    COMMAND_FAILED = "command-failed"
    INVALID_SCHEMA = "invalid-schema"
    PROWL_UNAVAILABLE = "prowl-unavailable"
    IDENTITY_UNAVAILABLE = "identity-unavailable"
    IDENTITY_AMBIGUOUS = "identity-ambiguous"
    MUTATION_UNAUTHORIZED = "mutation-unauthorized"
    OPERATION_UNAVAILABLE = "operation-unavailable"


class TargetMatchCardinality(StrEnum):
    ZERO = "zero"
    ONE = "one"
    MULTIPLE = "multiple"


class OpenResolution(StrEnum):
    EXACT_ROOT = "exact-root"
    INSIDE_ROOT = "inside-root"
    NEW_ROOT = "new-root"


def target_match_cardinality(candidate_count: int) -> TargetMatchCardinality:
    if candidate_count == 0:
        return TargetMatchCardinality.ZERO
    if candidate_count == 1:
        return TargetMatchCardinality.ONE
    return TargetMatchCardinality.MULTIPLE


class EnvelopeKind(StrEnum):
    DELEGATION_REQUEST = "delegation-request"


class TerminalKind(StrEnum):
    COMPLETED = "delegation-completed"
    FAILED = "delegation-failed"
    REJECTED = "delegation-rejected"
    UNAVAILABLE = "delegation-unavailable"


class CliOperation(StrEnum):
    RUN = "run"
    RESOLVE_TARGET = "resolve-target"
    DELEGATE = "delegate"
    HAND_BACK = "handback"
    PLAN_HAND_BACK = "plan-handback"


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
                stdin=subprocess.DEVNULL if stdin is None else None,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as error:
            raise ProwlEnvironmentError(
                ExecutionStatus.PROWL_UNAVAILABLE,
                "Prowl CLI is unavailable. Run this capability inside a Prowl environment with the public CLI installed.",
            ) from error
        except subprocess.TimeoutExpired as error:
            raise ProwlEnvironmentError(
                ExecutionStatus.COMMAND_FAILED,
                f"Prowl command exceeded the {self.timeout_seconds}-second bound: {' '.join(argv)}",
            ) from error
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class ProwlEnvironmentError(RuntimeError):
    def __init__(self, status: ExecutionStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an object at {location}."
        )
    return value


def _array(value: object, location: str) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an array at {location}."
        )
    return [_object(item, f"{location}[{index}]") for index, item in enumerate(value)]


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Expected a non-empty string at {location}.",
        )
    return value


def _optional_text(value: object, location: str) -> str | None:
    if value is None:
        return None
    return _text(value, location)


def _boolean(value: object, location: str) -> bool:
    if not isinstance(value, bool):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected a boolean at {location}."
        )
    return value


def _integer(value: object, location: str, *, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an integer at {location}."
        )
    if not minimum <= value <= maximum:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Expected {location} between {minimum} and {maximum}; received {value}.",
        )
    return value


def _operation(value: object) -> Operation:
    raw = _text(value, f"request.{OPERATION_FIELD}")
    try:
        return Operation(raw)
    except ValueError as error:
        valid = ", ".join(operation.value for operation in Operation)
        raise ProwlEnvironmentError(
            ExecutionStatus.OPERATION_UNAVAILABLE,
            f"Unsupported Prowl operation {raw!r}. Supported operations: {valid}.",
        ) from error


def _terminal_kind(value: object) -> TerminalKind:
    raw = _text(value, KIND_FIELD)
    try:
        return TerminalKind(raw)
    except ValueError as error:
        valid = ", ".join(kind.value for kind in TerminalKind)
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported terminal kind {raw!r}. Valid terminal kinds: {valid}.",
        ) from error


def _one_selector(arguments: dict[str, object]) -> None:
    selected = [field for field in SELECTOR_FIELDS if field in arguments]
    if len(selected) > 1:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation accepts at most one selector; received: {', '.join(selected)}.",
        )
    for field in selected:
        _text(arguments[field], f"request.{ARGUMENTS_FIELD}.{field}")


def _allowed_fields(operation: Operation) -> frozenset[str]:
    return OPERATION_CONTRACTS[operation].allowed_fields


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
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request fields are invalid ({'; '.join(details)}).",
        )
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request schema version must be {SCHEMA_VERSION}.",
        )
    operation = _operation(value.get(OPERATION_FIELD))
    arguments = _object(value.get(ARGUMENTS_FIELD), f"request.{ARGUMENTS_FIELD}")
    unexpected_arguments = sorted(set(arguments) - _allowed_fields(operation))
    if unexpected_arguments:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} contains unsupported arguments: {', '.join(unexpected_arguments)}.",
        )
    if (
        operation in MUTATING_OPERATIONS
        and arguments.get(MUTATION_AUTHORIZED_FIELD) is not True
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.MUTATION_UNAUTHORIZED,
            f"{operation.value} requires mutationAuthorized: true before command construction.",
        )
    argument_fields = frozenset(arguments)
    if not any(
        shape.accepts(argument_fields)
        for shape in OPERATION_CONTRACTS[operation].request_shapes
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} arguments do not match a source-owned request shape.",
        )
    _one_selector(arguments)

    if operation is Operation.SEND:
        _text(arguments.get(TEXT_FIELD), f"request.{ARGUMENTS_FIELD}.{TEXT_FIELD}")
        no_wait = arguments.get(NO_WAIT_FIELD)
        capture = arguments.get(CAPTURE_FIELD)
        if no_wait is not None:
            _boolean(no_wait, f"request.{ARGUMENTS_FIELD}.{NO_WAIT_FIELD}")
        if capture is not None:
            _boolean(capture, f"request.{ARGUMENTS_FIELD}.{CAPTURE_FIELD}")
        if no_wait is True and capture is True:
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                "send cannot combine noWait with capture.",
            )
    elif operation is Operation.KEY:
        _text(arguments.get(KEY_FIELD), f"request.{ARGUMENTS_FIELD}.{KEY_FIELD}")
    elif operation in {Operation.TAB_CLOSE, Operation.PANE_CLOSE} and not any(
        field in arguments for field in SELECTOR_FIELDS
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} requires one exact target selector.",
        )

    for field, (minimum, maximum) in INTEGER_BOUNDS.items():
        if field in arguments:
            _integer(
                arguments[field],
                f"request.{ARGUMENTS_FIELD}.{field}",
                minimum=minimum,
                maximum=maximum,
            )
    for field in BOOLEAN_ARGUMENT_FIELDS - {MUTATION_AUTHORIZED_FIELD}:
        if field in arguments:
            _boolean(arguments[field], f"request.{ARGUMENTS_FIELD}.{field}")
    if PATH_FIELD in arguments:
        _text(arguments[PATH_FIELD], f"request.{ARGUMENTS_FIELD}.{PATH_FIELD}")
    return operation, arguments


def operation_request(
    operation: Operation | str, **kwargs: object
) -> dict[str, object]:
    operation_value = Operation(operation)
    arguments: dict[str, object] = {}
    for name, value in kwargs.items():
        if name not in ARGUMENT_NAMES:
            valid = ", ".join(sorted(ARGUMENT_NAMES))
            raise ProwlEnvironmentError(
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


def _selector_arguments(arguments: dict[str, object]) -> list[str]:
    command: list[str] = []
    for field, option in (
        (TARGET_FIELD, TARGET_OPTION),
        (WORKTREE_FIELD, WORKTREE_OPTION),
        (TAB_FIELD, TAB_OPTION),
        (PANE_FIELD, PANE_OPTION),
    ):
        if field in arguments:
            command.extend((option, cast(str, arguments[field])))
    return command


def command_for(request: object) -> tuple[str, ...]:
    operation, arguments = _validated_request(request)
    if operation is Operation.LIST:
        return (PROWL_COMMAND, LIST_COMMAND, JSON_OPTION)
    if operation is Operation.AGENTS:
        return (PROWL_COMMAND, AGENTS_COMMAND, JSON_OPTION)
    if operation is Operation.OPEN:
        command = [PROWL_COMMAND, OPEN_COMMAND, JSON_OPTION]
        if PATH_FIELD in arguments:
            command.append(cast(str, arguments[PATH_FIELD]))
        return tuple(command)

    if operation is Operation.TAB_CREATE:
        command = [PROWL_COMMAND, TAB_COMMAND, CREATE_COMMAND]
    elif operation is Operation.TAB_CLOSE:
        command = [PROWL_COMMAND, TAB_COMMAND, CLOSE_COMMAND]
    elif operation is Operation.PANE_CLOSE:
        command = [PROWL_COMMAND, PANE_COMMAND, CLOSE_COMMAND]
    else:
        command = [PROWL_COMMAND, operation.value]
    command.extend(_selector_arguments(arguments))
    command.append(JSON_OPTION)

    if operation is Operation.READ:
        for field, option in (
            (LAST_FIELD, LAST_OPTION),
            (STABLE_INTERVAL_FIELD, STABLE_INTERVAL_OPTION),
            (STABLE_PERIOD_FIELD, STABLE_PERIOD_OPTION),
            (WAIT_TIMEOUT_FIELD, WAIT_TIMEOUT_OPTION),
        ):
            if field in arguments:
                command.extend((option, str(arguments[field])))
        if arguments.get(WAIT_STABLE_FIELD) is True:
            command.append(WAIT_STABLE_OPTION)
    elif operation is Operation.SEND:
        for field, option in (
            (NO_ENTER_FIELD, NO_ENTER_OPTION),
            (NO_WAIT_FIELD, NO_WAIT_OPTION),
            (CAPTURE_FIELD, CAPTURE_OPTION),
        ):
            if arguments.get(field) is True:
                command.append(option)
        if TIMEOUT_FIELD in arguments:
            command.extend((TIMEOUT_OPTION, str(arguments[TIMEOUT_FIELD])))
        command.append(cast(str, arguments[TEXT_FIELD]))
    elif operation is Operation.KEY:
        if REPEAT_FIELD in arguments:
            command.extend((REPEAT_OPTION, str(arguments[REPEAT_FIELD])))
        command.append(cast(str, arguments[KEY_FIELD]))
    elif operation is Operation.TAB_CREATE and PATH_FIELD in arguments:
        command.extend((PATH_OPTION, cast(str, arguments[PATH_FIELD])))
    elif (
        operation in {Operation.TAB_CLOSE, Operation.PANE_CLOSE}
        and arguments.get(FORCE_FIELD) is True
    ):
        command.append(FORCE_OPTION)
    return tuple(command)


def raw_prowl_command_violations(sources: Mapping[str, str]) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in RAW_PROWL_COMMAND_PATTERNS)
    )


def local_worktree_enumeration_violations(
    sources: Mapping[str, str],
) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in LOCAL_WORKTREE_ENUMERATION_PATTERNS)
    )


def validate_operation_result(
    result: object, expected_operation: Operation | None = None
) -> dict[str, object]:
    value = _object(result, "result")
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation result schema version must be {SCHEMA_VERSION}.",
        )
    operation = _operation(value.get(OPERATION_FIELD))
    if expected_operation is not None and operation is not expected_operation:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation result identifies {operation.value}; expected {expected_operation.value}.",
        )
    try:
        status = ExecutionStatus(_text(value.get(STATUS_FIELD), STATUS_FIELD))
    except ValueError as error:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported operation result status: {value.get(STATUS_FIELD)!r}.",
        ) from error

    if status is ExecutionStatus.SUCCEEDED:
        if set(value) != SUCCESS_RESULT_FIELDS:
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                "Successful operation result fields do not match the source-owned schema.",
            )
        exit_code = value.get(COMMAND_EXIT_CODE_FIELD)
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Expected an integer at result.{COMMAND_EXIT_CODE_FIELD}.",
            )
        response = _object(value.get(RESPONSE_FIELD), f"result.{RESPONSE_FIELD}")
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            STATUS_FIELD: status,
            COMMAND_EXIT_CODE_FIELD: exit_code,
            RESPONSE_FIELD: response,
        }

    allowed_fields = FAILURE_RESULT_REQUIRED_FIELDS | FAILURE_RESULT_OPTIONAL_FIELDS
    if not FAILURE_RESULT_REQUIRED_FIELDS <= set(value) or set(value) - allowed_fields:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Failed operation result fields do not match the source-owned schema.",
        )
    validated: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation,
        STATUS_FIELD: status,
        DETAIL_FIELD: _text(value.get(DETAIL_FIELD), f"result.{DETAIL_FIELD}"),
    }
    if COMMAND_EXIT_CODE_FIELD in value:
        exit_code = value[COMMAND_EXIT_CODE_FIELD]
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Expected an integer at result.{COMMAND_EXIT_CODE_FIELD}.",
            )
        validated[COMMAND_EXIT_CODE_FIELD] = exit_code
    return validated


def _failure_result(
    operation: Operation,
    status: ExecutionStatus,
    detail: str,
    command_exit_code: int | None,
) -> dict[str, object]:
    result: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation,
        STATUS_FIELD: status,
        DETAIL_FIELD: detail,
    }
    if command_exit_code is not None:
        result[COMMAND_EXIT_CODE_FIELD] = command_exit_code
    return validate_operation_result(result, operation)


def execute(request: object, runner: CommandRunner) -> dict[str, object]:
    operation, _ = _validated_request(request)
    command = command_for(request)
    try:
        result = runner.run(command)
    except ProwlEnvironmentError as error:
        return _failure_result(operation, error.status, str(error), None)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no command detail"
        return _failure_result(
            operation, ExecutionStatus.COMMAND_FAILED, detail, result.returncode
        )
    try:
        payload = _object(json.loads(result.stdout), "response")
    except json.JSONDecodeError as error:
        return _failure_result(
            operation,
            ExecutionStatus.INVALID_SCHEMA,
            f"Prowl returned invalid JSON: {error.msg}",
            result.returncode,
        )
    if payload.get(OK_FIELD) is not True:
        error_payload = payload.get(ERROR_FIELD)
        detail = "Prowl public response reported failure."
        if isinstance(error_payload, dict):
            message = error_payload.get(MESSAGE_FIELD)
            if isinstance(message, str) and message:
                detail = message
        return _failure_result(
            operation, ExecutionStatus.COMMAND_FAILED, detail, result.returncode
        )
    return validate_operation_result(
        {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            STATUS_FIELD: ExecutionStatus.SUCCEEDED,
            COMMAND_EXIT_CODE_FIELD: result.returncode,
            RESPONSE_FIELD: payload,
        },
        operation,
    )


def validate_identity(identity: object, location: str) -> dict[str, str]:
    value = _object(identity, location)
    unexpected = sorted(set(value) - IDENTITY_INPUT_FIELDS)
    missing = sorted(set(IDENTITY_FIELDS) - set(value))
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append(f"unsupported: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{location} identity fields are invalid ({'; '.join(details)}).",
        )
    validated = {
        field: _text(value.get(field), f"{location}.{field}")
        for field in IDENTITY_FIELDS
    }
    for path_field in (WORKTREE_FIELD, REPOSITORY_FIELD):
        if not os.path.isabs(validated[path_field]):
            raise ProwlEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Expected an absolute path at {location}.{path_field}.",
            )
    if RUN_FIELD in value:
        validated[RUN_FIELD] = _text(value.get(RUN_FIELD), f"{location}.{RUN_FIELD}")
    return validated


def participant_from_agent(item: object) -> dict[str, str]:
    value = _object(item, "agent")
    pane = _object(value.get(PANE_FIELD), f"agent.{PANE_FIELD}")
    worktree = _object(value.get(WORKTREE_FIELD), f"agent.{WORKTREE_FIELD}")
    project = _object(value.get(PROJECT_FIELD), f"agent.{PROJECT_FIELD}")
    identity = {
        AGENT_FIELD: _text(value.get(ID_FIELD), f"agent.{ID_FIELD}"),
        PANE_FIELD: _text(pane.get(ID_FIELD), f"agent.{PANE_FIELD}.{ID_FIELD}"),
        WORKTREE_FIELD: _text(
            worktree.get(PATH_FIELD), f"agent.{WORKTREE_FIELD}.{PATH_FIELD}"
        ),
        BRANCH_FIELD: _text(
            project.get(BRANCH_FIELD), f"agent.{PROJECT_FIELD}.{BRANCH_FIELD}"
        ),
        REPOSITORY_FIELD: _text(
            worktree.get(ROOT_PATH_FIELD),
            f"agent.{WORKTREE_FIELD}.{ROOT_PATH_FIELD}",
        ),
    }
    run = value.get(RUN_FIELD)
    if run is not None:
        identity[RUN_FIELD] = _text(
            _object(run, f"agent.{RUN_FIELD}").get(ID_FIELD),
            f"agent.{RUN_FIELD}.{ID_FIELD}",
        )
    return validate_identity(identity, "participant")


def participants_from_agents(payload: object) -> list[dict[str, str]]:
    response = _object(payload, "response")
    data = _object(response.get(DATA_FIELD), f"response.{DATA_FIELD}")
    agents = _array(data.get(AGENTS_FIELD), f"response.{DATA_FIELD}.{AGENTS_FIELD}")
    participants = [participant_from_agent(item) for item in agents]
    if not participants:
        raise ProwlEnvironmentError(
            ExecutionStatus.IDENTITY_UNAVAILABLE,
            "Prowl returned no positively identified agents.",
        )
    pane_ids = [participant[PANE_FIELD] for participant in participants]
    if len(pane_ids) != len(set(pane_ids)):
        raise ProwlEnvironmentError(
            ExecutionStatus.IDENTITY_AMBIGUOUS,
            "Prowl returned ambiguous duplicate agent pane identities.",
        )
    return participants


def participant_projection(payload: object) -> dict[str, object]:
    try:
        participants = participants_from_agents(payload)
    except ProwlEnvironmentError as error:
        status = (
            ExecutionStatus.IDENTITY_AMBIGUOUS
            if error.status is ExecutionStatus.IDENTITY_AMBIGUOUS
            else ExecutionStatus.IDENTITY_UNAVAILABLE
        )
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: Operation.AGENTS,
            STATUS_FIELD: status,
            DETAIL_FIELD: str(error),
        }
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: Operation.AGENTS,
        STATUS_FIELD: ExecutionStatus.SUCCEEDED,
        PARTICIPANTS_FIELD: participants,
    }


def _path_contains(root: str, target: str) -> bool:
    if not os.path.isabs(root):
        return False
    normalized_root = os.path.normpath(root)
    normalized_target = os.path.normpath(target)
    try:
        return (
            os.path.commonpath((normalized_root, normalized_target)) == normalized_root
        )
    except ValueError:
        return False


def _send_request_template(participant: Mapping[str, str]) -> dict[str, object]:
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: Operation.SEND,
        ARGUMENTS_FIELD: {
            PANE_FIELD: participant[PANE_FIELD],
            TEXT_FIELD: None,
            NO_WAIT_FIELD: True,
        },
    }


def _resolve_caller(
    participants: list[dict[str, str]], environment: Mapping[str, str]
) -> dict[str, str]:
    pane_id = environment.get(PROWL_PANE_ID_ENV)
    worktree_path = environment.get(PROWL_WORKTREE_PATH_ENV)
    if not pane_id and not worktree_path:
        raise ProwlEnvironmentError(
            ExecutionStatus.IDENTITY_UNAVAILABLE,
            "resolve-target requires caller identity from PROWL_PANE_ID or PROWL_WORKTREE_PATH.",
        )
    matches = [
        participant
        for participant in participants
        if (not pane_id or participant[PANE_FIELD] == pane_id)
        and (
            not worktree_path
            or os.path.normpath(participant[WORKTREE_FIELD])
            == os.path.normpath(worktree_path)
        )
    ]
    if len(matches) == 1:
        return matches[0]
    status = (
        ExecutionStatus.IDENTITY_AMBIGUOUS
        if len(matches) > 1
        else ExecutionStatus.IDENTITY_UNAVAILABLE
    )
    supplied = ", ".join(
        field for field in CALLER_IDENTITY_ENV_FIELDS if environment.get(field)
    )
    raise ProwlEnvironmentError(
        status,
        f"Caller identity from {supplied} matches {len(matches)} public Prowl agents.",
    )


def resolve_target(
    path: str, environment: Mapping[str, str], runner: CommandRunner
) -> dict[str, object]:
    if not path or not os.path.isabs(path):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "resolve-target path must be an absolute worktree, repository, or working-directory path.",
        )
    inventory = execute(operation_request(Operation.AGENTS), runner)
    participants: list[dict[str, str]] = []
    caller: dict[str, str] | None = None
    candidates: list[dict[str, object]] = []
    status = inventory[STATUS_FIELD]
    detail: str | None = None
    if status is ExecutionStatus.SUCCEEDED:
        try:
            participants = participants_from_agents(inventory[RESPONSE_FIELD])
            caller = _resolve_caller(participants, environment)
            matched = [
                participant
                for participant in participants
                if participant[PANE_FIELD] != caller[PANE_FIELD]
                and (
                    _path_contains(participant[WORKTREE_FIELD], path)
                    or os.path.normpath(participant[REPOSITORY_FIELD])
                    == os.path.normpath(path)
                )
            ]
            candidates = [
                {
                    PARTICIPANT_FIELD: participant,
                    SEND_REQUEST_TEMPLATE_FIELD: _send_request_template(participant),
                }
                for participant in matched
            ]
            cardinality = target_match_cardinality(len(candidates))
            if cardinality is TargetMatchCardinality.ZERO:
                status = ExecutionStatus.IDENTITY_UNAVAILABLE
                detail = f"No non-caller Prowl agent contains target path {path}."
            elif cardinality is TargetMatchCardinality.ONE:
                status = ExecutionStatus.SUCCEEDED
            elif cardinality is TargetMatchCardinality.MULTIPLE:
                status = ExecutionStatus.IDENTITY_AMBIGUOUS
                detail = f"Target path {path} matches multiple non-caller Prowl agents."
        except ProwlEnvironmentError as error:
            status = error.status
            detail = str(error)
    else:
        detail = cast(str, inventory.get(DETAIL_FIELD))

    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: CliOperation.RESOLVE_TARGET,
        STATUS_FIELD: status,
        DETAIL_FIELD: detail,
        INVENTORY_FIELD: inventory,
        PARTICIPANTS_FIELD: participants,
        CALLER_FIELD: caller,
        CANDIDATES_FIELD: candidates,
    }


def _canonical_reference(value: object) -> str:
    reference = _text(value, COORDINATION_REFERENCE_FIELD)
    try:
        return str(uuid.UUID(reference))
    except ValueError as error:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Coordination reference is not a UUID: {reference}",
        ) from error


def _handback_command(*, pane: str, completion_text: str) -> str:
    request = operation_request(
        Operation.SEND,
        pane=pane,
        text=completion_text,
        no_wait=True,
    )
    payload = json.dumps(request, sort_keys=True, separators=(",", ":"))
    adapter_path = str(Path(__file__).resolve())
    return (
        "printf '%s\\n' "
        f"{shlex.quote(payload)} | python3 {shlex.quote(adapter_path)} run"
    )


def handback_plan(
    *,
    sender: object,
    recipient: object,
    completion_text: str,
) -> dict[str, object]:
    validated_sender = validate_identity(sender, SENDER_FIELD)
    validated_recipient = validate_identity(recipient, RECIPIENT_FIELD)
    if validated_sender[PANE_FIELD] == validated_recipient[PANE_FIELD]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A handback recipient must be a different positively identified Prowl agent.",
        )
    completion = _text(completion_text, COMPLETION_TEXT_FIELD)
    adapter_path = str(Path(__file__).resolve())
    return {
        SCHEMA_VERSION_FIELD: HANDBACK_SCHEMA_VERSION,
        COMPLETION_TEXT_FIELD: completion,
        ADAPTER_PATH_FIELD: adapter_path,
        COMMAND_FIELD: _handback_command(
            pane=validated_sender[PANE_FIELD],
            completion_text=completion,
        ),
        SUCCESS_CRITERIA_FIELD: {
            STATUS_FIELD: ExecutionStatus.SUCCEEDED,
            COMMAND_EXIT_CODE_FIELD: 0,
            TRAILING_ENTER_SENT_FIELD: True,
        },
        RETRY_POLICY_FIELD: HANDBACK_RETRY_POLICY,
        SOCKET_FIELD: DEFAULT_SOCKET,
        EXPECTED_PANES_FIELD: [
            validated_sender[PANE_FIELD],
            validated_recipient[PANE_FIELD],
        ],
    }


def _validated_handback(
    value: object,
    *,
    sender: dict[str, str],
    recipient: dict[str, str],
) -> dict[str, object]:
    handback = _object(value, HANDBACK_FIELD)
    unexpected = sorted(set(handback) - HANDBACK_FIELDS)
    missing = sorted(HANDBACK_FIELDS - set(handback))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback must contain exactly the source-owned fields.",
        )
    if handback.get(SCHEMA_VERSION_FIELD) != HANDBACK_SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Handback schema version must be {HANDBACK_SCHEMA_VERSION}.",
        )
    completion = _text(
        handback.get(COMPLETION_TEXT_FIELD),
        f"{HANDBACK_FIELD}.{COMPLETION_TEXT_FIELD}",
    )
    adapter_path = _text(
        handback.get(ADAPTER_PATH_FIELD),
        f"{HANDBACK_FIELD}.{ADAPTER_PATH_FIELD}",
    )
    expected_adapter_path = str(Path(__file__).resolve())
    if adapter_path != expected_adapter_path:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback adapterPath must match the source-owned adapter path.",
        )
    expected_command = _handback_command(
        pane=sender[PANE_FIELD],
        completion_text=completion,
    )
    command = _text(handback.get(COMMAND_FIELD), f"{HANDBACK_FIELD}.{COMMAND_FIELD}")
    if command != expected_command:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback command does not match its semantic completion data.",
        )
    success = _object(
        handback.get(SUCCESS_CRITERIA_FIELD),
        f"{HANDBACK_FIELD}.{SUCCESS_CRITERIA_FIELD}",
    )
    command_exit_code = success.get(COMMAND_EXIT_CODE_FIELD)
    if (
        set(success) != HANDBACK_SUCCESS_FIELDS
        or success.get(STATUS_FIELD) != ExecutionStatus.SUCCEEDED
        or not isinstance(command_exit_code, int)
        or isinstance(command_exit_code, bool)
        or command_exit_code != 0
        or success.get(TRAILING_ENTER_SENT_FIELD) is not True
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback success criteria must require checked turn submission.",
        )
    if handback.get(RETRY_POLICY_FIELD) != HANDBACK_RETRY_POLICY:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Handback retryPolicy must be {HANDBACK_RETRY_POLICY}.",
        )
    if handback.get(SOCKET_FIELD) != DEFAULT_SOCKET:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Handback socket must be {DEFAULT_SOCKET}.",
        )
    if handback.get(EXPECTED_PANES_FIELD) != [
        sender[PANE_FIELD],
        recipient[PANE_FIELD],
    ]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Handback expectedPanes must preserve sender and recipient pane order.",
        )
    return {
        SCHEMA_VERSION_FIELD: HANDBACK_SCHEMA_VERSION,
        COMPLETION_TEXT_FIELD: completion,
        ADAPTER_PATH_FIELD: adapter_path,
        COMMAND_FIELD: command,
        SUCCESS_CRITERIA_FIELD: success,
        RETRY_POLICY_FIELD: HANDBACK_RETRY_POLICY,
        SOCKET_FIELD: DEFAULT_SOCKET,
        EXPECTED_PANES_FIELD: [sender[PANE_FIELD], recipient[PANE_FIELD]],
    }


def delegation_request(
    *,
    sender: object,
    recipient: object,
    subject: str,
    instruction: str,
    completion_text: str,
    coordination_reference: str | None = None,
) -> dict[str, object]:
    validated_sender = validate_identity(sender, SENDER_FIELD)
    validated_recipient = validate_identity(recipient, RECIPIENT_FIELD)
    if validated_sender[PANE_FIELD] == validated_recipient[PANE_FIELD]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A delegation recipient must be a different positively identified Prowl agent.",
        )
    reference = (
        str(uuid.uuid4())
        if coordination_reference is None
        else _canonical_reference(coordination_reference)
    )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: EnvelopeKind.DELEGATION_REQUEST,
        COORDINATION_REFERENCE_FIELD: reference,
        SENDER_FIELD: validated_sender,
        RECIPIENT_FIELD: validated_recipient,
        SUBJECT_FIELD: _text(subject, SUBJECT_FIELD),
        INSTRUCTION_FIELD: _text(instruction, INSTRUCTION_FIELD),
        HANDBACK_FIELD: handback_plan(
            sender=validated_sender,
            recipient=validated_recipient,
            completion_text=completion_text,
        ),
    }


def _validated_delegation(value: object) -> dict[str, object]:
    request = _object(value, "delegationRequest")
    unexpected = sorted(set(request) - DELEGATION_REQUEST_FIELDS)
    missing = sorted(DELEGATION_REQUEST_FIELDS - set(request))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Delegation request must contain exactly the source-owned request fields.",
        )
    if request.get(SCHEMA_VERSION_FIELD) != DELEGATION_SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Delegation request schema version must be {DELEGATION_SCHEMA_VERSION}.",
        )
    if request.get(KIND_FIELD) != EnvelopeKind.DELEGATION_REQUEST:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Delegation request kind must be {EnvelopeKind.DELEGATION_REQUEST}.",
        )
    sender = validate_identity(request.get(SENDER_FIELD), SENDER_FIELD)
    recipient = validate_identity(request.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    if sender[PANE_FIELD] == recipient[PANE_FIELD]:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A delegation recipient must be a different positively identified Prowl agent.",
        )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: EnvelopeKind.DELEGATION_REQUEST,
        COORDINATION_REFERENCE_FIELD: _canonical_reference(
            request.get(COORDINATION_REFERENCE_FIELD)
        ),
        SENDER_FIELD: sender,
        RECIPIENT_FIELD: recipient,
        SUBJECT_FIELD: _text(request.get(SUBJECT_FIELD), SUBJECT_FIELD),
        INSTRUCTION_FIELD: _text(request.get(INSTRUCTION_FIELD), INSTRUCTION_FIELD),
        HANDBACK_FIELD: _validated_handback(
            request.get(HANDBACK_FIELD),
            sender=sender,
            recipient=recipient,
        ),
    }


def _durable_reference(value: object) -> str:
    reference = _text(value, RESULT_REFERENCE_FIELD)
    parsed = urlparse(reference)
    if not parsed.scheme:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A durable result reference must include a URI scheme.",
        )
    return reference


def terminal_handback(
    delegation: object,
    terminal_kind: TerminalKind | str,
    *,
    inline_result: str | None = None,
    result_reference: str | None = None,
    projection: str | None = None,
) -> dict[str, object]:
    request = _validated_delegation(delegation)
    kind = TerminalKind(terminal_kind)
    inline = _optional_text(inline_result, INLINE_RESULT_FIELD)
    reference = (
        None if result_reference is None else _durable_reference(result_reference)
    )
    bounded_projection = _optional_text(projection, PROJECTION_FIELD)
    if inline is None and reference is None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A terminal handback requires inlineResult or resultReference with projection.",
        )
    if reference is not None and bounded_projection is None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A durable result reference requires a bounded inline projection.",
        )
    if reference is None and bounded_projection is not None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "projection is valid only with resultReference.",
        )
    if (
        bounded_projection is not None
        and len(bounded_projection) > MAX_RESULT_PROJECTION_CHARACTERS
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"projection exceeds {MAX_RESULT_PROJECTION_CHARACTERS} characters.",
        )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: kind,
        COORDINATION_REFERENCE_FIELD: request[COORDINATION_REFERENCE_FIELD],
        SENDER_FIELD: request[RECIPIENT_FIELD],
        RECIPIENT_FIELD: request[SENDER_FIELD],
        INLINE_RESULT_FIELD: inline,
        RESULT_REFERENCE_FIELD: reference,
        PROJECTION_FIELD: bounded_projection,
    }


def _validated_terminal(value: object) -> dict[str, object]:
    terminal = _object(value, "terminalHandback")
    unexpected = sorted(set(terminal) - TERMINAL_HANDBACK_FIELDS)
    missing = sorted(TERMINAL_HANDBACK_FIELDS - set(terminal))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Terminal handback must contain exactly the source-owned terminal fields.",
        )
    if terminal.get(SCHEMA_VERSION_FIELD) != DELEGATION_SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Terminal handback schema version must be {DELEGATION_SCHEMA_VERSION}.",
        )
    kind = _terminal_kind(terminal.get(KIND_FIELD))
    inline = _optional_text(terminal.get(INLINE_RESULT_FIELD), INLINE_RESULT_FIELD)
    reference = terminal.get(RESULT_REFERENCE_FIELD)
    projection = terminal.get(PROJECTION_FIELD)
    if reference is not None:
        reference = _durable_reference(reference)
    if projection is not None:
        projection = _text(projection, PROJECTION_FIELD)
    if inline is None and reference is None:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A terminal handback requires one supported result form.",
        )
    if (reference is None) != (projection is None):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "resultReference and projection must appear together.",
        )
    if (
        isinstance(projection, str)
        and len(projection) > MAX_RESULT_PROJECTION_CHARACTERS
    ):
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"projection exceeds {MAX_RESULT_PROJECTION_CHARACTERS} characters.",
        )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        KIND_FIELD: kind,
        COORDINATION_REFERENCE_FIELD: _canonical_reference(
            terminal.get(COORDINATION_REFERENCE_FIELD)
        ),
        SENDER_FIELD: validate_identity(terminal.get(SENDER_FIELD), SENDER_FIELD),
        RECIPIENT_FIELD: validate_identity(
            terminal.get(RECIPIENT_FIELD), RECIPIENT_FIELD
        ),
        INLINE_RESULT_FIELD: inline,
        RESULT_REFERENCE_FIELD: reference,
        PROJECTION_FIELD: projection,
    }


def reduce_terminal(current: object | None, incoming: object) -> dict[str, object]:
    validated_incoming = _validated_terminal(incoming)
    if current is None:
        return validated_incoming
    validated_current = _validated_terminal(current)
    if validated_current != validated_incoming:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "A conflicting terminal handback already exists for the coordination reference.",
        )
    return validated_current


def delegation_delivery_request(envelope: object) -> dict[str, object]:
    value = _object(envelope, "envelope")
    kind = value.get(KIND_FIELD)
    if kind == EnvelopeKind.DELEGATION_REQUEST:
        validated = _validated_delegation(value)
    else:
        validated = _validated_terminal(value)
    recipient = validate_identity(validated.get(RECIPIENT_FIELD), RECIPIENT_FIELD)
    return operation_request(
        Operation.SEND,
        pane=recipient[PANE_FIELD],
        text=json.dumps(validated, sort_keys=True),
        no_wait=True,
    )


def result_form_arguments(fields: Mapping[str, object]) -> dict[str, str | None]:
    unexpected = sorted(
        set(fields) - {INLINE_RESULT_FIELD, RESULT_REFERENCE_FIELD, PROJECTION_FIELD}
    )
    if unexpected:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported terminal result fields: {', '.join(unexpected)}.",
        )
    return {
        "inline_result": cast(str | None, fields.get(INLINE_RESULT_FIELD)),
        "result_reference": cast(str | None, fields.get(RESULT_REFERENCE_FIELD)),
        "projection": cast(str | None, fields.get(PROJECTION_FIELD)),
    }


def _json_input(stream: TextIO, location: str) -> dict[str, object]:
    try:
        return _object(json.load(stream), location)
    except json.JSONDecodeError as error:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{location} is invalid JSON: {error.msg}",
        ) from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="cli_operation", required=True)
    for operation in CliOperation:
        subparsers.add_parser(operation.value)
    return parser


def _delegation_from_cli(value: dict[str, object]) -> dict[str, object]:
    # Reading each field by name would ignore every other key, so a caller that
    # invents one sends a delegation missing the data it believed it supplied.
    # The envelope builder owns schemaVersion and kind, so they are not accepted
    # here; every remaining key must be one this function actually forwards.
    unexpected = sorted(set(value) - DELEGATION_CLI_FIELDS)
    if unexpected:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "Delegation request carries unsupported fields: " + ", ".join(unexpected),
        )
    return delegation_request(
        sender=value.get(SENDER_FIELD),
        recipient=value.get(RECIPIENT_FIELD),
        subject=_text(value.get(SUBJECT_FIELD), SUBJECT_FIELD),
        instruction=_text(value.get(INSTRUCTION_FIELD), INSTRUCTION_FIELD),
        completion_text=_text(value.get(COMPLETION_TEXT_FIELD), COMPLETION_TEXT_FIELD),
        coordination_reference=cast(
            str | None, value.get(COORDINATION_REFERENCE_FIELD)
        ),
    )


def _handback_from_cli(value: dict[str, object]) -> dict[str, object]:
    unexpected = sorted(set(value) - HANDBACK_PLAN_CLI_FIELDS)
    missing = sorted(HANDBACK_PLAN_CLI_FIELDS - set(value))
    if unexpected or missing:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "plan-handback requires exactly sender, recipient, and completionText.",
        )
    handback = handback_plan(
        sender=value.get(SENDER_FIELD),
        recipient=value.get(RECIPIENT_FIELD),
        completion_text=_text(value.get(COMPLETION_TEXT_FIELD), COMPLETION_TEXT_FIELD),
    )
    return {
        SCHEMA_VERSION_FIELD: DELEGATION_SCHEMA_VERSION,
        OPERATION_FIELD: CliOperation.PLAN_HAND_BACK,
        STATUS_FIELD: ExecutionStatus.SUCCEEDED,
        HANDBACK_FIELD: handback,
    }


def command_exit_code(result: object) -> int:
    value = _object(result, "result")
    status = value.get(STATUS_FIELD)
    if status == ExecutionStatus.SUCCEEDED:
        return 0
    if value.get(OPERATION_FIELD) == CliOperation.RESOLVE_TARGET and status in {
        ExecutionStatus.IDENTITY_UNAVAILABLE,
        ExecutionStatus.IDENTITY_AMBIGUOUS,
    }:
        return 0
    return 2


def _resolve_target_from_cli(
    value: dict[str, object],
    environment: Mapping[str, str],
    runner: CommandRunner,
) -> dict[str, object]:
    unexpected = sorted(set(value) - {SCHEMA_VERSION_FIELD, PATH_FIELD})
    if unexpected or value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise ProwlEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            "resolve-target requires exactly schemaVersion and path.",
        )
    return resolve_target(_text(value.get(PATH_FIELD), PATH_FIELD), environment, runner)


def _execute_cli_operation(
    cli_operation: CliOperation,
    value: dict[str, object],
    environment: Mapping[str, str],
    runner: CommandRunner,
) -> dict[str, object]:
    if cli_operation is CliOperation.RESOLVE_TARGET:
        return _resolve_target_from_cli(value, environment, runner)
    if cli_operation is CliOperation.RUN:
        return execute(value, runner)
    if cli_operation is CliOperation.PLAN_HAND_BACK:
        return _handback_from_cli(value)
    if cli_operation is CliOperation.DELEGATE:
        delegation = _delegation_from_cli(value)
        result = execute(delegation_delivery_request(delegation), runner)
        result[DELEGATION_FIELD] = delegation
        return result

    delegation = _object(value.get(DELEGATION_FIELD), DELEGATION_FIELD)
    terminal = terminal_handback(
        delegation,
        _terminal_kind(value.get(KIND_FIELD)),
        inline_result=cast(str | None, value.get(INLINE_RESULT_FIELD)),
        result_reference=cast(str | None, value.get(RESULT_REFERENCE_FIELD)),
        projection=cast(str | None, value.get(PROJECTION_FIELD)),
    )
    result = execute(delegation_delivery_request(terminal), runner)
    result[DELEGATION_FIELD] = delegation
    result[TERMINAL_FIELD] = terminal
    return result


def main(
    argv: list[str] | None = None,
    *,
    runner: CommandRunner | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
) -> int:
    args = _parser().parse_args(argv)
    cli_operation = CliOperation(args.cli_operation)
    command_runner = runner if runner is not None else SubprocessRunner()
    input_stream = stdin if stdin is not None else sys.stdin
    output_stream = stdout if stdout is not None else sys.stdout
    active_environment = environment if environment is not None else os.environ
    try:
        value = _json_input(input_stream, "stdin")
        result = _execute_cli_operation(
            cli_operation, value, active_environment, command_runner
        )
    except ProwlEnvironmentError as error:
        result = {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: error.status,
            DETAIL_FIELD: str(error),
        }
    print(json.dumps(result, sort_keys=True), file=output_stream)
    return command_exit_code(result)


if __name__ == "__main__":
    sys.exit(main())
