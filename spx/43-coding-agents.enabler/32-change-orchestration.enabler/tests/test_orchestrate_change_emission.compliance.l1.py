"""Compliance evidence for the per-target emission of `/orchestrate-change`.

The Codex and Claude Code emissions of the skill are compared below their front
matter. The lines only the Codex emission carries name the one result of the
skill's result list that no Start or Check step of the Claude Code emission
returns.
"""

from __future__ import annotations

import re
from pathlib import Path

from outcomeeng.distribution.contracts import (
    FRONTMATTER_DELIMITER,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    Target,
)
from outcomeeng_testing.harnesses.target_emission import emitted_texts

SKILL_PATH = (
    Path("coding-agents") / SKILLS_SUBDIR_NAME / "orchestrate-change" / SKILL_FILENAME
)
BACKTICKED_TOKEN = re.compile(r"`([^`\s]+)`")


def _body_lines(target: Target) -> list[str]:
    rows = [
        row
        for row in emitted_texts()
        if row.target is target and row.path == SKILL_PATH
    ]
    assert len(rows) == 1, (target, len(rows))
    text = rows[0].text
    _, _, body = text.split(FRONTMATTER_DELIMITER, 2)
    return body.splitlines()


def test_codex_emission_adds_lines_naming_the_result_start_never_returns_on_claude() -> (
    None
):
    # ALWAYS: on Codex, Start returns an explicit result naming the Change and writing no store state; on Claude Code, Start returns no such result.
    codex = _body_lines(Target.CODEX)
    claude = _body_lines(Target.CLAUDE)
    codex_only = [line for line in codex if line not in claude]
    claude_text = "\n".join(claude)
    codex_only_tokens = {
        token for line in codex_only for token in BACKTICKED_TOKEN.findall(line)
    }
    unreturned = {
        token
        for token in codex_only_tokens
        if f"`{token}`" in claude_text and f"result `{token}`" not in claude_text
    }

    assert any(line.strip() for line in codex_only), "no Codex-only lines"
    assert len(unreturned) == 1, (codex_only_tokens, unreturned)


def test_claude_emission_carries_no_line_the_codex_emission_lacks() -> None:
    # ALWAYS: Check runs unchanged on Codex, and on Claude Code Start returns no such result.
    codex = _body_lines(Target.CODEX)
    claude = _body_lines(Target.CLAUDE)

    assert [line for line in claude if line not in codex] == []
