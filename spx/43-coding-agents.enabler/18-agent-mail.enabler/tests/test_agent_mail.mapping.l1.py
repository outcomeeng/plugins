import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.harnesses.agent_mail import (
    AbsentExecutableRunner,
    CapturedInboxResponse,
    RecordingRunner,
    diagnosis_seeded_absent_store_runner,
    diagnosis_seeded_runner,
    failed_command_result,
    json_command_result,
    load_agent_mail,
    run_inbox_row_mapping,
    run_operation_mapping,
    run_project_key_mapping,
    run_recipient_boundary,
    run_store_response_cases,
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
                assert (
                    module.attached_option(
                        module.PUBLIC_AM_RECORD_OPTIONS[field_name], record[field_name]
                    )
                    in argv
                )
            assert (
                module.attached_option(
                    module.PUBLIC_AM_RECORD_OPTIONS[module.RECORD_SUBJECT_FIELD],
                    f"{module.KIND_PREFIX_OPEN}{record[module.KIND_FIELD]}"
                    f"{module.KIND_PREFIX_CLOSE}{record[module.RECORD_SUBJECT_FIELD]}",
                )
                in argv
            )
            assert (module.ACK_REQUIRED_OPTION in reading.options_seen) is (
                record[module.ACK_REQUIRED_FIELD]
            )
        elif operation is module.Operation.RECEIPT:
            assert reading.positionals == (str(arguments[module.MESSAGE_ID_FIELD]),)
        else:
            assert arguments[module.AGENT_FIELD] in argv

        payload = store_response_payload(module, operation, arguments)
        runner = diagnosis_seeded_runner(
            module, project_key, store_response_result(module, operation, arguments)
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
            assert [record[module.BODY_FIELD] for record in records] == [
                item.get(module.STORE_BODY_FIELD, "") for item in items
            ]
            assert [record[module.ACK_REQUIRED_FIELD] for record in records] == [
                item[module.STORE_ACK_STATUS_FIELD]
                in module.STORE_ACK_REQUIRED_STATUSES
                for item in items
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


def test_inbox_rows_map_totally_onto_records() -> None:
    def assert_rows(
        module: ModuleType,
        request: dict[str, object],
        project_key: str,
        captured: CapturedInboxResponse,
    ) -> None:
        result = module.execute(
            request, diagnosis_seeded_runner(module, project_key, captured.result)
        )

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED, (
            captured.capture
        )
        items = cast(
            list[dict[str, object]], captured.payload[module.STORE_INBOX_FIELD]
        )
        data = cast(dict[str, object], result[module.DATA_FIELD])
        records = cast(list[dict[str, object]], data[module.RECORDS_FIELD])
        assert len(records) == len(items)
        for record, item in zip(records, items, strict=True):
            assert record[module.RECORD_ID_FIELD] == item[module.STORE_ID_FIELD]
            assert record[module.SENDER_FIELD] == item[module.STORE_FROM_FIELD]
            assert record[module.BODY_FIELD] == item[module.STORE_BODY_FIELD]
            assert record[module.ACK_REQUIRED_FIELD] is (
                item[module.STORE_ACK_STATUS_FIELD]
                in module.STORE_ACK_REQUIRED_STATUSES
            )
            thread = item.get(module.STORE_THREAD_FIELD)
            if thread:
                assert record[module.CORRELATION_FIELD] == thread
            else:
                assert record[module.CORRELATION_FIELD] is None
                assert record[module.KIND_FIELD] == module.RecordKind.UNCLASSIFIED
                assert (
                    record[module.RECORD_SUBJECT_FIELD]
                    == item[module.STORE_SUBJECT_FIELD]
                )

    run_inbox_row_mapping(assert_rows)


def test_send_rejects_a_recipient_the_store_reads_as_several_agents() -> None:
    def assert_case(
        module: ModuleType, record: dict[str, object], project_key: str
    ) -> None:
        try:
            module.store_fields_for(record)
        except module.AgentMailError as error:
            assert error.status == module.ExecutionStatus.INVALID_SCHEMA
        else:
            raise AssertionError("a fan-out recipient reached the store fields")

        runner = diagnosis_seeded_runner(module, project_key)
        request = {
            module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION,
            module.OPERATION_FIELD: module.Operation.SEND.value,
            module.ARGUMENTS_FIELD: {module.RECORD_FIELD: record},
        }
        result = module.execute(request, runner)
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
        assert runner.calls == []

    run_recipient_boundary(assert_case)


def test_project_key_mapping() -> None:
    def assert_key(
        module: ModuleType,
        shape: str,
        payload: object,
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
        module: ModuleType,
        agent: str,
        project_key: str,
        exit_code: int,
        detail: str,
        malformed_text: str,
        unsupported_name: str,
    ) -> None:
        request = module.operation_request(module.Operation.INBOX, agent=agent)

        failed = module.execute(
            request,
            diagnosis_seeded_runner(
                module, project_key, failed_command_result(module, exit_code, detail)
            ),
        )
        assert failed[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
        assert failed[module.DETAIL_FIELD] == detail
        assert failed[module.COMMAND_EXIT_CODE_FIELD] == exit_code

        malformed = module.execute(
            request,
            diagnosis_seeded_runner(
                module, project_key, text_command_result(module, malformed_text)
            ),
        )
        assert malformed[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA

        unsupported = module.execute(
            {**request, module.OPERATION_FIELD: unsupported_name}, RecordingRunner([])
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

    run_store_response_cases(assert_case)
