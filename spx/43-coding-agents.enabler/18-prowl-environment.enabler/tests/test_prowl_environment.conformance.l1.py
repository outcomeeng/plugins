import json
from io import StringIO

from outcomeeng_testing.generators.prowl_environment import operation_requests
from outcomeeng_testing.harnesses.prowl_environment import (
    RecordingRunner,
    load_prowl_environment,
)


def test_prowl_environment_conformance() -> None:
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
        output_stream = StringIO()

        cli_exit_code = module.main(
            [module.CliOperation.RUN.value],
            runner=RecordingRunner([module.CommandResult(0, json.dumps(response), "")]),
            stdin=StringIO(json.dumps(request)),
            stdout=output_stream,
        )
        rendered = output_stream.getvalue()

        assert rendered.count("\n") == 1
        success = json.loads(rendered)
        assert cli_exit_code == 0
        validated = module.validate_operation_result(success, operation)
        assert validated[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert validated[module.RESPONSE_FIELD] == response
        assert validated[module.COMMAND_EXIT_CODE_FIELD] == 0


def test_prowl_environment_failure_results_conform() -> None:
    module = load_prowl_environment()
    request = module.operation_request(module.Operation.LIST)

    for command_result, expected_status in (
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
    ):
        result = module.execute(request, RecordingRunner([command_result]))
        validated = module.validate_operation_result(result, module.Operation.LIST)

        assert validated[module.STATUS_FIELD] == expected_status
        assert validated[module.COMMAND_EXIT_CODE_FIELD] == command_result.returncode
