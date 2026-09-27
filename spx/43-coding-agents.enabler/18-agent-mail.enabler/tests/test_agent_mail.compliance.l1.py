import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.agent_mail import UNREADABLE_INPUT_FAMILIES
from outcomeeng_testing.harnesses.agent_mail import (
    CommandResultContract,
    RaisingRunner,
    RecordingRunner,
    common_dir_seeded_absent_store_runner,
    common_dir_seeded_runner,
    git_project_key_violation_source,
    load_agent_mail,
    mail_command_source_texts,
    raw_mail_shell_violation_source,
    raw_mail_violation_source,
    requests_over_every_operation,
    run_activity_timestamp_cases,
    run_cli_in_process,
    run_cli_with_only_adapter_programs,
    run_cli_without_executables,
    run_generated_identities,
    run_nul_argument_cases,
    run_runner_error_cases,
    run_unreadable_input_cases,
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
            module.Operation.REGISTER, program=program, agent_model=model
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


def test_no_operation_derives_session_state_from_the_activity_timestamp() -> None:
    def assert_case(
        module: ModuleType,
        request: dict[str, object],
        project_key: str,
        varied: CommandResultContract,
        moved: dict[str, str],
    ) -> None:
        captured = module.execute(
            request,
            common_dir_seeded_runner(
                module,
                project_key,
                store_response_result(module, module.Operation.REGISTER),
            ),
        )
        result = module.execute(
            request, common_dir_seeded_runner(module, project_key, varied)
        )

        # A stale or a fresh activity timestamp changes nothing the operation
        # concludes: the status and the data are the ones the captured
        # timestamps give, and the timestamps themselves pass through verbatim.
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert result[module.STATUS_FIELD] == captured[module.STATUS_FIELD]
        assert result[module.DATA_FIELD] == captured[module.DATA_FIELD]
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        for name, moment in moved.items():
            assert response[name] == moment
        assert set(result) == set(captured)

    run_activity_timestamp_cases(assert_case)


def test_a_request_that_does_not_parse_yields_a_versioned_failure() -> None:
    families: set[str] = set()

    def assert_case(module: ModuleType, family: str, text: str) -> None:
        families.add(family)
        runner = RecordingRunner([])
        exit_code, stdout = run_cli_in_process(module, text, runner)

        result = json.loads(stdout)
        assert exit_code != 0
        assert result[module.SCHEMA_VERSION_FIELD] == module.SCHEMA_VERSION
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
        assert result[module.OPERATION_FIELD] == module.UNKNOWN_OPERATION
        assert result[module.DETAIL_FIELD]
        assert module.FAILURE_RESULT_REQUIRED_FIELDS <= set(result)
        assert set(result) <= (
            module.FAILURE_RESULT_REQUIRED_FIELDS
            | module.FAILURE_RESULT_OPTIONAL_FIELDS
        )
        assert runner.calls == []

    run_unreadable_input_cases(assert_case)

    assert families == set(UNREADABLE_INPUT_FAMILIES)


def test_a_runner_error_of_any_class_maps_to_a_named_failure() -> None:
    def assert_case(
        module: ModuleType,
        request: dict[str, object],
        program: str,
        error: Exception,
        runner: RaisingRunner,
    ) -> None:
        result = module.execute(request, runner)

        if program == module.PUBLIC_GIT_COMMON_DIR_COMMAND[0]:
            expected = module.ExecutionStatus.REPOSITORY_UNRESOLVED
        elif isinstance(error, FileNotFoundError):
            expected = module.ExecutionStatus.STORE_UNAVAILABLE
        else:
            expected = module.ExecutionStatus.COMMAND_FAILED
        assert result[module.STATUS_FIELD] == expected, (program, type(error))
        assert result[module.SCHEMA_VERSION_FIELD] == module.SCHEMA_VERSION
        assert result[module.OPERATION_FIELD] == request[module.OPERATION_FIELD]
        assert result[module.DETAIL_FIELD]
        assert set(result) <= (
            module.FAILURE_RESULT_REQUIRED_FIELDS
            | module.FAILURE_RESULT_OPTIONAL_FIELDS
        )
        assert runner.calls[-1][0][0] == program
        assert json.loads(json.dumps(result)) == result

    run_runner_error_cases(assert_case)


def test_a_text_argument_carrying_nul_is_rejected_before_any_command() -> None:
    locations: set[str] = set()

    def assert_case(
        module: ModuleType, location: str, request: dict[str, object]
    ) -> None:
        runner = RecordingRunner([])
        result = module.execute(request, runner)
        locations.add(location)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA, (
            location
        )
        assert result[module.SCHEMA_VERSION_FIELD] == module.SCHEMA_VERSION
        assert runner.calls == [], location

    run_nul_argument_cases(assert_case)

    module = load_agent_mail()
    assert locations >= {
        f"{module.RECORD_FIELD}.{module.CORRELATION_FIELD}",
        f"{module.RECORD_FIELD}.{module.RECORD_SUBJECT_FIELD}",
        f"{module.RECORD_FIELD}.{module.BODY_FIELD}",
        module.AGENT_FIELD,
        module.PROGRAM_FIELD,
    }


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
    git_path, git_source = git_project_key_violation_source()
    assert module.git_project_key_violations(git_source) == [git_path]
