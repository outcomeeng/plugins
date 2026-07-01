"""Compliance tests for direct /manage-pr closeout."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest


REPO_ROOT: Final = Path(__file__).resolve().parents[6]
SPEC_TREE_PLUGIN: Final = REPO_ROOT / "src" / "plugins" / "spec-tree"
CLAUDE_PLUGIN: Final = REPO_ROOT / "dist" / "claude" / "spec-tree"
CODEX_PLUGIN: Final = REPO_ROOT / "dist" / "codex" / "spec-tree"

MANAGE_PR_SKILL_FILES: Final = (
    SPEC_TREE_PLUGIN / "skills" / "manage-pr" / "SKILL.md",
    CLAUDE_PLUGIN / "skills" / "manage-pr" / "SKILL.md",
    CODEX_PLUGIN / "skills" / "manage-pr" / "SKILL.md",
)


@pytest.mark.parametrize("skill_path", MANAGE_PR_SKILL_FILES)
def test_direct_manage_pr_routes_closeout_through_handoff(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "Step 9 — Closeout routing" in text
    assert "/merging-standards `<branch_state_closeout>`" in text
    assert "safe cleanup policy" in text
    assert "When this skill is user-invoked directly" in text
    assert "Invoke `/handoff` plain" in text
    assert "**Remaining Branches**" in text
    assert "Do not emit a receipt-only response" in text
    assert "/handoff --no-session" not in text
