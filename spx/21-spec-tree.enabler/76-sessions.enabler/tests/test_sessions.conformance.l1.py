"""
Conformance tests for 76-sessions.enabler (sessions.md conformance assertion).

Verifies that the compactPrompt configuration in .claude/settings.json contains
all six state-schema section headers mandated by the spec. The compactPrompt
instructs Claude Code's summarization to append these sections; if any header
is absent, the compact summary produced during a live session will lack that
schema field, breaking post-compact continuity.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SETTINGS_FILE = REPO_ROOT / ".claude" / "settings.json"

REQUIRED_SECTION_HEADERS = [
    "### Active spec-tree node",
    "### Pre-compact markers",
    "### Modified files this session",
    "### Open questions",
    "### Last user request",
    "### In-flight observations",
]


@pytest.fixture(scope="module")
def compact_prompt() -> str:
    assert SETTINGS_FILE.exists(), f"settings file not found: {SETTINGS_FILE}"
    settings = json.loads(SETTINGS_FILE.read_text())
    prompt = settings.get("compactPrompt", "")
    assert prompt, "compactPrompt is missing or empty in .claude/settings.json"
    return prompt


class TestCompactPromptContainsStateSchemaHeaders:
    @pytest.mark.parametrize("header", REQUIRED_SECTION_HEADERS)
    def test_section_header_present(self, compact_prompt: str, header: str):
        assert header in compact_prompt, (
            f"compactPrompt in .claude/settings.json is missing section header: {header!r}"
        )

    def test_no_imperative_section_headers(self, compact_prompt: str):
        # Check for forbidden phrases used as Markdown section headers (### Title).
        # Plain mentions of these phrases inside prohibition instructions are fine
        # (e.g. 'Do not include "next step" framing'); only headers create imperative
        # sections that compound base-prompt residual imperatives.
        forbidden_headers = [
            "### next step",
            "### resume here",
            "### now do",
            "### persistence proposal",
            "### starting point",
            "### optional next step",
        ]
        found = [h for h in forbidden_headers if h in compact_prompt.lower()]
        assert not found, (
            f"compactPrompt contains forbidden imperative section headers: {found}. "
            "Imperative section headers compound base-prompt residual imperatives."
        )

    def test_state_recording_instruction_present(self, compact_prompt: str):
        assert (
            "past-tense" in compact_prompt.lower()
            or "factual" in compact_prompt.lower()
        ), "compactPrompt must instruct the agent to write in past-tense factual form"
