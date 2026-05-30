"""Conformance test for the /pr skill's portable-skill packaging.

Asserts the Conformance clause in ``../pr-orchestration.md``: the /pr entry
point ships as a portable Agent Skill rather than a Claude Code-only command,
so it activates on both runtimes (``/pr`` on Claude Code, ``$pr`` on Codex).

Per ``spx/13-plugin-and-runtime-conventions.adr.md``:

- A skill (``skills/pr/SKILL.md``), not a command (``commands/pr.md``), is the
  cross-runtime vehicle.
- ``$ARGUMENTS`` is the substitution token that carries the user's free-form
  instructions into the skill body.
- The skill is user-invocable (no ``user-invocable: false``).

This is an L1 conformance check: it reads the real source skill file from the
marketplace tree. No test doubles — the artifact under test is the file itself.
"""

from __future__ import annotations

import re
from pathlib import Path


def _marketplace_root() -> Path:
    """Walk up from this test to the marketplace root (the ``.claude-plugin`` marker)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / ".claude-plugin" / "marketplace.json").is_file():
            return parent
    raise RuntimeError("marketplace root (.claude-plugin/marketplace.json) not found")


MARKETPLACE_ROOT = _marketplace_root()
SPEC_TREE_PLUGIN = MARKETPLACE_ROOT / "src" / "plugins" / "spec-tree"
PR_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "pr" / "SKILL.md"
PR_COMMAND_FILE = SPEC_TREE_PLUGIN / "commands" / "pr.md"


def _frontmatter(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match is not None, (
        "the /pr SKILL.md must begin with a YAML frontmatter block "
        "delimited by '---' lines"
    )
    return match.group(1)


class TestPrSkillPackaging:
    """The /pr entry point is a portable, user-invocable skill reading $ARGUMENTS."""

    def test_skill_file_exists(self) -> None:
        assert PR_SKILL_FILE.is_file(), (
            "the /pr entry point must ship as a skill at "
            f"{PR_SKILL_FILE.relative_to(MARKETPLACE_ROOT)}"
        )

    def test_entry_point_is_a_skill_not_a_command(self) -> None:
        # Slash commands are Claude Code-only; a skill activates on both runtimes.
        assert not PR_COMMAND_FILE.exists(), (
            "the /pr entry point must be a skill, not a command — "
            f"{PR_COMMAND_FILE.relative_to(MARKETPLACE_ROOT)} must not exist"
        )

    def test_skill_is_user_invocable(self) -> None:
        frontmatter = _frontmatter(PR_SKILL_FILE.read_text(encoding="utf-8"))
        assert not re.search(
            r"^user-invocable:\s*false\b", frontmatter, re.MULTILINE
        ), "the /pr skill must be user-invocable (no 'user-invocable: false')"

    def test_skill_reads_arguments(self) -> None:
        body = PR_SKILL_FILE.read_text(encoding="utf-8")
        assert "$ARGUMENTS" in body, (
            "the /pr skill must read the user's free-form input via $ARGUMENTS"
        )
