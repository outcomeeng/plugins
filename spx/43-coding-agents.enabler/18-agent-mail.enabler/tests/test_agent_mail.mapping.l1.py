import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.harnesses.agent_mail import (
    AbsentExecutableRunner,
    RecordingRunner,
    diagnosis_seeded_absent_store_runner,
    diagnosis_seeded_runner,
    failed_command_result,
    json_command_result,
    load_agent_mail,
    run_generated_identities,
    run_operation_mapping,
    run_project_key_mapping,
    store_response_payload,
    store_response_result,
    text_command_result,
    usage_contract_for,
)
from outcomeeng_testing.harnesses.cli_usage import read_argv


def test_agent_mail_operation_mappings() -> None:
    module = load_agent_mail()
    operations = {operation.value for operation in module.Operation}
    seen_operations: set[str] = set()
    seen_kinds: set[str] = set()

    def assert_operation(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        seen_operations.add(operation.value)
        argv = module.command_for(request, project_key)
        contract = usage_contract_for(module, operation)
        reading = read_argv(contract, argv)

        assert reading.command_path == (module.AM_COMMAND, *contract.command_path)
        assert reading.unknown_options == ()
        assert contract.required_options <= set(reading.options_seen)
        assert module.PROJECT_OPTION in reading.options_seen
        assert argv[argv.index(module.PROJECT_OPTION) + 1] == project_key
        assert len(reading.positionals) == len(contract.required_positionals)
        assert (module.JSON_OPTION in reading.options_seen) == (
            operation in module.JSON_OPERATIONS
        )
        for option, count in reading.options_seen.items():
            assert count == 1 or option in contract.repeatable_options
        if operation is module.Operation.SEND:
            record = cast(dict[str, object], arguments[module.RECORD_FIELD])
            seen_kinds.add(str(record[module.KIND_FIELD]))
            for field_name in (
                module.SENDER_FIELD,
                module.RECIPIENT_FIELD,
                module.CORRELATION_FIELD,
                module.BODY_FIELD,
            ):
                assert record[field_name] in argv
            assert (
                f"{module.KIND_PREFIX_OPEN}{record[module.KIND_FIELD]}"
                f"{module.KIND_PREFIX_CLOSE}{record[module.RECORD_SUBJECT_FIELD]}"
            ) in argv
            assert (module.ACK_REQUIRED_OPTION in reading.options_seen) is (
                record[module.ACK_REQUIRED_FIELD]
            )
        elif operation is module.Operation.RECEIPT:
            assert reading.positionals == (str(arguments[module.MESSAGE_ID_FIELD]),)
        else:
            assert arguments[module.AGENT_FIELD] in argv

        payload = store_response_payload(module, operation)
        runner = diagnosis_seeded_runner(
            module, project_key, store_response_result(module, operation)
        )
        result = module.execute(request, runner)

        assert runner.calls == [
            (module.PUBLIC_SPX_DIAGNOSE_COMMAND, None),
            (argv, None),
        ]
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert result[module.PROJECT_KEY_FIELD] == project_key
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        data = cast(dict[str, object], result[module.DATA_FIELD])
        if operation is module.Operation.RECEIPT:
            assert response[module.OUTPUT_FIELD] == payload
            assert data[module.MESSAGE_ID_FIELD] == arguments[module.MESSAGE_ID_FIELD]
            return
        store = cast(dict[str, object], payload)
        if operation is module.Operation.INBOX:
            items = cast(list[dict[str, object]], store[module.STORE_INBOX_FIELD])
            records = cast(list[dict[str, object]], data[module.RECORDS_FIELD])
            assert response == store
            assert [record[module.RECORD_ID_FIELD] for record in records] == [
                item[module.STORE_ID_FIELD] for item in items
            ]
            assert [record[module.CORRELATION_FIELD] for record in records] == [
                item[module.STORE_THREAD_FIELD] for item in items
            ]
            assert [record[module.SENDER_FIELD] for record in records] == [
                item[module.STORE_FROM_FIELD] for item in items
            ]
        elif operation is module.Operation.SEND:
            assert response == store
            record = cast(dict[str, object], data[module.RECORD_FIELD])
            assert record[module.RECORD_ID_FIELD] == store[module.STORE_ID_FIELD]
        else:
            assert response == {
                key: value
                for key, value in store.items()
                if key != module.STORE_REGISTRATION_TOKEN_FIELD
            }
            assert data[module.AGENT_FIELD] == store[module.STORE_NAME_FIELD]

    run_operation_mapping(assert_operation)

    assert seen_operations == operations
    assert seen_kinds == {kind.value for kind in module.SENT_KINDS}


def test_project_key_mapping() -> None:
    def assert_key(
        module: ModuleType,
        shape: str,
        payload: dict[str, object],
        expected_key: str | None,
        agent: str,
    ) -> None:
        runner = RecordingRunner([json_command_result(module, payload)])
        request = module.operation_request(module.Operation.INBOX, agent=agent)
        if expected_key is None:
            try:
                module.project_key_from_diagnosis(payload)
            except module.AgentMailError as error:
                assert error.status == module.ExecutionStatus.DIAGNOSIS_UNAVAILABLE
            else:
                raise AssertionError(f"shape {shape} resolved a key without a path")
            result = module.execute(request, runner)
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
    def assert_case(
        module: ModuleType, agent: str, program: str, model: str, project_key: str
    ) -> None:
        request = module.operation_request(module.Operation.INBOX, agent=agent)

        failed = module.execute(
            request,
            diagnosis_seeded_runner(
                module, project_key, failed_command_result(module, 3, program)
            ),
        )
        assert failed[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
        assert failed[module.DETAIL_FIELD] == program
        assert failed[module.COMMAND_EXIT_CODE_FIELD] == 3

        malformed = module.execute(
            request,
            diagnosis_seeded_runner(
                module, project_key, text_command_result(module, model)
            ),
        )
        assert malformed[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA

        unsupported = module.execute(
            {**request, module.OPERATION_FIELD: program}, RecordingRunner([])
        )
        assert (
            unsupported[module.STATUS_FIELD]
            == module.ExecutionStatus.OPERATION_UNAVAILABLE
        )
        assert json.loads(json.dumps(unsupported)) == unsupported

        no_diagnosis = module.execute(
            request, AbsentExecutableRunner(module.SPX_COMMAND)
        )
        assert (
            no_diagnosis[module.STATUS_FIELD]
            == module.ExecutionStatus.DIAGNOSIS_UNAVAILABLE
        )
        no_store = module.execute(
            request, diagnosis_seeded_absent_store_runner(module, project_key)
        )
        assert no_store[module.STATUS_FIELD] == module.ExecutionStatus.STORE_UNAVAILABLE

    run_generated_identities(assert_case)
