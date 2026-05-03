"""Compliance tests for build-orchestration enabler.

Each test class verifies one ALWAYS assertion from
spx/18-plugin-build.enabler/65-build-orchestration.enabler/build-orchestration.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Skip the entire module if the build implementation hasn't landed yet.
# 18-plugin-build's child enablers all share this RED-phase gate.
pytest.importorskip(
    "outcomeeng.scripts.build_plugins",
    reason="18-plugin-build.enabler is in spx/EXCLUDE pending implementation",
)

REPO_ROOT = Path(__file__).resolve().parents[4]

JUSTFILE_PATH = REPO_ROOT / "justfile"
LEFTHOOK_CONFIG = REPO_ROOT / "lefthook.yml"
CLAUDE_MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"

JUST_RECIPE_NAME = "build-skills"
BUILD_MODULE_REFERENCE = "outcomeeng.scripts.build_plugins"
LEFTHOOK_PRE_COMMIT_KEY = "pre-commit"
DIST_CLAUDE_PREFIX = "./dist/claude"
DIST_CODEX_PREFIX = "./dist/codex"


class TestJustRecipe:
    """ALWAYS: just build-skills invokes the build, regenerating dist/ from src/."""

    def test_justfile_defines_build_skills_recipe(self) -> None:
        content = JUSTFILE_PATH.read_text()
        recipe_header_at_start = content.startswith(f"{JUST_RECIPE_NAME}:")
        recipe_header_inline = f"\n{JUST_RECIPE_NAME}:" in content
        assert recipe_header_at_start or recipe_header_inline, (
            f"justfile contains a `{JUST_RECIPE_NAME}` recipe definition"
        )

    def test_build_skills_recipe_invokes_build_module(self) -> None:
        content = JUSTFILE_PATH.read_text()
        assert BUILD_MODULE_REFERENCE in content, (
            f"justfile references {BUILD_MODULE_REFERENCE} for the build recipe"
        )


class TestLefthookHook:
    """ALWAYS: lefthook pre-commit hook runs the build and fails the commit when dist/ would change."""

    def test_lefthook_config_has_pre_commit_section(self) -> None:
        content = LEFTHOOK_CONFIG.read_text()
        assert f"{LEFTHOOK_PRE_COMMIT_KEY}:" in content

    def test_pre_commit_hook_references_build_recipe_or_module(self) -> None:
        content = LEFTHOOK_CONFIG.read_text()
        references_recipe = JUST_RECIPE_NAME in content
        references_module = BUILD_MODULE_REFERENCE in content
        assert references_recipe or references_module, (
            f"lefthook.yml references either `just {JUST_RECIPE_NAME}` "
            f"or `{BUILD_MODULE_REFERENCE}` in a pre-commit step"
        )


class TestClaudeMarketplaceTarget:
    """ALWAYS: .claude-plugin/marketplace.json references plugin sources under dist/claude/."""

    def test_every_claude_plugin_source_resolves_under_dist_claude(self) -> None:
        config = json.loads(CLAUDE_MARKETPLACE.read_text())
        plugin_root = config.get("metadata", {}).get("pluginRoot")

        if plugin_root == DIST_CLAUDE_PREFIX:
            return

        for plugin in config.get("plugins", []):
            source = plugin.get("source")
            assert isinstance(source, str), (
                f"plugin {plugin.get('name')} declares source={source!r}; "
                f"Claude marketplace expects string source paths"
            )
            assert source.startswith(DIST_CLAUDE_PREFIX), (
                f"plugin {plugin.get('name')} source={source!r} does not start "
                f"with {DIST_CLAUDE_PREFIX}"
            )


class TestCodexMarketplaceTarget:
    """ALWAYS: .agents/plugins/marketplace.json references plugin sources under dist/codex/."""

    def test_every_codex_plugin_source_path_starts_with_dist_codex(self) -> None:
        config = json.loads(CODEX_MARKETPLACE.read_text())
        for plugin in config.get("plugins", []):
            source = plugin.get("source", {})
            assert isinstance(source, dict), (
                f"plugin {plugin.get('name')} declares non-object source={source!r}"
            )
            path = source.get("path")
            assert isinstance(path, str), (
                f"plugin {plugin.get('name')} source.path={path!r} is not a string"
            )
            assert path.startswith(DIST_CODEX_PREFIX), (
                f"plugin {plugin.get('name')} source.path={path!r} does not start "
                f"with {DIST_CODEX_PREFIX}"
            )
