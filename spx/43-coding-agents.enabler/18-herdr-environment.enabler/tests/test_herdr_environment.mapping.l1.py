import json
from pathlib import PurePath
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.herdr_environment import (
    agent_item_variant,
    incomplete_agent_variants,
    operation_requests,
)
from outcomeeng_testing.harnesses.cli_usage import read_argv
from outcomeeng_testing.harnesses.herdr_environment import (
    AbsentExecutableRunner,
    CapturedResponse,
    RecordingRunner,
    captured_error_message,
    captured_error_responses,
    captured_incomplete_agents,
    captured_incomplete_response,
    captured_payload,
    captured_responses,
    captured_session_agent,
    captured_stopped_panes,
    captured_success_response,
    captured_worktree_list,
    evidence_usage_contract_for,
    inventory_envelope,
    load_herdr_environment,
    projected_error_variants,
    replay,
    request_for,
    run_inventory_mapping,
    run_option_prefix_rejections,
    run_unknown_operation_mapping,
    session_envelope,
    usage_contract_for,
)


def test_herdr_operation_mappings() -> None:
    module = load_herdr_environment()
    requests = operation_requests(module)

    assert {str(request[module.OPERATION_FIELD]) for request in requests} == {
        operation.value for operation in module.Operation
    }

    for request in requests:
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        argv = module.command_for(request)
        contract = usage_contract_for(module, operation)
        reading = read_argv(contract, argv)

        assert reading.command_path == (module.HERDR_COMMAND, *contract.command_path)
        assert reading.unknown_options == ()
        assert contract.required_options <= set(reading.options_seen)
        for option, count in reading.options_seen.items():
            assert count == 1 or option in contract.repeatable_options
        if contract.variadic_positional:
            assert len(reading.positionals) >= len(contract.required_positionals)
        else:
            assert len(reading.positionals) == len(contract.required_positionals)
        text_values = [
            value
            for field_name, value in arguments.items()
            if field_name in module.TEXT_ARGUMENT_FIELDS
        ]
        for value in text_values:
            assert value in argv
        for field_name in module.TEXT_LIST_ARGUMENT_FIELDS:
            for value in cast(list[str], arguments.get(field_name, [])):
                assert value in argv
        if module.TIMEOUT_FIELD in arguments:
            assert str(arguments[module.TIMEOUT_FIELD]) in argv
            assert module.TIMEOUT_OPTION in reading.options_seen
        else:
            assert module.TIMEOUT_OPTION not in reading.options_seen
        if module.AGENT_ARGUMENTS_FIELD in arguments:
            assert reading.trailing == tuple(
                cast(list[str], arguments[module.AGENT_ARGUMENTS_FIELD])
            )
        for field_name, option in module.PUBLIC_HERDR_ARGUMENT_OPTIONS.items():
            value = arguments.get(field_name)
            if (
                isinstance(value, str | int)
                and not isinstance(value, bool)
                and option in argv
            ):
                assert argv[argv.index(option) + 1] == str(value)
        evidence_argv = module.evidence_command_for(request)
        if operation in module.EVIDENCE_COMMAND_PREFIXES:
            evidence_contract = evidence_usage_contract_for(module, operation)
            evidence_reading = read_argv(evidence_contract, evidence_argv)
            assert evidence_reading.command_path == (
                module.HERDR_COMMAND,
                *evidence_contract.command_path,
            )
            assert evidence_reading.unknown_options == ()
            assert len(evidence_reading.positionals) == len(
                evidence_contract.required_positionals
            )
            assert argv[len(contract.command_path) + 1] in evidence_reading.positionals
        else:
            assert evidence_argv is None

        captured = captured_success_response(module, operation, arguments)
        if captured is None:
            # herdr emitted only an error for this command under capture; the
            # response mapping below covers it with that envelope.
            assert captured_error_responses(module, operation) != []
            continue
        runner = RecordingRunner(replay(captured))
        result = module.execute(request, runner)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert result[module.COMMAND_EXIT_CODE_FIELD] == 0
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        if operation in module.TEXT_OPERATIONS:
            assert response == {module.OUTPUT_FIELD: captured_payload(captured)}
        else:
            assert response == captured_payload(captured)
        assert [call[0] for call in runner.calls] == [
            argv,
            *([] if evidence_argv is None else [evidence_argv]),
        ]
        called_argv, stdin, bound = runner.calls[0]
        assert (called_argv, stdin) == (argv, None)
        assert bound == module.command_bound_seconds(request)
        if module.TIMEOUT_FIELD in arguments:
            assert bound * 1000 > cast(int, arguments[module.TIMEOUT_FIELD])
        else:
            assert bound == module.COMMAND_TIMEOUT_SECONDS


def test_captured_responses_map_to_results_without_rewriting() -> None:
    module = load_herdr_environment()
    covered: set[object] = set()

    for captured in captured_responses(module):
        operation = module.Operation(captured.operation)
        covered.add(operation)
        request = request_for(module, operation, captured.shaping_fields)
        result = module.execute(request, RecordingRunner(replay(captured)))

        assert json.loads(json.dumps(result)) == result
        if captured.error_code is None:
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            payload = captured_payload(captured)
            if operation in module.TEXT_OPERATIONS:
                assert result[module.RESPONSE_FIELD] == {module.OUTPUT_FIELD: payload}
            else:
                assert result[module.RESPONSE_FIELD] == payload
            continue
        assert result[module.STATUS_FIELD] == module.HERDR_ERROR_STATUSES.get(
            captured.error_code, module.ExecutionStatus.COMMAND_FAILED
        )
        assert result[module.ERROR_CODE_FIELD] == captured.error_code
        assert result[module.DETAIL_FIELD] == captured_error_message(module, captured)
        assert result[module.COMMAND_EXIT_CODE_FIELD] == replay(captured)[-1].returncode

    assert covered == set(module.Operation)


def test_start_and_wait_map_to_the_session_identity_and_state() -> None:
    module = load_herdr_environment()

    def session_of(
        operation: object, shaping_fields: frozenset[str] = frozenset()
    ) -> tuple[dict[str, object], dict[str, object]]:
        request = request_for(module, operation, shaping_fields)
        captured = captured_success_response(
            module, operation, cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        )
        assert captured is not None, f"no captured {operation} response"
        emitted = captured_session_agent(module, captured)
        executed = module.execute(request, RecordingRunner(replay(captured)))
        assert executed[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        return emitted, cast(dict[str, object], executed[module.SESSION_RESULT_FIELD])

    # Every session-bearing operation, and the prompt under both of its
    # response shapes: submitted alone, and observed after `--wait`.
    session_shapes = [
        (operation, frozenset[str]()) for operation in module.SESSION_OPERATIONS
    ]
    session_shapes.append((module.Operation.PROMPT, frozenset({module.WAIT_FIELD})))
    for operation, shaping_fields in session_shapes:
        emitted, session = session_of(operation, shaping_fields)
        assert session == {
            field_name: emitted[field_name] for field_name in module.PARTICIPANT_FIELDS
        }
        assert session[module.NAME_FIELD] == emitted[module.NAME_FIELD]
        assert session[module.PANE_ID_FIELD] == emitted[module.PANE_ID_FIELD]
        assert session[module.AGENT_STATUS_FIELD] in {
            member.value for member in module.AgentState
        }

    started, session = session_of(module.Operation.START)
    assert session[module.INTERACTIVE_READY_FIELD] is True
    assert session[module.AGENT_KIND_FIELD] == started[module.AGENT_KIND_FIELD]

    waited, session = session_of(module.Operation.WAIT)
    reached = module.AgentState(session[module.AGENT_STATUS_FIELD])
    until = module.operation_request(
        module.Operation.WAIT,
        agent=cast(str, waited[module.NAME_FIELD]),
        until=[reached.value],
        timeout=module.INTEGER_BOUNDS[module.TIMEOUT_FIELD][0],
    )
    assert reached.value in module.command_for(until)

    timed_out = [
        captured
        for captured in captured_error_responses(module, module.Operation.WAIT)
        if module.HERDR_ERROR_STATUSES.get(captured.error_code or "")
        is module.ExecutionStatus.WAIT_TIMEOUT
    ]
    assert timed_out != []
    for captured in timed_out:
        result = module.execute(
            request_for(module, module.Operation.WAIT),
            RecordingRunner(replay(captured)),
        )
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.WAIT_TIMEOUT
        assert result[module.ERROR_CODE_FIELD] == captured.error_code

    not_ready = [
        captured
        for captured in [
            *captured_error_responses(module, module.Operation.START),
            *projected_error_variants(module),
        ]
        if module.HERDR_ERROR_STATUSES.get(captured.error_code or "")
        is module.ExecutionStatus.AGENT_NOT_READY
    ]
    assert not_ready != []
    for captured in not_ready:
        result = module.execute(
            request_for(module, module.Operation.START),
            RecordingRunner(replay(captured)),
        )
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.AGENT_NOT_READY
        assert result[module.ERROR_CODE_FIELD] == captured.error_code


def test_inventory_maps_to_complete_participants_or_named_results() -> None:
    def assert_inventory(
        module: ModuleType,
        envelope: dict[str, object],
        agents: list[dict[str, object]],
        absent_name: str,
        state: object,
    ) -> None:
        participants = module.participants_from_inventory(envelope)

        assert [
            {
                field_name: participant[field_name]
                for field_name in module.PARTICIPANT_FIELDS
            }
            for participant in participants
        ] == [
            {field_name: agent[field_name] for field_name in module.PARTICIPANT_FIELDS}
            for agent in agents
        ]
        assert {
            participant[module.AGENT_STATUS_FIELD] for participant in participants
        } <= {member.value for member in module.AgentState}
        first_name = cast(str, agents[0][module.NAME_FIELD])
        assert module.participant_for(participants, first_name) == participants[0]
        if absent_name not in {agent[module.NAME_FIELD] for agent in agents}:
            try:
                module.participant_for(participants, absent_name)
            except module.HerdrEnvironmentError as error:
                assert error.status == module.ExecutionStatus.IDENTITY_UNAVAILABLE
            else:
                raise AssertionError("an absent name resolved to a participant")
        duplicated = [
            *agents,
            agent_item_variant(
                module, agents[0], len(agents) + 1, state, name=first_name
            ),
        ]
        try:
            module.participant_for(
                module.participants_from_inventory(
                    inventory_envelope(module, duplicated)
                ),
                first_name,
            )
        except module.HerdrEnvironmentError as error:
            assert error.status == module.ExecutionStatus.IDENTITY_AMBIGUOUS
        else:
            raise AssertionError("a duplicated name resolved to one participant")

    run_inventory_mapping(assert_inventory)


def test_herdr_error_codes_project_to_named_statuses() -> None:
    module = load_herdr_environment()
    projected: dict[str, CapturedResponse] = {}
    verbatim: list[CapturedResponse] = []

    for captured in [*captured_responses(module), *projected_error_variants(module)]:
        if captured.error_code is None:
            continue
        if captured.error_code in module.HERDR_ERROR_STATUSES:
            projected.setdefault(captured.error_code, captured)
        else:
            verbatim.append(captured)

    assert set(projected) == set(module.HERDR_ERROR_STATUSES)
    assert verbatim != []

    for code, captured in projected.items():
        result = module.execute(
            request_for(module, captured.operation), RecordingRunner(replay(captured))
        )
        assert result[module.STATUS_FIELD] == module.HERDR_ERROR_STATUSES[code]
        assert result[module.STATUS_FIELD] != module.ExecutionStatus.COMMAND_FAILED
        assert result[module.ERROR_CODE_FIELD] == code
        assert result[module.DETAIL_FIELD] == captured_error_message(module, captured)

    for captured in verbatim:
        result = module.execute(
            request_for(module, captured.operation), RecordingRunner(replay(captured))
        )
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
        assert result[module.ERROR_CODE_FIELD] == captured.error_code
        assert result[module.DETAIL_FIELD] == captured_error_message(module, captured)


def test_text_arguments_under_the_option_prefix_are_rejected_before_any_command() -> (
    None
):
    def assert_case(
        module: ModuleType, request: dict[str, object], field_name: str
    ) -> None:
        runner = RecordingRunner([])
        result = module.execute(request, runner)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA, (
            field_name
        )
        assert field_name in str(result[module.DETAIL_FIELD])
        assert runner.calls == []

    run_option_prefix_rejections(assert_case)


def test_absent_server_and_unsupported_operation_map_to_unavailable_results() -> None:
    module = load_herdr_environment()
    request = module.operation_request(module.Operation.INVENTORY)

    absent = AbsentExecutableRunner()
    result = module.execute(request, absent)
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SERVER_NOT_RUNNING
    assert absent.calls == [module.command_for(request)]

    not_running = [
        captured
        for captured in captured_error_responses(module, module.Operation.INVENTORY)
        if module.HERDR_ERROR_STATUSES.get(captured.error_code or "")
        is module.ExecutionStatus.SERVER_NOT_RUNNING
    ]
    assert not_running != []
    for captured in not_running:
        result = module.execute(request, RecordingRunner(replay(captured)))
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SERVER_NOT_RUNNING
        assert result[module.ERROR_CODE_FIELD] == captured.error_code

    def assert_unknown(module: ModuleType, name: str) -> None:
        unknown = {**request, module.OPERATION_FIELD: name}
        result = module.execute(unknown, RecordingRunner([]))
        assert (
            result[module.STATUS_FIELD] == module.ExecutionStatus.OPERATION_UNAVAILABLE
        )

    run_unknown_operation_mapping(assert_unknown)


def test_worktree_requests_map_to_a_workspace_grouped_with_the_named_one() -> None:
    module = load_herdr_environment()
    listed = captured_worktree_list(module)
    grouped: set[object] = set()

    for generated in operation_requests(module):
        operation = module.Operation(generated[module.OPERATION_FIELD])
        if operation not in module.WORKTREE_OPERATIONS:
            continue
        # The captured responses answer a request naming the workspace herdr's
        # captured worktree list was taken for.
        arguments = {
            **cast(dict[str, object], generated[module.ARGUMENTS_FIELD]),
            module.WORKSPACE_FIELD: listed.named_workspace,
        }
        request = {**generated, module.ARGUMENTS_FIELD: arguments}
        argv = module.command_for(request)
        assert (
            argv[argv.index(module.WORKSPACE_OPTION) + 1]
            == arguments[module.WORKSPACE_FIELD]
        )

        captured = captured_success_response(module, operation, arguments)
        assert captured is not None, f"no captured {operation} response"
        runner = RecordingRunner(replay(captured))
        result = module.execute(request, runner)

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert [call[0] for call in runner.calls] == [argv]
        envelope = cast(dict[str, object], captured_payload(captured))
        emitted = cast(dict[str, object], envelope[module.RESULT_FIELD])
        worktree = cast(dict[str, object], emitted[module.WORKTREE_RESPONSE_FIELD])
        workspace = cast(dict[str, object], emitted[module.WORKSPACE_RESPONSE_FIELD])
        root_pane = cast(dict[str, object], emitted[module.ROOT_PANE_RESPONSE_FIELD])
        projected = cast(dict[str, object], result[module.WORKTREE_RESULT_FIELD])
        assert projected == {
            module.PATH_FIELD: worktree[module.WORKTREE_PATH_RESPONSE_FIELD],
            module.WORKSPACE_FIELD: workspace[module.WORKSPACE_ID_FIELD],
            module.ROOT_PANE_RESULT_FIELD: root_pane[module.PANE_ID_FIELD],
        }
        assert root_pane[module.WORKSPACE_ID_FIELD] == projected[module.WORKSPACE_FIELD]
        assert (
            PurePath(cast(str, root_pane[module.CWD_FIELD])).name
            == PurePath(cast(str, projected[module.PATH_FIELD])).name
        )

        # Grouping, as herdr records it: the named workspace's worktree list
        # names the new checkout as a linked worktree open in the workspace the
        # result returns, which is not the named workspace itself.
        assert projected[module.WORKSPACE_FIELD] != listed.named_workspace
        entries = [
            entry
            for entry in listed.worktrees
            if entry.path == projected[module.PATH_FIELD]
        ]
        assert len(entries) == 1
        assert entries[0].open_workspace == projected[module.WORKSPACE_FIELD]
        assert entries[0].linked is True
        grouped.add(operation)

        without_workspace = {
            **request,
            module.ARGUMENTS_FIELD: {
                field_name: value
                for field_name, value in arguments.items()
                if field_name != module.WORKSPACE_FIELD
            },
        }
        refusing = RecordingRunner([])
        refused = module.execute(without_workspace, refusing)
        assert refused[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
        assert refusing.calls == []

    assert grouped == set(module.WORKTREE_OPERATIONS)


def test_inventory_maps_every_agent_in_full_or_to_its_named_incomplete_item() -> None:
    module = load_herdr_environment()
    captured = captured_incomplete_response(module, module.Operation.INVENTORY)
    agents = captured_incomplete_agents(module)
    missing = [
        {
            field_name
            for field_name in module.PARTICIPANT_FIELDS
            if field_name not in agent
        }
        for agent in agents
    ]
    assert set() in missing
    assert any(module.NAME_FIELD in fields for fields in missing)
    assert any(module.INTERACTIVE_READY_FIELD in fields for fields in missing)

    result = module.execute(
        request_for(module, module.Operation.INVENTORY),
        RecordingRunner(replay(captured)),
    )

    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    items = cast(list[dict[str, object]], result[module.AGENTS_RESULT_FIELD])
    assert len(items) == len(agents)
    for item, agent, absent in zip(items, agents, missing, strict=True):
        carried = {
            field_name: agent[field_name]
            for field_name in module.PARTICIPANT_FIELDS
            if field_name in agent
        }
        if absent:
            assert set(cast(list[str], item[module.MISSING_FIELDS_FIELD])) == absent
            assert {
                field_name: value
                for field_name, value in item.items()
                if field_name != module.MISSING_FIELDS_FIELD
            } == carried
        else:
            assert item == carried
    for item, agent in zip(items, agents, strict=True):
        assert (
            module.participant_for(items, cast(str, agent[module.PANE_ID_FIELD]))
            == item
        )

    template = next(agent for agent, absent in zip(agents, missing) if not absent)
    for dropped, variant in incomplete_agent_variants(module, template):
        complete, incomplete = module.participants_from_inventory(
            inventory_envelope(module, [template, variant])
        )
        assert complete == {
            field_name: template[field_name] for field_name in module.PARTICIPANT_FIELDS
        }
        assert set(cast(list[str], incomplete[module.MISSING_FIELDS_FIELD])) == dropped
        assert {
            field_name: value
            for field_name, value in incomplete.items()
            if field_name != module.MISSING_FIELDS_FIELD
        } == {
            field_name: template[field_name]
            for field_name in module.PARTICIPANT_FIELDS
            if field_name not in dropped
        }


def test_readiness_judgments_return_the_incomplete_result_on_missing_evidence() -> None:
    module = load_herdr_environment()
    judged = set()

    def assert_judgment(
        operation: object, captured: CapturedResponse, dropped: frozenset[str]
    ) -> None:
        result = module.execute(
            request_for(module, operation), RecordingRunner(replay(captured))
        )
        session = cast(dict[str, object], result[module.SESSION_RESULT_FIELD])
        assert set(cast(list[str], session.get(module.MISSING_FIELDS_FIELD, []))) == (
            dropped
        )
        if dropped & module.READINESS_FIELDS[operation]:
            assert (
                result[module.STATUS_FIELD]
                == module.ExecutionStatus.AGENT_EVIDENCE_INCOMPLETE
            )
            assert module.RESPONSE_FIELD not in result
        else:
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED

    for operation in module.READINESS_FIELDS:
        judged.add(operation)
        captured = captured_success_response(module, operation)
        assert captured is not None, f"no captured {operation} response"
        agent = captured_session_agent(module, captured)
        for dropped, variant in incomplete_agent_variants(module, agent):
            assert_judgment(
                operation, session_envelope(module, captured, variant), dropped
            )
        for listed in captured_incomplete_agents(module):
            assert_judgment(
                operation,
                session_envelope(module, captured, listed),
                frozenset(
                    field_name
                    for field_name in module.PARTICIPANT_FIELDS
                    if field_name not in listed
                ),
            )

    assert judged == {
        module.Operation.START,
        module.Operation.RELAUNCH,
        module.Operation.WAIT,
    }
    waited = captured_incomplete_response(module, module.Operation.WAIT)
    unnamed = captured_session_agent(module, waited)
    assert module.NAME_FIELD not in unnamed
    assert_judgment(
        module.Operation.WAIT,
        waited,
        frozenset(
            field_name
            for field_name in module.PARTICIPANT_FIELDS
            if field_name not in unnamed
        ),
    )


def test_read_and_prompt_to_an_incomplete_agent_carry_the_incomplete_item() -> None:
    module = load_herdr_environment()

    for operation in (module.Operation.READ, module.Operation.PROMPT):
        captured = captured_incomplete_response(module, operation)
        agent = captured_session_agent(module, captured)
        absent = {
            field_name
            for field_name in module.PARTICIPANT_FIELDS
            if field_name not in agent
        }
        assert absent != set()

        result = module.execute(
            request_for(module, operation), RecordingRunner(replay(captured))
        )

        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        response = cast(dict[str, object], result[module.RESPONSE_FIELD])
        if operation in module.TEXT_OPERATIONS:
            assert response == {module.OUTPUT_FIELD: captured_payload(captured)}
        else:
            assert response == captured_payload(captured)
        session = cast(dict[str, object], result[module.SESSION_RESULT_FIELD])
        assert set(cast(list[str], session[module.MISSING_FIELDS_FIELD])) == absent
        assert {
            field_name: value
            for field_name, value in session.items()
            if field_name != module.MISSING_FIELDS_FIELD
        } == {
            field_name: agent[field_name]
            for field_name in module.PARTICIPANT_FIELDS
            if field_name in agent
        }

        complete = captured_success_response(module, operation)
        assert complete is not None, f"no captured {operation} response"
        for dropped, variant in incomplete_agent_variants(
            module, captured_session_agent(module, complete)
        ):
            varied = module.execute(
                request_for(module, operation),
                RecordingRunner(replay(session_envelope(module, complete, variant))),
            )
            assert varied[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            carried = cast(dict[str, object], varied[module.SESSION_RESULT_FIELD])
            assert set(cast(list[str], carried[module.MISSING_FIELDS_FIELD])) == dropped


def test_stop_submits_the_agents_exit_and_keeps_its_pane_for_a_relaunch() -> None:
    module = load_herdr_environment()
    stopped = captured_success_response(module, module.Operation.STOP)
    assert stopped is not None, "no captured stop response"
    pane = cast(str, captured_session_agent(module, stopped)[module.PANE_ID_FIELD])
    request = module.operation_request(
        module.Operation.STOP, pane=pane, mutation_authorized=True
    )

    argv = module.command_for(request)
    assert argv == module.command_for(
        module.operation_request(
            module.Operation.PROMPT, pane=pane, text=module.AGENT_EXIT_TEXT
        )
    )
    runner = RecordingRunner(replay(stopped))
    result = module.execute(request, runner)
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert [call[0] for call in runner.calls] == [argv]

    kept = [
        listed
        for listed in captured_stopped_panes(module)
        if listed[module.PANE_ID_FIELD] == pane
    ]
    assert len(kept) == 1
    assert module.AGENT_KIND_FIELD not in kept[0]

    relaunched = captured_success_response(module, module.Operation.RELAUNCH)
    assert relaunched is not None, "no captured relaunch response"
    generated = request_for(module, module.Operation.RELAUNCH)
    relaunch = {
        **generated,
        module.ARGUMENTS_FIELD: {
            **cast(dict[str, object], generated[module.ARGUMENTS_FIELD]),
            module.PANE_FIELD: pane,
        },
    }
    relaunch_result = module.execute(relaunch, RecordingRunner(replay(relaunched)))
    assert relaunch_result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    session = cast(dict[str, object], relaunch_result[module.SESSION_RESULT_FIELD])
    assert session[module.PANE_ID_FIELD] == pane
    assert module.MISSING_FIELDS_FIELD not in session
