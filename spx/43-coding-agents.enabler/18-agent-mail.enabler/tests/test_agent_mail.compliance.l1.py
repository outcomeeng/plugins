import json
from types import ModuleType
from typing import cast

from outcomeeng_testing.harnesses.agent_mail import (
    common_dir_seeded_absent_store_runner,
    common_dir_seeded_runner,
    git_project_key_violation_source,
    load_agent_mail,
    mail_command_source_texts,
    raw_mail_violation_source,
    requests_over_every_operation,
    run_cli_with_only_adapter_programs,
    run_cli_without_executables,
    run_generated_identities,
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


def test_no_other_shipped_script_constructs_mail_commands_or_git_keys() -> None:
    module = load_agent_mail()

    assert module.raw_mail_command_violations(mail_command_source_texts()) == []
    assert module.git_project_key_violations(mail_command_source_texts()) == []

    raw_path, raw_source = raw_mail_violation_source()
    assert module.raw_mail_command_violations(raw_source) == [raw_path]
    git_path, git_source = git_project_key_violation_source()
    assert module.git_project_key_violations(git_source) == [git_path]
