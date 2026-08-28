import json
from io import StringIO

from outcomeeng_testing.generators.prowl_environment import operation_requests
from outcomeeng_testing.harnesses.prowl_environment import (
    RecordingRunner,
    load_prowl_environment,
)


def test_checked_responses_map_to_versioned_results() -> None:
    module = load_prowl_environment()

    for request in operation_requests(module):
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
        response_data = response[module.DATA_FIELD]
        if operation is module.Operation.OPEN:
            response_data[module.RESOLUTION_FIELD] = module.OpenResolution.EXACT_ROOT
            response_data[module.CREATED_TAB_FIELD] = True
        elif operation is module.Operation.SEND:
            response_data[module.INPUT_FIELD] = {module.TRAILING_ENTER_SENT_FIELD: True}
        output_stream = StringIO()

        cli_exit_code = module.main(
            [module.CliOperation.RUN.value],
            runner=RecordingRunner([module.CommandResult(0, json.dumps(response), "")]),
            stdin=StringIO(json.dumps(request)),
            stdout=output_stream,
        )

        assert output_stream.getvalue().count("\n") == 1
        assert cli_exit_code == 0
        assert json.loads(output_stream.getvalue()) == {
            module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION,
            module.OPERATION_FIELD: operation,
            module.STATUS_FIELD: module.ExecutionStatus.SUCCEEDED,
            module.COMMAND_EXIT_CODE_FIELD: 0,
            module.RESPONSE_FIELD: response,
        }


def test_command_failures_map_to_named_results() -> None:
    module = load_prowl_environment()
    request = module.operation_request(module.Operation.LIST)

    for command_result, expected_status, expected_detail in (
        (
            module.CommandResult(7, "", "command failed"),
            module.ExecutionStatus.COMMAND_FAILED,
            "command failed",
        ),
        (
            module.CommandResult(0, "{", ""),
            module.ExecutionStatus.INVALID_SCHEMA,
            "Prowl returned invalid JSON",
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
            "not accepted",
        ),
    ):
        result = module.execute(request, RecordingRunner([command_result]))

        assert result[module.SCHEMA_VERSION_FIELD] == module.SCHEMA_VERSION
        assert result[module.OPERATION_FIELD] == module.Operation.LIST
        assert result[module.STATUS_FIELD] == expected_status
        assert result[module.COMMAND_EXIT_CODE_FIELD] == command_result.returncode
        assert expected_detail in result[module.DETAIL_FIELD]
