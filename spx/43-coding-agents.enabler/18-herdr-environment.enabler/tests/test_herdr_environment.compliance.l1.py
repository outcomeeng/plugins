from typing import cast

from outcomeeng_testing.generators.herdr_environment import operation_requests
from outcomeeng_testing.harnesses.herdr_environment import (
    RecordingRunner,
    herdr_command_source_texts,
    herdr_help_violation_source,
    load_herdr_environment,
    raw_herdr_violation_source,
    request_for,
    run_bound_through_execute,
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
        arguments.pop(module.MUTATION_TARGET_FIELD, None)
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


def test_mutation_authorization_is_bound_to_the_exact_target() -> None:
    module = load_herdr_environment()
    gated = set()

    for request in operation_requests(module):
        operation = module.Operation(request[module.OPERATION_FIELD])
        if operation not in module.MUTATING_OPERATIONS:
            continue
        gated.add(operation)
        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        authorized_target = cast(
            dict[str, object], arguments[module.MUTATION_TARGET_FIELD]
        )
        target_field, target_value = next(iter(authorized_target.items()))
        mismatched_field = next(
            field for field in module.MUTATION_TARGET_FIELDS if field != target_field
        )
        mismatched_targets = (
            {mismatched_field: target_value},
            {target_field: f"{target_value}-different"},
        )
        for mismatched_target in mismatched_targets:
            mismatched = {
                **request,
                module.ARGUMENTS_FIELD: {
                    **arguments,
                    module.MUTATION_TARGET_FIELD: mismatched_target,
                },
            }
            runner = RecordingRunner([])
            result = module.execute(mismatched, runner)

            assert (
                result[module.STATUS_FIELD]
                == module.ExecutionStatus.MUTATION_UNAUTHORIZED
            )
            assert runner.calls == []

    assert gated == set(module.MUTATING_OPERATIONS)


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
