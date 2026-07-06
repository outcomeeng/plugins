"""Harness checks for compactPrompt conformance evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = REPO_ROOT / ".claude" / "settings.json"
REQUIRED_SECTION_HEADERS = (
    "### Active spec-tree node",
    "### Pre-compact markers",
    "### Modified files this session",
    "### Open questions",
    "### Last user request",
    "### In-flight observations",
)
FORBIDDEN_SECTION_HEADERS = (
    "### next step",
    "### resume here",
    "### now do",
    "### persistence proposal",
    "### starting point",
    "### optional next step",
)


@dataclass(frozen=True)
class CompactPromptValidation:
    name: str
    passed: bool
    evidence: str


def validate_compact_prompt_state_schema() -> CompactPromptValidation:
    prompt = _compact_prompt()
    missing = [header for header in REQUIRED_SECTION_HEADERS if header not in prompt]
    return CompactPromptValidation(
        name="state_schema_headers",
        passed=not missing,
        evidence="all required state-schema headers present"
        if not missing
        else f"missing state-schema headers: {missing}",
    )


def validate_compact_prompt_marker_gate() -> CompactPromptValidation:
    preamble = _compact_prompt().split("###", 1)[0]
    has_marker_gate = (
        "<SPEC_TREE_FOUNDATION>" in preamble or "<SPEC_TREE_CONTEXT>" in preamble
    )
    return CompactPromptValidation(
        name="marker_gate",
        passed=has_marker_gate,
        evidence="preamble gates appendix on a spec-tree marker"
        if has_marker_gate
        else "preamble lacks a concrete spec-tree marker gate",
    )


def compact_prompt_contains_state_schema_headers() -> bool:
    result = validate_compact_prompt_state_schema()
    assert result.passed, result.evidence
    return True


def compact_prompt_omits_imperative_section_headers() -> bool:
    prompt = _compact_prompt().lower()
    found = [header for header in FORBIDDEN_SECTION_HEADERS if header in prompt]
    assert not found, (
        f"compactPrompt contains forbidden imperative section headers: {found}. "
        "Imperative section headers compound base-prompt residual imperatives."
    )
    return True


def compact_prompt_requires_state_recording_voice() -> bool:
    prompt = _compact_prompt().lower()
    assert "past-tense" in prompt or "factual" in prompt, (
        "compactPrompt must instruct the agent to write in past-tense factual form"
    )
    return True


def compact_prompt_append_trigger_references_marker() -> bool:
    result = validate_compact_prompt_marker_gate()
    assert result.passed, result.evidence
    return True


def _compact_prompt() -> str:
    assert SETTINGS_FILE.exists(), f"settings file not found: {SETTINGS_FILE}"
    prompt = json.loads(SETTINGS_FILE.read_text()).get("compactPrompt", "")
    assert prompt, "compactPrompt is missing or empty in .claude/settings.json"
    return str(prompt)
