"""Scenario evidence for Claude agent to Codex custom-agent conversion."""

from __future__ import annotations

import tomllib
from pathlib import Path

from outcomeeng.distribution.agents import (
    convert_agent,
    parse_agent_markdown,
    render_agent_toml,
)

PLUGIN_NAME = "sample"
AGENT_NAME = "changes-reviewer"
AGENT_DESCRIPTION = "Review changes."
AGENT_BODY = "Review the diff and report findings."
SOURCE_AGENT = f"""---
name: {AGENT_NAME}
description: {AGENT_DESCRIPTION}
model: sonnet
skills:
  - spec-tree:reviewing-changes
tools: Read, Bash
---

{AGENT_BODY}
"""


def test_agent_frontmatter_and_body_convert_to_codex_toml(tmp_path: Path) -> None:
    source = tmp_path / PLUGIN_NAME / "agents" / f"{AGENT_NAME}.md"
    source.parent.mkdir(parents=True)
    source.write_text(SOURCE_AGENT, encoding="utf-8")

    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    parsed = tomllib.loads(rendered)

    assert parsed["name"] == AGENT_NAME
    assert parsed["description"] == AGENT_DESCRIPTION
    assert parsed["model"] == "gpt-5.4-mini"
    instructions = parsed["developer_instructions"]
    assert AGENT_BODY in instructions
    assert "spec-tree:reviewing-changes" in instructions
    assert "Read" in instructions
    assert "Bash" in instructions


def test_folded_yaml_description_converts_to_text(tmp_path: Path) -> None:
    source = tmp_path / PLUGIN_NAME / "agents" / f"{AGENT_NAME}.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        """---
name: changes-reviewer
description: >-
  Review working changes against a base ref.
  Accept optional PR, branch, or range inputs.
model: sonnet
---

Review the diff and report findings.
""",
        encoding="utf-8",
    )

    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    parsed = tomllib.loads(rendered)

    assert parsed["description"] == (
        "Review working changes against a base ref. "
        "Accept optional PR, branch, or range inputs."
    )


def test_skills_are_preserved_as_developer_instruction_guidance(
    tmp_path: Path,
) -> None:
    source = tmp_path / PLUGIN_NAME / "agents" / f"{AGENT_NAME}.md"
    source.parent.mkdir(parents=True)
    source.write_text(SOURCE_AGENT, encoding="utf-8")

    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    parsed = tomllib.loads(rendered)

    instructions = parsed["developer_instructions"]
    assert "skills" in instructions
    assert "prompt guidance" in instructions
    assert "preload" in instructions
