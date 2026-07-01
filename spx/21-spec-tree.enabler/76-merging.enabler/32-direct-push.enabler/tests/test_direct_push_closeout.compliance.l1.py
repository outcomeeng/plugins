"""Compliance tests for direct-push closeout."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest


REPO_ROOT: Final = Path(__file__).resolve().parents[5]
SPEC_TREE_PLUGIN: Final = REPO_ROOT / "src" / "plugins" / "spec-tree"
CLAUDE_PLUGIN: Final = REPO_ROOT / "dist" / "claude" / "spec-tree"
CODEX_PLUGIN: Final = REPO_ROOT / "dist" / "codex" / "spec-tree"

MERGE_SKILL_FILES: Final = (
    SPEC_TREE_PLUGIN / "skills" / "merge" / "SKILL.md",
    CLAUDE_PLUGIN / "skills" / "merge" / "SKILL.md",
    CODEX_PLUGIN / "skills" / "merge" / "SKILL.md",
)


@pytest.mark.parametrize("skill_path", MERGE_SKILL_FILES)
def test_direct_push_post_merge_closeout_uses_handoff(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "Step D5 — Post-merge, then continue or close" in text
    assert "/merging-standards `<branch_state_closeout>`" in text
    assert "release-source worktree state" in text
    assert "safe cleanup policy" in text
    assert "Invoke `/handoff` plain" in text
    assert "**Remaining Branches**" in text
    assert "operator-useful closeout" in text
    assert "Do not emit an independent merge receipt" in text
    assert "/handoff --no-session" not in text
