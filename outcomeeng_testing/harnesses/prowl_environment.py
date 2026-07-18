"""Test infrastructure for the shipped Prowl environment adapter."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_testing.generators.prowl_environment import (
    agent_identity,
    coordination_references,
    operation_requests,
    public_agent_item,
    result_forms,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
PROWL_ENVIRONMENT_PATH = (
    ROOT / "src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py"
)
CODING_AGENTS_SOURCE = ROOT / "src/plugins/coding-agents"
OPERATE_PROWL_SOURCE = CODING_AGENTS_SOURCE / "skills/operate-prowl"
PROPERTY_SEED = 2026071801
PROPERTY_EXAMPLES = 40
PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_environment.property.l1.py"
)


class CommandResultContract(Protocol):
    returncode: int
    stdout: str
    stderr: str


@dataclass
class RecordingRunner:
    results: list[CommandResultContract]
    calls: list[tuple[tuple[str, ...], str | None]] = field(default_factory=list)

    def run(
        self, argv: tuple[str, ...], stdin: str | None = None
    ) -> CommandResultContract:
        self.calls.append((argv, stdin))
        if not self.results:
            raise AssertionError(f"Unexpected command: {argv}")
        return self.results.pop(0)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "coding_agents_prowl_environment", PROWL_ENVIRONMENT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load Prowl environment module: {PROWL_ENVIRONMENT_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _selector(module: ModuleType, arguments: dict[str, object]) -> list[str]:
    command: list[str] = []
    for field_name, option in (
        (module.TARGET_FIELD, module.TARGET_OPTION),
        (module.WORKTREE_FIELD, module.WORKTREE_OPTION),
        (module.TAB_FIELD, module.TAB_OPTION),
        (module.PANE_FIELD, module.PANE_OPTION),
    ):
        value = arguments.get(field_name)
        if value is not None:
            command.extend((option, cast(str, value)))
    return command


def _expected_command(
    module: ModuleType, request: dict[str, object]
) -> tuple[str, ...]:
    operation = module.Operation(request[module.OPERATION_FIELD])
    arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
    if operation is module.Operation.LIST:
        return (module.PROWL_COMMAND, module.LIST_COMMAND, module.JSON_OPTION)
    if operation is module.Operation.AGENTS:
        return (module.PROWL_COMMAND, module.AGENTS_COMMAND, module.JSON_OPTION)
    if operation is module.Operation.OPEN:
        command = [module.PROWL_COMMAND, module.OPEN_COMMAND, module.JSON_OPTION]
        if arguments.get(module.PATH_FIELD) is not None:
            command.append(cast(str, arguments[module.PATH_FIELD]))
        return tuple(command)

    if operation is module.Operation.TAB_CREATE:
        command = [module.PROWL_COMMAND, module.TAB_COMMAND, module.CREATE_COMMAND]
    elif operation is module.Operation.TAB_CLOSE:
        command = [module.PROWL_COMMAND, module.TAB_COMMAND, module.CLOSE_COMMAND]
    elif operation is module.Operation.PANE_CLOSE:
        command = [module.PROWL_COMMAND, module.PANE_COMMAND, module.CLOSE_COMMAND]
    else:
        command = [module.PROWL_COMMAND, operation.value]
    command.extend(_selector(module, arguments))
    command.append(module.JSON_OPTION)

    if operation is module.Operation.READ:
        for field_name, option in (
            (module.LAST_FIELD, module.LAST_OPTION),
            (module.STABLE_INTERVAL_FIELD, module.STABLE_INTERVAL_OPTION),
            (module.STABLE_PERIOD_FIELD, module.STABLE_PERIOD_OPTION),
            (module.WAIT_TIMEOUT_FIELD, module.WAIT_TIMEOUT_OPTION),
        ):
            value = arguments.get(field_name)
            if value is not None:
                command.extend((option, str(value)))
        if arguments.get(module.WAIT_STABLE_FIELD) is True:
            command.append(module.WAIT_STABLE_OPTION)
    elif operation is module.Operation.SEND:
        for field_name, option in (
            (module.NO_ENTER_FIELD, module.NO_ENTER_OPTION),
            (module.NO_WAIT_FIELD, module.NO_WAIT_OPTION),
            (module.CAPTURE_FIELD, module.CAPTURE_OPTION),
        ):
            if arguments.get(field_name) is True:
                command.append(option)
        if arguments.get(module.TIMEOUT_FIELD) is not None:
            command.extend(
                (module.TIMEOUT_OPTION, str(arguments[module.TIMEOUT_FIELD]))
            )
        command.append(cast(str, arguments[module.TEXT_FIELD]))
    elif operation is module.Operation.KEY:
        if arguments.get(module.REPEAT_FIELD) is not None:
            command.extend((module.REPEAT_OPTION, str(arguments[module.REPEAT_FIELD])))
        command.append(cast(str, arguments[module.KEY_FIELD]))
    elif operation is module.Operation.TAB_CREATE:
        if arguments.get(module.PATH_FIELD) is not None:
            command.extend(
                (module.PATH_OPTION, cast(str, arguments[module.PATH_FIELD]))
            )
    elif operation in {module.Operation.TAB_CLOSE, module.Operation.PANE_CLOSE}:
        if arguments.get(module.FORCE_FIELD) is True:
            command.append(module.FORCE_OPTION)
    return tuple(command)


def verify_prowl_mappings() -> list[str]:
    module = _load()
    failures: list[str] = []
    requests = operation_requests(module)
    observed_operations = {
        module.Operation(request[module.OPERATION_FIELD]) for request in requests
    }
    if observed_operations != set(module.Operation):
        failures.append(
            "operation requests do not cover the complete Prowl command surface"
        )
    for request in requests:
        actual = module.command_for(request)
        expected = _expected_command(module, request)
        if actual != expected:
            failures.append(
                f"{request[module.OPERATION_FIELD]} mapped to {actual!r}, expected {expected!r}"
            )
        if module.HELP_OPTION in actual:
            failures.append("an operation command invoked Prowl help")

    public_item = public_agent_item(module, ordinal=1)
    projected = module.participant_from_agent(public_item)
    if projected != agent_identity(module, ordinal=1):
        failures.append("public Prowl identity fields were not preserved")

    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)
    reference = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    delegation = module.delegation_request(
        sender=sender,
        recipient=recipient,
        subject="run bounded audits",
        instruction="return the exact audit results",
        coordination_reference=reference,
    )
    for terminal_kind in module.TerminalKind:
        terminal = module.terminal_handback(
            delegation,
            terminal_kind,
            inline_result=f"{terminal_kind.value} result",
        )
        if terminal[module.COORDINATION_REFERENCE_FIELD] != reference:
            failures.append(f"{terminal_kind.value} did not preserve correlation")
        if terminal[module.KIND_FIELD] != terminal_kind:
            failures.append(f"{terminal_kind.value} mapped to the wrong terminal kind")
        if terminal[module.SENDER_FIELD] != recipient:
            failures.append(
                f"{terminal_kind.value} did not preserve the producing agent"
            )
        if terminal[module.RECIPIENT_FIELD] != sender:
            failures.append(
                f"{terminal_kind.value} did not target the delegating agent"
            )
        delivery = module.delegation_delivery_request(terminal)
        delivery_arguments = cast(dict[str, object], delivery[module.ARGUMENTS_FIELD])
        if delivery_arguments[module.PANE_FIELD] != sender[module.PANE_FIELD]:
            failures.append(f"{terminal_kind.value} delivery targeted the wrong pane")
    return failures


def verify_prowl_conformance() -> list[str]:
    module = _load()
    failures: list[str] = []
    request = module.operation_request(module.Operation.LIST)
    response = {
        module.OK_FIELD: True,
        module.COMMAND_FIELD: module.Operation.LIST,
        module.SCHEMA_VERSION_SNAKE_FIELD: "prowl.cli.list.v1",
        module.DATA_FIELD: {
            module.STATUS_FIELD: "terminal-green",
            module.CONCLUSION_FIELD: "success",
            module.ID_FIELD: "identity-verbatim",
        },
    }
    success_runner = RecordingRunner(
        [module.CommandResult(0, json.dumps(response), "")]
    )
    success = module.execute(request, success_runner)
    if success[module.STATUS_FIELD] != module.ExecutionStatus.SUCCEEDED:
        failures.append("valid public JSON did not map to succeeded")
    if success[module.RESPONSE_FIELD] != response:
        failures.append("public Prowl response values were rewritten")
    if success[module.COMMAND_EXIT_CODE_FIELD] != 0:
        failures.append("successful command exit code was not preserved")

    failure_cases = (
        (
            module.CommandResult(7, "", "command failed"),
            module.ExecutionStatus.COMMAND_FAILED,
        ),
        (
            module.CommandResult(0, "{", ""),
            module.ExecutionStatus.INVALID_SCHEMA,
        ),
        (
            module.CommandResult(
                0,
                json.dumps(
                    {
                        module.OK_FIELD: False,
                        module.ERROR_FIELD: {module.MESSAGE_FIELD: "not accepted"},
                    }
                ),
                "",
            ),
            module.ExecutionStatus.COMMAND_FAILED,
        ),
    )
    for command_result, expected_status in failure_cases:
        result = module.execute(request, RecordingRunner([command_result]))
        if result[module.STATUS_FIELD] != expected_status:
            failures.append(
                f"command result mapped to {result[module.STATUS_FIELD]}, expected {expected_status}"
            )
        if result[module.COMMAND_EXIT_CODE_FIELD] != command_result.returncode:
            failures.append("failure result did not preserve the checked exit code")
    return failures


def verify_prowl_properties() -> list[str]:
    module = _load()
    failures: list[str] = []
    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)

    @seed(PROPERTY_SEED)
    @settings(max_examples=PROPERTY_EXAMPLES, deadline=None, print_blob=True)
    @given(
        reference=coordination_references(),
        terminal_kind=st.sampled_from(tuple(module.TerminalKind)),
        result_form=result_forms(),
    )
    def generated_terminal_property(
        reference: str,
        terminal_kind: object,
        result_form: tuple[str | None, str | None, str | None],
    ) -> None:
        inline_result, result_reference, projection = result_form
        delegation = module.delegation_request(
            sender=sender,
            recipient=recipient,
            subject="property delegation",
            instruction="return terminal evidence",
            coordination_reference=reference,
        )
        terminal = module.terminal_handback(
            delegation,
            terminal_kind,
            inline_result=inline_result,
            result_reference=result_reference,
            projection=projection,
        )
        first = module.reduce_terminal(None, terminal)
        repeated = module.reduce_terminal(first, terminal)
        if repeated != first:
            failures.append("matching terminal handback was not idempotent")
        conflicting_kind = next(
            kind for kind in module.TerminalKind if kind is not terminal_kind
        )
        conflict = module.terminal_handback(
            delegation,
            conflicting_kind,
            inline_result="conflicting terminal result",
        )
        try:
            module.reduce_terminal(first, conflict)
            failures.append("conflicting terminal handback was accepted")
        except module.ProwlEnvironmentError as error:
            if error.status != module.ExecutionStatus.INVALID_SCHEMA:
                failures.append(
                    f"conflicting terminal mapped to unexpected status {error.status}"
                )

    run_replayable_property(
        generated_terminal_property,
        seed_value=PROPERTY_SEED,
        replay_path=PROPERTY_REPLAY_PATH,
    )
    return failures


def _raw_prowl_violations() -> list[str]:
    violations: list[str] = []
    raw_python = re.compile(r"PROWL_COMMAND|[\[(]['\"]prowl['\"]")
    raw_markdown = re.compile(r"`prowl(?:\s|`)|\bprowl-cli\b")
    for path in sorted(CODING_AGENTS_SOURCE.rglob("*")):
        if not path.is_file() or OPERATE_PROWL_SOURCE in path.parents:
            continue
        if path.suffix not in {".py", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        pattern = raw_python if path.suffix == ".py" else raw_markdown
        if pattern.search(text):
            violations.append(str(path.relative_to(ROOT)))
    return violations


def verify_prowl_compliance() -> list[str]:
    module = _load()
    failures: list[str] = []
    requests = operation_requests(module)
    for request in requests:
        operation = module.Operation(request[module.OPERATION_FIELD])
        if operation not in module.MUTATING_OPERATIONS:
            continue
        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        arguments.pop(module.MUTATION_AUTHORIZED_FIELD, None)
        unauthorized = {**request, module.ARGUMENTS_FIELD: arguments}
        try:
            module.command_for(unauthorized)
            failures.append(f"{operation.value} ran without mutation authorization")
        except module.ProwlEnvironmentError as error:
            if error.status != module.ExecutionStatus.MUTATION_UNAUTHORIZED:
                failures.append(
                    f"{operation.value} authorization failure mapped to {error.status}"
                )

    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)
    delegation = module.delegation_request(
        sender=sender,
        recipient=recipient,
        subject="result-shape evidence",
        instruction="return one terminal result",
        coordination_reference=str(uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")),
    )
    invalid_result_forms: tuple[dict[str, str], ...] = (
        {},
        {module.RESULT_REFERENCE_FIELD: "result://missing-projection"},
        {module.PROJECTION_FIELD: "projection without reference"},
    )
    for invalid_fields in invalid_result_forms:
        try:
            module.terminal_handback(
                delegation,
                module.TerminalKind.COMPLETED,
                **module.result_form_arguments(invalid_fields),
            )
            failures.append("invalid terminal result form was accepted")
        except module.ProwlEnvironmentError as error:
            if error.status != module.ExecutionStatus.INVALID_SCHEMA:
                failures.append(f"invalid result form mapped to {error.status}")

    violations = _raw_prowl_violations()
    if violations:
        failures.append(
            "raw Prowl command construction remains outside /operate-prowl: "
            + ", ".join(violations)
        )
    return failures
