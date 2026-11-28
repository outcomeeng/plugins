import io
import json
import subprocess
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.agent_mail import operation_requests
from outcomeeng_testing.harnesses.cli_usage import read_argv
from outcomeeng_testing.harnesses.agent_mail import (
    ROOT,
    NamedRepositoryCase,
    RecordingRunner,
    ScriptedClock,
    captured_inbox_responses_with_bodies,
    common_dir_seeded_absent_store_runner,
    common_dir_seeded_runner,
    decoy_workspace,
    event_page_with_ids,
    event_usage_contract,
    failed_command_result,
    full_listing_past,
    git_project_key_violation_source,
    inbox_response_with_ids,
    label_collision_variant,
    load_agent_mail,
    mail_command_source_texts,
    mail_pool,
    message_usage_contract,
    nul_tainted_requests,
    raw_mail_qualified_shell_violation_sources,
    raw_mail_shell_violation_source,
    raw_mail_violation_source,
    request_naming_repository,
    requests_over_every_operation,
    run_cli_project_key,
    run_cli_project_key_recording_opens,
    run_cli_with_only_adapter_programs,
    run_cli_without_executables,
    run_generated_identities,
    run_hung_command_under_bound,
    run_invalid_repository_cases,
    run_label_targeting_cases,
    run_named_repository_cases,
    run_operation_mapping,
    run_wait_cases,
    single_message_with_id,
    unresolved_then_fallback_runner,
    store_error_runner,
    store_program_names,
    store_response_payload,
    store_response_result,
    store_response_text,
    text_command_result,
    usage_contract_for,
    wait_request,
    wait_requests_without_valid_timeout,
    wait_store_commands,
    wait_store_runner,
    wait_workspace,
    workspace_entries,
)


def test_unavailable_results_admit_no_fallback() -> None:
    def assert_case(
        module: ModuleType, agent: str, program: str, model: str, project_key: str
    ) -> None:
        for request in requests_over_every_operation(module):
            operation = module.Operation(request[module.OPERATION_FIELD])

            completed = run_cli_without_executables(
                request, fallback_project=project_key
            )
            result = json.loads(completed.stdout)
            assert completed.returncode != 0, operation
            assert (
                result[module.STATUS_FIELD]
                == module.ExecutionStatus.REPOSITORY_UNRESOLVED
            )
            assert module.PROJECT_KEY_FIELD not in result
            assert project_key not in completed.stdout

            no_store = common_dir_seeded_absent_store_runner(module, project_key)
            result = module.execute(request, no_store)
            assert (
                result[module.STATUS_FIELD] == module.ExecutionStatus.STORE_UNAVAILABLE
            ), operation
            assert [argv[0] for argv, _ in no_store.calls] == [
                module.PUBLIC_GIT_COMMON_DIR_COMMAND[0],
                module.AM_COMMAND,
            ]

    run_generated_identities(assert_case)


def test_a_repository_that_is_no_absolute_path_string_never_reaches_a_command() -> None:
    def assert_case(module: ModuleType, value: object) -> None:
        for request in requests_over_every_operation(module):
            operation = module.Operation(request[module.OPERATION_FIELD])
            runner = RecordingRunner([])

            result = module.execute(
                request_naming_repository(module, request, value), runner
            )

            assert result[module.STATUS_FIELD] == (
                module.ExecutionStatus.INVALID_SCHEMA
            ), (operation, value)
            assert module.PROJECT_KEY_FIELD not in result, (operation, value)
            assert runner.calls == [], (operation, value)

        if isinstance(value, str):
            exit_code, payload = run_cli_project_key(ROOT, repository=value)
            assert exit_code != 0, value
            assert payload[module.STATUS_FIELD] == (
                module.ExecutionStatus.INVALID_SCHEMA
            ), value
            assert module.PROJECT_KEY_FIELD not in payload, value

    run_invalid_repository_cases(assert_case)


def test_a_named_path_that_resolves_to_no_repository_admits_no_fallback() -> None:
    def assert_case(module: ModuleType, case: NamedRepositoryCase) -> None:
        for request in requests_over_every_operation(module):
            operation = module.Operation(request[module.OPERATION_FIELD])
            arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
            runner = unresolved_then_fallback_runner(
                module, case, store_response_result(module, operation, arguments)
            )

            result = module.execute(
                request_naming_repository(module, request, case.repository), runner
            )

            assert result[module.STATUS_FIELD] == (
                module.ExecutionStatus.REPOSITORY_UNRESOLVED
            ), operation
            assert module.PROJECT_KEY_FIELD not in result, operation
            assert case.other_key not in json.dumps(result), operation
            # The failed lookup is the only command: no second lookup answers
            # from the working directory and no store command follows.
            assert len(runner.calls) == 1, (operation, runner.calls)

    run_named_repository_cases(assert_case)

    module = load_agent_mail()
    with mail_pool() as pool:
        unresolved = {
            "directory that is no repository": run_cli_project_key(
                pool.main_checkout, repository=pool.outside
            ),
            "path that does not exist": run_cli_project_key(
                pool.main_checkout, repository=pool.outside / "absent-checkout"
            ),
        }

    # The working directory is a repository, so a key that fell back to it
    # would resolve; each named path instead resolves nothing.
    for case, (exit_code, payload) in unresolved.items():
        assert exit_code != 0, (case, payload)
        assert payload[module.STATUS_FIELD] == (
            module.ExecutionStatus.REPOSITORY_UNRESOLVED
        ), (case, payload)
        assert module.PROJECT_KEY_FIELD not in payload, (case, payload)


def test_a_send_from_a_name_the_store_does_not_hold_registers_nobody() -> None:
    def assert_case(module: ModuleType, case: NamedRepositoryCase) -> None:
        send = module.Operation.SEND
        register = module.Operation.REGISTER
        send_path = (module.AM_COMMAND, *usage_contract_for(module, send).command_path)
        register_path = (
            module.AM_COMMAND,
            *usage_contract_for(module, register).command_path,
        )
        sends = [
            request
            for request in requests_over_every_operation(module)
            if request[module.OPERATION_FIELD] == send
        ]
        assert len(sends) == 1

        for request in (
            sends[0],
            request_naming_repository(module, sends[0], case.repository),
        ):
            runner = common_dir_seeded_runner(
                module,
                case.project_key,
                failed_command_result(module, case.exit_code, case.detail),
            )

            result = module.execute(request, runner)

            assert result[module.STATUS_FIELD] == (
                module.ExecutionStatus.COMMAND_FAILED
            )
            assert result[module.DETAIL_FIELD] == case.detail
            assert result[module.COMMAND_EXIT_CODE_FIELD] == case.exit_code
            # The lookup and the send are the only commands: the store's
            # refusal ends the operation, and no registration precedes a retry.
            assert len(runner.calls) == 2, runner.calls
            sent = runner.calls[1][0]
            assert sent[: len(send_path)] == send_path
            assert all(
                argv[: len(register_path)] != register_path for argv, _ in runner.calls
            )

    run_named_repository_cases(assert_case)


def test_the_adapter_reads_no_overlay_or_configuration_to_select_a_repository() -> None:
    module = load_agent_mail()

    with mail_pool() as pool, decoy_workspace(pool) as workspace:
        roots = (workspace, pool.outside)
        named = run_cli_project_key_recording_opens(
            workspace, pool.main_checkout, roots
        )
        standing = run_cli_project_key_recording_opens(pool.main_checkout, None, roots)
        expected_key = str(pool.bare)
        decoy_key = str(pool.foreign)

    # The decoys sit beside the working directory and at and above the named
    # repository, each naming another repository: a reader that selected a
    # repository from one would report that key or open the file.
    for case, (exit_code, payload, opened) in {
        "named from a working directory beside decoys": named,
        "standing in a checkout holding decoys": standing,
    }.items():
        assert exit_code == 0, (case, payload)
        assert payload[module.PROJECT_KEY_FIELD] == expected_key, (case, payload)
        assert payload[module.PROJECT_KEY_FIELD] != decoy_key, (case, payload)
        assert opened == [], (case, opened)


def test_registration_result_carries_no_token() -> None:
    def assert_case(
        module: ModuleType, agent: str, program: str, model: str, project_key: str
    ) -> None:
        request = module.operation_request(
            module.Operation.REGISTER, agent=agent, program=program, agent_model=model
        )
        captured = cast(
            dict[str, object], store_response_payload(module, module.Operation.REGISTER)
        )
        token = cast(str, captured[module.STORE_REGISTRATION_TOKEN_FIELD])
        runner = common_dir_seeded_runner(
            module,
            project_key,
            store_response_result(module, module.Operation.REGISTER),
        )

        result = module.execute(request, runner)

        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert module.STORE_REGISTRATION_TOKEN_FIELD not in response
        assert token not in json.dumps(result)
        assert response[module.STORE_NAME_FIELD] == captured[module.STORE_NAME_FIELD]

    run_generated_identities(assert_case)


def test_registrations_result_carries_no_token() -> None:
    def assert_case(
        module: ModuleType, agent: str, program: str, model: str, project_key: str
    ) -> None:
        token = cast(
            dict[str, object], store_response_payload(module, module.Operation.REGISTER)
        )[module.STORE_REGISTRATION_TOKEN_FIELD]
        listing = cast(
            list[dict[str, object]],
            store_response_payload(module, module.Operation.REGISTRATIONS),
        )
        variant = [
            {**entry, module.STORE_REGISTRATION_TOKEN_FIELD: token} for entry in listing
        ]
        runner = common_dir_seeded_runner(
            module,
            project_key,
            module.CommandResult(0, json.dumps(variant), ""),
        )

        result = module.execute(
            module.operation_request(module.Operation.REGISTRATIONS), runner
        )

        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        entries = cast(list[dict[str, object]], response[module.STORE_LISTING_FIELD])
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert [entry[module.STORE_NAME_FIELD] for entry in entries] == [
            entry[module.STORE_NAME_FIELD] for entry in listing
        ]
        assert all(
            module.STORE_REGISTRATION_TOKEN_FIELD not in entry for entry in entries
        )
        assert cast(str, token) not in json.dumps(result)

    run_generated_identities(assert_case)


def test_operations_reach_no_program_outside_the_adapters_own_commands() -> None:
    module = load_agent_mail()

    # The store's own captures name the program the adapter must reach, so a
    # constant renamed to another program fails here rather than passing a
    # probe that stubs whatever the source declares.
    assert module.AM_COMMAND in store_program_names(module)

    def assert_case(
        module: ModuleType, agent: str, program: str, model: str, project_key: str
    ) -> None:
        for request in requests_over_every_operation(module):
            operation = module.Operation(request[module.OPERATION_FIELD])

            completed = run_cli_with_only_adapter_programs(
                request,
                project_key=project_key,
                store_response=store_response_text(module, operation),
            )
            result = json.loads(completed.stdout)

            assert completed.returncode == 0, (operation, completed.stderr)
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            assert result[module.PROJECT_KEY_FIELD] == project_key

    run_generated_identities(assert_case)


def test_no_operation_invokes_a_command_the_adapter_does_not_own() -> None:
    module = load_agent_mail()

    # The injected runner is the one boundary every external call crosses, so a
    # call whose result the adapter discarded is still recorded here. The
    # stub-path case above observes only that each operation completes where the
    # adapter's own two programs resolve, which an ignored invocation survives;
    # the programs the runner recorded are what an ignored invocation cannot.
    adapter_programs = frozenset({module.GIT_COMMAND, module.AM_COMMAND})

    def assert_case(
        module: ModuleType, agent: str, program: str, model: str, project_key: str
    ) -> None:
        for request in requests_over_every_operation(module):
            operation = module.Operation(request[module.OPERATION_FIELD])
            arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
            runner = common_dir_seeded_runner(
                module, project_key, store_response_result(module, operation, arguments)
            )

            result = module.execute(request, runner)

            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            invoked = frozenset(argv[0] for argv, _ in runner.calls)
            assert invoked <= adapter_programs, (operation, invoked)

    run_generated_identities(assert_case)


def test_no_other_shipped_script_constructs_mail_commands_or_git_keys() -> None:
    module = load_agent_mail()

    assert module.raw_mail_command_violations(mail_command_source_texts()) == []
    assert module.git_project_key_violations(mail_command_source_texts()) == []

    raw_path, raw_source = raw_mail_violation_source()
    assert module.raw_mail_command_violations(raw_source) == [raw_path]
    shell_path, shell_source = raw_mail_shell_violation_source()
    assert module.raw_mail_command_violations(shell_source) == [shell_path]
    for (
        qualified_path,
        qualified_source,
    ) in raw_mail_qualified_shell_violation_sources():
        assert module.raw_mail_command_violations(qualified_source) == [qualified_path]
    git_path, git_source = git_project_key_violation_source()
    assert module.git_project_key_violations(git_source) == [git_path]


def test_a_label_in_a_target_position_is_passed_as_the_identity_never_resolved() -> (
    None
):
    def assert_case(
        module: ModuleType,
        project_key: str,
        label: str,
        sender: str,
        recipient: str,
        collision: str,
        message_id: int,
    ) -> None:
        def send(from_agent: str, to_agent: str) -> dict[str, object]:
            return module.operation_request(
                module.Operation.SEND,
                record=module.message_record(
                    kind=module.RecordKind.FACT,
                    correlation=collision,
                    sender=from_agent,
                    recipient=to_agent,
                    subject=collision,
                    body=collision,
                ),
            )

        targets = [
            (
                module.operation_request(
                    module.Operation.REGISTER,
                    agent=label,
                    program=collision,
                    agent_model=collision,
                ),
                module.NAME_OPTION,
            ),
            (
                send(label, recipient),
                module.PUBLIC_AM_RECORD_OPTIONS[module.SENDER_FIELD],
            ),
            (
                send(sender, label),
                module.PUBLIC_AM_RECORD_OPTIONS[module.RECIPIENT_FIELD],
            ),
            (
                module.operation_request(module.Operation.LIST, agent=label),
                module.PUBLIC_AM_ARGUMENT_OPTIONS[module.AGENT_FIELD],
            ),
            (
                module.operation_request(
                    module.Operation.READ, agent=label, message_id=message_id
                ),
                module.PUBLIC_AM_ARGUMENT_OPTIONS[module.AGENT_FIELD],
            ),
            (
                module.operation_request(
                    module.Operation.ACKNOWLEDGE, agent=label, message_id=message_id
                ),
                module.PUBLIC_AM_ARGUMENT_OPTIONS[module.AGENT_FIELD],
            ),
        ]
        for request, option in targets:
            operation = module.Operation(request[module.OPERATION_FIELD])
            arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
            runner = common_dir_seeded_runner(
                module, project_key, store_response_result(module, operation, arguments)
            )

            result = module.execute(request, runner)

            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED, (
                operation
            )
            assert [argv[0] for argv, _ in runner.calls] == [
                module.GIT_COMMAND,
                module.AM_COMMAND,
            ], (operation, runner.calls)
            store_argv = runner.calls[1][0]
            assert module.attached_option(option, label) in store_argv, operation
            assert sum(label in part for part in store_argv) == 1, operation

    run_label_targeting_cases(assert_case)


def test_a_store_label_never_selects_the_sender_or_recipient_of_a_record() -> None:
    def assert_case(
        module: ModuleType,
        project_key: str,
        label: str,
        sender: str,
        recipient: str,
        collision: str,
        message_id: int,
    ) -> None:
        # The sender label is another agent's stable name, the shape a label
        # that selected by name would be fooled by.
        inbox_request = module.operation_request(
            module.Operation.LIST, agent=recipient, include_bodies=True
        )
        inbox_arguments = cast(dict[str, object], inbox_request[module.ARGUMENTS_FIELD])
        inbox_variant = label_collision_variant(
            module,
            module.Operation.LIST,
            inbox_arguments,
            sender_label=collision,
            recipient_label=label,
        )
        inbox_runner = common_dir_seeded_runner(
            module, project_key, inbox_variant.result
        )

        inbox_result = module.execute(inbox_request, inbox_runner)

        assert inbox_result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        items = cast(
            list[dict[str, object]], inbox_variant.payload[module.STORE_INBOX_FIELD]
        )
        records = cast(
            list[dict[str, object]],
            cast(dict[str, object], inbox_result[module.DATA_FIELD])[
                module.RECORDS_FIELD
            ],
        )
        assert len(records) == len(items) > 0, inbox_variant.capture
        for record, item in zip(records, items, strict=True):
            assert record[module.SENDER_FIELD] == item[module.STORE_FROM_FIELD], (
                inbox_variant.capture
            )
            assert record[module.RECIPIENT_FIELD] == recipient
        assert len(inbox_runner.calls) == 2

        send_request = module.operation_request(
            module.Operation.SEND,
            record=module.message_record(
                kind=module.RecordKind.FACT,
                correlation=str(message_id),
                sender=sender,
                recipient=recipient,
                subject=label,
                body=label,
            ),
        )
        send_variant = label_collision_variant(
            module,
            module.Operation.SEND,
            cast(dict[str, object], send_request[module.ARGUMENTS_FIELD]),
            sender_label=collision,
            recipient_label=collision,
        )
        send_runner = common_dir_seeded_runner(module, project_key, send_variant.result)

        send_result = module.execute(send_request, send_runner)

        assert send_result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        record = cast(
            dict[str, object],
            cast(dict[str, object], send_result[module.DATA_FIELD])[
                module.RECORD_FIELD
            ],
        )
        assert record[module.SENDER_FIELD] == sender, send_variant.capture
        assert record[module.RECIPIENT_FIELD] == recipient, send_variant.capture
        assert len(send_runner.calls) == 2

    run_label_targeting_cases(assert_case)


def test_an_empty_string_is_rejected_in_every_text_field_but_the_display_name() -> None:
    module = load_agent_mail()
    rejected_fields: set[str] = set()
    for request in operation_requests(module):
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        for field_name in module.TEXT_ARGUMENT_FIELDS & set(arguments):
            violating = {
                **request,
                module.ARGUMENTS_FIELD: {**arguments, field_name: ""},
            }
            if field_name == module.DISPLAY_NAME_FIELD:
                module.command_for(violating, "/registered/project")
                continue
            rejected_fields.add(field_name)
            try:
                module.command_for(violating, "/registered/project")
            except module.AgentMailError as error:
                assert error.status is module.ExecutionStatus.INVALID_SCHEMA
            else:
                raise AssertionError(f"{field_name} accepted an empty string")

    assert rejected_fields == module.TEXT_ARGUMENT_FIELDS - {module.DISPLAY_NAME_FIELD}


def test_a_wait_without_a_valid_timeout_runs_no_store_command() -> None:
    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        for request in wait_requests_without_valid_timeout(module, agent):
            clock = ScriptedClock()
            runner = wait_store_runner(module, project_key, clock)

            result = module.execute(request, runner, clock)

            assert result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
            assert runner.calls == [], request
            assert clock.sleeps == []

    run_wait_cases(assert_case)


def test_no_store_command_inside_a_wait_outlives_the_timeout() -> None:
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
            request = wait_request(module, agent, after_id, timeout_seconds)
            for replies, repeating in (
                ((None,), None),
                ((), capture.result),
                ((capture.result, None), None),
            ):
                clock = ScriptedClock()
                runner = wait_store_runner(
                    module, project_key, clock, *replies, repeating=repeating
                )

                result = module.execute(request, runner, clock)

                data = cast(dict[str, object], result[module.DATA_FIELD])
                assert data[module.OUTCOME_FIELD] == module.WaitOutcome.TIMEOUT
                store_calls = list(zip(runner.started, runner.timeouts))[1:]
                assert store_calls
                for started, bound in store_calls:
                    assert bound is not None
                    assert started + bound <= timeout_seconds, capture.capture
                assert clock.current <= timeout_seconds

    run_wait_cases(assert_case)


def test_a_store_command_that_outlives_its_bound_is_stopped_at_the_bound() -> None:
    module = load_agent_mail()

    observation = run_hung_command_under_bound(module, 1)

    assert observation.timed_out
    assert observation.elapsed_seconds < module.COMMAND_TIMEOUT_SECONDS


def test_a_wait_keeps_no_state_past_its_run() -> None:
    """wait-stateless: a wait leaves no file behind, runs only the listing, the
    delivery-events page, and the single-message read, and every wait pages
    the delivery events from their start, whatever an earlier wait read."""

    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        listing = module.PUBLIC_AM_COMMAND_PREFIXES[module.Operation.WAIT]
        events_contract = event_usage_contract(module)
        prefixes = (
            listing,
            module.WAIT_EVENTS_COMMAND_PREFIX,
            module.WAIT_MESSAGE_COMMAND_PREFIX,
        )
        for capture in captured_inbox_responses_with_bodies(module):
            ids = sorted(
                cast(int, row[module.STORE_ID_FIELD])
                for row in cast(
                    list[dict[str, object]], capture.payload[module.STORE_INBOX_FIELD]
                )
            )
            last = ids[-1]
            cut_off = full_listing_past(module, capture, last)
            events = event_page_with_ids(
                module, [last, last + 1], cursor_offset=3, next_cursor=None
            )
            message = single_message_with_id(module, last + 1)
            scripts = (
                ((), capture.result, ids[0] - 1),
                ((), capture.result, last),
                ((cut_off.result, events.result, message.result), None, last),
                ((cut_off.result, events.result, message.result), None, last),
            )
            for replies, repeating, after_id in scripts:
                with wait_workspace() as workspace:
                    before = workspace_entries(workspace)
                    clock = ScriptedClock()
                    runner = wait_store_runner(
                        module, project_key, clock, *replies, repeating=repeating
                    )

                    result = module.execute(
                        wait_request(module, agent, after_id, timeout_seconds),
                        runner,
                        clock,
                    )

                    after = workspace_entries(workspace)
                assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
                assert after == before, capture.capture
                store_commands = wait_store_commands(runner)
                assert store_commands
                for argv in store_commands:
                    assert any(argv[: len(prefix)] == prefix for prefix in prefixes)
                pages = [
                    argv
                    for argv in store_commands
                    if argv[: len(module.WAIT_EVENTS_COMMAND_PREFIX)]
                    == module.WAIT_EVENTS_COMMAND_PREFIX
                ]
                if pages:
                    first = read_argv(events_contract, pages[0])
                    assert module.AFTER_OPTION not in first.options_seen, pages[0]

    run_wait_cases(assert_case)


def test_a_wait_past_more_than_a_full_listing_returns_the_first_record_past_its_id() -> (
    None
):
    """wait-large-inbox: a requester holding more than 1000 records past the
    id gets the first record past the id, read through the single-message
    read, never through a command that changes read state."""
    module = load_agent_mail()
    judging = {
        usage_contract_for(module, operation).command_path
        for operation in (module.Operation.READ, module.Operation.ACKNOWLEDGE)
    }
    message_contract = message_usage_contract(module)

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
            held = list(range(after_id + 1, after_id + 2 + module.WAIT_LISTING_LIMIT))
            assert len(held) > module.WAIT_LISTING_LIMIT
            listing = full_listing_past(module, capture, after_id)
            events = event_page_with_ids(
                module, [after_id, *held], cursor_offset=0, next_cursor=None
            )
            message = single_message_with_id(module, after_id + 1)
            clock = ScriptedClock()
            runner = wait_store_runner(
                module,
                project_key,
                clock,
                listing.result,
                events.result,
                message.result,
            )

            result = module.execute(
                wait_request(module, agent, after_id, timeout_seconds), runner, clock
            )

            data = cast(dict[str, object], result[module.DATA_FIELD])
            record = cast(dict[str, object], data[module.RECORD_FIELD])
            assert data[module.OUTCOME_FIELD] == module.WaitOutcome.RECEIVED
            assert record[module.RECORD_ID_FIELD] == after_id + 1, listing.capture
            read = wait_store_commands(runner)[-1]
            reading = read_argv(message_contract, read)
            assert reading.command_path == (
                module.AM_COMMAND,
                *message_contract.command_path,
            )
            assert reading.command_path[1:] not in judging
            for argv in wait_store_commands(runner):
                assert tuple(argv[1:3]) not in judging, argv

    run_wait_cases(assert_case)


def test_a_wait_command_that_reaches_its_bound_with_time_left_ends_no_wait() -> None:
    """wait-command-bound: a listing or an events page that reaches the
    per-command bound while time remains ends no wait; the wait reads again at
    its next interval and ends as a timeout only at its deadline."""

    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        bound = module.COMMAND_TIMEOUT_SECONDS
        interval = module.WAIT_POLL_INTERVAL_SECONDS
        timeout = timeout_seconds + 2 * (bound + interval)
        for capture in captured_inbox_responses_with_bodies(module):
            ids = sorted(
                cast(int, row[module.STORE_ID_FIELD])
                for row in cast(
                    list[dict[str, object]], capture.payload[module.STORE_INBOX_FIELD]
                )
            )
            after_id = ids[-1]
            cut_off = full_listing_past(module, capture, after_id)
            events = event_page_with_ids(
                module, [after_id, after_id + 1], cursor_offset=5, next_cursor=None
            )
            message = single_message_with_id(module, after_id + 1)
            later = inbox_response_with_ids(module, capture, [after_id, after_id + 1])
            for replies in (
                (None, later.result),
                (cut_off.result, None, cut_off.result, events.result, message.result),
            ):
                clock = ScriptedClock()
                runner = wait_store_runner(module, project_key, clock, *replies)

                result = module.execute(
                    wait_request(module, agent, after_id, timeout), runner, clock
                )

                data = cast(dict[str, object], result[module.DATA_FIELD])
                record = cast(dict[str, object], data[module.RECORD_FIELD])
                assert data[module.OUTCOME_FIELD] == module.WaitOutcome.RECEIVED
                assert record[module.RECORD_ID_FIELD] == after_id + 1
                assert clock.sleeps and clock.sleeps[0] == interval, clock.sleeps
                for given in runner.timeouts[1:]:
                    assert given is not None and given <= bound

            clock = ScriptedClock()
            runner = wait_store_runner(module, project_key, clock, repeating_hangs=True)
            result = module.execute(
                wait_request(module, agent, after_id, timeout), runner, clock
            )
            data = cast(dict[str, object], result[module.DATA_FIELD])
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            assert data[module.OUTCOME_FIELD] == module.WaitOutcome.TIMEOUT
            assert clock.current >= timeout
            assert len(runner.calls[1:]) > 1
            for started, given in list(zip(runner.started, runner.timeouts))[1:]:
                assert given is not None and started + given <= timeout

    run_wait_cases(assert_case)


def test_a_wait_pages_delivery_events_by_next_cursor_and_reads_message_ids() -> None:
    """wait-event-fields: the first events page carries no `--after`, each
    later page the `next_cursor` of the page before, the pages run one after
    another with no sleep, and the record read is the event's `message_id`,
    never its cursor."""

    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        events_contract = event_usage_contract(module)
        message_contract = message_usage_contract(module)
        for capture in captured_inbox_responses_with_bodies(module):
            after_id = max(
                cast(int, row[module.STORE_ID_FIELD])
                for row in cast(
                    list[dict[str, object]], capture.payload[module.STORE_INBOX_FIELD]
                )
            )
            cut_off = full_listing_past(module, capture, after_id)
            offset = 1_000
            first_cursor = after_id + offset + 17
            second_cursor = first_cursor + 40
            first = event_page_with_ids(
                module,
                [after_id - 2, after_id - 1],
                cursor_offset=offset,
                next_cursor=first_cursor,
            )
            second = event_page_with_ids(
                module, [after_id], cursor_offset=offset, next_cursor=second_cursor
            )
            third = event_page_with_ids(
                module,
                [after_id + 1, after_id + 3],
                cursor_offset=offset,
                next_cursor=None,
            )
            message = single_message_with_id(module, after_id + 1)
            clock = ScriptedClock()
            runner = wait_store_runner(
                module,
                project_key,
                clock,
                cut_off.result,
                first.result,
                second.result,
                third.result,
                message.result,
            )

            result = module.execute(
                wait_request(module, agent, after_id, timeout_seconds), runner, clock
            )

            data = cast(dict[str, object], result[module.DATA_FIELD])
            assert data[module.OUTCOME_FIELD] == module.WaitOutcome.RECEIVED
            commands = wait_store_commands(runner)
            pages = [read_argv(events_contract, argv) for argv in commands[1:4]]
            for page, argv in zip(pages, commands[1:4]):
                assert page.command_path == (
                    module.AM_COMMAND,
                    *events_contract.command_path,
                ), argv
                assert page.unknown_options == ()
                assert module.JSON_OPTION in page.options_seen
            assert module.AFTER_OPTION not in pages[0].options_seen
            assert (
                module.attached_option(module.AFTER_OPTION, first_cursor)
                in (commands[2])
            )
            assert (
                module.attached_option(module.AFTER_OPTION, second_cursor)
                in (commands[3])
            )
            read = read_argv(message_contract, commands[4])
            assert read.positionals == (str(after_id + 1),), commands[4]
            assert clock.sleeps == []

    run_wait_cases(assert_case)


def test_a_text_argument_carrying_a_nul_byte_never_reaches_a_store_command() -> None:
    def assert_operation(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        tainted = nul_tainted_requests(module, request)
        # A request with no arguments, the bare registrations listing, carries
        # no text a NUL byte could ride in.
        assert tainted or not request[module.ARGUMENTS_FIELD]
        for variant in tainted:
            runner = common_dir_seeded_runner(module, project_key)
            result = module.execute(variant, runner)

            assert (
                result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
            ), variant
            assert runner.calls == []

    run_operation_mapping(assert_operation)


def test_an_over_long_thread_id_never_reaches_a_store_command() -> None:
    module = load_agent_mail()
    limit = module.THREAD_ID_MAXIMUM_LENGTH

    def assert_operation(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        if module.Operation(request[module.OPERATION_FIELD]) is not (
            module.Operation.SEND
        ):
            return
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        record = cast(dict[str, object], arguments[module.RECORD_FIELD])

        def sent_with(correlation: str) -> dict[str, object]:
            return {
                **request,
                module.ARGUMENTS_FIELD: {
                    **arguments,
                    module.RECORD_FIELD: {
                        **record,
                        module.CORRELATION_FIELD: correlation,
                    },
                },
            }

        refused = common_dir_seeded_runner(module, project_key)
        result = module.execute(sent_with("a" * (limit + 1)), refused)
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
        assert refused.calls == []

        escaped = common_dir_seeded_runner(module, project_key)
        result = module.execute(sent_with("\u00e9" * limit), escaped)
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
        assert escaped.calls == []

        at_limit = common_dir_seeded_runner(
            module,
            project_key,
            store_response_result(module, module.Operation.SEND, arguments),
        )
        result = module.execute(sent_with("a" * limit), at_limit)
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert len(at_limit.calls) == 2

    run_operation_mapping(assert_operation)


def test_every_result_carries_the_versioned_shape_and_a_runner_error_is_named() -> None:
    module = load_agent_mail()

    def assert_operation(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        for error, status in (
            (FileNotFoundError("absent"), module.ExecutionStatus.STORE_UNAVAILABLE),
            (PermissionError("denied"), module.ExecutionStatus.STORE_UNAVAILABLE),
            (
                subprocess.TimeoutExpired(module.AM_COMMAND, 1),
                module.ExecutionStatus.COMMAND_FAILED,
            ),
            (RuntimeError("broken"), module.ExecutionStatus.COMMAND_FAILED),
            (ValueError("odd"), module.ExecutionStatus.COMMAND_FAILED),
        ):
            clock = ScriptedClock()
            result = module.execute(
                request,
                store_error_runner(module, project_key, error),
                clock,
            )

            if module.Operation(request[module.OPERATION_FIELD]) is (
                module.Operation.WAIT
            ) and isinstance(error, subprocess.TimeoutExpired):
                # A wait command that reaches its bound while time remains ends
                # no wait: the wait reads again and ends as a timeout at its
                # deadline (wait-command-bound).
                arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
                data = cast(dict[str, object], result[module.DATA_FIELD])
                assert result[module.STATUS_FIELD] == (
                    module.ExecutionStatus.SUCCEEDED
                ), request
                assert data[module.OUTCOME_FIELD] == module.WaitOutcome.TIMEOUT
                assert clock.current >= cast(
                    int, arguments[module.TIMEOUT_SECONDS_FIELD]
                )
            else:
                assert result[module.STATUS_FIELD] == status, (request, error)
            assert module.validate_operation_result(result) == result
            assert result[module.SCHEMA_VERSION_FIELD] == module.SCHEMA_VERSION

    run_operation_mapping(assert_operation)

    unparsed = io.StringIO()
    code = module.main(
        [module.CliOperation.RUN.value],
        stdin=io.StringIO("{"),
        stdout=unparsed,
    )
    emitted = json.loads(unparsed.getvalue())
    assert code != 0
    assert emitted[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
    assert module.validate_operation_result(emitted) == emitted


def test_no_operation_derives_liveness_from_the_stores_activity_timestamp() -> None:
    module = load_agent_mail()
    register = module.Operation.REGISTER
    request = next(
        candidate
        for candidate in requests_over_every_operation(module)
        if candidate[module.OPERATION_FIELD] == register
    )
    arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
    payload = cast(
        dict[str, object], store_response_payload(module, register, arguments)
    )
    activity_fields = [name for name in payload if "active" in name]
    assert activity_fields
    other_instant = cast(
        dict[str, object],
        store_response_payload(
            module,
            module.Operation.SEND,
            {},
        ),
    )["created_ts"]

    def assert_operation(
        module: ModuleType, _request: dict[str, object], project_key: str
    ) -> None:
        data: list[object] = []
        for variant in (
            payload,
            {**payload, **{name: other_instant for name in activity_fields}},
            {**payload, **{name: None for name in activity_fields}},
        ):
            runner = common_dir_seeded_runner(
                module, project_key, text_command_result(module, json.dumps(variant))
            )
            result = module.execute(request, runner)
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            data.append(result[module.DATA_FIELD])
        assert data[0] == data[1] == data[2]

    run_operation_mapping(assert_operation)


def test_only_read_and_acknowledge_reach_a_command_that_changes_read_state() -> None:
    module = load_agent_mail()
    judging = {module.Operation.READ, module.Operation.ACKNOWLEDGE}
    judging_paths = {
        usage_contract_for(module, operation).command_path for operation in judging
    }
    seen: set[object] = set()

    def assert_operation(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        operation = module.Operation(request[module.OPERATION_FIELD])
        contract = usage_contract_for(module, operation)
        reading = read_argv(contract, module.command_for(request, project_key))
        seen.add(operation)
        assert (reading.command_path[1:] in judging_paths) is (operation in judging)
        if operation not in judging:
            assert reading.positionals == ()

    run_operation_mapping(assert_operation)

    assert seen == set(module.Operation)


def test_a_list_request_carries_bodies_unless_it_declines_them() -> None:
    module = load_agent_mail()
    contract = usage_contract_for(module, module.Operation.LIST)
    forms: set[bool] = set()

    def assert_list(
        module: ModuleType, request: dict[str, object], project_key: str
    ) -> None:
        if module.Operation(request[module.OPERATION_FIELD]) is not (
            module.Operation.LIST
        ):
            return
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        for choice in (None, True, False):
            variant_arguments = {
                name: value
                for name, value in arguments.items()
                if name != module.INCLUDE_BODIES_FIELD
            }
            if choice is not None:
                variant_arguments[module.INCLUDE_BODIES_FIELD] = choice
            variant = {**request, module.ARGUMENTS_FIELD: variant_arguments}
            reading = read_argv(contract, module.command_for(variant, project_key))
            forms.add(variant_arguments.get(module.ALL_RECORDS_FIELD) is True)

            assert reading.unknown_options == ()
            assert (module.INCLUDE_BODIES_OPTION in reading.options_seen) is (
                choice is not False
            ), variant_arguments

    run_operation_mapping(assert_list)

    assert forms == {False, True}


def test_a_wait_lists_at_most_once_per_wait_interval() -> None:
    def assert_case(
        module: ModuleType, agent: str, project_key: str, timeout_seconds: int
    ) -> None:
        interval = module.WAIT_POLL_INTERVAL_SECONDS
        for capture in captured_inbox_responses_with_bodies(module):
            after_id = max(
                cast(int, row[module.STORE_ID_FIELD])
                for row in cast(
                    list[dict[str, object]], capture.payload[module.STORE_INBOX_FIELD]
                )
            )
            for timeout in (timeout_seconds, timeout_seconds + 2 * interval):
                clock = ScriptedClock()
                runner = wait_store_runner(
                    module, project_key, clock, repeating=capture.result
                )

                result = module.execute(
                    wait_request(module, agent, after_id, timeout), runner, clock
                )

                data = cast(dict[str, object], result[module.DATA_FIELD])
                listings = runner.started[1:]
                gaps = [
                    later - earlier for earlier, later in zip(listings, listings[1:])
                ]
                assert data[module.OUTCOME_FIELD] == module.WaitOutcome.TIMEOUT
                assert listings[0] == 0, capture.capture
                assert all(gap >= interval for gap in gaps), listings
                assert timeout - listings[-1] <= interval, listings
                if timeout < interval:
                    assert len(listings) == 1, listings

    run_wait_cases(assert_case)
