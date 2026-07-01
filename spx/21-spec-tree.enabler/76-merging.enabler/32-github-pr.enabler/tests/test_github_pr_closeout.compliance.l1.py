"""Compliance tests for GitHub-PR transport closeout."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest


REPO_ROOT: Final = Path(__file__).resolve().parents[5]
SPEC_TREE_PLUGIN: Final = REPO_ROOT / "src" / "plugins" / "spec-tree"
CLAUDE_PLUGIN: Final = REPO_ROOT / "dist" / "claude" / "spec-tree"
CODEX_PLUGIN: Final = REPO_ROOT / "dist" / "codex" / "spec-tree"

MANAGE_GITHUB_PR_SKILL_FILES: Final = (
    SPEC_TREE_PLUGIN / "skills" / "manage-github-pr" / "SKILL.md",
    CLAUDE_PLUGIN / "skills" / "manage-github-pr" / "SKILL.md",
    CODEX_PLUGIN / "skills" / "manage-github-pr" / "SKILL.md",
)
MANAGE_PR_SKILL_FILES: Final = (
    SPEC_TREE_PLUGIN / "skills" / "manage-pr" / "SKILL.md",
    CLAUDE_PLUGIN / "skills" / "manage-pr" / "SKILL.md",
    CODEX_PLUGIN / "skills" / "manage-pr" / "SKILL.md",
)


@pytest.mark.parametrize("skill_path", MANAGE_GITHUB_PR_SKILL_FILES)
def test_manage_github_pr_uses_handoff_for_final_closeout(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "The final operator-facing closeout comes from `/handoff`" in text
    assert "Invoke `/handoff` plain" in text
    assert "branch-state closeout record" in text
    assert "**Remaining Branches**" in text
    assert "Do not append a separate merge receipt" in text
    assert "never receives `--no-session`" in text
    assert "/handoff --no-session" not in text


@pytest.mark.parametrize("skill_path", MANAGE_PR_SKILL_FILES)
def test_manage_pr_returns_or_invokes_handoff_closeout(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "Step 9 — Closeout routing" in text
    assert "/merging-standards `<branch_state_closeout>`" in text
    assert "return closeout-ready evidence to `/manage-github-pr` Step 7" in text
    assert "branch-state closeout record with **Remaining Branches** groups" in text
    assert "Invoke `/handoff` plain" in text
    assert "receipt-only response" in text
    assert "/handoff --no-session" not in text
