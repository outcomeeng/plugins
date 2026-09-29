import json
import string
from typing import cast

from outcomeeng_testing.generators.herdr_environment import operation_requests
from outcomeeng_testing.harnesses.herdr_environment import (
    RecordingRunner,
    captured_success_response,
    disposable_worktree,
    herdr_command_source_texts,
    herdr_help_violation_source,
    load_herdr_environment,
    raw_herdr_violation_source,
    replay,
    request_for,
    run_bound_through_execute,
    worktree_envelope,
)


def test_mutating_operations_fail_before_execution_without_authorization() -> None:
    module = load_herdr_environment()
    gated = set()

    for request in operation_requests(module):
        operation = module.Operation(request[module.OPERATION_FIELD])
        if operation not in module.MUTATING_OPERATIONS:
            continue
        gated.add(operation)
        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        arguments.pop(module.MUTATION_AUTHORIZED_FIELD, None)
        absent = {**request, module.ARGUMENTS_FIELD: arguments}
        withheld = {
            **request,
            module.ARGUMENTS_FIELD: {
                **arguments,
                module.MUTATION_AUTHORIZED_FIELD: False,
            },
        }

        for unauthorized in (absent, withheld):
            try:
                module.command_for(unauthorized)
            except module.HerdrEnvironmentError as error:
                assert error.status == module.ExecutionStatus.MUTATION_UNAUTHORIZED
            else:
                raise AssertionError(
                    f"{operation.value} built a command without authorization"
                )

    assert gated == set(module.MUTATING_OPERATIONS)


def test_a_malformed_gated_request_is_invalid_whatever_its_authorization() -> None:
    module = load_herdr_environment()
    gated_requests: list[dict[str, object]] = []
    for request in operation_requests(module):
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
        if operation in module.MUTATING_OPERATIONS:
            gated_requests.append(request)
        elif operation is module.Operation.PROMPT:
            gated_requests.extend(
                {
                    **request,
                    module.ARGUMENTS_FIELD: {**arguments, module.TEXT_FIELD: text},
                }
                for text in module.AGENT_SESSION_ENDING_TEXTS
            )
    malformed_seen = set()

    for request in gated_requests:
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        arguments.pop(module.MUTATION_AUTHORIZED_FIELD, None)
        # The session-ending text is what gates the prompt, so a prompt keeps it
        # and carries its malformation in another text argument.
        malformable = sorted(
            field_name
            for field_name in module.TEXT_ARGUMENT_FIELDS & set(arguments)
            if not (
                operation is module.Operation.PROMPT and field_name == module.TEXT_FIELD
            )
        )
        assert malformable, operation.value
        malformed_seen.add(operation)

        unauthorized_forms: list[dict[str, object]] = []
        for field_name in malformable:
            malformed = {
                **arguments,
                field_name: f"{module.LONG_OPTION_PREFIX}{arguments[field_name]}",
            }
            unauthorized_forms.append(malformed)
            unauthorized_forms.append(
                {**malformed, module.MUTATION_AUTHORIZED_FIELD: False}
            )
        # Authorization spelled as JSON text rather than the JSON boolean.
        unauthorized_forms.append(
            {**arguments, module.MUTATION_AUTHORIZED_FIELD: json.dumps(True)}
        )

        for form in unauthorized_forms:
            runner = RecordingRunner([])
            result = module.execute({**request, module.ARGUMENTS_FIELD: form}, runner)
            assert (
                result[module.STATUS_FIELD] == module.ExecutionStatus.INVALID_SCHEMA
            ), (operation.value, form)
            assert runner.calls == [], (operation.value, form)

    assert malformed_seen == {*module.MUTATING_OPERATIONS, module.Operation.PROMPT}


def test_a_prompt_carrying_the_stop_exit_runs_no_command_without_authorization() -> (
    None
):
    module = load_herdr_environment()
    prompts = [
        request
        for request in operation_requests(module)
        if module.Operation(request[module.OPERATION_FIELD]) is module.Operation.PROMPT
    ]
    assert prompts

    for request in prompts:
        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        arguments.pop(module.MUTATION_AUTHORIZED_FIELD, None)
        captured = captured_success_response(module, module.Operation.PROMPT, arguments)
        assert captured is not None, "no captured prompt response"

        # Conforming: a prompt carrying any other text needs no authorization.
        ordinary = {**request, module.ARGUMENTS_FIELD: arguments}
        runner = RecordingRunner(replay(captured))
        result = module.execute(ordinary, runner)
        assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
        assert [call[0] for call in runner.calls] == [module.command_for(ordinary)]

        # Conforming: a longer message that mentions a session-ending command
        # inside it ends no session and needs no authorization.
        for member in module.AGENT_SESSION_ENDING_TEXTS:
            mentioning = {
                **request,
                module.ARGUMENTS_FIELD: {
                    **arguments,
                    module.TEXT_FIELD: f"{arguments[module.TEXT_FIELD]}{member}",
                },
            }
            runner = RecordingRunner(replay(captured))
            result = module.execute(mentioning, runner)
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            assert [call[0] for call in runner.calls] == [
                module.command_for(mentioning)
            ]

        # Violating: every session-ending command, bare or padded with any
        # whitespace character, with authorization absent or false.
        ending_texts = [
            variant
            for member in module.AGENT_SESSION_ENDING_TEXTS
            for variant in (
                member,
                *(f"{padding}{member}{padding}" for padding in string.whitespace),
            )
        ]
        for text in ending_texts:
            ending = {**arguments, module.TEXT_FIELD: text}
            absent = {**request, module.ARGUMENTS_FIELD: ending}
            withheld = {
                **request,
                module.ARGUMENTS_FIELD: {
                    **ending,
                    module.MUTATION_AUTHORIZED_FIELD: False,
                },
            }
            for unauthorized in (absent, withheld):
                runner = RecordingRunner(replay(captured))
                result = module.execute(unauthorized, runner)
                assert (
                    result[module.STATUS_FIELD]
                    == module.ExecutionStatus.MUTATION_UNAUTHORIZED
                ), text
                assert runner.calls == [], text

            # Conforming: the same text under authorization runs its command.
            authorized = {
                **request,
                module.ARGUMENTS_FIELD: {
                    **ending,
                    module.MUTATION_AUTHORIZED_FIELD: True,
                },
            }
            runner = RecordingRunner(replay(captured))
            result = module.execute(authorized, runner)
            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            assert [call[0] for call in runner.calls] == [
                module.command_for(authorized)
            ]

        # The refused exit text is stop's own vector, not a lookalike.
        if module.PANE_FIELD in arguments and module.WAIT_FIELD not in arguments:
            stop = module.operation_request(
                module.Operation.STOP,
                pane=arguments[module.PANE_FIELD],
                mutation_authorized=True,
            )
            exit_request = {
                **request,
                module.ARGUMENTS_FIELD: {
                    **arguments,
                    module.TEXT_FIELD: module.AGENT_EXIT_TEXT,
                    module.MUTATION_AUTHORIZED_FIELD: True,
                },
            }
            assert module.command_for(stop) == module.command_for(exit_request)


def test_wait_bearing_requests_carry_a_bound_and_the_runner_is_bounded() -> None:
    module = load_herdr_environment()
    bounded = set()

    for request in operation_requests(module):
        operation = module.Operation(request[module.OPERATION_FIELD])
        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        if module.TIMEOUT_FIELD not in arguments:
            continue
        bounded.add(operation)
        arguments.pop(module.TIMEOUT_FIELD)
        unbounded = {**request, module.ARGUMENTS_FIELD: arguments}

        try:
            module.command_for(unbounded)
        except module.HerdrEnvironmentError as error:
            assert error.status == module.ExecutionStatus.INVALID_SCHEMA
        else:
            raise AssertionError(f"{operation.value} accepted a wait without a bound")

    assert bounded == set(module.WAIT_BEARING_OPERATIONS)

    request = request_for(module, module.Operation.WAIT)
    smallest = cast(
        int,
        cast(dict[str, object], request[module.ARGUMENTS_FIELD])[module.TIMEOUT_FIELD],
    )
    result, bounds, child_sleep = run_bound_through_execute(module, request)

    assert bounds == [module.command_bound_seconds(request)]
    assert bounds[0] * 1000 > smallest
    assert bounds[0] < child_sleep
    assert result[module.STATUS_FIELD] == module.ExecutionStatus.COMMAND_FAILED
    assert module.COMMAND_EXIT_CODE_FIELD not in result


def test_no_other_shipped_script_constructs_herdr_commands() -> None:
    module = load_herdr_environment()

    assert module.raw_herdr_command_violations(herdr_command_source_texts()) == []
    assert module.herdr_help_violations(herdr_command_source_texts()) == []

    raw_path, raw_source = raw_herdr_violation_source()
    assert module.raw_herdr_command_violations(raw_source) == [raw_path]
    help_path, help_source = herdr_help_violation_source()
    assert module.herdr_help_violations(help_source) == [help_path]


def test_create_worktree_records_no_occupancy_claim() -> None:
    module = load_herdr_environment()
    created = 0

    with disposable_worktree() as worktree:
        unclaimed = worktree.occupancy()
        untouched = worktree.files()

        for request in operation_requests(module):
            if (
                module.Operation(request[module.OPERATION_FIELD])
                is not module.Operation.CREATE_WORKTREE
            ):
                continue
            created += 1
            arguments = cast(dict[str, object], request[module.ARGUMENTS_FIELD])
            captured = captured_success_response(
                module, module.Operation.CREATE_WORKTREE, arguments
            )
            assert captured is not None, "no captured create-worktree response"
            runner = RecordingRunner(
                replay(worktree_envelope(module, captured, worktree.path))
            )

            result = module.execute(request, runner)

            assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
            projected = cast(dict[str, object], result[module.WORKTREE_RESULT_FIELD])
            assert projected[module.PATH_FIELD] == str(worktree.path)
            assert [call[0] for call in runner.calls] == [module.command_for(request)]
            assert module.evidence_command_for(request) is None
            assert worktree.occupancy() == unclaimed
            assert worktree.files() == untouched

        # The violating case: the same created worktree once an occupancy claim
        # is recorded on it. Spx's own report and the repository both show it.
        worktree.record_claim()
        assert worktree.occupancy() != unclaimed
        assert worktree.files() != untouched

    assert created > 0
