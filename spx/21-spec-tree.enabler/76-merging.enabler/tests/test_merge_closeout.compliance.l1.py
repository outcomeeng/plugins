"""Compliance tests for merge lifecycle closeout."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest


REPO_ROOT: Final = Path(__file__).resolve().parents[4]
SPEC_TREE_PLUGIN: Final = REPO_ROOT / "src" / "plugins" / "spec-tree"
CLAUDE_PLUGIN: Final = REPO_ROOT / "dist" / "claude" / "spec-tree"
CODEX_PLUGIN: Final = REPO_ROOT / "dist" / "codex" / "spec-tree"

MERGE_SKILL_FILES: Final = (
    SPEC_TREE_PLUGIN / "skills" / "merge" / "SKILL.md",
    CLAUDE_PLUGIN / "skills" / "merge" / "SKILL.md",
    CODEX_PLUGIN / "skills" / "merge" / "SKILL.md",
)
MERGING_STANDARDS_FILES: Final = (
    SPEC_TREE_PLUGIN / "skills" / "merging-standards" / "SKILL.md",
    CLAUDE_PLUGIN / "skills" / "merging-standards" / "SKILL.md",
    CODEX_PLUGIN / "skills" / "merging-standards" / "SKILL.md",
)


@pytest.mark.parametrize("skill_path", MERGE_SKILL_FILES)
def test_merge_lifecycle_closeout_invokes_handoff_plain(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "Invoke `/handoff` plain" in text
    assert "operator-useful closeout" in text
    assert "Do not emit an independent merge receipt" in text
    assert "never receives `--no-session`" in text
    assert "/handoff --no-session" not in text


@pytest.mark.parametrize("skill_path", MERGING_STANDARDS_FILES)
def test_shared_merge_vocabulary_declares_close_phase(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "<close_phase>" in text
    assert "`CLOSE` is the lifecycle disposition phase" in text
    assert "invoking `/handoff` plain" in text
    assert "receipt-only response" in text
    assert "without receiving `--no-session`" in text


@pytest.mark.parametrize("skill_path", MERGING_STANDARDS_FILES)
def test_shared_merge_vocabulary_declares_branch_state_closeout(
    skill_path: Path,
) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "<branch_state_closeout>" in text
    assert "PR number and merge commit SHA" in text
    assert "Whether the local branch tracks a gone upstream" in text
    assert "git cherry -v --abbrev=40" in text
    assert "Never delete a branch checked out in another live worktree" in text
    assert "Never delete a branch whose commits are neither ancestors" in text
    assert "**Deleted locally**" in text
    assert "**Deleted remotely**" in text
    assert "**Retained, with reason**" in text
    assert "**Needs operator decision, with exact evidence**" in text
