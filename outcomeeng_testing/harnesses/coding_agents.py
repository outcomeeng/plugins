"""Test infrastructure for the shipped coding-agent message protocol."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import uuid
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Callable, cast

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.coding_agents import message_content
from outcomeeng_testing.generators.prowl_environment import (
    message_texts,
    public_agent_item,
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


def mutation_observation(
    module: ModuleType,
    participant: dict[str, str],
) -> tuple[dict[str, object], dict[str, object]]:
    """Return a synthetic mutation target and its projected observed state."""
    target: dict[str, object] = {
        module.PANE_FIELD: participant[module.PANE_FIELD],
        module.WORKTREE_FIELD: participant[module.WORKTREE_FIELD],
        module.BRANCH_FIELD: participant[module.BRANCH_FIELD],
        module.REPOSITORY_FIELD: participant[module.REPOSITORY_FIELD],
        module.HEAD_FIELD: hashlib.sha1(
            participant[module.PANE_FIELD].encode(), usedforsecurity=False
        ).hexdigest(),
        module.STATUS_FIELD: module.CLEAN_STATUS,
    }
    state = {field: target[field] for field in module.OBSERVED_STATE_FIELDS}
    return target, state


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
        raise AssertionError(f"handback plan failed: {stdout.getvalue()}")
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
