import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.herdr_environment import (
    agent_item_variant,
    operation_requests,
)
from outcomeeng_testing.harnesses.cli_usage import read_argv
from outcomeeng_testing.harnesses.herdr_environment import (
    AbsentExecutableRunner,
    CapturedResponse,
    RecordingRunner,
    captured_error_message,
    captured_error_responses,
    captured_payload,
    captured_responses,
    captured_success_response,
    inventory_envelope,
    load_herdr_environment,
    projected_error_variants,
    request_for,
    run_inventory_mapping,
    run_unknown_operation_mapping,
    usage_contract_for,
)


def test_herdr_operation_mappings() -> None:
    module = load_herdr_environment()
    requests = operation_requests(module)

    assert {str(request[module.OPERATION_FIELD]) for request in requests} == {
        operation.value for operation in module.Operation
    }

    for request in requests:
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        argv = module.command_for(request)
        contract = usage_contract_for(module, operation)
        reading = read_argv(contract, argv)

        assert reading.command_path == (module.HERDR_COMMAND, *contract.command_path)
        assert reading.unknown_options == ()
        assert contract.required_options <= set(reading.options_seen)
        for option, count in reading.options_seen.items():
            assert count == 1 or option in contract.repeatable_options
        if contract.variadic_positional:
            assert len(reading.positionals) >= len(contract.required_positionals)
        else:
            assert len(reading.positionals) == len(contract.required_positionals)
        text_values = [
            value
            for field_name, value in arguments.items()
            if field_name in module.TEXT_ARGUMENT_FIELDS
        ]
        for value in text_values:
            assert value in argv
        for field_name in module.TEXT_LIST_ARGUMENT_FIELDS:
            for value in cast(list[str], arguments.get(field_name, [])):
                assert value in argv
        if module.TIMEOUT_FIELD in arguments:
            assert str(arguments[module.TIMEOUT_FIELD]) in argv
            assert module.TIMEOUT_OPTION in reading.options_seen
        else:
            assert module.TIMEOUT_OPTION not in reading.options_seen
        if module.AGENT_ARGUMENTS_FIELD in arguments:
            assert reading.trailing == tuple(
                cast(list[str], arguments[module.AGENT_ARGUMENTS_FIELD])
            )

        captured = captured_success_response(module, operation, arguments)
        if captured is None:
            # herdr emitted only an error for this command under capture; the
            # response mapping below covers it with that envelope.
            assert captured_error_responses(module, operation) != []
            continue
        runner = RecordingRunner([captured.result])
        result = module.execute(request, runner)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert result[module.COMMAND_EXIT_CODE_FIELD] == 0
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        if operation in module.TEXT_OPERATIONS:
            assert response == {module.OUTPUT_FIELD: captured_payload(captured)}
        else:
            assert response == captured_payload(captured)
        assert len(runner.calls) == 1
        called_argv, stdin, bound = runner.calls[0]
        assert (called_argv, stdin) == (argv, None)
        assert bound == module.command_bound_seconds(request)
        if module.TIMEOUT_FIELD in arguments:
            assert bound * 1000 > cast(int, arguments[module.TIMEOUT_FIELD])
        else:
            assert bound == module.COMMAND_TIMEOUT_SECONDS


def test_captured_responses_map_to_results_without_rewriting() -> None:
    module = load_herdr_environment()
    covered: set[object] = set()

    for captured in captured_responses(module):
        operation = module.Operation(captured.operation)
        covered.add(operation)
        request = request_for(module, operation, captured.shaping_fields)
        result = module.execute(request, RecordingRunner([captured.result]))

        assert json.loads(json.dumps(result)) == result
        if captured.error_code is None:
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            payload = captured_payload(captured)
            if operation in module.TEXT_OPERATIONS:
                assert result[module.RESPONSE_FIELD] == {module.OUTPUT_FIELD: payload}
            else:
                assert result[module.RESPONSE_FIELD] == payload
            continue
        assert result[module.STATUS_FIELD] == module.HERDR_ERROR_STATUSES.get(
            captured.error_code, module.ExecutionStatus.COMMAND_FAILED
        )
        assert result[module.ERROR_CODE_FIELD] == captured.error_code
        assert result[module.DETAIL_FIELD] == captured_error_message(module, captured)
        assert result[module.COMMAND_EXIT_CODE_FIELD] == captured.result.returncode

    assert covered == set(module.Operation)


def test_start_and_wait_map_to_the_session_identity_and_state() -> None:
    module = load_herdr_environment()

    def session_of(
        operation: object, shaping_fields: frozenset[str] = frozenset()
    ) -> tuple[dict[str, object], dict[str, object]]:
        request = request_for(module, operation, shaping_fields)
        captured = captured_success_response(
            module, operation, cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        )
        assert captured is not None, f"no captured {operation} response"
        envelope = cast(dict[str, object], captured_payload(captured))
        result = cast(dict[str, object], envelope[module.RESULT_FIELD])
        emitted = cast(dict[str, object], result[module.SESSION_FIELD])
        executed = module.execute(request, RecordingRunner([captured.result]))
        assert executed[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        return emitted, module.session_from_response(executed[module.RESPONSE_FIELD])

    # Every session-bearing operation, and the prompt under both of its
    # response shapes: submitted alone, and observed after `--wait`.
    session_shapes = [
        (operation, frozenset[str]()) for operation in module.SESSION_OPERATIONS
    ]
    session_shapes.append((module.Operation.PROMPT, frozenset({module.WAIT_FIELD})))
    for operation, shaping_fields in session_shapes:
        emitted, session = session_of(operation, shaping_fields)
        assert session == {
            field_name: emitted[field_name] for field_name in module.PARTICIPANT_FIELDS
        }
        assert session[module.NAME_FIELD] == emitted[module.NAME_FIELD]
        assert session[module.PANE_ID_FIELD] == emitted[module.PANE_ID_FIELD]
        assert session[module.AGENT_STATUS_FIELD] in {
            member.value for member in module.AgentState
        }

    started, session = session_of(module.Operation.START)
    assert session[module.INTERACTIVE_READY_FIELD] is True
    assert session[module.AGENT_KIND_FIELD] == started[module.AGENT_KIND_FIELD]

    waited, session = session_of(module.Operation.WAIT)
    reached = module.AgentState(session[module.AGENT_STATUS_FIELD])
    until = module.operation_request(
        module.Operation.WAIT,
        agent=cast(str, waited[module.NAME_FIELD]),
        until=[reached.value],
        timeout=module.INTEGER_BOUNDS[module.TIMEOUT_FIELD][0],
    )
    assert reached.value in module.command_for(until)

    timed_out = [
        captured
        for captured in captured_error_responses(module, module.Operation.WAIT)
        if module.HERDR_ERROR_STATUSES.get(captured.error_code or "")
        is module.ExecutionStatus.WAIT_TIMEOUT
    ]
    assert timed_out != []
    for captured in timed_out:
        result = module.execute(
            request_for(module, module.Operation.WAIT),
            RecordingRunner([captured.result]),
        )
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.WAIT_TIMEOUT
        assert result[module.ERROR_CODE_FIELD] == captured.error_code

    not_ready = [
        captured
        for captured in projected_error_variants(module)
        if module.HERDR_ERROR_STATUSES.get(captured.error_code or "")
        is module.ExecutionStatus.AGENT_NOT_READY
    ]
    assert not_ready != []
    for captured in not_ready:
        result = module.execute(
            request_for(module, module.Operation.START),
            RecordingRunner([captured.result]),
        )
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.AGENT_NOT_READY
        assert result[module.ERROR_CODE_FIELD] == captured.error_code


def test_inventory_maps_to_complete_participants_or_named_results() -> None:
    def assert_inventory(
        module: ModuleType,
        envelope: dict[str, object],
        agents: list[dict[str, object]],
        absent_name: str,
        state: object,
    ) -> None:
        participants = module.participants_from_inventory(envelope)

        assert [
            {
                field_name: participant[field_name]
                for field_name in module.PARTICIPANT_FIELDS
            }
            for participant in participants
        ] == [
            {field_name: agent[field_name] for field_name in module.PARTICIPANT_FIELDS}
            for agent in agents
        ]
        assert {
            participant[module.AGENT_STATUS_FIELD] for participant in participants
        } <= {member.value for member in module.AgentState}
        first_name = cast(str, agents[0][module.NAME_FIELD])
        assert module.participant_for(participants, first_name) == participants[0]
        if absent_name not in {agent[module.NAME_FIELD] for agent in agents}:
            try:
                module.participant_for(participants, absent_name)
            except module.HerdrEnvironmentError as error:
                assert error.status == module.ExecutionStatus.IDENTITY_UNAVAILABLE
            else:
                raise AssertionError("an absent name resolved to a participant")
        duplicated = [
            *agents,
            agent_item_variant(
                module, agents[0], len(agents) + 1, state, name=first_name
            ),
        ]
        try:
            module.participant_for(
                module.participants_from_inventory(
                    inventory_envelope(module, duplicated)
                ),
                first_name,
            )
        except module.HerdrEnvironmentError as error:
            assert error.status == module.ExecutionStatus.IDENTITY_AMBIGUOUS
        else:
            raise AssertionError("a duplicated name resolved to one participant")

    run_inventory_mapping(assert_inventory)


def test_herdr_error_codes_project_to_named_statuses() -> None:
    module = load_herdr_environment()
    projected: dict[str, CapturedResponse] = {}
    verbatim: list[CapturedResponse] = []

    for captured in [*captured_responses(module), *projected_error_variants(module)]:
        if captured.error_code is None:
            continue
        if captured.error_code in module.HERDR_ERROR_STATUSES:
            projected.setdefault(captured.error_code, captured)
        else:
            verbatim.append(captured)

    assert set(projected) == set(module.HERDR_ERROR_STATUSES)
    assert verbatim != []

    for code, captured in projected.items():
        result = module.execute(
            request_for(module, captured.operation), RecordingRunner([captured.result])
        )
        assert result[module.STATUS_FIELD] == module.HERDR_ERROR_STATUSES[code]
        assert result[module.STATUS_FIELD] != module.ExecutionStatus.COMMAND_FAILED
        assert result[module.ERROR_CODE_FIELD] == code
        assert result[module.DETAIL_FIELD] == captured_error_message(module, captured)

    for captured in verbatim:
        result = module.execute(
            request_for(module, captured.operation), RecordingRunner([captured.result])
        )
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
        assert result[module.ERROR_CODE_FIELD] == captured.error_code
        assert result[module.DETAIL_FIELD] == captured_error_message(module, captured)


def test_absent_server_and_unsupported_operation_map_to_unavailable_results() -> None:
    module = load_herdr_environment()
    request = module.operation_request(module.Operation.INVENTORY)

    absent = AbsentExecutableRunner()
    result = module.execute(request, absent)
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SERVER_NOT_RUNNING
    assert absent.calls == [module.command_for(request)]

    not_running = [
        captured
        for captured in captured_error_responses(module, module.Operation.INVENTORY)
        if module.HERDR_ERROR_STATUSES.get(captured.error_code or "")
        is module.ExecutionStatus.SERVER_NOT_RUNNING
    ]
    assert not_running != []
    for captured in not_running:
        result = module.execute(request, RecordingRunner([captured.result]))
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SERVER_NOT_RUNNING
        assert result[module.ERROR_CODE_FIELD] == captured.error_code

    def assert_unknown(module: ModuleType, name: str) -> None:
        unknown = {**request, module.OPERATION_FIELD: name}
        result = module.execute(unknown, RecordingRunner([]))
        assert (
            result[module.STATUS_FIELD] == module.ExecutionStatus.OPERATION_UNAVAILABLE
        )

    run_unknown_operation_mapping(assert_unknown)
