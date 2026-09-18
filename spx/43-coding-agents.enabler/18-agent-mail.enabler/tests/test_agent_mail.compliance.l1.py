import json
from typing import cast

from outcomeeng_testing.harnesses.agent_mail import (
    AbsentExecutableRunner,
    RecordingRunner,
    agent_mail_source_texts,
    diagnosis_with_main_checkout,
    git_project_key_violation_source,
    json_command_result,
    load_agent_mail,
    mail_command_source_texts,
    raw_mail_violation_source,
    run_cli_without_executables,
)


def test_unavailable_results_admit_no_fallback() -> None:
    module = load_agent_mail()
    request = module.operation_request(module.Operation.INBOX, agent="Reader")

    completed = run_cli_without_executables(
        request, fallback_project="/fallback/project"
    )
    result = json.loads(completed.stdout)
    assert completed.returncode != 0
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.DIAGNOSIS_UNAVAILABLE
    assert module.PROJECT_KEY_FIELD not in result
    assert "/fallback/project" not in completed.stdout

    diagnosis = json_command_result(
        module, diagnosis_with_main_checkout(module, "/pool/main")
    )
    no_store = AbsentExecutableRunner(module.AM_COMMAND, [diagnosis])
    result = module.execute(request, no_store)
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.STORE_UNAVAILABLE
    assert [argv[0] for argv, _ in no_store.calls] == [
        module.SPX_COMMAND,
        module.AM_COMMAND,
    ]


def test_registration_result_carries_no_token() -> None:
    module = load_agent_mail()
    request = module.operation_request(
        module.Operation.REGISTER, agent="Officer", program="claude-code", model="opus"
    )
    token = "secret-registration-token"
    runner = RecordingRunner(
        [
            json_command_result(
                module, diagnosis_with_main_checkout(module, "/pool/main")
            ),
            json_command_result(
                module,
                {
                    module.STORE_ID_FIELD: 7,
                    module.STORE_NAME_FIELD: "Officer",
                    module.STORE_PROGRAM_FIELD: "claude-code",
                    module.STORE_MODEL_FIELD: "opus",
                    module.STORE_REGISTRATION_TOKEN_FIELD: token,
                },
            ),
        ]
    )

    result = module.execute(request, runner)

    response = cast(dict[str, object], result[module.RESPONSE_FIELD])
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert module.STORE_REGISTRATION_TOKEN_FIELD not in response
    assert token not in json.dumps(result)
    assert response[module.STORE_NAME_FIELD] == "Officer"


def test_no_other_shipped_script_constructs_mail_commands_or_git_keys() -> None:
    module = load_agent_mail()

    assert module.raw_mail_command_violations(mail_command_source_texts()) == []
    assert module.git_project_key_violations(mail_command_source_texts()) == []
    assert module.git_project_key_violations(agent_mail_source_texts()) == []

    raw_path, raw_source = raw_mail_violation_source()
    assert module.raw_mail_command_violations(raw_source) == [raw_path]
    git_path, git_source = git_project_key_violation_source()
    assert module.git_project_key_violations(git_source) == [git_path]
