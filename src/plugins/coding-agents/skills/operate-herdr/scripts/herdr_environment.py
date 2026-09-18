#!/usr/bin/env python3
"""Operate herdr through a checked, versioned environment contract."""

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
COMMAND_TIMEOUT_SECONDS = 30
# Every wait-bearing command gets its own bound plus this margin for the
# subprocess, so the adapter's bound always exceeds the request's.
WAIT_MARGIN_SECONDS = 5

# Public command grammar of herdr.
HERDR_COMMAND = "herdr"
AGENT_COMMAND = "agent"
PANE_COMMAND = "pane"
WORKTREE_COMMAND = "worktree"
LIST_COMMAND = "list"
READ_COMMAND = "read"
WAIT_COMMAND = "wait"
PROMPT_COMMAND = "prompt"
SEND_KEYS_COMMAND = "send-keys"
START_COMMAND = "start"
CLOSE_COMMAND = "close"
OPEN_COMMAND = "open"
SOURCE_OPTION = "--source"
LINES_OPTION = "--lines"
UNTIL_OPTION = "--until"
TIMEOUT_OPTION = "--timeout"
WAIT_OPTION = "--wait"
KIND_OPTION = "--kind"
PANE_OPTION = "--pane"
PATH_OPTION = "--path"
NO_FOCUS_OPTION = "--no-focus"
AGENT_ARGUMENTS_SEPARATOR = "--"

# Fields of herdr's public JSON envelope.
ID_FIELD = "id"
RESULT_FIELD = "result"
ERROR_FIELD = "error"
CODE_FIELD = "code"
MESSAGE_FIELD = "message"
AGENTS_FIELD = "agents"
# Fields of one hosted agent session in that envelope.
NAME_FIELD = "name"
AGENT_KIND_FIELD = "agent"
AGENT_STATUS_FIELD = "agent_status"
PANE_ID_FIELD = "pane_id"
TAB_ID_FIELD = "tab_id"
WORKSPACE_ID_FIELD = "workspace_id"
CWD_FIELD = "cwd"
INTERACTIVE_READY_FIELD = "interactive_ready"
PARTICIPANT_FIELDS = (
    NAME_FIELD,
    AGENT_KIND_FIELD,
    AGENT_STATUS_FIELD,
    PANE_ID_FIELD,
    TAB_ID_FIELD,
    WORKSPACE_ID_FIELD,
    CWD_FIELD,
    INTERACTIVE_READY_FIELD,
)

# Fields of the capability's requests and results.
SCHEMA_VERSION_FIELD = "schemaVersion"
OPERATION_FIELD = "operation"
ARGUMENTS_FIELD = "arguments"
STATUS_FIELD = "status"
DETAIL_FIELD = "detail"
COMMAND_FIELD = "command"
COMMAND_EXIT_CODE_FIELD = "commandExitCode"
RESPONSE_FIELD = "response"
ERROR_CODE_FIELD = "errorCode"
AGENT_FIELD = "agent"
PANE_FIELD = "pane"
TEXT_FIELD = "text"
KEYS_FIELD = "keys"
SOURCE_FIELD = "source"
LINES_FIELD = "lines"
UNTIL_FIELD = "until"
TIMEOUT_FIELD = "timeout"
WAIT_FIELD = "wait"
KIND_FIELD = "kind"
PATH_FIELD = "path"
AGENT_ARGUMENTS_FIELD = "agentArguments"
MUTATION_AUTHORIZED_FIELD = "mutationAuthorized"
PARTICIPANTS_FIELD = "participants"
PARTICIPANT_FIELD = "participant"

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
FAILURE_RESULT_OPTIONAL_FIELDS = frozenset({COMMAND_EXIT_CODE_FIELD, ERROR_CODE_FIELD})
SELECTOR_FIELDS = (AGENT_FIELD, PANE_FIELD)


class Operation(StrEnum):
    INVENTORY = "inventory"
    READ = "read"
    WAIT = "wait"
    PROMPT = "prompt"
    KEY = "key"
    START = "start"
    RELAUNCH = "relaunch"
    STOP = "stop"
    OPEN_WORKTREE = "open-worktree"


MUTATING_OPERATIONS = frozenset(
    {
        Operation.KEY,
        Operation.START,
        Operation.RELAUNCH,
        Operation.STOP,
        Operation.OPEN_WORKTREE,
    }
)
# Operations whose command waits on the agent; each carries an explicit timeout.
WAIT_BEARING_OPERATIONS = frozenset(
    {Operation.WAIT, Operation.START, Operation.RELAUNCH}
)


class AgentState(StrEnum):
    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    DONE = "done"
    UNKNOWN = "unknown"


class ReadSource(StrEnum):
    VISIBLE = "visible"
    RECENT = "recent"
    RECENT_UNWRAPPED = "recent-unwrapped"
    DETECTION = "detection"


class ExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    COMMAND_FAILED = "command-failed"
    INVALID_SCHEMA = "invalid-schema"
    SERVER_NOT_RUNNING = "server-not-running"
    IDENTITY_UNAVAILABLE = "identity-unavailable"
    IDENTITY_AMBIGUOUS = "identity-ambiguous"
    AGENT_NOT_READY = "agent-not-ready"
    AGENT_BLOCKED = "agent-blocked"
    PROMPT_STALLED = "prompt-stalled"
    WAIT_TIMEOUT = "wait-timeout"
    MUTATION_UNAUTHORIZED = "mutation-unauthorized"
    OPERATION_UNAVAILABLE = "operation-unavailable"


# The herdr error codes the operating workflows branch on, projected to a
# named status; every other code stays verbatim under command-failed.
HERDR_ERROR_STATUSES: Final[Mapping[str, ExecutionStatus]] = {
    "server_not_running": ExecutionStatus.SERVER_NOT_RUNNING,
    "agent_not_found": ExecutionStatus.IDENTITY_UNAVAILABLE,
    "agent_not_ready": ExecutionStatus.AGENT_NOT_READY,
    "agent_blocked": ExecutionStatus.AGENT_BLOCKED,
    "agent_prompt_stalled": ExecutionStatus.PROMPT_STALLED,
    "timeout": ExecutionStatus.WAIT_TIMEOUT,
}


class CliOperation(StrEnum):
    RUN = "run"


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


def _prompt_shapes() -> tuple[RequestShape, ...]:
    shapes: list[RequestShape] = []
    for selector in SELECTOR_FIELDS:
        base = frozenset({selector, TEXT_FIELD})
        shapes.append(RequestShape(base))
        shapes.append(
            RequestShape(base | {WAIT_FIELD, TIMEOUT_FIELD}, frozenset({UNTIL_FIELD}))
        )
    return tuple(shapes)


START_SHAPE = RequestShape(
    frozenset(
        {NAME_FIELD, KIND_FIELD, PANE_FIELD, TIMEOUT_FIELD, MUTATION_AUTHORIZED_FIELD}
    ),
    frozenset({AGENT_ARGUMENTS_FIELD}),
)
OPERATION_CONTRACTS: Final[Mapping[Operation, OperationContract]] = {
    Operation.INVENTORY: OperationContract((RequestShape(),)),
    Operation.READ: OperationContract(
        _selector_shapes(frozenset(), frozenset({SOURCE_FIELD, LINES_FIELD}))
    ),
    Operation.WAIT: OperationContract(
        _selector_shapes(frozenset({TIMEOUT_FIELD}), frozenset({UNTIL_FIELD}))
    ),
    Operation.PROMPT: OperationContract(_prompt_shapes()),
    Operation.KEY: OperationContract(
        _selector_shapes(frozenset({KEYS_FIELD, MUTATION_AUTHORIZED_FIELD}))
    ),
    Operation.START: OperationContract((START_SHAPE,)),
    Operation.RELAUNCH: OperationContract((START_SHAPE,)),
    Operation.STOP: OperationContract(
        (RequestShape(frozenset({PANE_FIELD, MUTATION_AUTHORIZED_FIELD})),)
    ),
    Operation.OPEN_WORKTREE: OperationContract(
        (RequestShape(frozenset({PATH_FIELD, MUTATION_AUTHORIZED_FIELD})),)
    ),
}
PUBLIC_HERDR_COMMAND_PREFIXES: Final[Mapping[Operation, tuple[str, ...]]] = {
    Operation.INVENTORY: (HERDR_COMMAND, AGENT_COMMAND, LIST_COMMAND),
    Operation.READ: (HERDR_COMMAND, AGENT_COMMAND, READ_COMMAND),
    Operation.WAIT: (HERDR_COMMAND, AGENT_COMMAND, WAIT_COMMAND),
    Operation.PROMPT: (HERDR_COMMAND, AGENT_COMMAND, PROMPT_COMMAND),
    Operation.KEY: (HERDR_COMMAND, AGENT_COMMAND, SEND_KEYS_COMMAND),
    Operation.START: (HERDR_COMMAND, AGENT_COMMAND, START_COMMAND),
    Operation.RELAUNCH: (HERDR_COMMAND, AGENT_COMMAND, START_COMMAND),
    Operation.STOP: (HERDR_COMMAND, PANE_COMMAND, CLOSE_COMMAND),
    Operation.OPEN_WORKTREE: (HERDR_COMMAND, WORKTREE_COMMAND, OPEN_COMMAND),
}
PUBLIC_HERDR_ARGUMENT_OPTIONS: Final[Mapping[str, str]] = {
    SOURCE_FIELD: SOURCE_OPTION,
    LINES_FIELD: LINES_OPTION,
    UNTIL_FIELD: UNTIL_OPTION,
    TIMEOUT_FIELD: TIMEOUT_OPTION,
    WAIT_FIELD: WAIT_OPTION,
    KIND_FIELD: KIND_OPTION,
    PANE_FIELD: PANE_OPTION,
    PATH_FIELD: PATH_OPTION,
}
INTEGER_BOUNDS: Final[Mapping[str, tuple[int, int]]] = {
    LINES_FIELD: (1, 100_000),
    TIMEOUT_FIELD: (1, 300_000),
}
BOOLEAN_ARGUMENT_FIELDS = frozenset({WAIT_FIELD, MUTATION_AUTHORIZED_FIELD})
TEXT_ARGUMENT_FIELDS = frozenset(
    {AGENT_FIELD, PANE_FIELD, TEXT_FIELD, NAME_FIELD, KIND_FIELD, PATH_FIELD}
)
TEXT_LIST_ARGUMENT_FIELDS = frozenset({KEYS_FIELD, UNTIL_FIELD, AGENT_ARGUMENTS_FIELD})
ARGUMENT_NAMES: Final[Mapping[str, str]] = {
    "agent": AGENT_FIELD,
    "pane": PANE_FIELD,
    "text": TEXT_FIELD,
    "keys": KEYS_FIELD,
    "source": SOURCE_FIELD,
    "lines": LINES_FIELD,
    "until": UNTIL_FIELD,
    "timeout": TIMEOUT_FIELD,
    "wait": WAIT_FIELD,
    "name": NAME_FIELD,
    "kind": KIND_FIELD,
    "path": PATH_FIELD,
    "agent_arguments": AGENT_ARGUMENTS_FIELD,
    "mutation_authorized": MUTATION_AUTHORIZED_FIELD,
}
RAW_HERDR_COMMAND_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bHERDR_COMMAND\b|[\[(]['\"]herdr['\"]"),
)
HERDR_HELP_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"herdr[^\n]*['\"](?:--help|--skill)['\"]"),
    re.compile(r"\bHERDR_COMMAND\b[^\n]*\bHELP_OPTION\b"),
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
        *,
        timeout_seconds: int = COMMAND_TIMEOUT_SECONDS,
    ) -> CommandResult: ...


class HerdrEnvironmentError(RuntimeError):
    def __init__(self, status: ExecutionStatus, message: str) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class SubprocessRunner:
    """Run one bounded, reaped command; absence and timeouts propagate as raised."""

    def run(
        self,
        argv: tuple[str, ...],
        stdin: str | None = None,
        *,
        timeout_seconds: int = COMMAND_TIMEOUT_SECONDS,
    ) -> CommandResult:
        completed = subprocess.run(
            argv,
            input=stdin,
            stdin=subprocess.DEVNULL if stdin is None else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an object at {location}."
        )
    return cast(dict[str, object], value)


def _array(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an array at {location}."
        )
    return cast(list[object], value)


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected non-empty text at {location}."
        )
    return value


def _text_list(value: object, location: str) -> list[str]:
    items = _array(value, location)
    if not items:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected a non-empty array at {location}."
        )
    return [_text(item, f"{location}[{index}]") for index, item in enumerate(items)]


def _boolean(value: object, location: str) -> bool:
    if not isinstance(value, bool):
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected a boolean at {location}."
        )
    return value


def _integer(value: object, location: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Expected an integer at {location}."
        )
    if not minimum <= value <= maximum:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Expected an integer between {minimum} and {maximum} at {location}.",
        )
    return value


def _operation(value: object) -> Operation:
    try:
        return Operation(_text(value, OPERATION_FIELD))
    except ValueError as error:
        valid = ", ".join(sorted(operation.value for operation in Operation))
        raise HerdrEnvironmentError(
            ExecutionStatus.OPERATION_UNAVAILABLE,
            f"Unsupported herdr operation: {value!r}. Valid operations: {valid}.",
        ) from error


def _agent_state(value: object, location: str) -> AgentState:
    try:
        return AgentState(_text(value, location))
    except ValueError as error:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"Unsupported agent state at {location}."
        ) from error


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
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request fields are invalid ({'; '.join(details)}).",
        )
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation request schema version must be {SCHEMA_VERSION}.",
        )
    operation = _operation(value.get(OPERATION_FIELD))
    arguments = _object(value.get(ARGUMENTS_FIELD), f"request.{ARGUMENTS_FIELD}")
    contract = OPERATION_CONTRACTS[operation]
    unexpected_arguments = sorted(set(arguments) - contract.allowed_fields)
    if unexpected_arguments:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} contains unsupported arguments: {', '.join(unexpected_arguments)}.",
        )
    if (
        operation in MUTATING_OPERATIONS
        and arguments.get(MUTATION_AUTHORIZED_FIELD) is not True
    ):
        raise HerdrEnvironmentError(
            ExecutionStatus.MUTATION_UNAUTHORIZED,
            f"{operation.value} requires {MUTATION_AUTHORIZED_FIELD}: true before command construction.",
        )
    if not any(
        shape.accepts(frozenset(arguments)) for shape in contract.request_shapes
    ):
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} arguments do not match a source-owned request shape; "
            f"accepted shapes: {_describe_shapes(contract)}.",
        )
    selectors = [field for field in SELECTOR_FIELDS if field in arguments]
    if (
        operation not in {Operation.INVENTORY, Operation.OPEN_WORKTREE}
        and len(selectors) != 1
    ):
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"{operation.value} requires exactly one selector: {', '.join(SELECTOR_FIELDS)}.",
        )
    location = f"request.{ARGUMENTS_FIELD}"
    for field_name in TEXT_ARGUMENT_FIELDS:
        if field_name in arguments:
            _text(arguments[field_name], f"{location}.{field_name}")
    for field_name in TEXT_LIST_ARGUMENT_FIELDS:
        if field_name in arguments:
            _text_list(arguments[field_name], f"{location}.{field_name}")
    for field_name in BOOLEAN_ARGUMENT_FIELDS:
        if field_name in arguments:
            _boolean(arguments[field_name], f"{location}.{field_name}")
    for field_name, (minimum, maximum) in INTEGER_BOUNDS.items():
        if field_name in arguments:
            _integer(
                arguments[field_name],
                f"{location}.{field_name}",
                minimum=minimum,
                maximum=maximum,
            )
    if UNTIL_FIELD in arguments:
        for index, state in enumerate(cast(list[object], arguments[UNTIL_FIELD])):
            _agent_state(state, f"{location}.{UNTIL_FIELD}[{index}]")
    if SOURCE_FIELD in arguments:
        try:
            ReadSource(str(arguments[SOURCE_FIELD]))
        except ValueError as error:
            raise HerdrEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                f"Unsupported read source at {location}.{SOURCE_FIELD}.",
            ) from error
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
            raise HerdrEnvironmentError(
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


def _target(arguments: dict[str, object]) -> str:
    for field_name in SELECTOR_FIELDS:
        value = arguments.get(field_name)
        if value is not None:
            return str(value)
    raise HerdrEnvironmentError(
        ExecutionStatus.INVALID_SCHEMA, "The request carries no selector."
    )


def command_for(request: object) -> tuple[str, ...]:
    """Map one checked request onto the exact herdr argument vector."""
    operation, arguments = _validated_request(request)
    options = PUBLIC_HERDR_ARGUMENT_OPTIONS
    command = list(PUBLIC_HERDR_COMMAND_PREFIXES[operation])
    if operation is Operation.INVENTORY:
        return tuple(command)
    if operation in {Operation.START, Operation.RELAUNCH}:
        command.append(str(arguments[NAME_FIELD]))
        for field_name in (KIND_FIELD, PANE_FIELD):
            command.extend((options[field_name], str(arguments[field_name])))
        command.extend((options[TIMEOUT_FIELD], str(arguments[TIMEOUT_FIELD])))
        if AGENT_ARGUMENTS_FIELD in arguments:
            command.append(AGENT_ARGUMENTS_SEPARATOR)
            command.extend(cast(list[str], arguments[AGENT_ARGUMENTS_FIELD]))
        return tuple(command)
    if operation is Operation.STOP:
        command.append(str(arguments[PANE_FIELD]))
        return tuple(command)
    if operation is Operation.OPEN_WORKTREE:
        command.extend(
            (options[PATH_FIELD], str(arguments[PATH_FIELD]), NO_FOCUS_OPTION)
        )
        return tuple(command)
    command.append(_target(arguments))
    if operation is Operation.READ:
        for field_name in (SOURCE_FIELD, LINES_FIELD):
            if field_name in arguments:
                command.extend((options[field_name], str(arguments[field_name])))
    elif operation is Operation.WAIT:
        for state in cast(list[str], arguments.get(UNTIL_FIELD, [])):
            command.extend((options[UNTIL_FIELD], state))
        command.extend((options[TIMEOUT_FIELD], str(arguments[TIMEOUT_FIELD])))
    elif operation is Operation.PROMPT:
        command.append(str(arguments[TEXT_FIELD]))
        if arguments.get(WAIT_FIELD) is True:
            command.append(options[WAIT_FIELD])
            for state in cast(list[str], arguments.get(UNTIL_FIELD, [])):
                command.extend((options[UNTIL_FIELD], state))
            command.extend((options[TIMEOUT_FIELD], str(arguments[TIMEOUT_FIELD])))
    elif operation is Operation.KEY:
        command.extend(cast(list[str], arguments[KEYS_FIELD]))
    return tuple(command)


def command_bound_seconds(request: object) -> int:
    """The subprocess bound for one request: above its own wait, never open."""
    _, arguments = _validated_request(request)
    timeout = arguments.get(TIMEOUT_FIELD)
    if isinstance(timeout, int) and not isinstance(timeout, bool):
        return -(-timeout // 1000) + WAIT_MARGIN_SECONDS
    return COMMAND_TIMEOUT_SECONDS


def participants_from_inventory(response: object) -> list[dict[str, object]]:
    """Project herdr's agent inventory onto complete source-preserved participants."""
    envelope = _object(response, RESPONSE_FIELD)
    result = _object(envelope.get(RESULT_FIELD), f"{RESPONSE_FIELD}.{RESULT_FIELD}")
    agents = _array(
        result.get(AGENTS_FIELD), f"{RESPONSE_FIELD}.{RESULT_FIELD}.{AGENTS_FIELD}"
    )
    participants: list[dict[str, object]] = []
    for index, item in enumerate(agents):
        location = f"{AGENTS_FIELD}[{index}]"
        agent = _object(item, location)
        participant: dict[str, object] = {}
        for field_name in PARTICIPANT_FIELDS:
            if field_name not in agent:
                raise HerdrEnvironmentError(
                    ExecutionStatus.INVALID_SCHEMA,
                    f"Agent evidence at {location} carries no {field_name}.",
                )
            participant[field_name] = agent[field_name]
        _text(participant[NAME_FIELD], f"{location}.{NAME_FIELD}")
        _text(participant[PANE_ID_FIELD], f"{location}.{PANE_ID_FIELD}")
        _agent_state(
            participant[AGENT_STATUS_FIELD], f"{location}.{AGENT_STATUS_FIELD}"
        )
        participants.append(participant)
    return participants


def participant_for(
    participants: list[dict[str, object]], selector: str
) -> dict[str, object]:
    """Select one participant by live agent name or pane id."""
    matches = [
        participant
        for participant in participants
        if participant[NAME_FIELD] == selector or participant[PANE_ID_FIELD] == selector
    ]
    if not matches:
        raise HerdrEnvironmentError(
            ExecutionStatus.IDENTITY_UNAVAILABLE,
            f"No hosted agent session matches {selector!r}.",
        )
    if len(matches) > 1:
        raise HerdrEnvironmentError(
            ExecutionStatus.IDENTITY_AMBIGUOUS,
            f"{len(matches)} hosted agent sessions match {selector!r}.",
        )
    return matches[0]


def raw_herdr_command_violations(sources: Mapping[str, str]) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in RAW_HERDR_COMMAND_PATTERNS)
    )


def herdr_help_violations(sources: Mapping[str, str]) -> list[str]:
    return sorted(
        name
        for name, text in sources.items()
        if any(pattern.search(text) for pattern in HERDR_HELP_PATTERNS)
    )


def validate_operation_result(result: object) -> dict[str, object]:
    """Return a result checked against the source-owned success or failure shape."""
    value = _object(result, "result")
    if value.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Operation result schema version must be {SCHEMA_VERSION}.",
        )
    operation_value = _text(value.get(OPERATION_FIELD), OPERATION_FIELD)
    try:
        status = ExecutionStatus(_text(value.get(STATUS_FIELD), STATUS_FIELD))
    except ValueError as error:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA,
            f"Unsupported operation result status: {value.get(STATUS_FIELD)!r}.",
        ) from error
    exit_bounds = {"minimum": -1_000_000, "maximum": 1_000_000}
    if status is ExecutionStatus.SUCCEEDED:
        if set(value) != SUCCESS_RESULT_FIELDS:
            raise HerdrEnvironmentError(
                ExecutionStatus.INVALID_SCHEMA,
                "Successful operation result fields do not match the source-owned schema.",
            )
        return {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: Operation(operation_value),
            STATUS_FIELD: status,
            COMMAND_EXIT_CODE_FIELD: _integer(
                value.get(COMMAND_EXIT_CODE_FIELD),
                f"result.{COMMAND_EXIT_CODE_FIELD}",
                **exit_bounds,
            ),
            RESPONSE_FIELD: _object(value.get(RESPONSE_FIELD), RESPONSE_FIELD),
        }
    allowed = FAILURE_RESULT_REQUIRED_FIELDS | FAILURE_RESULT_OPTIONAL_FIELDS
    if not FAILURE_RESULT_REQUIRED_FIELDS <= set(value) or set(value) - allowed:
        raise HerdrEnvironmentError(
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
            **exit_bounds,
        )
    if ERROR_CODE_FIELD in value:
        validated[ERROR_CODE_FIELD] = _text(value[ERROR_CODE_FIELD], ERROR_CODE_FIELD)
    return validated


def _failure_result(
    operation: str,
    status: ExecutionStatus,
    detail: str,
    command_exit_code: int | None = None,
    error_code: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        OPERATION_FIELD: operation,
        STATUS_FIELD: status,
        DETAIL_FIELD: detail,
    }
    if command_exit_code is not None:
        result[COMMAND_EXIT_CODE_FIELD] = command_exit_code
    if error_code is not None:
        result[ERROR_CODE_FIELD] = error_code
    return validate_operation_result(result)


def _error_envelope(text: str) -> tuple[str, str] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    error = payload.get(ERROR_FIELD)
    if not isinstance(error, dict):
        return None
    code = error.get(CODE_FIELD)
    message = error.get(MESSAGE_FIELD)
    if not isinstance(code, str) or not code:
        return None
    return code, message if isinstance(message, str) and message else code


def execute(request: object, runner: CommandRunner) -> dict[str, object]:
    """Run one herdr command and return the checked, projected result."""
    operation_value = "unknown"
    try:
        raw = _object(request, "request")
        candidate = raw.get(OPERATION_FIELD)
        if isinstance(candidate, str) and candidate:
            operation_value = candidate
        operation, _ = _validated_request(request)
        command = command_for(request)
        bound = command_bound_seconds(request)
    except HerdrEnvironmentError as error:
        return _failure_result(operation_value, error.status, str(error))
    try:
        result = runner.run(command, timeout_seconds=bound)
    except FileNotFoundError:
        return _failure_result(
            operation.value,
            ExecutionStatus.SERVER_NOT_RUNNING,
            "herdr is unavailable on this machine; no herdr server can be reached.",
        )
    except subprocess.TimeoutExpired:
        return _failure_result(
            operation.value,
            ExecutionStatus.COMMAND_FAILED,
            f"herdr command exceeded the {bound}-second bound: {' '.join(command)}",
        )
    if result.returncode != 0:
        envelope = _error_envelope(result.stderr.strip()) or _error_envelope(
            result.stdout.strip()
        )
        if envelope is None:
            detail = (
                result.stderr.strip() or result.stdout.strip() or "no command detail"
            )
            return _failure_result(
                operation.value,
                ExecutionStatus.COMMAND_FAILED,
                detail,
                result.returncode,
            )
        code, message = envelope
        return _failure_result(
            operation.value,
            HERDR_ERROR_STATUSES.get(code, ExecutionStatus.COMMAND_FAILED),
            message,
            result.returncode,
            code,
        )
    try:
        response = _object(json.loads(result.stdout), RESPONSE_FIELD)
    except (json.JSONDecodeError, HerdrEnvironmentError) as error:
        return _failure_result(
            operation.value,
            ExecutionStatus.INVALID_SCHEMA,
            f"herdr returned an unexpected response: {error}",
            result.returncode,
        )
    return validate_operation_result(
        {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            OPERATION_FIELD: operation,
            STATUS_FIELD: ExecutionStatus.SUCCEEDED,
            COMMAND_EXIT_CODE_FIELD: result.returncode,
            RESPONSE_FIELD: response,
        }
    )


def _json_input(stream: TextIO, location: str) -> dict[str, object]:
    try:
        return _object(json.load(stream), location)
    except json.JSONDecodeError as error:
        raise HerdrEnvironmentError(
            ExecutionStatus.INVALID_SCHEMA, f"{location} is not valid JSON: {error.msg}"
        ) from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="herdr_environment")
    parser.add_argument("cli_operation", choices=[op.value for op in CliOperation])
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    _parser().parse_args(argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    runner = SubprocessRunner() if runner is None else runner
    try:
        request = _json_input(stdin, "request")
    except HerdrEnvironmentError as error:
        json.dump({STATUS_FIELD: error.status, DETAIL_FIELD: str(error)}, stdout)
        stdout.write("\n")
        return 2
    result = execute(request, runner)
    json.dump(result, stdout)
    stdout.write("\n")
    return 0 if result[STATUS_FIELD] is ExecutionStatus.SUCCEEDED else 1


if __name__ == "__main__":
    sys.exit(main())
