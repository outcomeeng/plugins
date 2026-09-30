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
    PARENT_DIRECTORY_SEGMENT,
    SKILL_FILENAME,
    main,
)
from outcomeeng_testing.harnesses.skill_injection_safety import (
    inline_injection,
    write_skill,
)


def test_violating_skill_is_rejected(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, body=f"# Heading\n\n{INJECTION_FENCE_TOKEN}\n")
    assert main([str(skill)]) != 0


def test_compliant_skill_is_accepted(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, body="# Heading\n\nno injection fence here\n")
    assert main([str(skill)]) == 0


def test_sister_skill_injection_is_rejected(tmp_path: Path) -> None:
    command = f"cat {PARENT_DIRECTORY_SEGMENT}sibling/{SKILL_FILENAME}"
    skill = write_skill(tmp_path, body=f"# Heading\n\n{inline_injection(command)}\n")
    assert main([str(skill)]) != 0


def test_own_skill_injection_is_accepted(tmp_path: Path) -> None:
    skill = write_skill(
        tmp_path, body=f"# Heading\n\n{inline_injection('git status')}\n"
    )
    assert main([str(skill)]) == 0
