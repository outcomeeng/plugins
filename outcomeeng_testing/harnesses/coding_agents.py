"""Test infrastructure for the shipped coding-agent message protocol."""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import cast

from outcomeeng_testing.generators.coding_agents import message_content

ROOT = Path(__file__).parents[2]
AGENT_MESSAGE_PATH = (
    ROOT / "src/plugins/coding-agents/skills/message-agents/scripts/agent_message.py"
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


def agent_discovery(
    module: ModuleType,
    roster: list[dict[str, object]],
    pane_id: str,
) -> dict[str, object]:
    return cast(
        dict[str, object],
        module.discover(roster, {module.PROWL_PANE_ID_ENV: pane_id}),
    )


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


def successful_transport(module: ModuleType) -> dict[str, object]:
    return {
        module.SCHEMA_VERSION_FIELD: module.TRANSPORT_SCHEMA_VERSION,
        module.TRANSPORT_OPERATION_FIELD: module.TRANSPORT_SEND_OPERATION,
        module.STATUS_FIELD: module.TRANSPORT_SUCCEEDED_STATUS,
        module.COMMAND_EXIT_CODE_FIELD: 0,
        module.TRANSPORT_RESPONSE_FIELD: {
            module.DATA_FIELD: {
                module.INPUT_FIELD: {
                    module.TRAILING_ENTER_SENT_FIELD: True,
                }
            }
        },
    }


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
