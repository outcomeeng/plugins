"""Generated public-Prowl identity domains for coding-agent evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import ModuleType

from hypothesis import strategies as st

from outcomeeng_testing.generators.agent_mail import (
    agent_names,
    position_labels,
    store_message_ids,
)


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


def delegation_authority(module: ModuleType, owner: str) -> dict[str, object]:
    """One conforming same-worktree authority for the named owner: no write
    scope, no Git mutation."""
    return {module.OWNER_FIELD: owner, module.GIT_MUTATION_FIELD: False}


def scoped_delegation_authority(
    module: ModuleType, authority: dict[str, object], ordinal: int
) -> dict[str, object]:
    """A conforming scope-less authority with a write scope added: the one
    field a same-worktree delegation never carries."""
    return {**authority, module.WRITE_SCOPE_FIELD: [f"delegation-{ordinal}/answer.md"]}


def unrenderable_labels() -> tuple[str, ...]:
    """The finite set of labels a doorbell cannot carry: the empty label, a label
    holding a line break, and a label holding one of the four bracket and angle
    delimiters. The set follows the governing spec's statement of when a label
    does not render."""
    return (
        "",
        *(f"Front{line_break}Desk" for line_break in ("\n", "\r", "\r\n")),
        *(f"Front{delimiter}Desk" for delimiter in ("[", "]", "<", ">")),
    )


def doorbell_labels() -> st.SearchStrategy[str | None]:
    """Sender labels over the doorbell's open domain: absent, position-shaped,
    free text without line separators, and every unrenderable label."""
    free_text = st.text(
        alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Zl", "Zp")),
        max_size=60,
    )
    return st.one_of(
        st.none(),
        position_labels(),
        free_text,
        st.sampled_from(unrenderable_labels()),
    )


def doorbell_lines() -> st.SearchStrategy[tuple[str, int, str | None]]:
    """Sender names, store ids, and sender labels over the doorbell's open domain."""
    return st.tuples(agent_names(), store_message_ids(), doorbell_labels())


# The synthetic mutation-target status a proposal reports, and a status that
# differs from it for a stale-target case.
OBSERVED_TARGET_STATUS = "clean"
MISMATCHED_TARGET_STATUS = "dirty"


def mutation_observation(
    module: ModuleType,
    participant: dict[str, str],
) -> tuple[dict[str, object], dict[str, object]]:
    """A synthetic mutation target for one participant and its projected observed state."""
    target: dict[str, object] = {
        module.PANE_FIELD: participant[module.PANE_FIELD],
        module.WORKTREE_FIELD: participant[module.WORKTREE_FIELD],
        module.BRANCH_FIELD: participant[module.BRANCH_FIELD],
        module.REPOSITORY_FIELD: participant[module.REPOSITORY_FIELD],
        module.HEAD_FIELD: hashlib.sha1(
            participant[module.PANE_FIELD].encode(), usedforsecurity=False
        ).hexdigest(),
        module.STATUS_FIELD: OBSERVED_TARGET_STATUS,
    }
    state = {field: target[field] for field in module.OBSERVED_STATE_FIELDS}
    return target, state


def unsupported_capability_operation(capability: ModuleType) -> str:
    """An operation name outside the capability's declared operations, derived
    from every declared name so no member can equal it."""
    return "-".join(operation.value for operation in capability.Operation)
