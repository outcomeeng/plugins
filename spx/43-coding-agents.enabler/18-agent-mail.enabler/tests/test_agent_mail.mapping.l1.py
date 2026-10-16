import json
from pathlib import Path
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.agent_mail import operation_requests
from outcomeeng_testing.harnesses.agent_mail import (
    AbsentExecutableRunner,
    CapturedInboxResponse,
    CapturedLabelResponse,
    RecordingRunner,
    ScriptedClock,
    captured_inbox_responses_with_bodies,
    common_dir_seeded_absent_store_runner,
    common_dir_seeded_runner,
    failed_command_result,
    git_location_variables,
    inbox_response_up_to,
    inbox_response_with_ids,
    load_agent_mail,
    mail_pool,
    run_cli_project_key,
    run_inbox_row_mapping,
    run_label_response_mapping,
    run_operation_mapping,
    run_project_key_mapping,
    run_recipient_boundary,
    run_store_response_cases,
    run_wait_cases,
    store_response_payload,
    store_response_result,
    text_command_result,
    usage_contract_for,
    wait_request,
    wait_store_runner,
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
        elif operation is module.Operation.REGISTER:
            assert (
                module.attached_option(
                    module.NAME_OPTION, arguments[module.AGENT_FIELD]
                )
                in argv
            )
            display_name_option = module.PUBLIC_AM_ARGUMENT_OPTIONS[
                module.DISPLAY_NAME_FIELD
            ]
            assert (display_name_option in reading.options_seen) is (
                module.DISPLAY_NAME_FIELD in arguments
            )
            for field_name in (
                module.PROGRAM_FIELD,
                module.MODEL_FIELD,
                module.TASK_FIELD,
                module.DISPLAY_NAME_FIELD,
            ):
                if field_name in arguments:
                    assert (
                        module.attached_option(
                            module.PUBLIC_AM_ARGUMENT_OPTIONS[field_name],
                            arguments[field_name],
                        )
                        in argv
                    )
        else:
            if operation is module.Operation.RECEIPT:
                assert reading.positionals == (str(arguments[module.MESSAGE_ID_FIELD]),)
            if operation is module.Operation.WAIT:
                bodies_option = module.PUBLIC_AM_ARGUMENT_OPTIONS[
                    module.INCLUDE_BODIES_FIELD
                ]
                limit_option = module.PUBLIC_AM_ARGUMENT_OPTIONS[module.LIMIT_FIELD]
                assert bodies_option in reading.options_seen
                assert module.PUBLIC_AM_ARGUMENT_OPTIONS[
                    module.UNREAD_ONLY_FIELD
                ] not in (reading.options_seen)
                assert argv[argv.index(limit_option) + 1] == str(
                    module.WAIT_LISTING_LIMIT
                )
            assert (
                module.attached_option(
                    module.PUBLIC_AM_ARGUMENT_OPTIONS[module.AGENT_FIELD],
                    arguments[module.AGENT_FIELD],
                )
                in argv
            )

        payload = store_response_payload(module, operation, arguments)
        runner = common_dir_seeded_runner(
            module, project_key, store_response_result(module, operation, arguments)
        )
        result = module.execute(request, runner)

        assert runner.calls == [
            (module.PUBLIC_GIT_COMMON_DIR_COMMAND, None),
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
        if operation is module.Operation.WAIT:
            items = cast(list[dict[str, object]], store[module.STORE_INBOX_FIELD])
            later = [
                item
                for item in items
                if cast(int, item[module.STORE_ID_FIELD])
                > cast(int, arguments[module.AFTER_ID_FIELD])
            ]
            first = min(later, key=lambda item: cast(int, item[module.STORE_ID_FIELD]))
            record = cast(dict[str, object], data[module.RECORD_FIELD])
            assert response == store
            assert data[module.OUTCOME_FIELD] == module.WaitOutcome.RECEIVED.value
            assert record[module.RECORD_ID_FIELD] == first[module.STORE_ID_FIELD]
            (bound,) = cast(list[float], runner.timeouts[1:])
            assert 0 < bound <= cast(int, arguments[module.TIMEOUT_SECONDS_FIELD])
        elif operation is module.Operation.INBOX:
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


def test_store_labels_map_verbatim_beside_the_message_record() -> None:
    def assert_case(
        module: ModuleType, project_key: str, captured: CapturedLabelResponse
    ) -> None:
        runner = common_dir_seeded_runner(module, project_key, captured.result)

        result = module.execute(captured.request, runner)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED, (
            captured.capture
        )
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        data = cast(dict[str, object], result[module.DATA_FIELD])
        label_fields = (
            module.STORE_SENDER_DISPLAY_NAME_FIELD,
            module.STORE_TO_DISPLAY_NAMES_FIELD,
        )
        if captured.operation is module.Operation.REGISTER:
            assert (
                response[module.STORE_DISPLAY_NAME_FIELD]
                == captured.payload[module.STORE_DISPLAY_NAME_FIELD]
            ), captured.capture
        elif captured.operation is module.Operation.SEND:
            for field_name in label_fields:
                assert field_name in response, (captured.capture, field_name)
                assert response[field_name] == captured.payload[field_name], (
                    captured.capture,
                    field_name,
                )
            record = cast(dict[str, object], data[module.RECORD_FIELD])
            assert set(record) == module.RECORD_FIELDS, captured.capture
        else:
            captured_items = cast(
                list[dict[str, object]], captured.payload[module.STORE_INBOX_FIELD]
            )
            returned_items = cast(
                list[dict[str, object]], response[module.STORE_INBOX_FIELD]
            )
            records = cast(list[dict[str, object]], data[module.RECORDS_FIELD])
            assert len(returned_items) == len(captured_items) == len(records)
            for returned, item, record in zip(
                returned_items, captured_items, records, strict=True
            ):
                for field_name in label_fields:
                    assert field_name in returned, (captured.capture, field_name)
                    assert returned[field_name] == item[field_name], (
                        captured.capture,
                        field_name,
                    )
                assert set(record) == module.RECORD_FIELDS, captured.capture

    run_label_response_mapping(assert_case)


def test_inbox_rows_map_totally_onto_records() -> None:
    def assert_rows(
        module: ModuleType,
        request: dict[str, object],
        project_key: str,
        captured: CapturedInboxResponse,
    ) -> None:
        result = module.execute(
            request, common_dir_seeded_runner(module, project_key, captured.result)
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

        runner = common_dir_seeded_runner(module, project_key)
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
        output: str,
        expected_key: str | None,
        agent: str,
    ) -> None:
        runner = RecordingRunner([text_command_result(module, output)])
        request = module.operation_request(module.Operation.INBOX, agent=agent)
        if expected_key is None:
            try:
                module.project_key_from_common_dir(output)
            except module.AgentMailError as error:
                assert error.status == module.ExecutionStatus.REPOSITORY_UNRESOLVED
            else:
                raise AssertionError(f"shape {shape} resolved a key from no directory")
            result = module.execute(request, runner)
            assert (
                result[module.STATUS_FIELD]
                == module.ExecutionStatus.REPOSITORY_UNRESOLVED
            )
            assert runner.calls == [(module.PUBLIC_GIT_COMMON_DIR_COMMAND, None)]
        else:
            assert module.project_key_from_common_dir(output) == expected_key
            assert module.resolve_project_key(runner) == expected_key

    run_project_key_mapping(assert_key)


def test_every_checkout_shape_of_one_pool_maps_to_one_project_key() -> None:
    module = load_agent_mail()

    with mail_pool() as pool:
        shapes = (
            pool.bare,
            pool.main_checkout,
            pool.linked_worktree,
            pool.symlinked_worktree,
        )
        keys = {shape.name: run_cli_project_key(shape) for shape in shapes}
        outside_code, outside_payload = run_cli_project_key(pool.outside)
        expected_key = str(pool.bare)
        symlinked_route = str(pool.symlinked_worktree)
        physical_route = str(pool.linked_worktree)

    assert len(keys) == len(shapes)
    for name, (exit_code, payload) in keys.items():
        assert exit_code == 0, (name, payload)
        assert payload[module.PROJECT_KEY_FIELD] == expected_key, (name, payload)

    # The symlinked route is a second spelling of one checkout, so a key that
    # carried the path a caller typed would differ from its physical route's.
    assert symlinked_route != physical_route

    assert outside_code != 0
    assert module.PROJECT_KEY_FIELD not in outside_payload
    assert (
        outside_payload[module.STATUS_FIELD]
        == module.ExecutionStatus.REPOSITORY_UNRESOLVED
    )


def test_git_location_variables_leave_the_project_key_on_its_own_repository() -> None:
    # The domain is the set Git itself confirms: every candidate Git's own
    # `rev-parse --local-env-vars` reports, widened by its discovery-bounding
    # variables, that redirects raw Git away from the working directory's own
    # repository. Each confirmed case carries the working directory and the
    # caller's environment that redirected raw Git, so the adapter is read
    # against Git's behaviour rather than against its own removal list, and the
    # complete set together follows as one further case.
    module = load_agent_mail()
    combined = "every-confirmed-variable"

    with mail_pool() as pool:
        confirmed = git_location_variables(pool)
        cases: list[tuple[str, Path, dict[str, str]]] = [
            (probe.variable, probe.working_directory, probe.environment)
            for probe in confirmed
        ]
        every_variable = {
            variable: value
            for probe in confirmed
            for variable, value in probe.environment.items()
        }
        cases += [
            (combined, probe.working_directory, every_variable) for probe in confirmed
        ]
        inside = {
            (case, str(directory)): run_cli_project_key(directory, environment)
            for case, directory, environment in cases
        }
        outside = {
            case: run_cli_project_key(pool.outside, environment)
            for case, _, environment in cases
        }
        expected_key = str(pool.bare)
        redirections = {probe.variable: probe.outcome for probe in confirmed}

    for inside_case, (exit_code, payload) in inside.items():
        assert exit_code == 0, (inside_case, payload, redirections)
        assert payload[module.PROJECT_KEY_FIELD] == expected_key, (
            inside_case,
            payload,
        )

    for outside_case, (exit_code, payload) in outside.items():
        assert exit_code != 0, (outside_case, payload)
        assert module.PROJECT_KEY_FIELD not in payload, (outside_case, payload)
        assert (
            payload[module.STATUS_FIELD] == module.ExecutionStatus.REPOSITORY_UNRESOLVED
        ), (outside_case, payload)

    # Git confirmed each of these against its own answer, so a removal list that
    # dropped one would leave the shape that confirmed it resolving the wrong
    # repository or none at all.
    assert set(redirections) <= set(module.GIT_LOCATION_VARIABLES), redirections


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
            common_dir_seeded_runner(
                module, project_key, failed_command_result(module, exit_code, detail)
            ),
        )
        assert failed[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
        assert failed[module.DETAIL_FIELD] == detail
        assert failed[module.COMMAND_EXIT_CODE_FIELD] == exit_code

        malformed = module.execute(
            request,
            common_dir_seeded_runner(
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

        no_repository = module.execute(
            request,
            AbsentExecutableRunner(module.PUBLIC_GIT_COMMON_DIR_COMMAND[0]),
        )
        assert (
            no_repository[module.STATUS_FIELD]
            == module.ExecutionStatus.REPOSITORY_UNRESOLVED
        )
        no_store = module.execute(
            request, common_dir_seeded_absent_store_runner(module, project_key)
        )
        assert no_store[module.STATUS_FIELD] == module.ExecutionStatus.STORE_UNAVAILABLE

    run_store_response_cases(assert_case)


def test_an_empty_display_name_reaches_the_store_as_an_empty_value() -> None:
    module = load_agent_mail()
    project_key = "/registered/project"
    registrations = [
        cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        for request in operation_requests(module)
        if module.Operation(request[module.OPERATION_FIELD])
        is module.Operation.REGISTER
    ]
    empty = [
        arguments
        for arguments in registrations
        if arguments.get(module.DISPLAY_NAME_FIELD) == ""
    ]
    absent = [
        arguments
        for arguments in registrations
        if module.DISPLAY_NAME_FIELD not in arguments
    ]
    option = module.PUBLIC_AM_ARGUMENT_OPTIONS[module.DISPLAY_NAME_FIELD]

    assert empty
    assert absent
    for arguments in empty:
        request = module.operation_request(
            module.Operation.REGISTER,
            **{
                name: arguments[field]
                for name, field in module.ARGUMENT_NAMES.items()
                if field in arguments
            },
        )
        argv = module.command_for(request, project_key)
        assert module.attached_option(option, "") in argv
        assert sum(1 for word in argv if word.startswith(option)) == 1
    for arguments in absent:
        request = module.operation_request(
            module.Operation.REGISTER,
            **{
                name: arguments[field]
                for name, field in module.ARGUMENT_NAMES.items()
                if field in arguments
            },
        )
        argv = module.command_for(request, project_key)
        assert not any(word.startswith(option) for word in argv)


def test_wait_maps_the_inbox_to_the_first_later_record_or_a_named_outcome() -> None:
    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        for capture in captured_inbox_responses_with_bodies(module):
            rows = cast(
                list[dict[str, object]], capture.payload[module.STORE_INBOX_FIELD]
            )
            ids = sorted(cast(int, row[module.STORE_ID_FIELD]) for row in rows)
            for after_id in (ids[0] - 1, *ids):
                later = [row_id for row_id in ids if row_id > after_id]
                clock = ScriptedClock()
                runner = wait_store_runner(
                    module, project_key, clock, repeating=capture.result
                )

                result = module.execute(
                    wait_request(module, agent, after_id, timeout_seconds),
                    runner,
                    clock,
                )

                data = cast(dict[str, object], result[module.DATA_FIELD])
                assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
                if not later:
                    assert data[module.OUTCOME_FIELD] == module.WaitOutcome.TIMEOUT
                    assert module.RECORD_FIELD not in data
                    assert clock.current >= timeout_seconds, capture.capture
                    continue
                first = next(
                    row for row in rows if row[module.STORE_ID_FIELD] == later[0]
                )
                record = cast(dict[str, object], data[module.RECORD_FIELD])
                assert data[module.OUTCOME_FIELD] == module.WaitOutcome.RECEIVED
                assert record[module.RECORD_ID_FIELD] == later[0]
                assert record[module.SENDER_FIELD] == first[module.STORE_FROM_FIELD]
                assert (
                    record[module.CORRELATION_FIELD] == first[module.STORE_THREAD_FIELD]
                )
                assert record[module.BODY_FIELD] == first[module.STORE_BODY_FIELD]
                assert record[module.RECIPIENT_FIELD] == agent
                assert clock.sleeps == []

    run_wait_cases(assert_case)


def test_wait_returns_a_record_that_arrives_before_the_timeout() -> None:
    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        if timeout_seconds <= module.WAIT_POLL_INTERVAL_SECONDS:
            return
        for capture in captured_inbox_responses_with_bodies(module):
            ids = sorted(
                cast(int, row[module.STORE_ID_FIELD])
                for row in cast(
                    list[dict[str, object]], capture.payload[module.STORE_INBOX_FIELD]
                )
            )
            after_id = ids[0]
            earlier = inbox_response_up_to(module, capture, after_id)
            clock = ScriptedClock()
            runner = wait_store_runner(
                module, project_key, clock, earlier.result, capture.result
            )

            result = module.execute(
                wait_request(module, agent, after_id, timeout_seconds), runner, clock
            )

            data = cast(dict[str, object], result[module.DATA_FIELD])
            record = cast(dict[str, object], data[module.RECORD_FIELD])
            assert data[module.OUTCOME_FIELD] == module.WaitOutcome.RECEIVED
            assert record[module.RECORD_ID_FIELD] == ids[1], earlier.capture
            assert len(runner.calls) == 3
            assert 0 < clock.current <= timeout_seconds

    run_wait_cases(assert_case)


def test_wait_names_a_listing_that_cannot_reach_back_to_the_id() -> None:
    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        for capture in captured_inbox_responses_with_bodies(module):
            after_id = max(
                cast(int, row[module.STORE_ID_FIELD])
                for row in cast(
                    list[dict[str, object]], capture.payload[module.STORE_INBOX_FIELD]
                )
            )
            cut_off = inbox_response_with_ids(
                module,
                capture,
                list(range(after_id + 1, after_id + 1 + module.WAIT_LISTING_LIMIT)),
            )
            reaching = inbox_response_with_ids(
                module,
                capture,
                list(range(after_id, after_id + module.WAIT_LISTING_LIMIT)),
            )

            clock = ScriptedClock()
            cut_off_runner = wait_store_runner(
                module, project_key, clock, cut_off.result
            )
            cut_off_result = module.execute(
                wait_request(module, agent, after_id, timeout_seconds),
                cut_off_runner,
                clock,
            )
            reaching_runner = wait_store_runner(
                module, project_key, ScriptedClock(), reaching.result
            )
            reaching_result = module.execute(
                wait_request(module, agent, after_id, timeout_seconds),
                reaching_runner,
                ScriptedClock(),
            )

            cut_off_data = cast(dict[str, object], cut_off_result[module.DATA_FIELD])
            reaching_data = cast(dict[str, object], reaching_result[module.DATA_FIELD])
            assert cut_off_data[module.OUTCOME_FIELD] == module.WaitOutcome.UNREACHABLE
            assert module.RECORD_FIELD not in cut_off_data, cut_off.capture
            assert len(cut_off_runner.calls) == 2
            assert reaching_data[module.OUTCOME_FIELD] == module.WaitOutcome.RECEIVED
            record = cast(dict[str, object], reaching_data[module.RECORD_FIELD])
            assert record[module.RECORD_ID_FIELD] == after_id + 1, reaching.capture

    run_wait_cases(assert_case)
