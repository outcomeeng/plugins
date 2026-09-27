import json
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

from outcomeeng_testing.generators.agent_mail import SUBJECT_BRANCHES, SubjectShape
from outcomeeng_testing.harnesses.agent_mail import (
    AbsentExecutableRunner,
    CapturedStoreResponse,
    ListingReplay,
    RecordingRunner,
    acknowledgement_requirements,
    argv_option_values,
    common_dir_seeded_absent_store_runner,
    common_dir_seeded_runner,
    failed_command_result,
    git_location_variables,
    listing_captures,
    load_agent_mail,
    mail_pool,
    registration_response_named,
    run_cli_project_key,
    run_listing_mapping,
    run_listing_row_mapping,
    run_operation_mapping,
    run_project_key_mapping,
    run_recipient_boundary,
    run_registration_cases,
    run_store_error_cases,
    run_store_response_cases,
    run_subject_classification,
    store_error_capture_names,
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
    seen_booleans: set[tuple[str, object]] = set()
    command_paths: dict[str, tuple[str, ...]] = {}

    def assert_operation(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        seen_operations.add(operation.value)
        argv = module.command_for(request, project_key)
        contract = usage_contract_for(module, operation)
        reading = read_argv(contract, argv)
        bound = argv_option_values(contract, argv)
        command_paths[operation.value] = reading.command_path

        assert reading.command_path == (module.AM_COMMAND, *contract.command_path)
        assert reading.unknown_options == ()
        assert contract.required_options <= set(reading.options_seen)

        # The mapping law, option by option: each request field binds its own
        # option to its own value, a true boolean binds its flag and a false
        # one binds nothing, and no option appears that no field binds.
        expected: dict[str, list[str | None]] = {module.PROJECT_OPTION: [project_key]}
        if operation in module.JSON_OPERATIONS:
            expected[module.JSON_OPTION] = [None]
        positionals: tuple[str, ...] = ()
        if operation is module.Operation.SEND:
            record = cast(dict[str, object], arguments[module.RECORD_FIELD])
            seen_kinds.add(str(record[module.KIND_FIELD]))
            seen_booleans.add(
                (module.ACK_REQUIRED_FIELD, record[module.ACK_REQUIRED_FIELD])
            )
            for field_name in (
                module.SENDER_FIELD,
                module.RECIPIENT_FIELD,
                module.CORRELATION_FIELD,
                module.BODY_FIELD,
            ):
                expected[module.PUBLIC_AM_RECORD_OPTIONS[field_name]] = [
                    cast(str, record[field_name])
                ]
            expected[module.PUBLIC_AM_RECORD_OPTIONS[module.RECORD_SUBJECT_FIELD]] = [
                f"{module.KIND_PREFIX_OPEN}{record[module.KIND_FIELD]}"
                f"{module.KIND_PREFIX_CLOSE}{record[module.RECORD_SUBJECT_FIELD]}"
            ]
            if record[module.ACK_REQUIRED_FIELD] is True:
                expected[module.PUBLIC_AM_RECORD_OPTIONS[module.ACK_REQUIRED_FIELD]] = [
                    None
                ]
        else:
            for field_name, value in arguments.items():
                option = module.PUBLIC_AM_ARGUMENT_OPTIONS.get(field_name)
                if isinstance(value, bool):
                    seen_booleans.add((field_name, value))
                    if value:
                        expected[option] = [None]
                elif field_name == module.MESSAGE_ID_FIELD:
                    positionals = (str(value),)
                else:
                    expected[option] = [str(value)]
            if operation is module.Operation.LIST:
                mode = (
                    module.PUBLIC_AM_ARGUMENT_OPTIONS[module.ALL_RECORDS_FIELD]
                    if arguments.get(module.ALL_RECORDS_FIELD) is True
                    else module.UNJUDGED_LISTING_OPTION
                )
                expected[mode] = [None]
        assert bound == expected
        assert reading.positionals == positionals
        assert len(reading.positionals) == len(contract.required_positionals)

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
        if operation in module.MESSAGE_OPERATIONS:
            assert response[module.OUTPUT_FIELD] == payload
            assert data[module.MESSAGE_ID_FIELD] == arguments[module.MESSAGE_ID_FIELD]
            assert data[module.AGENT_FIELD] == arguments[module.AGENT_FIELD]
            return
        store = cast(dict[str, object], payload)
        if operation is module.Operation.LIST:
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
            assert [record[module.RECIPIENT_FIELD] for record in records] == [
                arguments[module.AGENT_FIELD] for _ in items
            ]
            assert [record[module.BODY_FIELD] for record in records] == [
                item.get(module.STORE_BODY_FIELD, "") for item in items
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
            assert data[module.RECORD_ID_FIELD] == store[module.STORE_ID_FIELD]

    run_operation_mapping(assert_operation)

    assert seen_operations == operations
    assert seen_kinds == {kind.value for kind in module.SENT_KINDS}
    for field_name in (*module.BOOLEAN_ARGUMENT_FIELDS, module.ACK_REQUIRED_FIELD):
        assert {(field_name, True), (field_name, False)} <= seen_booleans, field_name
    # Every operation binds its own store command; read and acknowledgement in
    # particular never share one.
    assert len(set(command_paths.values())) == len(operations)


def test_listing_requests_map_to_the_non_marking_surface_in_their_mode() -> None:
    module = load_agent_mail()
    captures = listing_captures(module)
    contract = usage_contract_for(module, module.Operation.LIST)
    # Options other listing fields bind, so what remains of a vector's flags is
    # the mode it lists in.
    bound_elsewhere = frozenset(
        {
            module.JSON_OPTION,
            module.PUBLIC_AM_ARGUMENT_OPTIONS[module.INCLUDE_BODIES_FIELD],
        }
    )

    def mode_flags(argv: tuple[str, ...]) -> frozenset[str]:
        seen = read_argv(contract, argv).options_seen
        return frozenset(o for o in seen if not contract.options[o]) - bound_elsewhere

    # The store's own vectors: the probe's complete listing names one mode
    # flag, its unjudged listings name another or leave the store's default.
    complete_modes = {mode_flags(captured.argv) for captured in captures.complete}
    unjudged_modes = {mode_flags(captured.argv) for captured in captures.unjudged} - {
        frozenset()
    }
    assert len(complete_modes) == 1
    assert len(unjudged_modes) == 1
    complete_mode = complete_modes.pop()
    unjudged_mode = unjudged_modes.pop()
    assert complete_mode and unjudged_mode
    assert not complete_mode & unjudged_mode
    listing_paths = {
        read_argv(contract, captured.argv).command_path
        for captured in (*captures.unjudged, *captures.complete)
    }
    assert len(listing_paths) == 1
    seen_modes: set[frozenset[str]] = set()

    def assert_request(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        argv = module.command_for(request, project_key)
        reading = read_argv(contract, argv)

        assert reading.command_path in listing_paths
        assert reading.unknown_options == ()
        expected_mode = (
            complete_mode
            if arguments.get(module.ALL_RECORDS_FIELD) is True
            else unjudged_mode
        )
        assert mode_flags(argv) == expected_mode, (arguments, argv)
        seen_modes.add(mode_flags(argv))

    run_listing_mapping(assert_request)

    assert seen_modes == {complete_mode, unjudged_mode}


def test_listing_rows_map_totally_onto_records() -> None:
    module = load_agent_mail()
    requirements = acknowledgement_requirements(module)
    captures = listing_captures(module)
    observed_requirements: dict[object, set[object]] = {}
    replayed: set[str] = set()

    def assert_rows(
        module: ModuleType, replay: ListingReplay, project_key: str
    ) -> None:
        captured = replay.captured
        arguments = cast(dict[str, object], replay.request[module.ARGUMENTS_FIELD])
        result = module.execute(
            replay.request,
            common_dir_seeded_runner(module, project_key, captured.result),
        )

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED, (
            captured.capture
        )
        replayed.add(captured.capture)
        items = cast(
            list[dict[str, object]], captured.payload[module.STORE_INBOX_FIELD]
        )
        data = cast(dict[str, object], result[module.DATA_FIELD])
        records = cast(list[dict[str, object]], data[module.RECORDS_FIELD])
        assert len(records) == len(items)
        for record, item in zip(records, items, strict=True):
            assert record[module.RECORD_ID_FIELD] == item[module.STORE_ID_FIELD]
            assert record[module.SENDER_FIELD] == item[module.STORE_FROM_FIELD]
            assert record[module.RECIPIENT_FIELD] == arguments[module.AGENT_FIELD]
            assert record[module.BODY_FIELD] == item.get(module.STORE_BODY_FIELD, "")
            observed_requirements.setdefault(item[module.STORE_ID_FIELD], set()).add(
                record[module.ACK_REQUIRED_FIELD]
            )
            thread = item.get(module.STORE_THREAD_FIELD)
            if thread:
                assert record[module.CORRELATION_FIELD] == thread
            else:
                assert record[module.CORRELATION_FIELD] is None
                assert record[module.KIND_FIELD] == module.RecordKind.UNCLASSIFIED
            if record[module.KIND_FIELD] == module.RecordKind.UNCLASSIFIED:
                assert (
                    record[module.RECORD_SUBJECT_FIELD]
                    == item[module.STORE_SUBJECT_FIELD]
                )
            else:
                assert item[module.STORE_SUBJECT_FIELD] == (
                    f"{module.KIND_PREFIX_OPEN}{record[module.KIND_FIELD]}"
                    f"{module.KIND_PREFIX_CLOSE}{record[module.RECORD_SUBJECT_FIELD]}"
                )

    run_listing_row_mapping(assert_rows)

    assert {
        captured.capture for captured in (*captures.unjudged, *captures.complete)
    } <= replayed
    # One message's acknowledgement requirement is one fact, whatever status a
    # listing reports it under before or after the acknowledgement; and it is
    # the requirement the store answered for that message when it was sent and
    # acknowledged, not a reading of the listing status.
    for message_id, values in observed_requirements.items():
        assert len(values) == 1, (message_id, values)
    for message_id, required in requirements.items():
        assert observed_requirements[message_id] == {required}, message_id


def test_listing_rows_classify_kind_and_subject_on_every_branch() -> None:
    seen: set[str] = set()

    def assert_case(
        module: ModuleType,
        branch: str,
        item: dict[str, object],
        recipient: str,
        shape: SubjectShape,
        threadless: bool,
    ) -> None:
        record = module.record_from_inbox_item(item, recipient=recipient)
        seen.add(branch)

        if threadless:
            assert record[module.KIND_FIELD] == module.RecordKind.UNCLASSIFIED
            assert record[module.RECORD_SUBJECT_FIELD] == shape.subject
            assert record[module.CORRELATION_FIELD] is None
        else:
            assert record[module.KIND_FIELD] == shape.kind, (branch, shape.subject)
            assert record[module.RECORD_SUBJECT_FIELD] == shape.record_subject, (
                branch,
                shape.subject,
            )
            assert record[module.CORRELATION_FIELD] == item[module.STORE_THREAD_FIELD]
        assert record[module.RECIPIENT_FIELD] == recipient

    run_subject_classification(assert_case)

    assert seen == set(SUBJECT_BRANCHES)


def test_registration_carries_no_name_and_returns_the_assigned_name() -> None:
    def assert_case(
        module: ModuleType,
        request: dict[str, object],
        requested: str,
        assigned: str,
        project_key: str,
    ) -> None:
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        contract = usage_contract_for(module, module.Operation.REGISTER)
        argv = module.command_for(request, project_key)

        # The vector binds exactly the options the request's own fields bind,
        # so the store's name option is absent and the store assigns the name.
        assert set(argv_option_values(contract, argv)) == {
            module.PROJECT_OPTION,
            module.JSON_OPTION,
            *(module.PUBLIC_AM_ARGUMENT_OPTIONS[name] for name in arguments),
        }

        named = {
            **request,
            module.ARGUMENTS_FIELD: {**arguments, module.AGENT_FIELD: requested},
        }
        refusing = RecordingRunner([])
        refused = module.execute(named, refusing)
        assert refused[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
        assert refusing.calls == []

        runner = common_dir_seeded_runner(
            module, project_key, registration_response_named(module, assigned)
        )
        result = module.execute(request, runner)
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        data = cast(dict[str, object], result[module.DATA_FIELD])
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        assert data[module.AGENT_FIELD] == assigned
        assert response[module.STORE_NAME_FIELD] == assigned

    run_registration_cases(assert_case)


def test_send_rejects_a_recipient_the_store_reads_as_several_agents() -> None:
    def assert_case(
        module: ModuleType, record: dict[str, object], project_key: str
    ) -> None:
        with pytest.raises(module.AgentMailError) as rejection:
            module.store_fields_for(record)
        assert rejection.value.status == module.ExecutionStatus.INVALID_SCHEMA

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
        request = module.operation_request(module.Operation.LIST, agent=agent)
        if expected_key is None:
            with pytest.raises(module.AgentMailError) as unresolved:
                module.project_key_from_common_dir(output)
            assert (
                unresolved.value.status == module.ExecutionStatus.REPOSITORY_UNRESOLVED
            ), shape
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

    for case, (exit_code, payload) in inside.items():
        assert exit_code == 0, (case, payload, redirections)
        assert payload[module.PROJECT_KEY_FIELD] == expected_key, (case, payload)

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
        request = module.operation_request(module.Operation.LIST, agent=agent)

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


def test_captured_store_failures_map_to_named_failures_verbatim() -> None:
    replayed: set[str] = set()

    def assert_case(
        module: ModuleType,
        request: dict[str, object],
        project_key: str,
        captured: CapturedStoreResponse,
    ) -> None:
        result = module.execute(
            request, common_dir_seeded_runner(module, project_key, captured.result)
        )
        replayed.add(captured.capture)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
        assert result[module.OPERATION_FIELD] == request[module.OPERATION_FIELD]
        assert result[module.COMMAND_EXIT_CODE_FIELD] == captured.result.returncode
        assert result[module.DETAIL_FIELD] == captured.result.stderr.strip()
        assert module.PROJECT_KEY_FIELD not in result

    run_store_error_cases(assert_case)

    assert replayed == store_error_capture_names()
