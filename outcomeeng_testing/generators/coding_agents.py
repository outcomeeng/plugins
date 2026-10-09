"""Generated public-Prowl identity domains for coding-agent evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import ModuleType

from hypothesis import strategies as st

from outcomeeng_testing.generators.agent_mail import (
    DOORBELL_DELIMITER_CHARACTERS,
    PRINTABLE_CATEGORIES,
    UnicodeCategory,
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


# Unicode general categories whose members never print: control, format,
# private-use, unassigned, and the line, paragraph, and space separators. The
# surrogate category is covered by the finite set because a lone surrogate is
# not a character a generated text alphabet draws.
UNPRINTABLE_CATEGORIES: tuple[UnicodeCategory, ...] = (
    "Cc",
    "Cf",
    "Co",
    "Cn",
    "Zl",
    "Zp",
    "Zs",
)

# Characters of the classes the governing spec names as never rendering, each
# written as its code point: control (NUL, tab, line feed, vertical tab, form
# feed, carriage return, escape, DEL, NEL), format (zero-width space, the
# bidirectional marks, embeddings, overrides and isolates, byte-order mark),
# line and paragraph separators, other separators (no-break space, ogham space
# mark, em space, ideographic space), an unassigned code point, a private-use
# code point, and a lone surrogate.
UNPRINTABLE_CHARACTERS = (
    "\u0000",
    "\u0009",
    "\u000a",
    "\u000b",
    "\u000c",
    "\u000d",
    "\u001b",
    "\u007f",
    "\u0085",
    "\u00a0",
    "\u1680",
    "\u200b",
    "\u200e",
    "\u200f",
    "\u2003",
    "\u2028",
    "\u2029",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
    "\u3000",
    "\ufeff",
    "\u0378",
    "\ue000",
    "\ud800",
)


def unrenderable_labels() -> tuple[str, ...]:
    """The finite set of labels a doorbell cannot carry: the empty label, a label
    holding a line break, a label holding one of the four bracket and angle
    delimiters, and a label holding one character of each unprintable class the
    governing spec names. The set follows the spec's statement of when a label
    does not render."""
    return (
        "",
        *(f"Front{line_break}Desk" for line_break in ("\n", "\r", "\r\n")),
        *(f"Front{delimiter}Desk" for delimiter in DOORBELL_DELIMITER_CHARACTERS),
        *(f"Front{character}Desk" for character in UNPRINTABLE_CHARACTERS),
    )


def unrenderable_label_texts() -> st.SearchStrategy[str]:
    """Labels over the open domain of unrenderable labels, each built around at
    least one character that never prints or one doorbell delimiter, between
    arbitrary printable text."""
    flaw = st.one_of(
        st.sampled_from(UNPRINTABLE_CHARACTERS),
        st.sampled_from(DOORBELL_DELIMITER_CHARACTERS),
        st.characters(categories=UNPRINTABLE_CATEGORIES, exclude_characters=" "),
    )
    printable = st.text(
        alphabet=st.characters(categories=PRINTABLE_CATEGORIES), max_size=20
    )
    return st.builds(
        lambda head, bad, tail: f"{head}{bad}{tail}", printable, flaw, printable
    )


def renderable_label_texts() -> st.SearchStrategy[str]:
    """Labels over the open domain of renderable labels: non-empty, built from
    printable characters and the ASCII space, free of the four delimiters."""
    return st.text(
        alphabet=st.one_of(
            st.characters(
                categories=PRINTABLE_CATEGORIES,
                exclude_characters=DOORBELL_DELIMITER_CHARACTERS,
            ),
            st.just(" "),
        ),
        min_size=1,
        max_size=60,
    )


def doorbell_labels() -> st.SearchStrategy[str | None]:
    """Sender labels over the doorbell's open domain: absent, position-shaped,
    free text over every Unicode category including the control, format,
    separator, private-use, and unassigned ones, and every unrenderable label."""
    free_text = st.text(
        alphabet=st.characters(
            categories=(*PRINTABLE_CATEGORIES, *UNPRINTABLE_CATEGORIES)
        ),
        max_size=60,
    )
    return st.one_of(
        st.none(),
        position_labels(),
        free_text,
        unrenderable_label_texts(),
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
