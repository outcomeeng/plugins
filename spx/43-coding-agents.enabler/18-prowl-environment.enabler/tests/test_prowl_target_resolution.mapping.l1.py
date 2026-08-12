import json
from io import StringIO
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.prowl_environment import (
    public_agent_item,
    resolver_caller_environments,
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


def _expected_resolution_status(module: ModuleType, cardinality: object) -> object:
    if cardinality is module.TargetMatchCardinality.ZERO:
        return module.ExecutionStatus.IDENTITY_UNAVAILABLE
    if cardinality is module.TargetMatchCardinality.ONE:
        return module.ExecutionStatus.SUCCEEDED
    if cardinality is module.TargetMatchCardinality.MULTIPLE:
        return module.ExecutionStatus.IDENTITY_AMBIGUOUS
    raise AssertionError(f"Unknown target-match cardinality: {cardinality}")


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

    for cardinality in module.TargetMatchCardinality:
        target_path = resolver_target_path(module, agents, cardinality)
        runner = RecordingRunner([prowl_agents_command_result(module, agents)])
        output = StringIO()
        exit_code = module.main(
            [module.CliOperation.RESOLVE_TARGET],
            runner=runner,
            stdin=StringIO(
                json.dumps(
                    {
                        module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION,
                        module.PATH_FIELD: target_path,
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

        assert exit_code == 0
        assert result[module.STATUS_FIELD] == _expected_resolution_status(
            module, cardinality
        )
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


def test_resolver_cli_rejects_malformed_input_and_execution_failure() -> None:
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(2)]
    environment = {
        module.PROWL_PANE_ID_ENV: cast(dict[str, str], agents[0][module.PANE_FIELD])[
            module.ID_FIELD
        ]
    }
    malformed_output = StringIO()

    malformed_exit_code = module.main(
        [module.CliOperation.RESOLVE_TARGET],
        runner=RecordingRunner([]),
        stdin=StringIO(
            json.dumps({module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION})
        ),
        stdout=malformed_output,
        environment=environment,
    )

    malformed_result = json.loads(malformed_output.getvalue())
    assert malformed_exit_code != 0
    assert (
        malformed_result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
    )

    failed_output = StringIO()
    failed_runner = RecordingRunner(
        [module.CommandResult(1, "", str(module.ExecutionStatus.COMMAND_FAILED))]
    )
    target_path = cast(
        str,
        cast(dict[str, object], agents[1][module.WORKTREE_FIELD])[module.PATH_FIELD],
    )

    failed_exit_code = module.main(
        [module.CliOperation.RESOLVE_TARGET],
        runner=failed_runner,
        stdin=StringIO(
            json.dumps(
                {
                    module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION,
                    module.PATH_FIELD: target_path,
                }
            )
        ),
        stdout=failed_output,
        environment=environment,
    )

    failed_result = json.loads(failed_output.getvalue())
    assert failed_exit_code != 0
    assert failed_result[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
    assert failed_runner.calls == [
        (module.command_for(module.operation_request(module.Operation.AGENTS)), None)
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
        {
            module.PROWL_PANE_ID_ENV: cast(
                dict[str, str], agents[0][module.PANE_FIELD]
            )[module.ID_FIELD]
        },
        runner,
    )

    assert result[module.STATUS_FIELD] == module.ExecutionStatus.IDENTITY_UNAVAILABLE
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
        {
            module.PROWL_PANE_ID_ENV: cast(
                dict[str, str], agents[0][module.PANE_FIELD]
            )[module.ID_FIELD]
        },
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
        {prowl.PROWL_PANE_ID_ENV: expected_participants[0][prowl.PANE_FIELD]},
        runner,
    )
    candidate = resolved[prowl.CANDIDATES_FIELD][0]
    participant = candidate[prowl.PARTICIPANT_FIELD]
    discovery = {
        message.SCHEMA_VERSION_FIELD: message.SCHEMA_VERSION,
        message.STATUS_FIELD: message.DISCOVERY_READY_STATUS,
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


def test_ambiguous_resolver_requires_one_authoritative_message_pane() -> None:
    prowl = load_prowl_environment()
    message = load_agent_message()
    agents = [public_agent_item(prowl, ordinal) for ordinal in range(4)]
    participants = [_expected_participant(prowl, agent) for agent in agents]
    runner = RecordingRunner([prowl_agents_command_result(prowl, agents)])
    resolved = prowl.resolve_target(
        participants[1][prowl.REPOSITORY_FIELD],
        {prowl.PROWL_PANE_ID_ENV: participants[0][prowl.PANE_FIELD]},
        runner,
    )
    candidates = resolved[prowl.CANDIDATES_FIELD]
    selected = candidates[0][prowl.PARTICIPANT_FIELD]
    discovery = {
        message.SCHEMA_VERSION_FIELD: message.SCHEMA_VERSION,
        message.STATUS_FIELD: message.DISCOVERY_READY_STATUS,
        message.DETAIL_FIELD: None,
        message.CALLER_FIELD: resolved[prowl.CALLER_FIELD],
        message.TARGETS_FIELD: [
            candidate[prowl.PARTICIPANT_FIELD] for candidate in candidates
        ],
    }
    request = message.build_request(
        to_pane=selected[prowl.PANE_FIELD],
        kind=message.MessageKind.FACT,
        subject=selected[prowl.BRANCH_FIELD],
        facts=[selected[prowl.WORKTREE_FIELD]],
        request=None,
    )

    built = message.send_request(request, discovery)

    assert resolved[prowl.STATUS_FIELD] == prowl.ExecutionStatus.IDENTITY_AMBIGUOUS
    assert len(candidates) == 3
    assert built[message.ENVELOPE_FIELD][message.RECIPIENT_FIELD] == selected
    assert (
        built[message.DELIVERY_FIELD][message.TO_PANE_FIELD]
        == selected[prowl.PANE_FIELD]
    )
    assert runner.calls == [
        (prowl.command_for(prowl.operation_request(prowl.Operation.AGENTS)), None)
    ]

    for targets in (
        [],
        [selected, selected],
    ):
        invalid_discovery = {**discovery, message.TARGETS_FIELD: targets}
        try:
            message.send_request(request, invalid_discovery)
        except message.MessageError as error:
            assert error.status == message.DeliveryStatus.INVALID_IDENTITY
        else:
            raise AssertionError(
                "message build accepted a pane without exactly one discovered target"
            )
    assert runner.calls == [
        (prowl.command_for(prowl.operation_request(prowl.Operation.AGENTS)), None)
    ]


def test_resolver_maps_each_source_owned_caller_identity_shape() -> None:
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(2)]
    participants = [_expected_participant(module, agent) for agent in agents]

    assert module.CALLER_IDENTITY_ENV_FIELDS == (
        module.PROWL_PANE_ID_ENV,
        module.PROWL_WORKTREE_PATH_ENV,
    )
    for environment in resolver_caller_environments(module, participants[0]):
        runner = RecordingRunner([prowl_agents_command_result(module, agents)])
        result = module.resolve_target(
            participants[1][module.WORKTREE_FIELD], environment, runner
        )

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert result[module.CALLER_FIELD] == participants[0]
        assert (
            result[module.CANDIDATES_FIELD][0][module.PARTICIPANT_FIELD]
            == (participants[1])
        )


def test_resolver_rejects_ambiguous_worktree_caller_identity() -> None:
    module = load_prowl_environment()
    agents = [public_agent_item(module, ordinal) for ordinal in range(3)]
    first_worktree = cast(dict[str, str], agents[0][module.WORKTREE_FIELD])
    second_worktree = cast(dict[str, str], agents[1][module.WORKTREE_FIELD])
    second_worktree[module.PATH_FIELD] = first_worktree[module.PATH_FIELD]
    runner = RecordingRunner([prowl_agents_command_result(module, agents)])

    result = module.resolve_target(
        cast(
            str,
            cast(dict[str, object], agents[2][module.WORKTREE_FIELD])[
                module.PATH_FIELD
            ],
        ),
        {module.PROWL_WORKTREE_PATH_ENV: first_worktree[module.PATH_FIELD]},
        runner,
    )

    assert result[module.STATUS_FIELD] == module.ExecutionStatus.IDENTITY_AMBIGUOUS
    assert result[module.CALLER_FIELD] is None
    assert result[module.CANDIDATES_FIELD] == []
