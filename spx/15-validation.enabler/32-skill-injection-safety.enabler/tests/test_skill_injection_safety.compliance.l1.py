"""Compliance evidence: the injection-fence token is forbidden in any SKILL.md.

Spec: spx/15-validation.enabler/32-skill-injection-safety.enabler/skill-injection-safety.md
Rule: NEVER a committed SKILL.md contains a loader-executable command-injection fence
token. The case is the rule itself — a violating SKILL.md exercised against the validator,
plus a compliant counterpart so enforcement is not trivially always-failing.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.skill_injection_safety import INJECTION_FENCE_TOKEN, main


def test_violating_skill_is_rejected(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text(f"# Heading\n\n{INJECTION_FENCE_TOKEN}\n", encoding="utf-8")
    assert main([str(skill)]) != 0


def test_compliant_skill_is_accepted(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("# Heading\n\nno injection fence here\n", encoding="utf-8")
    assert main([str(skill)]) == 0
