"""Scenario evidence for Claude agent to Codex custom-agent conversion."""

from __future__ import annotations

import tomllib
from pathlib import Path

from outcomeeng.distribution.agents import (
    CODEX_AGENT_ENV_VAR,
    READ_ONLY_SANDBOX_MODE,
    WEB_SEARCH_DISABLED,
    agent_environment_marker,
    convert_agent,
    parse_agent_markdown,
    render_agent_toml,
)
from outcomeeng_testing.harnesses.src_tree import write_agent_source

PLUGIN_NAME = "sample"
AGENT_NAME = "changes-reviewer"
AGENT_DESCRIPTION = "Review changes."
AGENT_BODY = "Review the diff and report findings."
SOURCE_AGENT = f"""---
name: {AGENT_NAME}
description: {AGENT_DESCRIPTION}
model: sonnet
skills:
  - spec-tree:review-changes
tools: Read, Bash
---

{AGENT_BODY}
"""


def test_agent_frontmatter_and_body_convert_to_codex_toml(tmp_path: Path) -> None:
    source = write_agent_source(tmp_path, PLUGIN_NAME, AGENT_NAME, SOURCE_AGENT)
    agent = parse_agent_markdown(source)

    rendered = render_agent_toml(convert_agent(agent))
    parsed = tomllib.loads(rendered)

    assert parsed["name"] == AGENT_NAME
    assert parsed["description"] == AGENT_DESCRIPTION
    assert parsed["model"] == "gpt-5.4"
    assert parsed["web_search"] == WEB_SEARCH_DISABLED
    assert "sandbox_mode" not in parsed
    assert parsed["shell_environment_policy"]["set"] == {
        CODEX_AGENT_ENV_VAR: agent_environment_marker(agent)
    }
    instructions = parsed["developer_instructions"]
    assert AGENT_BODY in instructions
    assert "spec-tree:review-changes" in instructions
    assert "Read" in instructions
    assert "Bash" in instructions


def test_folded_yaml_description_converts_to_text(tmp_path: Path) -> None:
    source = write_agent_source(
        tmp_path,
        PLUGIN_NAME,
        AGENT_NAME,
        """---
name: changes-reviewer
description: >-
  Review working changes against a base ref.
  Accept optional PR, branch, or range inputs.
model: sonnet
---

Review the diff and report findings.
""",
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
    source = write_agent_source(tmp_path, PLUGIN_NAME, AGENT_NAME, SOURCE_AGENT)

    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    parsed = tomllib.loads(rendered)

    instructions = parsed["developer_instructions"]
    assert "skills" in instructions
    assert "prompt guidance" in instructions
    assert "preload" in instructions


def test_explicit_empty_tools_frontmatter_converts_to_restrictive_codex_config(
    tmp_path: Path,
) -> None:
    source = write_agent_source(
        tmp_path,
        PLUGIN_NAME,
        AGENT_NAME,
        """---
name: changes-reviewer
description: Review changes.
tools: []
---

Review the diff and report findings.
""",
    )

    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    parsed = tomllib.loads(rendered)

    assert parsed["web_search"] == WEB_SEARCH_DISABLED
    assert parsed["sandbox_mode"] == READ_ONLY_SANDBOX_MODE
