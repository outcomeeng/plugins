"""Compliance evidence for build orchestration wiring."""

from __future__ import annotations

import json
from pathlib import Path

JUSTFILE = Path("Justfile")
LEFTHOOK = Path("lefthook.yml")
CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
BUILD_RECIPE = "build-skills"
BUILD_MODULE = "outcomeeng.distribution.build"
CLAUDE_PLUGIN_ROOT = "./dist/claude"
CODEX_PLUGIN_ROOT = "./dist/codex"


def test_justfile_declares_build_skills_recipe() -> None:
    justfile = JUSTFILE.read_text(encoding="utf-8")

    assert f"{BUILD_RECIPE}:" in justfile
    assert BUILD_MODULE in justfile


def test_lefthook_runs_build_and_checks_dist_drift() -> None:
    lefthook = LEFTHOOK.read_text(encoding="utf-8")

    assert BUILD_RECIPE in lefthook
    assert "git diff --exit-code dist" in lefthook


def test_claude_marketplace_points_at_dist_claude() -> None:
    data = json.loads(CLAUDE_MARKETPLACE.read_text(encoding="utf-8"))

    assert data["metadata"]["pluginRoot"] == CLAUDE_PLUGIN_ROOT
    for plugin in data["plugins"]:
        assert plugin["source"].startswith(CLAUDE_PLUGIN_ROOT)


def test_codex_marketplace_points_at_dist_codex() -> None:
    data = json.loads(CODEX_MARKETPLACE.read_text(encoding="utf-8"))

    for plugin in data["plugins"]:
        assert plugin["source"]["path"].startswith(CODEX_PLUGIN_ROOT)
