import json
import uuid
from typing import cast

from outcomeeng_testing.generators.prowl_environment import (
    agent_identity,
    delegation_text_case,
    operation_requests,
    public_agent_item,
    public_prowl_operation_names,
)
from outcomeeng_testing.harnesses.prowl_environment import (
    RecordingRunner,
    load_prowl_environment,
)


def test_prowl_environment_mappings() -> None:
    module = load_prowl_environment()
    requests = operation_requests(module)
    required_operations = set(public_prowl_operation_names(module))

    assert {operation.value for operation in module.Operation} == required_operations
    assert {
        str(request[module.OPERATION_FIELD]) for request in requests
    } == required_operations

    for request in requests:
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        public_command = list(module.PUBLIC_PROWL_COMMAND_PREFIXES[operation])
        if operation in {module.Operation.LIST, module.Operation.AGENTS}:
            public_command.append(module.PUBLIC_PROWL_JSON_OPTION)
        elif operation is module.Operation.OPEN:
            public_command.append(module.PUBLIC_PROWL_JSON_OPTION)
            if arguments.get(module.PATH_FIELD) is not None:
                public_command.append(cast(str, arguments[module.PATH_FIELD]))
        else:
            for field_name in module.SELECTOR_FIELDS:
                value = arguments.get(field_name)
                if value is not None:
                    public_command.extend(
                        (
                            module.PUBLIC_PROWL_SELECTOR_OPTIONS[field_name],
                            cast(str, value),
                        )
                    )
            public_command.append(module.PUBLIC_PROWL_JSON_OPTION)
            if operation is module.Operation.READ:
                for field_name in (
                    module.LAST_FIELD,
                    module.STABLE_INTERVAL_FIELD,
                    module.STABLE_PERIOD_FIELD,
                    module.WAIT_TIMEOUT_FIELD,
                ):
                    value = arguments.get(field_name)
                    if value is not None:
                        public_command.extend(
                            (
                                module.PUBLIC_PROWL_ARGUMENT_OPTIONS[field_name],
                                str(value),
                            )
                        )
                if arguments.get(module.WAIT_STABLE_FIELD) is True:
                    public_command.append(
                        module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.WAIT_STABLE_FIELD]
                    )
            elif operation is module.Operation.SEND:
                for field_name in (
                    module.NO_ENTER_FIELD,
                    module.NO_WAIT_FIELD,
                    module.CAPTURE_FIELD,
                ):
                    if arguments.get(field_name) is True:
                        public_command.append(
                            module.PUBLIC_PROWL_ARGUMENT_OPTIONS[field_name]
                        )
                if arguments.get(module.TIMEOUT_FIELD) is not None:
                    public_command.extend(
                        (
                            module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.TIMEOUT_FIELD],
                            str(arguments[module.TIMEOUT_FIELD]),
                        )
                    )
                public_command.append(cast(str, arguments[module.TEXT_FIELD]))
            elif operation is module.Operation.KEY:
                if arguments.get(module.REPEAT_FIELD) is not None:
                    public_command.extend(
                        (
                            module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.REPEAT_FIELD],
                            str(arguments[module.REPEAT_FIELD]),
                        )
                    )
                public_command.append(cast(str, arguments[module.KEY_FIELD]))
            elif operation is module.Operation.TAB_CREATE:
                if arguments.get(module.PATH_FIELD) is not None:
                    public_command.extend(
                        (
                            module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.PATH_FIELD],
                            cast(str, arguments[module.PATH_FIELD]),
                        )
                    )
            elif (
                operation
                in {
                    module.Operation.TAB_CLOSE,
                    module.Operation.PANE_CLOSE,
                }
                and arguments.get(module.FORCE_FIELD) is True
            ):
                public_command.append(
                    module.PUBLIC_PROWL_ARGUMENT_OPTIONS[module.FORCE_FIELD]
                )

        actual = module.command_for(request)
        assert actual == tuple(public_command)
        assert module.HELP_OPTION not in actual

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
        assert executed[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert executed[module.OPERATION_FIELD] == operation
        assert executed[module.RESPONSE_FIELD] == response

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
            except module.ProwlEnvironmentError as error:
                assert selectorless_allowed is False
                assert error.status == module.ExecutionStatus.INVALID_SCHEMA
            else:
                assert selectorless_allowed is True

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
            except module.ProwlEnvironmentError as error:
                assert error.status == module.ExecutionStatus.INVALID_SCHEMA
            else:
                raise AssertionError(
                    f"{operation.value} accepted conflicting target selectors"
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
            except module.ProwlEnvironmentError as error:
                assert error.status == module.ExecutionStatus.INVALID_SCHEMA
            else:
                raise AssertionError(
                    "send accepted conflicting no-wait and capture shapes"
                )


def test_public_agent_evidence_maps_to_complete_identity_results() -> None:
    module = load_prowl_environment()
    public_item = public_agent_item(module, ordinal=1)
    projected = module.participant_from_agent(public_item)

    assert projected == agent_identity(module, ordinal=1)

    projection = module.participant_projection(
        {module.DATA_FIELD: {module.AGENTS_FIELD: [public_item]}}
    )
    assert projection[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert projection[module.PARTICIPANTS_FIELD] == [projected]

    for unavailable_payload in (
        {},
        {module.DATA_FIELD: {module.AGENTS_FIELD: []}},
        {module.DATA_FIELD: {module.AGENTS_FIELD: [{}]}},
    ):
        unavailable = module.participant_projection(unavailable_payload)
        assert (
            unavailable[module.STATUS_FIELD]
            == module.ExecutionStatus.IDENTITY_UNAVAILABLE
        )

    ambiguous = module.participant_projection(
        {module.DATA_FIELD: {module.AGENTS_FIELD: [public_item, {**public_item}]}}
    )
    assert ambiguous[module.STATUS_FIELD] == module.ExecutionStatus.IDENTITY_AMBIGUOUS


def test_terminal_kinds_map_to_correlated_handbacks() -> None:
    module = load_prowl_environment()
    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)
    content = delegation_text_case(1)
    reference = str(uuid.uuid5(uuid.NAMESPACE_URL, sender[module.PANE_FIELD]))
    delegation = module.delegation_request(
        sender=sender,
        recipient=recipient,
        subject=content.subject,
        instruction=content.instruction,
        coordination_reference=reference,
    )

    for terminal_kind in module.TerminalKind:
        terminal = module.terminal_handback(
            delegation,
            terminal_kind,
            inline_result=f"{content.inline_result}: {terminal_kind.value}",
        )
        assert terminal[module.COORDINATION_REFERENCE_FIELD] == reference
        assert terminal[module.KIND_FIELD] == terminal_kind
        assert terminal[module.SENDER_FIELD] == recipient
        assert terminal[module.RECIPIENT_FIELD] == sender
        assert module.reduce_terminal(None, terminal) == terminal

        delivery = module.delegation_delivery_request(terminal)
        delivery_arguments = cast(dict[str, object], delivery[module.ARGUMENTS_FIELD])
        assert delivery_arguments[module.PANE_FIELD] == sender[module.PANE_FIELD]

        durable = module.terminal_handback(
            delegation,
            terminal_kind,
            result_reference=f"{content.result_reference}-{terminal_kind.value}",
            projection=f"{content.projection}: {terminal_kind.value}",
        )
        assert durable[module.RESULT_REFERENCE_FIELD] == (
            f"{content.result_reference}-{terminal_kind.value}"
        )
        assert durable[module.PROJECTION_FIELD] == (
            f"{content.projection}: {terminal_kind.value}"
        )
