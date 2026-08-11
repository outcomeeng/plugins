import json
from io import StringIO
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.prowl_environment import (
    public_agent_item,
    resolver_target_path,
)
from outcomeeng_testing.harnesses.coding_agents import load_agent_message
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
    expected_participants = [_expected_participant(module, agent) for agent in agents]
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


def test_resolver_reports_each_non_caller_match_cardinality_without_sending() -> None:
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(3)]

    for (
        cardinality,
        expected_status,
    ) in module.TARGET_RESOLUTION_STATUS_BY_CARDINALITY.items():
        target_path = resolver_target_path(module, agents, cardinality)
        runner = RecordingRunner([prowl_agents_command_result(module, agents)])
        result = module.resolve_target(
            target_path,
            cast(dict[str, str], agents[0][module.PANE_FIELD])[module.ID_FIELD],
            runner,
        )

        assert result[module.STATUS_FIELD] == expected_status
        assert (
            module.target_match_cardinality(len(result[module.CANDIDATES_FIELD]))
            is cardinality
        )
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


def test_repository_child_path_does_not_match_repository_root() -> None:
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(3)]
    repository = cast(
        str,
        cast(dict[str, object], agents[0][module.WORKTREE_FIELD])[
            module.ROOT_PATH_FIELD
        ],
    )
    runner = RecordingRunner([prowl_agents_command_result(module, agents)])

    result = module.resolve_target(
        f"{repository}/docs",
        cast(dict[str, str], agents[0][module.PANE_FIELD])[module.ID_FIELD],
        runner,
    )

    assert (
        result[module.STATUS_FIELD]
        == module.TARGET_RESOLUTION_STATUS_BY_CARDINALITY[
            module.TargetMatchCardinality.ZERO
        ]
    )
    assert result[module.CANDIDATES_FIELD] == []
    assert runner.calls == [
        (module.command_for(module.operation_request(module.Operation.AGENTS)), None)
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


def test_resolver_output_builds_and_delivers_one_message_envelope() -> None:
    prowl = load_prowl_environment()
    message = load_agent_message()
    agents = [public_agent_item(prowl, ordinal) for ordinal in range(2)]
    expected_participants = [_expected_participant(prowl, agent) for agent in agents]
    runner = RecordingRunner(
        [
            prowl_agents_command_result(prowl, agents),
            prowl_send_command_result(prowl, trailing_enter_sent=True),
        ]
    )
    resolved = prowl.resolve_target(
        expected_participants[1][prowl.WORKTREE_FIELD],
        expected_participants[0][prowl.PANE_FIELD],
        runner,
    )
    candidate = resolved[prowl.CANDIDATES_FIELD][0]
    participant = candidate[prowl.PARTICIPANT_FIELD]
    discovery = {
        message.SCHEMA_VERSION_FIELD: message.SCHEMA_VERSION,
        message.STATUS_FIELD: message.CallerStatus.PROWL_PANE,
        message.DETAIL_FIELD: None,
        message.CALLER_FIELD: resolved[prowl.CALLER_FIELD],
        message.TARGETS_FIELD: resolved[prowl.PARTICIPANTS_FIELD],
    }
    message_request = message.build_request(
        to_pane=participant[prowl.PANE_FIELD],
        kind=message.MessageKind.FACT,
        subject=participant[prowl.BRANCH_FIELD],
        facts=[participant[prowl.WORKTREE_FIELD]],
        request=None,
    )
    built = message.send_request(message_request, discovery)
    delivery = built[message.DELIVERY_FIELD]
    request = candidate[prowl.SEND_REQUEST_TEMPLATE_FIELD]
    request[prowl.ARGUMENTS_FIELD][prowl.TEXT_FIELD] = delivery[message.TEXT_FIELD]

    transport = prowl.execute(request, runner)
    result = message.delivery_result(
        built[message.ENVELOPE_FIELD],
        delivered=True,
        command_exit_code=transport[prowl.COMMAND_EXIT_CODE_FIELD],
        transport=transport,
    )

    envelope = built[message.ENVELOPE_FIELD]
    assert envelope[message.SENDER_FIELD] == expected_participants[0]
    assert envelope[message.RECIPIENT_FIELD] == expected_participants[1]
    assert delivery[message.TO_PANE_FIELD] == expected_participants[1][prowl.PANE_FIELD]
    assert (
        request[prowl.ARGUMENTS_FIELD][prowl.PANE_FIELD]
        == delivery[message.TO_PANE_FIELD]
    )
    assert result[message.STATUS_FIELD] == message.DeliveryStatus.DELIVERED
    assert result[message.TRANSPORT_FIELD] == transport
    assert runner.calls == [
        (prowl.command_for(prowl.operation_request(prowl.Operation.AGENTS)), None),
        (prowl.command_for(request), None),
    ]
