import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.herdr_environment import (
    herdr_agent_item,
    operation_requests,
)
from outcomeeng_testing.harnesses.herdr_environment import (
    AbsentExecutableRunner,
    RecordingRunner,
    herdr_error_result,
    herdr_inventory_result,
    herdr_success_result,
    load_herdr_environment,
    run_error_projection_mapping,
    run_inventory_mapping,
    run_unknown_operation_mapping,
)


def _target(module: ModuleType, arguments: dict[str, object]) -> str:
    for field_name in module.SELECTOR_FIELDS:
        value = arguments.get(field_name)
        if value is not None:
            return cast(str, value)
    raise AssertionError("request carries no selector")


def _expected_command(
    module: ModuleType, request: dict[str, object]
) -> tuple[str, ...]:
    operation = module.Operation(request[module.OPERATION_FIELD])
    arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
    options = module.PUBLIC_HERDR_ARGUMENT_OPTIONS
    command = list(module.PUBLIC_HERDR_COMMAND_PREFIXES[operation])
    if operation is module.Operation.INVENTORY:
        return tuple(command)
    if operation in {module.Operation.START, module.Operation.RELAUNCH}:
        command.append(cast(str, arguments[module.NAME_FIELD]))
        for field_name in (module.KIND_FIELD, module.PANE_FIELD):
            command.extend((options[field_name], cast(str, arguments[field_name])))
        command.extend(
            (options[module.TIMEOUT_FIELD], str(arguments[module.TIMEOUT_FIELD]))
        )
        if module.AGENT_ARGUMENTS_FIELD in arguments:
            command.append(module.AGENT_ARGUMENTS_SEPARATOR)
            command.extend(cast(list[str], arguments[module.AGENT_ARGUMENTS_FIELD]))
        return tuple(command)
    if operation is module.Operation.STOP:
        command.append(cast(str, arguments[module.PANE_FIELD]))
        return tuple(command)
    if operation is module.Operation.OPEN_WORKTREE:
        command.extend(
            (options[module.PATH_FIELD], cast(str, arguments[module.PATH_FIELD]))
        )
        command.append(module.NO_FOCUS_OPTION)
        return tuple(command)
    command.append(_target(module, arguments))
    if operation is module.Operation.READ:
        for field_name in (module.SOURCE_FIELD, module.LINES_FIELD):
            if field_name in arguments:
                command.extend((options[field_name], str(arguments[field_name])))
    elif operation is module.Operation.WAIT:
        for state in cast(list[str], arguments.get(module.UNTIL_FIELD, [])):
            command.extend((options[module.UNTIL_FIELD], state))
        command.extend(
            (options[module.TIMEOUT_FIELD], str(arguments[module.TIMEOUT_FIELD]))
        )
    elif operation is module.Operation.PROMPT:
        command.append(cast(str, arguments[module.TEXT_FIELD]))
        if arguments.get(module.WAIT_FIELD) is True:
            command.append(options[module.WAIT_FIELD])
            for state in cast(list[str], arguments.get(module.UNTIL_FIELD, [])):
                command.extend((options[module.UNTIL_FIELD], state))
            command.extend(
                (options[module.TIMEOUT_FIELD], str(arguments[module.TIMEOUT_FIELD]))
            )
    elif operation is module.Operation.KEY:
        command.extend(cast(list[str], arguments[module.KEYS_FIELD]))
    return tuple(command)


def test_herdr_operation_mappings() -> None:
    module = load_herdr_environment()
    requests = operation_requests(module)

    assert {str(request[module.OPERATION_FIELD]) for request in requests} == {
        operation.value for operation in module.Operation
    }

    for ordinal, request in enumerate(requests, start=1):
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        expected = _expected_command(module, request)
        assert module.command_for(request) == expected

        envelope_result = {
            module.AGENTS_FIELD: [
                herdr_agent_item(module, ordinal, module.AgentState.IDLE)
            ]
        }
        runner = RecordingRunner([herdr_success_result(module, envelope_result)])
        result = module.execute(request, runner)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert result[module.COMMAND_EXIT_CODE_FIELD] == 0
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        assert response[module.RESULT_FIELD] == envelope_result
        assert len(runner.calls) == 1
        argv, stdin, bound = runner.calls[0]
        assert (argv, stdin) == (expected, None)
        if module.TIMEOUT_FIELD in arguments:
            assert bound * 1000 > cast(int, arguments[module.TIMEOUT_FIELD])
        else:
            assert bound == module.COMMAND_TIMEOUT_SECONDS


def test_inventory_maps_to_complete_participants_or_named_results() -> None:
    def assert_inventory(
        module: ModuleType,
        agents: list[dict[str, object]],
        absent_name: str,
        state: object,
    ) -> None:
        runner = RecordingRunner([herdr_inventory_result(module, agents)])
        result = module.execute(
            module.operation_request(module.Operation.INVENTORY), runner
        )
        participants = module.participants_from_inventory(result[module.RESPONSE_FIELD])

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
            herdr_agent_item(module, len(agents) + 1, state, name=first_name),
        ]
        try:
            module.participant_for(
                module.participants_from_inventory(
                    {module.RESULT_FIELD: {module.AGENTS_FIELD: duplicated}}
                ),
                first_name,
            )
        except module.HerdrEnvironmentError as error:
            assert error.status == module.ExecutionStatus.IDENTITY_AMBIGUOUS
        else:
            raise AssertionError("a duplicated name resolved to one participant")

    run_inventory_mapping(assert_inventory)


def test_herdr_error_codes_project_to_named_statuses() -> None:
    def assert_projection(
        module: ModuleType, code: str, message: str, projected: bool
    ) -> None:
        request = module.operation_request(
            module.Operation.WAIT, agent="officer", timeout=1000
        )
        runner = RecordingRunner([herdr_error_result(module, code, message)])
        result = module.execute(request, runner)

        expected_status = (
            module.HERDR_ERROR_STATUSES[code]
            if projected
            else module.ExecutionStatus.COMMAND_FAILED
        )
        assert result[module.STATUS_FIELD] == expected_status
        assert result[module.ERROR_CODE_FIELD] == code
        assert result[module.DETAIL_FIELD] == message
        assert result[module.COMMAND_EXIT_CODE_FIELD] == 1
        assert json.loads(json.dumps(result)) == result

    run_error_projection_mapping(assert_projection)


def test_absent_server_and_unsupported_operation_map_to_unavailable_results() -> None:
    module = load_herdr_environment()
    request = module.operation_request(module.Operation.INVENTORY)

    absent = AbsentExecutableRunner()
    result = module.execute(request, absent)
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SERVER_NOT_RUNNING
    assert absent.calls == [module.command_for(request)]

    def assert_unknown(module: ModuleType, name: str) -> None:
        unknown = {**request, module.OPERATION_FIELD: name}
        result = module.execute(unknown, RecordingRunner([]))
        assert (
            result[module.STATUS_FIELD] == module.ExecutionStatus.OPERATION_UNAVAILABLE
        )

    run_unknown_operation_mapping(assert_unknown)
