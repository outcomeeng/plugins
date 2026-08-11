"""Test infrastructure for the shipped Prowl environment adapter."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_testing.generators.prowl_environment import (
    agent_identity,
    coordination_references,
    delegation_text_case,
    operation_requests,
    public_agent_item,
    public_prowl_operation_names,
    result_forms,
    subprocess_input_texts,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

ROOT = Path(__file__).parents[2]
PROWL_ENVIRONMENT_PATH = (
    ROOT / "src/plugins/coding-agents/skills/operate-prowl/scripts/prowl_environment.py"
)
CODING_AGENTS_RUNTIME_ROOTS = (
    ROOT / "src/plugins/coding-agents",
    ROOT / "dist/claude/coding-agents",
    ROOT / "dist/codex/coding-agents",
)
OPERATE_PROWL_RELATIVE = Path("skills/operate-prowl")
RAW_PROWL_VIOLATION_FIXTURE = (
    ROOT / "outcomeeng_testing/fixtures/prowl_environment/raw_prowl_command.py.txt"
)
PROPERTY_SEED = 2026071801
PROPERTY_EXAMPLES = 40
PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_environment.property.l1.py"
)
SUBPROCESS_INPUT_PROPERTY_SEED = 2026081101
SUBPROCESS_INPUT_PROPERTY_EXAMPLES = 40
SUBPROCESS_INPUT_PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/18-prowl-environment.enabler/tests/"
    "test_prowl_subprocess_input.property.l1.py"
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


def observe_delegation_cli_fields(extra_key: str | None) -> str | None:
    """Submit a delegation request over the CLI path and report the outcome.

    Returns None when the request is accepted, or the error detail when the
    adapter rejects it. The caller owns the pass/fail predicate.
    """
    module = _load()
    sender = agent_identity(module, 0)
    recipient = agent_identity(module, 1)
    request: dict[str, object] = {
        "sender": sender,
        "recipient": recipient,
        "subject": "bounded subject",
        "instruction": "bounded instruction",
        "coordinationReference": None,
    }
    if extra_key is not None:
        request[extra_key] = {"pane": sender["pane"]}
    try:
        module._delegation_from_cli(request)
    except module.ProwlEnvironmentError as error:
        return str(error)
    return None


def observe_delegation_sender_pane() -> tuple[str, str]:
    """Return the submitted sender pane and the pane the envelope carries."""
    module = _load()
    sender = agent_identity(module, 0)
    envelope = module._delegation_from_cli(
        {
            "sender": sender,
            "recipient": agent_identity(module, 1),
            "subject": "bounded subject",
            "instruction": "bounded instruction",
            "coordinationReference": None,
        }
    )
    carried = cast(dict[str, object], envelope["sender"])
    return sender["pane"], cast(str, carried["pane"])


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


def load_prowl_environment() -> ModuleType:
    """Load the shipped adapter so linked tests can inspect its public contract."""
    return _load()


def prowl_agents_command_result(
    module: ModuleType, agents: list[dict[str, object]]
) -> CommandResultContract:
    """Return one controlled public agents response from the Prowl boundary."""
    return cast(
        CommandResultContract,
        module.CommandResult(
            0,
            json.dumps(
                {
                    module.OK_FIELD: True,
                    module.DATA_FIELD: {module.AGENTS_FIELD: agents},
                }
            ),
            "",
        ),
    )


def prowl_send_command_result(
    module: ModuleType, *, trailing_enter_sent: bool
) -> CommandResultContract:
    """Return one controlled public send response from the Prowl boundary."""
    return cast(
        CommandResultContract,
        module.CommandResult(
            0,
            json.dumps(
                {
                    module.OK_FIELD: True,
                    module.DATA_FIELD: {
                        module.INPUT_FIELD: {
                            module.TRAILING_ENTER_SENT_FIELD: trailing_enter_sent
                        }
                    },
                },
            ),
            "",
        ),
    )


def _selector(module: ModuleType, arguments: dict[str, object]) -> list[str]:
    command: list[str] = []
    for field_name in module.SELECTOR_FIELDS:
        public_option = module.PUBLIC_PROWL_SELECTOR_OPTIONS[field_name]
        value = arguments.get(field_name)
        if value is not None:
            command.extend((public_option, cast(str, value)))
    return command


def _expected_command(
    module: ModuleType, request: dict[str, object]
) -> tuple[str, ...]:
    operation = module.Operation(request[module.OPERATION_FIELD])
    arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
    command = list(module.PUBLIC_PROWL_COMMAND_PREFIXES[operation])
    if operation in {module.Operation.LIST, module.Operation.AGENTS}:
        return (*command, module.PUBLIC_PROWL_JSON_OPTION)
    if operation is module.Operation.OPEN:
        command.append(module.PUBLIC_PROWL_JSON_OPTION)
        if arguments.get(module.PATH_FIELD) is not None:
            command.append(cast(str, arguments[module.PATH_FIELD]))
        return tuple(command)

    command.extend(_selector(module, arguments))
    command.append(module.PUBLIC_PROWL_JSON_OPTION)

    if operation is module.Operation.READ:
        for field_name in (
            module.LAST_FIELD,
            module.STABLE_INTERVAL_FIELD,
            module.STABLE_PERIOD_FIELD,
            module.WAIT_TIMEOUT_FIELD,
        ):
            public_option = module.PUBLIC_PROWL_ARGUMENT_OPTIONS[field_name]
            value = arguments.get(field_name)
            if value is not None:
                command.extend((public_option, str(value)))
        if arguments.get(module.WAIT_STABLE_FIELD) is True:
            command.append(
                module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.WAIT_STABLE_FIELD]
            )
    elif operation is module.Operation.SEND:
        for field_name in (
            module.NO_ENTER_FIELD,
            module.NO_WAIT_FIELD,
            module.CAPTURE_FIELD,
        ):
            public_option = module.PUBLIC_PROWL_ARGUMENT_OPTIONS[field_name]
            if arguments.get(field_name) is True:
                command.append(public_option)
        if arguments.get(module.TIMEOUT_FIELD) is not None:
            command.extend(
                (
                    module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.TIMEOUT_FIELD],
                    str(arguments[module.TIMEOUT_FIELD]),
                )
            )
        command.append(cast(str, arguments[module.TEXT_FIELD]))
    elif operation is module.Operation.KEY:
        if arguments.get(module.REPEAT_FIELD) is not None:
            command.extend(
                (
                    module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.REPEAT_FIELD],
                    str(arguments[module.REPEAT_FIELD]),
                )
            )
        command.append(cast(str, arguments[module.KEY_FIELD]))
    elif operation is module.Operation.TAB_CREATE:
        if arguments.get(module.PATH_FIELD) is not None:
            command.extend(
                (
                    module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.PATH_FIELD],
                    cast(str, arguments[module.PATH_FIELD]),
                )
            )
    elif operation in {module.Operation.TAB_CLOSE, module.Operation.PANE_CLOSE}:
        if arguments.get(module.FORCE_FIELD) is True:
            command.append(module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.FORCE_FIELD])
    return tuple(command)


def verify_prowl_mappings() -> list[str]:
    module = _load()
    failures: list[str] = []
    requests = operation_requests(module)
    required_operations = set(public_prowl_operation_names(module))
    declared_operations = {operation.value for operation in module.Operation}
    if declared_operations != required_operations:
        failures.append(
            "adapter operation registry differs from the required public Prowl surface"
        )
    observed_operations = {str(request[module.OPERATION_FIELD]) for request in requests}
    if observed_operations != required_operations:
        failures.append(
            "operation requests do not cover the required public Prowl surface"
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
        operation = module.Operation(request[module.OPERATION_FIELD])
        response = {
            module.OK_FIELD: True,
            module.COMMAND_FIELD: operation,
            module.SCHEMA_VERSION_SNAKE_FIELD: f"prowl.cli.{operation.value}.v1",
            module.DATA_FIELD: {module.ID_FIELD: f"{operation.value}-response"},
        }
        executed = module.execute(
            request,
            RecordingRunner([module.CommandResult(0, json.dumps(response), "")]),
        )
        if executed[module.STATUS_FIELD] != module.ExecutionStatus.SUCCEEDED:
            failures.append(
                f"{operation.value} did not produce a checked success result"
            )
        if executed[module.OPERATION_FIELD] != operation:
            failures.append(f"{operation.value} checked result changed the operation")
        if executed[module.RESPONSE_FIELD] != response:
            failures.append(f"{operation.value} checked result rewrote the response")

        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        selected = [field for field in module.SELECTOR_FIELDS if field in arguments]
        if selected:
            without_selector = {
                **request,
                module.ARGUMENTS_FIELD: {
                    field: value
                    for field, value in arguments.items()
                    if field not in module.SELECTOR_FIELDS
                },
            }
            selectorless_fields = frozenset(
                cast(dict[str, object], without_selector[module.ARGUMENTS_FIELD])
            )
            selectorless_allowed = any(
                shape.accepts(selectorless_fields)
                for shape in module.OPERATION_CONTRACTS[operation].request_shapes
            )
            try:
                module.command_for(without_selector)
                if not selectorless_allowed:
                    failures.append(
                        f"{operation.value} accepted a request without its required selector"
                    )
            except module.ProwlEnvironmentError as error:
                if selectorless_allowed:
                    failures.append(
                        f"{operation.value} rejected its declared selectorless shape"
                    )
                elif error.status != module.ExecutionStatus.INVALID_SCHEMA:
                    failures.append(
                        f"{operation.value} selector omission mapped to {error.status}"
                    )

            second_selector = next(
                field for field in module.SELECTOR_FIELDS if field not in selected
            )
            combined_selectors = {
                **request,
                module.ARGUMENTS_FIELD: {
                    **arguments,
                    second_selector: f"combined-{second_selector}",
                },
            }
            try:
                module.command_for(combined_selectors)
                failures.append(
                    f"{operation.value} accepted conflicting target selectors"
                )
            except module.ProwlEnvironmentError as error:
                if error.status != module.ExecutionStatus.INVALID_SCHEMA:
                    failures.append(
                        f"{operation.value} selector conflict mapped to {error.status}"
                    )

        if operation is module.Operation.SEND and arguments.get(module.NO_WAIT_FIELD):
            conflicting_send = {
                **request,
                module.ARGUMENTS_FIELD: {
                    **arguments,
                    module.CAPTURE_FIELD: True,
                },
            }
            try:
                module.command_for(conflicting_send)
                failures.append("send accepted conflicting no-wait and capture shapes")
            except module.ProwlEnvironmentError as error:
                if error.status != module.ExecutionStatus.INVALID_SCHEMA:
                    failures.append(f"send shape conflict mapped to {error.status}")

    public_item = public_agent_item(module, ordinal=1)
    projected = module.participant_from_agent(public_item)
    if projected != agent_identity(module, ordinal=1):
        failures.append("public Prowl identity fields were not preserved")
    public_payload = {module.DATA_FIELD: {module.AGENTS_FIELD: [public_item]}}
    projection = module.participant_projection(public_payload)
    if projection[module.STATUS_FIELD] != module.ExecutionStatus.SUCCEEDED:
        failures.append("valid public agent evidence did not map to success")
    if projection[module.PARTICIPANTS_FIELD] != [projected]:
        failures.append("public agent projection rewrote preserved identities")
    unavailable_payloads: tuple[dict[str, object], ...] = (
        {},
        {module.DATA_FIELD: {module.AGENTS_FIELD: []}},
        {module.DATA_FIELD: {module.AGENTS_FIELD: [{}]}},
    )
    for unavailable_payload in unavailable_payloads:
        unavailable = module.participant_projection(unavailable_payload)
        if (
            unavailable[module.STATUS_FIELD]
            != module.ExecutionStatus.IDENTITY_UNAVAILABLE
        ):
            failures.append("unusable public agent evidence lacked unavailable result")
    ambiguous_payload = {
        module.DATA_FIELD: {module.AGENTS_FIELD: [public_item, {**public_item}]}
    }
    ambiguous = module.participant_projection(ambiguous_payload)
    if ambiguous[module.STATUS_FIELD] != module.ExecutionStatus.IDENTITY_AMBIGUOUS:
        failures.append("duplicate public pane identities lacked ambiguous result")

    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)
    reference = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    delegation_text = delegation_text_case(1)
    delegation = module.delegation_request(
        sender=sender,
        recipient=recipient,
        subject=delegation_text.subject,
        instruction=delegation_text.instruction,
        coordination_reference=reference,
    )
    for terminal_kind in module.TerminalKind:
        terminal = module.terminal_handback(
            delegation,
            terminal_kind,
            inline_result=f"{delegation_text.inline_result}: {terminal_kind.value}",
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
        reduced = module.reduce_terminal(None, terminal)
        if reduced != terminal:
            failures.append(
                f"{terminal_kind.value} did not reduce to one exact terminal outcome"
            )
        delivery = module.delegation_delivery_request(terminal)
        delivery_arguments = cast(dict[str, object], delivery[module.ARGUMENTS_FIELD])
        if delivery_arguments[module.PANE_FIELD] != sender[module.PANE_FIELD]:
            failures.append(f"{terminal_kind.value} delivery targeted the wrong pane")
        durable = module.terminal_handback(
            delegation,
            terminal_kind,
            result_reference=(
                f"{delegation_text.result_reference}-{terminal_kind.value}"
            ),
            projection=f"{delegation_text.projection}: {terminal_kind.value}",
        )
        if durable[module.RESULT_REFERENCE_FIELD] != (
            f"{delegation_text.result_reference}-{terminal_kind.value}"
        ):
            failures.append(f"{terminal_kind.value} did not preserve durable reference")
        if (
            durable[module.PROJECTION_FIELD]
            != f"{delegation_text.projection}: {terminal_kind.value}"
        ):
            failures.append(
                f"{terminal_kind.value} did not preserve bounded projection"
            )
    return failures


def run_subprocess_input_probe(input_text: str | None) -> CommandResultContract:
    """Run a child that reports how the default runner connected stdin."""
    module = _load()
    return cast(
        CommandResultContract,
        module.SubprocessRunner().run(
            (
                sys.executable,
                "-c",
                """
import json
import os
import stat
import sys

print(json.dumps({
    "isCharDevice": stat.S_ISCHR(os.fstat(0).st_mode),
    "input": sys.stdin.read(),
}))
""",
            ),
            stdin=input_text,
        ),
    )


def run_subprocess_input_property(assert_input: Callable[[str], None]) -> None:
    """Drive generated explicit input while the linked test owns its predicate."""

    @seed(SUBPROCESS_INPUT_PROPERTY_SEED)
    @settings(
        max_examples=SUBPROCESS_INPUT_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(input_text=subprocess_input_texts())
    def generated_input_property(input_text: str) -> None:
        assert_input(input_text)

    run_replayable_property(
        generated_input_property,
        seed_value=SUBPROCESS_INPUT_PROPERTY_SEED,
        replay_path=SUBPROCESS_INPUT_PROPERTY_REPLAY_PATH,
    )


def verify_prowl_conformance() -> list[str]:
    module = _load()
    failures: list[str] = []
    requests = operation_requests(module)
    for request in requests:
        operation = module.Operation(request[module.OPERATION_FIELD])
        response = {
            module.OK_FIELD: True,
            module.COMMAND_FIELD: operation,
            module.SCHEMA_VERSION_SNAKE_FIELD: f"prowl.cli.{operation.value}.v1",
            module.DATA_FIELD: {
                module.STATUS_FIELD: "terminal-green",
                module.CONCLUSION_FIELD: "success",
                module.ID_FIELD: f"{operation.value}-identity-verbatim",
            },
        }
        output_stream = StringIO()
        cli_exit_code = module.main(
            [module.CliOperation.RUN.value],
            runner=RecordingRunner([module.CommandResult(0, json.dumps(response), "")]),
            stdin=StringIO(json.dumps(request)),
            stdout=output_stream,
        )
        rendered = output_stream.getvalue()
        if rendered.count("\n") != 1:
            failures.append(
                f"{operation.value} CLI emitted more or less than one JSON document"
            )
        try:
            success = json.loads(rendered)
        except json.JSONDecodeError as error:
            failures.append(
                f"{operation.value} CLI emitted malformed JSON: {error.msg}"
            )
            continue
        if cli_exit_code != 0:
            failures.append(f"{operation.value} CLI success exited {cli_exit_code}")
        try:
            validated = module.validate_operation_result(success, operation)
        except module.ProwlEnvironmentError as error:
            failures.append(f"{operation.value} result failed source schema: {error}")
            continue
        if validated[module.STATUS_FIELD] != module.ExecutionStatus.SUCCEEDED:
            failures.append(f"{operation.value} public JSON did not map to succeeded")
        if validated[module.RESPONSE_FIELD] != response:
            failures.append(f"{operation.value} public response values were rewritten")
        if validated[module.COMMAND_EXIT_CODE_FIELD] != 0:
            failures.append(f"{operation.value} command exit code was not preserved")

    request = module.operation_request(module.Operation.LIST)
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
        try:
            validated = module.validate_operation_result(result, module.Operation.LIST)
        except module.ProwlEnvironmentError as error:
            failures.append(f"failure result did not conform to source schema: {error}")
            continue
        if validated[module.STATUS_FIELD] != expected_status:
            failures.append(
                f"command result mapped to {validated[module.STATUS_FIELD]}, expected {expected_status}"
            )
        if validated[module.COMMAND_EXIT_CODE_FIELD] != command_result.returncode:
            failures.append("failure result did not preserve the checked exit code")
    return failures


def verify_prowl_properties() -> list[str]:
    module = _load()
    failures: list[str] = []
    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)
    property_text = delegation_text_case(2)

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
            subject=property_text.subject,
            instruction=property_text.instruction,
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
            inline_result=property_text.inline_result,
        )
        conflicts = (
            conflict,
            module.terminal_handback(
                delegation,
                terminal_kind,
                inline_result=(
                    f"{inline_result}!"
                    if inline_result is not None
                    else property_text.inline_result
                ),
            ),
            module.terminal_handback(
                delegation,
                terminal_kind,
                result_reference=property_text.result_reference,
                projection=property_text.projection,
            ),
        )
        for conflicting_terminal in conflicts:
            try:
                module.reduce_terminal(first, conflicting_terminal)
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


def _source_texts(paths: Iterable[Path]) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
        for path in sorted(paths)
    }


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
    compliance_text = delegation_text_case(3)
    delegation = module.delegation_request(
        sender=sender,
        recipient=recipient,
        subject=compliance_text.subject,
        instruction=compliance_text.instruction,
        coordination_reference=str(uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")),
    )
    invalid_result_forms: tuple[dict[str, str], ...] = (
        {},
        {module.RESULT_REFERENCE_FIELD: "result://missing-projection"},
        {module.PROJECTION_FIELD: "projection without reference"},
        {
            module.RESULT_REFERENCE_FIELD: "result://overlength-projection",
            module.PROJECTION_FIELD: (
                "x" * (module.MAX_RESULT_PROJECTION_CHARACTERS + 1)
            ),
        },
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

    script_paths = (
        path
        for runtime_root in CODING_AGENTS_RUNTIME_ROOTS
        for path in runtime_root.rglob("*.py")
        if OPERATE_PROWL_RELATIVE not in path.relative_to(runtime_root).parents
    )
    violations = module.raw_prowl_command_violations(_source_texts(script_paths))
    if violations:
        failures.append(
            "raw Prowl command construction remains in a script outside /operate-prowl: "
            + ", ".join(violations)
        )

    expected_fixture = str(RAW_PROWL_VIOLATION_FIXTURE.relative_to(ROOT))
    fixture_violations = module.raw_prowl_command_violations(
        _source_texts((RAW_PROWL_VIOLATION_FIXTURE,))
    )
    if fixture_violations != [expected_fixture]:
        failures.append("raw Prowl command rule accepted its violating script fixture")
    return failures
