"""Generated domains for sessions evidence."""

from __future__ import annotations

import json
import hashlib
import uuid
from dataclasses import dataclass, replace

from outcomeeng.spec_tree_structure import (
    MIN_NODE_INDEX,
    NodeKind,
    format_node_directory_name,
)


@dataclass(frozen=True)
class HandoffPayload:
    """Generated handoff request and the values its body carries."""

    header: dict[str, object]
    body: str
    active_node_path: str
    coordination_note: str

    def with_field(self, field: str, value: object) -> HandoffPayload:
        """Return a copy carrying one source-owned protocol field."""
        header = dict(self.header)
        header[field] = value
        return replace(self, header=header)

    def wire_text(self) -> str:
        """Render the JSON-header-plus-body input accepted by the CLI."""
        return f"{json.dumps(self.header)}\n{self.body}"


def generated_token() -> str:
    """Return an invocation-unique synthetic value."""
    return uuid.uuid4().hex


def generated_relative_path() -> str:
    """Return a generated checkout-relative Markdown path."""
    return f"{generated_token()}.md"


def generated_number() -> str:
    """Return a generated decimal identifier."""
    return str(uuid.uuid4().int)


def generated_sha() -> str:
    """Return a generated full-width hexadecimal object identifier."""
    return hashlib.sha1(uuid.uuid4().bytes, usedforsecurity=False).hexdigest()


def generated_handoff_payload(required_fields: tuple[str, ...]) -> HandoffPayload:
    """Generate a valid request from fields reported required by the real CLI."""
    active_node_path = format_node_directory_name(
        MIN_NODE_INDEX,
        generated_token(),
        NodeKind.ENABLER,
    )
    coordination_note = generated_token()
    body = "\n".join((generated_token(), active_node_path, coordination_note, ""))
    return HandoffPayload(
        header={field: generated_token() for field in required_fields},
        body=body,
        active_node_path=active_node_path,
        coordination_note=coordination_note,
    )


def generated_handoff_batch(
    required_fields: tuple[str, ...],
) -> tuple[HandoffPayload, ...]:
    """Generate the smallest batch that exercises a multi-session release."""
    return (
        generated_handoff_payload(required_fields),
        generated_handoff_payload(required_fields),
    )


__all__ = [
    "HandoffPayload",
    "generated_handoff_batch",
    "generated_handoff_payload",
    "generated_number",
    "generated_relative_path",
    "generated_sha",
    "generated_token",
]
