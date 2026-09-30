"""Compliance evidence: forbidden injections in any SKILL.md.

Spec: spx/15-validation.enabler/32-skill-injection-safety.enabler/skill-injection-safety.md
Rules: NEVER a committed SKILL.md contains a loader-executable command-injection fence
token; NEVER a committed SKILL.md carries an execution-time injection that reads
sister-skill content. Each case is the rule itself — a violating SKILL.md exercised
against the validator, plus a compliant counterpart so enforcement is not trivially
always-failing.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.skill_injection_safety import (
    INJECTION_FENCE_TOKEN,
    INLINE_INJECTION_END,
    INLINE_INJECTION_START,
    PARENT_DIRECTORY_SEGMENT,
    SKILL_FILENAME,
    main,
)


def test_violating_skill_is_rejected(tmp_path: Path) -> None:
    skill = tmp_path / SKILL_FILENAME
    skill.write_text(f"# Heading\n\n{INJECTION_FENCE_TOKEN}\n", encoding="utf-8")
    assert main([str(skill)]) != 0


def test_compliant_skill_is_accepted(tmp_path: Path) -> None:
    skill = tmp_path / SKILL_FILENAME
    skill.write_text("# Heading\n\nno injection fence here\n", encoding="utf-8")
    assert main([str(skill)]) == 0


def test_sister_skill_injection_is_rejected(tmp_path: Path) -> None:
    command = f"cat {PARENT_DIRECTORY_SEGMENT}sibling/{SKILL_FILENAME}"
    skill = tmp_path / SKILL_FILENAME
    skill.write_text(
        f"# Heading\n\n{INLINE_INJECTION_START}{command}{INLINE_INJECTION_END}\n",
        encoding="utf-8",
    )
    assert main([str(skill)]) != 0


def test_own_skill_injection_is_accepted(tmp_path: Path) -> None:
    skill = tmp_path / SKILL_FILENAME
    skill.write_text(
        f"# Heading\n\n{INLINE_INJECTION_START}git status{INLINE_INJECTION_END}\n",
        encoding="utf-8",
    )
    assert main([str(skill)]) == 0
