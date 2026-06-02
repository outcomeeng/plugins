"""Path access and readers for the ``32-skill-surface.enabler`` tests.

The compliance tests under
``spx/21-spec-tree.enabler/76-sessions.enabler/32-skill-surface.enabler/tests/``
read the authored ``/handoff`` and ``/pickup`` ``SKILL.md`` files and the
spec-tree commands directory to verify each skill's declared invocation
surface. The path constants and the small frontmatter/context readers live
here per ``spx/15-test-infrastructure.pdr.md`` — shared test scaffolding is
production code outside ``tests/`` and outside ``spx/``.
"""

from __future__ import annotations

import re
from pathlib import Path

# ``parents[2]`` reaches the repository root from
# ``outcomeeng_testing/harnesses/skill_surface.py`` (harnesses ->
# outcomeeng_testing -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]

_SKILLS_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "skills"
HANDOFF_SKILL = _SKILLS_DIR / "handoff" / "SKILL.md"
PICKUP_SKILL = _SKILLS_DIR / "pickup" / "SKILL.md"
COMMANDS_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "commands"

_ARGUMENT_HINT = re.compile(r'^argument-hint:\s*"([^"]*)"', re.MULTILINE)
_CONTEXT_BLOCK = re.compile(r"<context>(.*?)</context>", re.DOTALL)


def argument_hint(skill_file: Path) -> str | None:
    """Return the skill's ``argument-hint`` frontmatter value, or None if absent."""
    match = _ARGUMENT_HINT.search(skill_file.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def context_block(skill_file: Path) -> str:
    """Return the text inside the skill's ``<context>`` block, or empty string."""
    match = _CONTEXT_BLOCK.search(skill_file.read_text(encoding="utf-8"))
    return match.group(1) if match else ""
