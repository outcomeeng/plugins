"""Compliance evidence for converted Codex agent boundaries."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from outcomeeng.distribution.agents import (
    GENERATED_MANIFEST_FILENAME,
    AgentConversionError,
    install_agents,
)

PLUGIN_NAME = "sample"
AGENT_NAME = "guarded-writer"
SOURCE_AGENT = f"""---
name: {AGENT_NAME}
description: Guarded writer.
model: opus
permissionMode: bypassPermissions
tools:
  - Read
disallowedTools:
  - Bash
skills:
  - develop:audit-subagents
unknownField: keep-me-visible
---

Review write behavior.
"""


def test_manual_guidance_preserves_claude_only_fields(tmp_path: Path) -> None:
    source_root = tmp_path / "dist" / "claude"
    agent_path = source_root / PLUGIN_NAME / "agents" / f"{AGENT_NAME}.md"
    agent_path.parent.mkdir(parents=True)
    agent_path.write_text(SOURCE_AGENT, encoding="utf-8")
    target_root = tmp_path / "codex-agents"

    (installed_path,) = install_agents(source_root, target_root)
    parsed = tomllib.loads(installed_path.read_text(encoding="utf-8"))

    instructions = parsed["developer_instructions"]
    assert "tools" in instructions
    assert "disallowedTools" in instructions
    assert "skills" in instructions
    assert "permissionMode: bypassPermissions" in instructions
    assert "unknownField" in instructions
    assert "sandbox_mode" not in parsed


def test_generated_toml_stays_outside_codex_plugin_manifest_content(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "dist" / "claude"
    codex_root = tmp_path / "dist" / "codex" / PLUGIN_NAME
    agent_path = source_root / PLUGIN_NAME / "agents" / f"{AGENT_NAME}.md"
    manifest_path = codex_root / ".codex-plugin" / "plugin.json"
    agent_path.parent.mkdir(parents=True)
    manifest_path.parent.mkdir(parents=True)
    agent_path.write_text(SOURCE_AGENT, encoding="utf-8")
    manifest_path.write_text(
        '{"name": "sample", "version": "0.0.1"}\n',
        encoding="utf-8",
    )

    install_agents(source_root, tmp_path / "codex-agents")

    assert not tuple(codex_root.rglob("*.toml"))
    assert "agents" not in manifest_path.read_text(encoding="utf-8")


def test_invalid_generated_manifest_uses_converter_error(tmp_path: Path) -> None:
    source_root = tmp_path / "dist" / "claude"
    target_root = tmp_path / "codex-agents"
    target_root.mkdir()
    manifest_path = target_root / GENERATED_MANIFEST_FILENAME
    manifest_path.write_text("{", encoding="utf-8")

    with pytest.raises(AgentConversionError, match="invalid generated-agent manifest"):
        install_agents(source_root, target_root)


def test_install_refuses_to_claim_untracked_identical_agent(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "dist" / "claude"
    agent_path = source_root / PLUGIN_NAME / "agents" / f"{AGENT_NAME}.md"
    agent_path.parent.mkdir(parents=True)
    agent_path.write_text(SOURCE_AGENT, encoding="utf-8")
    generated_root = tmp_path / "generated-codex-agents"
    target_root = tmp_path / "codex-agents"

    (generated_path,) = install_agents(source_root, generated_root)
    target_root.mkdir()
    target_path = target_root / generated_path.name
    target_path.write_text(generated_path.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(
        AgentConversionError,
        match="refusing to overwrite user-owned Codex agent",
    ):
        install_agents(source_root, target_root)

    assert not (target_root / GENERATED_MANIFEST_FILENAME).exists()
