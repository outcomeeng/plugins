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
    assert "`/handoff` computes the branch-state closeout record" in text
    assert "using its own closeout tool surface" in text
    assert "safe cleanup policy" in text
    assert "Invoke `/handoff` plain" in text
    assert "**Remaining Branches**" in text
    assert "operator-useful closeout" in text
    assert "Do not emit an independent merge receipt" in text
    assert "/handoff --no-session" not in text


@pytest.mark.parametrize("skill_path", MERGE_SKILL_FILES)
def test_direct_push_closeout_has_required_git_permissions(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    required_tools = (
        "Bash(git push:*)",
        "Bash(git symbolic-ref:*)",
        "Bash(git rev-parse:*)",
        "Bash(git diff:*)",
    )
    for tool in required_tools:
        assert tool in text

    forbidden_tools = (
        "Bash(git fetch:*)",
        "Bash(git switch:*)",
        "Bash(git worktree list:*)",
        "Bash(git show-ref:*)",
        "Bash(git ls-remote:*)",
        "Bash(git merge-base:*)",
        "Bash(git cherry:*)",
    )
    for tool in forbidden_tools:
        assert tool not in text

    assert "Bash(git worktree:*)" not in text
