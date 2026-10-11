"""Source-owned assertion-audit payload contract.

``/audit-assertions`` records one scope unit per ``[audit]`` assertion of a node
spec. SPX refuses audit class ``assertion``; the pair it accepts for a node spec
subject is class ``spec`` with kind ``spec``, and the assertion's designator
travels in the unit key and the finding message.
"""

from __future__ import annotations

from typing import Final

ASSERTION_AUDIT_CLASS: Final = "spec"
ASSERTION_AUDIT_KIND: Final = "spec"
ASSERTION_AUDIT_SKILL_NAME: Final = "audit-assertions"
ASSERTION_AUDITOR_AGENT_NAME: Final = "assertion-auditor"
UNIT_KEY_PREFIX: Final = "assertion"


def assertion_audit_unit_key(designator: str, node_spec_path: str) -> str:
    """Return the stable identity of one assertion's scope unit."""
    return f"{UNIT_KEY_PREFIX}:{designator}:{node_spec_path}"
