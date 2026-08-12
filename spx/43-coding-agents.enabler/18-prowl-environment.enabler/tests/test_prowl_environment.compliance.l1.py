import uuid
from typing import cast

from outcomeeng_testing.generators.prowl_environment import (
    agent_identity,
    delegation_text_case,
    operation_requests,
)
from outcomeeng_testing.harnesses.prowl_environment import (
    load_prowl_environment,
    observe_delegation_sender_pane,
    prowl_command_source_texts,
    raw_prowl_violation_source,
)


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
