import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.agent_mail import operation_requests
from outcomeeng_testing.harnesses.agent_mail import (
    common_dir_seeded_absent_store_runner,
    common_dir_seeded_runner,
    git_project_key_violation_source,
    label_collision_variant,
    load_agent_mail,
    mail_command_source_texts,
    raw_mail_violation_source,
    requests_over_every_operation,
    run_cli_with_only_adapter_programs,
    run_cli_without_executables,
    run_generated_identities,
    run_label_targeting_cases,
    store_program_names,
    store_response_payload,
    store_response_result,
    store_response_text,
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
                module.operation_request(module.Operation.INBOX, agent=label),
                module.PUBLIC_AM_ARGUMENT_OPTIONS[module.AGENT_FIELD],
            ),
            (
                module.operation_request(
                    module.Operation.RECEIPT, agent=label, message_id=message_id
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
            module.Operation.INBOX, agent=recipient, include_bodies=True
        )
        inbox_arguments = cast(dict[str, object], inbox_request[module.ARGUMENTS_FIELD])
        inbox_variant = label_collision_variant(
            module,
            module.Operation.INBOX,
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
