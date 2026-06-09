"""Conformance tests for the /pr skill's portable routing contract.

Asserts the Conformance clauses in ``../pr-orchestration.md``: the /pr router
ships as a portable Agent Skill, reads free-form arguments, honors local
lifecycle routing, and owns the user-facing PR route while the concrete opening
and managing protocols stay internal.

Per ``spx/13-plugin-and-runtime-conventions.adr.md``:

- A skill (``skills/pr/SKILL.md``), not a command (``commands/pr.md``), is the
  cross-runtime vehicle.
- ``$ARGUMENTS`` is the substitution token that carries the user's free-form
  instructions into the skill body.
- The skill is user-invocable (no ``user-invocable: false``).
- ``opening-pr`` and ``managing-pr`` are loadable internal protocols.
- A direct ``open-pr`` command wrapper is absent; /pr routes PR opening.

This is an L1 conformance check: it reads the real source skill files from the
marketplace tree. No test doubles: the artifacts under test are the files
themselves.
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
PR_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "pr" / "SKILL.md"
PR_COMMAND_FILE = SPEC_TREE_PLUGIN / "commands" / "pr.md"
OPEN_PR_COMMAND_FILE = SPEC_TREE_PLUGIN / "commands" / "open-pr.md"
OPENING_PR_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "opening-pr" / "SKILL.md"
MANAGING_PR_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "managing-pr" / "SKILL.md"
UNDERSTANDING_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "understanding" / "SKILL.md"
STANDARDIZING_MERGING_SKILL_FILE = (
    SPEC_TREE_PLUGIN / "skills" / "standardizing-merging" / "SKILL.md"
)
PR_ORCHESTRATION_SPEC_FILE = Path(__file__).resolve().parents[1] / "pr-orchestration.md"


def _frontmatter(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match is not None, (
        "the /pr SKILL.md must begin with a YAML frontmatter block "
        "delimited by '---' lines"
    )
    return match.group(1)


class TestPrSkillPackaging:
    """The /pr router is a portable, user-invocable skill reading $ARGUMENTS."""

    def test_skill_file_exists(self) -> None:
        assert PR_SKILL_FILE.is_file(), (
            "the /pr router must ship as a skill at "
            f"{PR_SKILL_FILE.relative_to(MARKETPLACE_ROOT)}"
        )

    def test_router_is_a_skill_not_a_command(self) -> None:
        # Slash commands are Claude Code-only; a skill activates on both runtimes.
        assert not PR_COMMAND_FILE.exists(), (
            "the /pr router must be a skill, not a command; "
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

    def test_description_keeps_pr_trigger_narrow(self) -> None:
        frontmatter = _frontmatter(PR_SKILL_FILE.read_text(encoding="utf-8"))
        assert "ALWAYS invoke this skill when the user asks to ship" in frontmatter
        assert "open or manage a PR" in frontmatter
        forbidden = ("public" + " entry point", "one" + " entry point")
        assert all(phrase not in frontmatter for phrase in forbidden)


class TestPrLifecycleRouting:
    """The PR lifecycle routes through /pr while concrete protocols stay internal."""

    def test_open_pr_command_wrapper_is_absent(self) -> None:
        assert not OPEN_PR_COMMAND_FILE.exists(), (
            "direct /open-pr command wrapper must not exist; route shipping through /pr"
        )

    def test_opening_and_managing_pr_protocols_are_internal(self) -> None:
        opening_frontmatter = _frontmatter(
            OPENING_PR_SKILL_FILE.read_text(encoding="utf-8")
        )
        managing_frontmatter = _frontmatter(
            MANAGING_PR_SKILL_FILE.read_text(encoding="utf-8")
        )

        assert re.search(
            r"^user-invocable:\s*false\b", opening_frontmatter, re.MULTILINE
        )
        assert re.search(
            r"^user-invocable:\s*false\b", managing_frontmatter, re.MULTILINE
        )
        assert "Loaded by /pr" in opening_frontmatter
        assert "Loaded by /pr" in managing_frontmatter

    def test_pr_skill_detects_and_manages_existing_prs(self) -> None:
        body = PR_SKILL_FILE.read_text(encoding="utf-8")
        assert "**Open PR**" in body
        assert "PR number or PR URL" in body
        assert "skip directly to Step 6" in body
        assert "Skip this step in Open PR mode" in body

    def test_understanding_reads_local_merging_overlay(self) -> None:
        body = UNDERSTANDING_SKILL_FILE.read_text(encoding="utf-8")
        assert "spx/local/merging.md" in body
        assert "disabling PRs" in body
        assert "default /pr lifecycle" in body

    def test_standardizing_merging_heartbeats_reenter_pr(self) -> None:
        body = STANDARDIZING_MERGING_SKILL_FILE.read_text(encoding="utf-8")
        assert "/pr <pr-number>" in body
        assert "/managing-pr <pr-number>" not in body

    def test_spec_describes_eval_model_without_eval_links(self) -> None:
        spec = PR_ORCHESTRATION_SPEC_FILE.read_text(encoding="utf-8")
        assert "## Eval Coverage Model" in spec
        assert "Local lifecycle overlay mode" in spec
        assert "Existing open PR mode" in spec
        assert "[eval]" not in spec
