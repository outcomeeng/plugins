"""Conformance tests for merge-gate policy in shipped skill text."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest


REPO_ROOT: Final = Path(__file__).resolve().parents[4]
STANDARDIZING_MERGING_SKILLS: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "merging-standards"
    / "SKILL.md",
    REPO_ROOT
    / "dist"
    / "claude"
    / "spec-tree"
    / "skills"
    / "merging-standards"
    / "SKILL.md",
    REPO_ROOT
    / "dist"
    / "codex"
    / "spec-tree"
    / "skills"
    / "merging-standards"
    / "SKILL.md",
)


@pytest.mark.parametrize("skill_path", STANDARDIZING_MERGING_SKILLS)
def test_shipped_skill_declares_production_readiness_mapping(
    skill_path: Path,
) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "`PRODUCTION_READINESS`" in text
    assert "not production-relevant" in text
    assert "operator has explicitly approved" in text
    assert "no recognition mechanism" in text
    assert "AWAIT_APPROVAL" in text


@pytest.mark.parametrize("skill_path", STANDARDIZING_MERGING_SKILLS)
def test_shipped_skill_declares_terminal_green_mapping(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "**terminal-green.**" in text
    assert "`status == COMPLETED`" in text
    assert "`conclusion == SUCCESS`" in text
    assert "`state == SUCCESS`" in text
    assert "`SKIPPED`" in text
    assert "`NEUTRAL`" in text
    assert "`TIMED_OUT`" in text
    assert "absent from the rollup" in text


@pytest.mark.parametrize("skill_path", STANDARDIZING_MERGING_SKILLS)
def test_shipped_skill_declares_auditor_verdict_handling(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")

    assert "`REJECTED` overall verdict" in text
    assert "`UNKNOWN` overall verdict" in text
    assert "`FAIL` or `UNKNOWN` row" in text
    assert "`REJECT` finding" in text
    assert "in-slice unresolved work" in text
    assert "fix the bug or resolve the audit uncertainty" in text
