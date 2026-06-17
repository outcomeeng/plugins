#!/usr/bin/env python3
"""PostToolUse hook for the spec-tree:apply skill.

Fires after each Skill tool invocation. When the invoked skill is one of the
applying flow's step skills (architecture, test, implementation), emits
``additionalContext`` reminding the agent to run the matching audit gate before
proceeding. Any other skill yields no output.

Python stdlib only — no shell, no ``jq``. A consumer environment is guaranteed to
have ``python3`` (every skill already runs it) but not a shell or ``jq``, so a
Python hook adds no runtime requirement.
"""

from __future__ import annotations

import json
import sys

GATE_REMINDERS = {
    "architecting": "GATE: Architecture step complete. Invoke the architecture auditing skill NOW before proceeding to Step 5 (tests).",
    "test": "GATE: Testing step complete. Invoke the test auditing skill NOW before proceeding to Step 7 (implementation).",
    "coding": "GATE: Implementation step complete. Invoke the code auditing skill NOW before declaring done.",
}

GATE_SKILL_PREFIXES = {
    "architecting": ("architecting-", "architect-"),
    "test": ("testing-", "test-"),
    "coding": ("coding-", "code-"),
}


def reminder_for_skill(skill: str) -> str | None:
    """Map an invoked skill name to its audit-gate reminder, or None when no gate applies.

    Matches by flow stage independent of language. A step skill is named with a
    stage prefix plus a language suffix, optionally ``<plugin>:`` prefixed, so
    every language plugin's step skills map without per-language enumeration. The
    bare spec-tree ``test`` skill has no language suffix and does not match.
    """
    name = skill.rsplit(":", 1)[-1]
    for gate, prefixes in GATE_SKILL_PREFIXES.items():
        if name.startswith(prefixes):
            return GATE_REMINDERS[gate]
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    if not isinstance(data, dict):
        return 0
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    skill = tool_input.get("skill")
    if not isinstance(skill, str):
        return 0
    reminder = reminder_for_skill(skill)
    if reminder is not None:
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": reminder,
                }
            },
            sys.stdout,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
