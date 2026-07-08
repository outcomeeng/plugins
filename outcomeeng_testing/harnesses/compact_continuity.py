"""Harnesses for compact-summary continuity evidence."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
COMPACT_PROMPT_FIELD = "compactPrompt"
SPEC_TREE_FOUNDATION_MARKER = "<SPEC_TREE_FOUNDATION>"
SPEC_TREE_CONTEXT_MARKER = "<SPEC_TREE_CONTEXT>"
STATE_SCHEMA_SECTION_HEADINGS = (
    "### Active spec-tree node",
    "### Pre-compact markers",
    "### Modified files this session",
    "### Open questions",
    "### Last user request",
    "### In-flight observations",
)
IMPERATIVE_SECTION_HEADINGS = (
    "### Next step",
    "### Resume here",
    "### Now do X",
    "### Persistence proposal",
    "### Starting point",
)
SKILL_INVOCATION_TOKENS = (
    "/understand",
    "/contextualize",
    "/apply",
    "/handoff",
    "/pickup",
)


def compact_prompt_contains_state_schema_sections() -> bool:
    compact_prompt = _compact_prompt()
    return all(heading in compact_prompt for heading in STATE_SCHEMA_SECTION_HEADINGS)


def compact_prompt_uses_marker_trigger() -> bool:
    compact_prompt = _compact_prompt()
    return (
        SPEC_TREE_FOUNDATION_MARKER in compact_prompt
        and SPEC_TREE_CONTEXT_MARKER in compact_prompt
        and "contains a `<SPEC_TREE_FOUNDATION>` or `<SPEC_TREE_CONTEXT>` marker"
        in compact_prompt
    )


def compact_prompt_omits_imperative_sections() -> bool:
    headings = _compact_prompt_headings()
    return not any(heading in headings for heading in IMPERATIVE_SECTION_HEADINGS)


def compact_prompt_omits_skill_invocations() -> bool:
    compact_prompt = _compact_prompt()
    return not any(token in compact_prompt for token in SKILL_INVOCATION_TOKENS)


def _compact_prompt() -> str:
    with CLAUDE_SETTINGS_PATH.open(encoding="utf-8") as settings_file:
        settings = json.load(settings_file)
    compact_prompt = settings.get(COMPACT_PROMPT_FIELD)
    if not isinstance(compact_prompt, str):
        raise TypeError(f"{COMPACT_PROMPT_FIELD} must be a string")
    return compact_prompt


def _compact_prompt_headings() -> set[str]:
    return {
        line.strip()
        for line in _compact_prompt().splitlines()
        if line.startswith("### ")
    }
