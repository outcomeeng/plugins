import json
from io import StringIO
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.prowl_environment import public_agent_item
from outcomeeng_testing.harnesses.prowl_environment import (
    RecordingRunner,
    load_prowl_environment,
    prowl_agents_command_result,
    prowl_send_command_result,
)


def _expected_participant(
    module: ModuleType, agent: dict[str, object]
) -> dict[str, str]:
    pane = cast(dict[str, str], agent[module.PANE_FIELD])
    worktree = cast(dict[str, str], agent[module.WORKTREE_FIELD])
    project = cast(dict[str, str], agent[module.PROJECT_FIELD])
    run = cast(dict[str, str], agent[module.RUN_FIELD])
    return {
        module.AGENT_FIELD: cast(str, agent[module.ID_FIELD]),
        module.PANE_FIELD: pane[module.ID_FIELD],
        module.WORKTREE_FIELD: worktree[module.PATH_FIELD],
        module.BRANCH_FIELD: project[module.BRANCH_FIELD],
        module.REPOSITORY_FIELD: worktree[module.ROOT_PATH_FIELD],
        module.RUN_FIELD: run[module.ID_FIELD],
    }


def test_resolver_returns_complete_inventory_and_one_non_caller_template() -> None:
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(3)]
    expected_participants = [
        _expected_participant(module, agent) for agent in agents
    ]
    runner = RecordingRunner([prowl_agents_command_result(module, agents)])
    output = StringIO()

    exit_code = module.main(
        [module.CliOperation.RESOLVE_TARGET],
        runner=runner,
        stdin=StringIO(
            json.dumps(
                {
                    module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION,
                    module.PATH_FIELD: (
                        cast(dict[str, object], agents[1][module.WORKTREE_FIELD])[
                            module.PATH_FIELD
                        ]
                        + "/src"
                    ),
                }
            )
        ),
        stdout=output,
        environment={
            module.PROWL_PANE_ID_ENV: cast(
                dict[str, str], agents[0][module.PANE_FIELD]
            )[module.ID_FIELD]
        },
    )

    result = json.loads(output.getvalue())
    candidate = result[module.CANDIDATES_FIELD][0]
    template = candidate[module.SEND_REQUEST_TEMPLATE_FIELD]
    assert exit_code == 0
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert result[module.INVENTORY_FIELD][module.STATUS_FIELD] == str(
        module.ExecutionStatus.SUCCEEDED
    )
    assert result[module.PARTICIPANTS_FIELD] == expected_participants
    assert result[module.CALLER_FIELD] == expected_participants[0]
    assert candidate[module.PARTICIPANT_FIELD] == expected_participants[1]
    assert template[module.ARGUMENTS_FIELD] == {
        module.PANE_FIELD: expected_participants[1][module.PANE_FIELD],
        module.TEXT_FIELD: None,
        module.NO_WAIT_FIELD: True,
    }
    assert runner.calls == [
        (module.command_for(module.operation_request(module.Operation.AGENTS)), None)
    ]


def test_resolver_reports_zero_and_multiple_non_caller_matches_without_sending() -> (
    None
):
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(3)]

    for target_path, expected_status, expected_count in (
        (
            cast(dict[str, object], agents[0][module.WORKTREE_FIELD])[
                module.PATH_FIELD
            ],
            module.ExecutionStatus.IDENTITY_UNAVAILABLE,
            0,
        ),
        (
            cast(dict[str, object], agents[0][module.WORKTREE_FIELD])[
                module.ROOT_PATH_FIELD
            ],
            module.ExecutionStatus.IDENTITY_AMBIGUOUS,
            2,
        ),
    ):
        runner = RecordingRunner([prowl_agents_command_result(module, agents)])
        result = module.resolve_target(
            cast(str, target_path),
            cast(dict[str, str], agents[0][module.PANE_FIELD])[module.ID_FIELD],
            runner,
        )

        assert result[module.STATUS_FIELD] == expected_status
        assert len(result[module.CANDIDATES_FIELD]) == expected_count
        assert all(
            candidate[module.PARTICIPANT_FIELD][module.PANE_FIELD]
            != result[module.CALLER_FIELD][module.PANE_FIELD]
            for candidate in result[module.CANDIDATES_FIELD]
        )
        assert runner.calls == [
            (
                module.command_for(module.operation_request(module.Operation.AGENTS)),
                None,
            )
        ]


def test_filled_resolver_template_returns_one_complete_checked_send_result() -> None:
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(2)]
    runner = RecordingRunner(
        [
            prowl_agents_command_result(module, agents),
            prowl_send_command_result(module, trailing_enter_sent=True),
        ]
    )
    resolved = module.resolve_target(
        cast(
            str,
            cast(dict[str, object], agents[1][module.WORKTREE_FIELD])[
                module.PATH_FIELD
            ],
        ),
        cast(dict[str, str], agents[0][module.PANE_FIELD])[module.ID_FIELD],
        runner,
    )
    request = resolved[module.CANDIDATES_FIELD][0][module.SEND_REQUEST_TEMPLATE_FIELD]
    request[module.ARGUMENTS_FIELD][module.TEXT_FIELD] = "complete result ready"

    result = module.execute(request, runner)

    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert result[module.COMMAND_EXIT_CODE_FIELD] == 0
    assert result[module.RESPONSE_FIELD][module.DATA_FIELD][module.INPUT_FIELD][
        module.TRAILING_ENTER_SENT_FIELD
    ]
    assert runner.calls == [
        (module.command_for(module.operation_request(module.Operation.AGENTS)), None),
        (module.command_for(request), None),
    ]
