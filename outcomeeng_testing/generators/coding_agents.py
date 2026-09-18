"""Generated public-Prowl identity domains for coding-agent evidence."""

from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType

from hypothesis import strategies as st

from outcomeeng_testing.generators.agent_mail import agent_names, store_message_ids


@dataclass(frozen=True)
class MessageContent:
    subject: str
    facts: tuple[str, ...]
    request: str | None


def message_content(
    kind: object,
    ordinal: int,
    *,
    request_required: bool = False,
) -> MessageContent:
    kind_value = str(kind)
    suffix = str(ordinal)
    return MessageContent(
        subject=f"{kind_value} subject {suffix}",
        facts=(f"{kind_value} fact {suffix}",),
        request=(f"{kind_value} request {suffix}" if request_required else None),
    )


def mail_record_input(
    module: ModuleType,
    ordinal: int,
    kind: object,
    *,
    ack_required: bool = False,
) -> dict[str, object]:
    """One message request on the mail route with generated text values."""
    suffix = str(ordinal)
    return {
        module.KIND_FIELD: kind,
        module.RECORD_CORRELATION_FIELD: f"thread-{suffix}",
        module.SENDER_FIELD: f"Sender{suffix}",
        module.RECIPIENT_FIELD: f"Recipient{suffix}",
        module.SUBJECT_FIELD: f"generated subject {suffix}",
        module.BODY_FIELD: f"generated body {suffix}",
        module.ACK_REQUIRED_FIELD: ack_required,
    }


def delegation_authority(
    module: ModuleType, owner: str, ordinal: int
) -> dict[str, object]:
    """One conforming same-worktree authority for the named owner."""
    return {
        module.OWNER_FIELD: owner,
        module.WRITE_SCOPE_FIELD: [f"scope-{ordinal}/answer.md"],
        module.GIT_MUTATION_FIELD: False,
    }


def doorbell_lines() -> st.SearchStrategy[tuple[str, int]]:
    """Sender names and store ids over the doorbell's open domain."""
    return st.tuples(agent_names(), store_message_ids())
