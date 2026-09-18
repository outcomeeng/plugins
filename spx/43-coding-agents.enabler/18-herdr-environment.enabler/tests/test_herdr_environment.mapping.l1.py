import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.herdr_environment import (
    herdr_agent_item,
    operation_requests,
)
from outcomeeng_testing.harnesses.cli_usage import read_argv
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
    usage_contract_for,
)


def test_herdr_operation_mappings() -> None:
    module = load_herdr_environment()
    requests = operation_requests(module)

    assert {str(request[module.OPERATION_FIELD]) for request in requests} == {
        operation.value for operation in module.Operation
    }

    for ordinal, request in enumerate(requests, start=1):
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
        called_argv, stdin, bound = runner.calls[0]
        assert (called_argv, stdin) == (argv, None)
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
        module: ModuleType,
        code: str,
        message: str,
        projected: bool,
        selector: str,
        timeout: int,
    ) -> None:
        request = module.operation_request(
            module.Operation.WAIT, agent=selector, timeout=timeout
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
