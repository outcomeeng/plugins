"""Test infrastructure for the shipped coding-agent message protocol."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Callable, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.coding_agents import (
    doorbell_lines,
    message_content,
    unsupported_capability_operation,
)
from outcomeeng_testing.generators.prowl_environment import (
    message_texts,
    public_agent_item,
)
from outcomeeng_testing.harnesses.agent_mail import (
    AbsentExecutableRunner,
    common_dir_reply,
    failed_command_result,
    load_agent_mail,
    store_response_result,
    text_command_result,
)
from outcomeeng_testing.harnesses.agent_mail import (
    RecordingRunner as MailRecordingRunner,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property
from outcomeeng_testing.harnesses.prowl_environment import (
    RecordingRunner,
    load_prowl_environment,
    prowl_agents_command_result,
    prowl_send_command_result,
)

ROOT = Path(__file__).parents[2]
AGENT_MESSAGE_PATH = (
    ROOT / "src/plugins/coding-agents/skills/message-agents/scripts/agent_message.py"
)
HANDBACK_PROPERTY_SEED = 2026082801
HANDBACK_PROPERTY_EXAMPLES = 40
HANDBACK_PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/21-agent-communication.enabler/tests/"
    "test_agent_message.property.l1.py"
)
DOORBELL_PROPERTY_SEED = 2026091809
DOORBELL_PROPERTY_EXAMPLES = 60
DOORBELL_PROPERTY_REPLAY_PATH = (
    "spx/43-coding-agents.enabler/21-agent-communication.enabler/tests/"
    "test_doorbell.property.l1.py"
)
# Failure simulation at the store boundary: the store rejects the send.
STORE_REJECTION_EXIT_CODE = 3
STORE_REJECTION_DETAIL = "store rejected the send"
# Failure simulation at the store boundary: the store's reply is not JSON.
STORE_UNREADABLE_REPLY = "not a json reply"
# Failure simulation at the Prowl boundary: the environment rejects the turn.
PROWL_REJECTION_EXIT_CODE = 7
PROWL_REJECTION_DETAIL = "transport rejected"


class HandbackPlanError(RuntimeError):
    """The environment capability's plan-handback command did not complete."""


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, AGENT_MESSAGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load message module: {AGENT_MESSAGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_agent_message() -> ModuleType:
    return _load("coding_agents_agent_message")


def observed_message_participants() -> tuple[
    ModuleType,
    ModuleType,
    list[dict[str, object]],
    list[dict[str, str]],
]:
    """Return identities observed through the public Prowl agents operation."""
    prowl = load_prowl_environment()
    message = load_agent_message()
    roster = [public_agent_item(prowl, ordinal) for ordinal in range(3)]
    runner = RecordingRunner([prowl_agents_command_result(prowl, roster)])
    inventory = prowl.execute(prowl.operation_request(prowl.Operation.AGENTS), runner)
    participants = prowl.participants_from_agents(inventory[prowl.RESPONSE_FIELD])
    return prowl, message, roster, participants


def public_message_context() -> tuple[
    ModuleType,
    dict[str, str],
    dict[str, str],
    dict[str, object],
]:
    """Return a sender, recipient, and discovery from public Prowl evidence."""
    _, message, roster, participants = observed_message_participants()
    sender, recipient = participants[:2]
    discovery = resolver_discovery(message, participants, sender)
    return message, sender, recipient, discovery


def observe_send_transport(pane: str) -> dict[str, object]:
    """Return the complete adapter result for a submitted Prowl turn."""
    prowl = load_prowl_environment()
    runner = RecordingRunner(
        [prowl_send_command_result(prowl, trailing_enter_sent=True)]
    )
    request = prowl.operation_request(
        prowl.Operation.SEND,
        pane=pane,
        text="source-checked message delivery",
        no_wait=True,
    )
    return cast(dict[str, object], prowl.execute(request, runner))


def resolver_discovery(
    module: ModuleType,
    participants: list[dict[str, str]],
    caller: dict[str, str],
) -> dict[str, object]:
    return {
        module.SCHEMA_VERSION_FIELD: module.SCHEMA_VERSION,
        module.STATUS_FIELD: module.DISCOVERY_READY_STATUS,
        module.DETAIL_FIELD: None,
        module.CALLER_FIELD: caller,
        module.TARGETS_FIELD: participants,
    }


def fact_envelope(
    module: ModuleType,
    sender: dict[str, str],
    recipient: dict[str, str],
) -> dict[str, object]:
    content = message_content(module.MessageKind.FACT, 1)
    return cast(
        dict[str, object],
        module.build_envelope(
            kind=module.MessageKind.FACT,
            sender=sender,
            recipient=recipient,
            subject=content.subject,
            facts=list(content.facts),
            request=content.request,
            uuid_factory=lambda: uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
        ),
    )


def production_handback(
    sender: dict[str, str],
    recipient: dict[str, str],
    completion_text: str = "Requested artifact completed.",
) -> dict[str, object]:
    """Return a structured handback produced by the environment capability."""
    return cast(
        dict[str, object],
        production_handback_plan(sender, recipient, completion_text)["handback"],
    )


def production_handback_plan(
    sender: dict[str, str],
    recipient: dict[str, str],
    completion_text: str = "Requested artifact completed.",
) -> dict[str, object]:
    """Return the complete public plan-handback result."""
    prowl = load_prowl_environment()
    stdout = StringIO()
    exit_code = prowl.main(
        [prowl.CliOperation.PLAN_HAND_BACK],
        stdin=StringIO(
            json.dumps(
                {
                    prowl.SENDER_FIELD: sender,
                    prowl.RECIPIENT_FIELD: recipient,
                    prowl.COMPLETION_TEXT_FIELD: completion_text,
                }
            )
        ),
        stdout=stdout,
    )
    if exit_code != 0:
        raise HandbackPlanError(
            f"plan-handback exited {exit_code}: {stdout.getvalue()}"
        )
    return cast(dict[str, object], json.loads(stdout.getvalue()))


def run_handback_preservation_property(
    assert_handback: Callable[
        [
            ModuleType,
            dict[str, str],
            dict[str, str],
            dict[str, object],
            dict[str, object],
        ],
        None,
    ],
) -> None:
    """Drive generated handbacks while the linked test owns preservation."""
    message, sender, recipient, discovery = public_message_context()

    @seed(HANDBACK_PROPERTY_SEED)
    @settings(
        max_examples=HANDBACK_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(completion_text=message_texts())
    def generated_handback_property(completion_text: str) -> None:
        assert_handback(
            message,
            sender,
            recipient,
            discovery,
            production_handback(sender, recipient, completion_text),
        )

    run_replayable_property(
        generated_handback_property,
        seed_value=HANDBACK_PROPERTY_SEED,
        replay_path=HANDBACK_PROPERTY_REPLAY_PATH,
    )


def generated_envelope(
    module: ModuleType,
    *,
    kind: object,
    sender: dict[str, str],
    recipient: dict[str, str],
    ordinal: int,
    request_required: bool = False,
    **fields: object,
) -> dict[str, object]:
    content = message_content(kind, ordinal, request_required=request_required)
    return cast(
        dict[str, object],
        module.build_envelope(
            kind=kind,
            sender=sender,
            recipient=recipient,
            subject=content.subject,
            facts=list(content.facts),
            request=content.request,
            **fields,
        ),
    )


def _mail_send_result(
    message: ModuleType,
    record: dict[str, object],
    runner: MailRecordingRunner | AbsentExecutableRunner,
) -> dict[str, object]:
    agent_mail = load_agent_mail()
    return cast(
        dict[str, object],
        agent_mail.execute(message.mail_send_request(record), runner),
    )


def observe_mail_send(
    message: ModuleType, record: dict[str, object]
) -> dict[str, object]:
    """The capability's checked send result over the store's captured reply."""
    agent_mail = load_agent_mail()
    runner = MailRecordingRunner(
        [
            common_dir_reply(agent_mail),
            store_response_result(agent_mail, agent_mail.Operation.SEND),
        ]
    )
    return _mail_send_result(message, record, runner)


def observe_rejected_mail_send(
    message: ModuleType, record: dict[str, object]
) -> dict[str, object]:
    """The capability's result when the store rejects the send (failure simulation)."""
    agent_mail = load_agent_mail()
    runner = MailRecordingRunner(
        [
            common_dir_reply(agent_mail),
            failed_command_result(
                agent_mail, STORE_REJECTION_EXIT_CODE, STORE_REJECTION_DETAIL
            ),
        ]
    )
    return _mail_send_result(message, record, runner)


def observe_unresolved_repository_mail_send(
    message: ModuleType, record: dict[str, object]
) -> dict[str, object]:
    """The capability's result when the repository lookup's program is absent
    (failure simulation)."""
    agent_mail = load_agent_mail()
    runner = AbsentExecutableRunner(agent_mail.PUBLIC_GIT_COMMON_DIR_COMMAND[0], [])
    return _mail_send_result(message, record, runner)


def observe_unreadable_store_reply_mail_send(
    message: ModuleType, record: dict[str, object]
) -> dict[str, object]:
    """The capability's result when the store replies with text that is not JSON
    (failure simulation)."""
    agent_mail = load_agent_mail()
    runner = MailRecordingRunner(
        [
            common_dir_reply(agent_mail),
            text_command_result(agent_mail, STORE_UNREADABLE_REPLY),
        ]
    )
    return _mail_send_result(message, record, runner)


def observe_unsupported_operation_mail_send(
    message: ModuleType, record: dict[str, object]
) -> dict[str, object]:
    """The capability's result for a send request whose operation the capability
    does not declare."""
    agent_mail = load_agent_mail()
    request = {
        **message.mail_send_request(record),
        message.TRANSPORT_OPERATION_FIELD: unsupported_capability_operation(agent_mail),
    }
    runner = MailRecordingRunner([common_dir_reply(agent_mail)])
    return cast(dict[str, object], agent_mail.execute(request, runner))


def observe_absent_store_mail_send(
    message: ModuleType, record: dict[str, object]
) -> dict[str, object]:
    """The capability's result when no store executable exists (failure simulation)."""
    agent_mail = load_agent_mail()
    runner = AbsentExecutableRunner(
        agent_mail.AM_COMMAND, [common_dir_reply(agent_mail)]
    )
    return _mail_send_result(message, record, runner)


def observe_doorbell_transport(
    pane: str, *, trailing_enter_sent: bool
) -> dict[str, object]:
    """The complete Prowl adapter result for one doorbell line sent into a pane."""
    prowl = load_prowl_environment()
    runner = RecordingRunner(
        [prowl_send_command_result(prowl, trailing_enter_sent=trailing_enter_sent)]
    )
    request = prowl.operation_request(
        prowl.Operation.SEND,
        pane=pane,
        text="doorbell line under test",
        no_wait=True,
    )
    return cast(dict[str, object], prowl.execute(request, runner))


def run_doorbell_roundtrip_property(
    assert_roundtrip: Callable[[ModuleType, str, int], None],
) -> None:
    """Drive generated doorbell senders and ids while the linked test owns the law."""
    message = load_agent_message()

    @seed(DOORBELL_PROPERTY_SEED)
    @settings(
        max_examples=DOORBELL_PROPERTY_EXAMPLES,
        deadline=None,
        print_blob=True,
    )
    @given(line=doorbell_lines())
    def generated_doorbell_property(line: tuple[str, int]) -> None:
        sender, message_id = line
        assert_roundtrip(message, sender, message_id)

    run_replayable_property(
        generated_doorbell_property,
        seed_value=DOORBELL_PROPERTY_SEED,
        replay_path=DOORBELL_PROPERTY_REPLAY_PATH,
    )
