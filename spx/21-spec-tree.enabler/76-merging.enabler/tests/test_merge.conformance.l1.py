"""Conformance tests for the /merge dispatcher's packaging contract.

Asserts the structural Conformance clause in ``../merging.md``: the /merge
dispatcher ships as a portable, user-invocable Agent Skill (a `SKILL.md`, not a
command), so it activates on both runtimes.

Per ``spx/13-plugin-and-runtime-conventions.adr.md`` a skill, not a command, is
the cross-runtime vehicle, and `user-invocable: false` would hide a user-facing
dispatcher from the menu.

These are L1 conformance checks over the real source files — packaging facts
(file presence/absence, frontmatter flags), never prose-grep proxies for
behavior. /merge's transport-selection and delegation behavior is a semantic
constraint verified by audit, not asserted here by matching strings in the body.
"""

from __future__ import annotations

import re
from pathlib import Path


def _marketplace_root() -> Path:
    """Walk up from this test to the marketplace root marker."""
    for parent in Path(__file__).resolve().parents:
        if (parent / ".claude-plugin" / "marketplace.json").is_file():
            return parent
    raise RuntimeError("marketplace root (.claude-plugin/marketplace.json) not found")


MARKETPLACE_ROOT = _marketplace_root()
SPEC_TREE_PLUGIN = MARKETPLACE_ROOT / "src" / "plugins" / "spec-tree"
MERGE_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "merge" / "SKILL.md"
MERGE_COMMAND_FILE = SPEC_TREE_PLUGIN / "commands" / "merge.md"


def _frontmatter(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match is not None, (
        "the /merge SKILL.md must begin with a YAML frontmatter block "
        "delimited by '---' lines"
    )
    return match.group(1)


class TestMergePackaging:
    """The /merge dispatcher is a portable, user-invocable skill, not a command."""

    def test_skill_file_exists(self) -> None:
        assert MERGE_SKILL_FILE.is_file(), (
            "the /merge dispatcher must ship as a skill at "
            f"{MERGE_SKILL_FILE.relative_to(MARKETPLACE_ROOT)}"
        )

    def test_is_a_skill_not_a_command(self) -> None:
        # Slash commands are Claude Code-only; a skill activates on both runtimes.
        assert not MERGE_COMMAND_FILE.exists(), (
            "the /merge dispatcher must be a skill, not a command; "
            f"{MERGE_COMMAND_FILE.relative_to(MARKETPLACE_ROOT)} must not exist"
        )

    def test_skill_is_user_invocable(self) -> None:
        frontmatter = _frontmatter(MERGE_SKILL_FILE.read_text(encoding="utf-8"))
        assert not re.search(
            r"^user-invocable:\s*false\b", frontmatter, re.MULTILINE
        ), "the /merge dispatcher must be user-invocable (no 'user-invocable: false')"
