"""Generated public-Prowl identity domains for coding-agent evidence."""

from __future__ import annotations

from dataclasses import dataclass


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
