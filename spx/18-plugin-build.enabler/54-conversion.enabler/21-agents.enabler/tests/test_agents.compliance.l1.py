"""Compliance evidence for converted Codex agent boundaries."""

from __future__ import annotations

from pathlib import Path
import tomllib

import pytest

from outcomeeng.distribution.agents import (
    CODEX_AGENT_ENV_SEPARATOR,
    CODEX_AGENT_ENV_VAR,
    DEFAULT_SOURCE_ROOT,
    GENERATED_MANIFEST_FILENAME,
    AgentConversionError,
    ClaudeAgent,
    agent_environment_marker,
    install_agents,
)
from outcomeeng_testing.harnesses.src_tree import write_agent_tree

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
    source_root = write_agent_tree(tmp_path, PLUGIN_NAME, {AGENT_NAME: SOURCE_AGENT})
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


def test_default_source_root_uses_rendered_codex_agents() -> None:
    assert DEFAULT_SOURCE_ROOT == Path("dist") / "codex"


def test_generated_toml_stays_outside_codex_plugin_manifest_content(
    tmp_path: Path,
) -> None:
    source_root = write_agent_tree(tmp_path, PLUGIN_NAME, {AGENT_NAME: SOURCE_AGENT})
    codex_root = tmp_path / "dist" / "codex" / PLUGIN_NAME
    manifest_path = codex_root / ".codex-plugin" / "plugin.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        '{"name": "sample", "version": "0.0.1"}\n',
        encoding="utf-8",
    )

    install_agents(source_root, tmp_path / "codex-agents")

    assert not tuple(codex_root.rglob("*.toml"))
    assert "agents" not in manifest_path.read_text(encoding="utf-8")


def test_environment_marker_is_namespaced_by_source_plugin(
    tmp_path: Path,
) -> None:
    source_root = write_agent_tree(
        tmp_path,
        "alpha",
        {AGENT_NAME: SOURCE_AGENT},
    )
    write_agent_tree(
        tmp_path,
        "beta",
        {
            "read-only-reviewer": SOURCE_AGENT.replace(
                f"name: {AGENT_NAME}",
                "name: read-only-reviewer",
            )
        },
    )
    target_root = tmp_path / "codex-agents"

    installed_paths = install_agents(source_root, target_root)

    markers = {
        tomllib.loads(path.read_text(encoding="utf-8"))["shell_environment_policy"][
            "set"
        ][CODEX_AGENT_ENV_VAR]
        for path in installed_paths
    }
    assert markers == {
        f"alpha{CODEX_AGENT_ENV_SEPARATOR}{AGENT_NAME}",
        f"beta{CODEX_AGENT_ENV_SEPARATOR}read-only-reviewer",
    }


def test_environment_marker_without_source_plugin_uses_agent_name() -> None:
    marker = agent_environment_marker(
        ClaudeAgent(
            source_path=Path("reviewer.md"),
            name=AGENT_NAME,
            description="Review.",
            body="Review.",
        )
    )

    assert marker == AGENT_NAME


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
    source_root = write_agent_tree(tmp_path, PLUGIN_NAME, {AGENT_NAME: SOURCE_AGENT})
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


def test_install_overwrites_generated_owned_agent_from_manifest(
    tmp_path: Path,
) -> None:
    source_root = write_agent_tree(tmp_path, PLUGIN_NAME, {AGENT_NAME: SOURCE_AGENT})
    target_root = tmp_path / "codex-agents"

    (installed_path,) = install_agents(source_root, target_root)
    installed_path.write_text(
        "user-visible stale generated content\n", encoding="utf-8"
    )

    (rewritten_path,) = install_agents(source_root, target_root)

    assert rewritten_path == installed_path
    assert "user-visible stale generated content" not in rewritten_path.read_text(
        encoding="utf-8"
    )


def test_duplicate_generated_agent_filename_fails_before_install_writes(
    tmp_path: Path,
) -> None:
    source_root = write_agent_tree(
        tmp_path,
        PLUGIN_NAME,
        {
            "reviewer": """---
name: reviewer
description: First reviewer.
---

Review one.
""",
            "reviewer-bang": """---
name: reviewer!
description: Second reviewer.
---

Review two.
""",
        },
    )
    target_root = tmp_path / "codex-agents"

    with pytest.raises(AgentConversionError, match="multiple Claude agents convert"):
        install_agents(source_root, target_root)

    assert not target_root.exists()
