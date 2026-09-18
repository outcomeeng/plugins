import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.agent_mail import operation_requests
from outcomeeng_testing.harnesses.agent_mail import (
    AbsentExecutableRunner,
    RecordingRunner,
    diagnosis_with_main_checkout,
    failed_command_result,
    json_command_result,
    load_agent_mail,
    run_project_key_mapping,
    text_command_result,
)


def _expected_command(
    module: ModuleType, request: dict[str, object], project_key: str
) -> tuple[str, ...]:
    operation = module.Operation(request[module.OPERATION_FIELD])
    arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
    command = [
        *module.PUBLIC_AM_COMMAND_PREFIXES[operation],
        module.PROJECT_OPTION,
        project_key,
    ]
    if operation is module.Operation.SEND:
        record = cast(dict[str, object], arguments[module.RECORD_FIELD])
        for field_name in (
            module.SENDER_FIELD,
            module.RECIPIENT_FIELD,
            module.CORRELATION_FIELD,
        ):
            command.extend(
                (
                    module.PUBLIC_AM_RECORD_OPTIONS[field_name],
                    cast(str, record[field_name]),
                )
            )
        command.extend(
            (
                module.PUBLIC_AM_RECORD_OPTIONS[module.RECORD_SUBJECT_FIELD],
                f"{module.KIND_PREFIX_OPEN}{record[module.KIND_FIELD]}"
                f"{module.KIND_PREFIX_CLOSE}{record[module.RECORD_SUBJECT_FIELD]}",
                module.PUBLIC_AM_RECORD_OPTIONS[module.BODY_FIELD],
                cast(str, record[module.BODY_FIELD]),
            )
        )
        if record[module.ACK_REQUIRED_FIELD] is True:
            command.append(module.PUBLIC_AM_RECORD_OPTIONS[module.ACK_REQUIRED_FIELD])
    elif operation is module.Operation.REGISTER:
        for field_name in (module.PROGRAM_FIELD, module.MODEL_FIELD):
            command.extend(
                (
                    module.PUBLIC_AM_ARGUMENT_OPTIONS[field_name],
                    cast(str, arguments[field_name]),
                )
            )
        command.extend((module.NAME_OPTION, cast(str, arguments[module.AGENT_FIELD])))
        if module.TASK_FIELD in arguments:
            command.extend(
                (
                    module.PUBLIC_AM_ARGUMENT_OPTIONS[module.TASK_FIELD],
                    cast(str, arguments[module.TASK_FIELD]),
                )
            )
    else:
        command.extend(
            (
                module.PUBLIC_AM_ARGUMENT_OPTIONS[module.AGENT_FIELD],
                cast(str, arguments[module.AGENT_FIELD]),
            )
        )
        if operation is module.Operation.INBOX:
            for field_name in (module.UNREAD_ONLY_FIELD, module.INCLUDE_BODIES_FIELD):
                if arguments.get(field_name) is True:
                    command.append(module.PUBLIC_AM_ARGUMENT_OPTIONS[field_name])
            if module.LIMIT_FIELD in arguments:
                command.extend(
                    (
                        module.PUBLIC_AM_ARGUMENT_OPTIONS[module.LIMIT_FIELD],
                        str(arguments[module.LIMIT_FIELD]),
                    )
                )
        else:
            command.append(str(arguments[module.MESSAGE_ID_FIELD]))
    if operation in module.JSON_OPERATIONS:
        command.append(module.JSON_OPTION)
    return tuple(command)


def _store_payload(
    module: ModuleType, request: dict[str, object], ordinal: int
) -> object:
    operation = module.Operation(request[module.OPERATION_FIELD])
    arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
    if operation is module.Operation.REGISTER:
        return {
            module.STORE_ID_FIELD: ordinal,
            module.STORE_NAME_FIELD: arguments[module.AGENT_FIELD],
            module.STORE_PROGRAM_FIELD: arguments[module.PROGRAM_FIELD],
            module.STORE_MODEL_FIELD: arguments[module.MODEL_FIELD],
        }
    if operation is module.Operation.SEND:
        record = cast(dict[str, object], arguments[module.RECORD_FIELD])
        return {
            module.STORE_ID_FIELD: ordinal,
            module.STORE_THREAD_ID_FIELD: record[module.CORRELATION_FIELD],
            module.STORE_FROM_FIELD: record[module.SENDER_FIELD],
            module.STORE_TO_FIELD: [record[module.RECIPIENT_FIELD]],
        }
    if operation is module.Operation.INBOX:
        return {
            module.STORE_INBOX_FIELD: [
                {
                    module.STORE_ID_FIELD: ordinal,
                    module.STORE_FROM_FIELD: f"Sender{ordinal}",
                    module.STORE_SUBJECT_FIELD: f"subject {ordinal}",
                    module.STORE_THREAD_FIELD: f"thread-{ordinal}",
                    module.STORE_ACK_STATUS_FIELD: module.STORE_ACK_STATUS_NONE,
                    module.STORE_BODY_FIELD: f"body {ordinal}",
                }
            ]
        }
    return f"Message {arguments[module.MESSAGE_ID_FIELD]} acknowledged"


def test_agent_mail_operation_mappings() -> None:
    module = load_agent_mail()
    requests = operation_requests(module)
    project_key = "/pool/main"
    diagnosis = diagnosis_with_main_checkout(module, project_key)

    assert {str(request[module.OPERATION_FIELD]) for request in requests} == {
        operation.value for operation in module.Operation
    }
    sent_kinds = {
        str(
            cast(
                dict[str, object],
                cast(dict[str, object], request[module.ARGUMENTS_FIELD])[
                    module.RECORD_FIELD
                ],
            )[module.KIND_FIELD]
        )
        for request in requests
        if request[module.OPERATION_FIELD] == module.Operation.SEND
    }
    assert sent_kinds == {kind.value for kind in module.SENT_KINDS}

    for ordinal, request in enumerate(requests, start=1):
        operation = module.Operation(request[module.OPERATION_FIELD])
        expected = _expected_command(module, request, project_key)
        assert module.command_for(request, project_key) == expected

        payload = _store_payload(module, request, ordinal)
        store_result = (
            json_command_result(module, payload)
            if operation in module.JSON_OPERATIONS
            else text_command_result(module, cast(str, payload))
        )
        runner = RecordingRunner([json_command_result(module, diagnosis), store_result])
        result = module.execute(request, runner)

        assert runner.calls == [
            (module.PUBLIC_SPX_DIAGNOSE_COMMAND, None),
            (expected, None),
        ]
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert result[module.PROJECT_KEY_FIELD] == project_key
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        data = cast(dict[str, object], result[module.DATA_FIELD])
        if operation is module.Operation.INBOX:
            items = cast(
                list[dict[str, object]],
                cast(dict[str, object], payload)[module.STORE_INBOX_FIELD],
            )
            records = cast(list[dict[str, object]], data[module.RECORDS_FIELD])
            assert response == payload
            assert [record[module.RECORD_ID_FIELD] for record in records] == [
                item[module.STORE_ID_FIELD] for item in items
            ]
            assert [record[module.CORRELATION_FIELD] for record in records] == [
                item[module.STORE_THREAD_FIELD] for item in items
            ]
        elif operation is module.Operation.RECEIPT:
            assert response[module.OUTPUT_FIELD] == payload
            assert (
                data[module.MESSAGE_ID_FIELD]
                == cast(dict[str, object], request[module.ARGUMENTS_FIELD])[
                    module.MESSAGE_ID_FIELD
                ]
            )
        elif operation is module.Operation.SEND:
            assert response == payload
            record = cast(dict[str, object], data[module.RECORD_FIELD])
            assert (
                record[module.RECORD_ID_FIELD]
                == cast(dict[str, object], payload)[module.STORE_ID_FIELD]
            )
        else:
            assert response == payload
            assert (
                data[module.AGENT_FIELD]
                == cast(dict[str, object], payload)[module.STORE_NAME_FIELD]
            )


def test_project_key_mapping() -> None:
    def assert_key(
        module: ModuleType, payload: dict[str, object], expected_key: str | None
    ) -> None:
        runner = RecordingRunner([json_command_result(module, payload)])
        if expected_key is None:
            try:
                module.project_key_from_diagnosis(payload)
            except module.AgentMailError as error:
                assert error.status == module.ExecutionStatus.DIAGNOSIS_UNAVAILABLE
            else:
                raise AssertionError(
                    "diagnosis without a main checkout path resolved a key"
                )
            result = module.execute(
                module.operation_request(module.Operation.INBOX, agent="Reader"), runner
            )
            assert (
                result[module.STATUS_FIELD]
                == module.ExecutionStatus.DIAGNOSIS_UNAVAILABLE
            )
            assert runner.calls == [(module.PUBLIC_SPX_DIAGNOSE_COMMAND, None)]
        else:
            assert module.project_key_from_diagnosis(payload) == expected_key
            assert module.resolve_project_key(runner) == expected_key

    run_project_key_mapping(assert_key)


def test_store_responses_map_to_results_without_rewriting() -> None:
    module = load_agent_mail()
    project_key = "/pool/main"
    diagnosis = json_command_result(
        module, diagnosis_with_main_checkout(module, project_key)
    )
    request = module.operation_request(module.Operation.INBOX, agent="Reader")

    failed = module.execute(
        request,
        RecordingRunner([diagnosis, failed_command_result(module, 3, "store refused")]),
    )
    assert failed[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
    assert failed[module.DETAIL_FIELD] == "store refused"
    assert failed[module.COMMAND_EXIT_CODE_FIELD] == 3

    malformed = module.execute(
        request,
        RecordingRunner(
            [
                json_command_result(
                    module, diagnosis_with_main_checkout(module, project_key)
                ),
                text_command_result(module, "not json"),
            ]
        ),
    )
    assert malformed[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA

    unsupported = module.execute(
        {**request, module.OPERATION_FIELD: "forward"}, RecordingRunner([])
    )
    assert (
        unsupported[module.STATUS_FIELD] == module.ExecutionStatus.OPERATION_UNAVAILABLE
    )
    assert json.loads(json.dumps(unsupported)) == unsupported


def test_absent_executables_map_to_named_unavailable_results() -> None:
    module = load_agent_mail()
    request = module.operation_request(module.Operation.INBOX, agent="Reader")
    diagnosis = json_command_result(
        module, diagnosis_with_main_checkout(module, "/pool/main")
    )

    no_diagnosis = module.execute(request, AbsentExecutableRunner(module.SPX_COMMAND))
    assert (
        no_diagnosis[module.STATUS_FIELD]
        == module.ExecutionStatus.DIAGNOSIS_UNAVAILABLE
    )

    no_store = module.execute(
        request, AbsentExecutableRunner(module.AM_COMMAND, [diagnosis])
    )
    assert no_store[module.STATUS_FIELD] == module.ExecutionStatus.STORE_UNAVAILABLE
