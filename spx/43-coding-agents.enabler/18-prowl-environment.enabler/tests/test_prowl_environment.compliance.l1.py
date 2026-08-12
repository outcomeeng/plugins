import json
import uuid
from typing import cast

from outcomeeng_testing.generators.prowl_environment import (
    agent_identity,
    delegation_text_case,
    operation_requests,
    public_agent_item,
)
from outcomeeng_testing.harnesses.prowl_environment import (
    RecordingRunner,
    load_prowl_environment,
    local_worktree_enumeration_violation_source,
    observe_delegation_sender_pane,
    prowl_command_source_texts,
    prowl_environment_source_texts,
    raw_prowl_violation_source,
)


def test_list_and_open_preserve_lazy_terminal_resolution() -> None:
    module = load_prowl_environment()
    instantiated_pane = public_agent_item(module, 0)
    worktree = cast(dict[str, object], instantiated_pane[module.WORKTREE_FIELD])
    worktree_path = cast(str, worktree[module.PATH_FIELD])
    list_request = module.operation_request(module.Operation.LIST)
    open_request = module.operation_request(
        module.Operation.OPEN,
        path=worktree_path,
        mutation_authorized=True,
    )
    runner = RecordingRunner(
        [
            module.CommandResult(
                0,
                json.dumps(
                    {
                        module.OK_FIELD: True,
                        module.DATA_FIELD: {
                            module.ITEMS_FIELD: [instantiated_pane],
                        },
                    }
                ),
                "",
            ),
            module.CommandResult(
                0,
                json.dumps(
                    {
                        module.OK_FIELD: True,
                        module.DATA_FIELD: {
                            module.RESOLUTION_FIELD: module.OpenResolution.EXACT_ROOT,
                            module.CREATED_TAB_FIELD: True,
                            module.TARGET_FIELD: instantiated_pane,
                        },
                    }
                ),
                "",
            ),
        ]
    )

    listed = module.execute(list_request, runner)
    opened = module.execute(open_request, runner)

    listed_response = cast(dict[str, object], listed[module.RESPONSE_FIELD])
    listed_data = cast(dict[str, object], listed_response[module.DATA_FIELD])
    listed_items = cast(list[dict[str, object]], listed_data[module.ITEMS_FIELD])
    opened_response = cast(dict[str, object], opened[module.RESPONSE_FIELD])
    opened_data = cast(dict[str, object], opened_response[module.DATA_FIELD])
    opened_target = cast(dict[str, object], opened_data[module.TARGET_FIELD])
    listed_pane = cast(dict[str, object], listed_items[0][module.PANE_FIELD])
    opened_pane = cast(dict[str, object], opened_target[module.PANE_FIELD])

    assert listed[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert listed_items == [instantiated_pane]
    assert opened[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert opened_data[module.RESOLUTION_FIELD] == module.OpenResolution.EXACT_ROOT
    assert opened_data[module.CREATED_TAB_FIELD] is True
    assert opened_pane[module.ID_FIELD] == listed_pane[module.ID_FIELD]
    assert runner.calls == [
        (module.command_for(list_request), None),
        (module.command_for(open_request), None),
    ]
    assert (
        module.local_worktree_enumeration_violations(prowl_environment_source_texts())
        == []
    )
    fixture_path, fixture_source = local_worktree_enumeration_violation_source()
    assert module.local_worktree_enumeration_violations(fixture_source) == [
        fixture_path
    ]


def test_prowl_environment_compliance() -> None:
    module = load_prowl_environment()

    for request in operation_requests(module):
        operation = module.Operation(request[module.OPERATION_FIELD])
        if operation not in module.MUTATING_OPERATIONS:
            continue
        arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
        arguments.pop(module.MUTATION_AUTHORIZED_FIELD, None)
        unauthorized = {**request, module.ARGUMENTS_FIELD: arguments}

        try:
            module.command_for(unauthorized)
        except module.ProwlEnvironmentError as error:
            assert error.status == module.ExecutionStatus.MUTATION_UNAUTHORIZED
        else:
            raise AssertionError(
                f"{operation.value} ran without mutation authorization"
            )


def test_terminal_handbacks_require_one_complete_result_form() -> None:
    module = load_prowl_environment()
    sender = agent_identity(module, ordinal=1)
    recipient = agent_identity(module, ordinal=2)
    content = delegation_text_case(3)
    delegation = module.delegation_request(
        sender=sender,
        recipient=recipient,
        subject=content.subject,
        instruction=content.instruction,
        coordination_reference=str(
            uuid.uuid5(uuid.NAMESPACE_URL, sender[module.PANE_FIELD])
        ),
    )

    for invalid_fields in (
        {},
        {module.RESULT_REFERENCE_FIELD: "result://missing-projection"},
        {module.PROJECTION_FIELD: "projection without reference"},
        {
            module.RESULT_REFERENCE_FIELD: "result://overlength-projection",
            module.PROJECTION_FIELD: (
                "x" * (module.MAX_RESULT_PROJECTION_CHARACTERS + 1)
            ),
        },
    ):
        try:
            module.terminal_handback(
                delegation,
                module.TerminalKind.COMPLETED,
                **module.result_form_arguments(invalid_fields),
            )
        except module.ProwlEnvironmentError as error:
            assert error.status == module.ExecutionStatus.INVALID_SCHEMA
        else:
            raise AssertionError("invalid terminal result form was accepted")


def test_raw_prowl_command_rule_rejects_only_the_violating_fixture() -> None:
    module = load_prowl_environment()
    assert module.raw_prowl_command_violations(prowl_command_source_texts()) == []

    fixture_path, fixture_source = raw_prowl_violation_source()
    assert module.raw_prowl_command_violations(fixture_source) == [fixture_path]


def test_delegation_cli_rejects_an_unsupported_field() -> None:
    module = load_prowl_environment()
    sender = agent_identity(module, 0)
    request = {
        module.SENDER_FIELD: sender,
        module.RECIPIENT_FIELD: agent_identity(module, 1),
        module.SUBJECT_FIELD: "bounded subject",
        module.INSTRUCTION_FIELD: "bounded instruction",
        module.COORDINATION_REFERENCE_FIELD: None,
        "returnAddress": {module.PANE_FIELD: sender[module.PANE_FIELD]},
    }

    try:
        module._delegation_from_cli(request)
    except module.ProwlEnvironmentError as error:
        assert "returnAddress" in str(error)
    else:
        raise AssertionError(
            "an unsupported delegation field was accepted; a caller inventing a "
            "field would send a delegation missing the data it believed it supplied"
        )


def test_delegation_cli_accepts_the_supported_fields() -> None:
    module = load_prowl_environment()
    sender = agent_identity(module, 0)

    envelope = module._delegation_from_cli(
        {
            module.SENDER_FIELD: sender,
            module.RECIPIENT_FIELD: agent_identity(module, 1),
            module.SUBJECT_FIELD: "bounded subject",
            module.INSTRUCTION_FIELD: "bounded instruction",
            module.COORDINATION_REFERENCE_FIELD: None,
        }
    )

    assert envelope[module.SENDER_FIELD] == sender


def test_delegation_envelope_carries_the_sender_pane() -> None:
    submitted, carried = observe_delegation_sender_pane()

    assert carried == submitted, (
        f"envelope carried sender pane {carried!r}, not the submitted {submitted!r}; "
        "the recipient reads its return path from this field alone"
    )
