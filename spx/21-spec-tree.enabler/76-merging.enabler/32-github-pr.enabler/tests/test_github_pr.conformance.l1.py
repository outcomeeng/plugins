"""Conformance tests for the GitHub-PR transport's /manage-github-pr packaging contract.

Asserts the structural Conformance clauses in ``../manage-github-pr.md``: the
/manage-github-pr orchestration ships as a portable Agent Skill (not a command) and is
user-invocable; no /open-pr command wrapper exists; /open-pr stays internal
(user-invocable: false); and /manage-pr stays user-invocable because it is the
direct open-PR management entry point.

Per ``spx/13-plugin-and-runtime-conventions.adr.md`` a skill, not a command, is
the cross-runtime vehicle.

These are L1 conformance checks over the real source files — packaging facts
(file presence/absence, frontmatter flags), never prose-grep proxies for
behavior. The transport-selection behavior (/manage-github-pr is selected by /merge and
defers transport selection to it) is a semantic constraint verified by audit
(and, in a follow-up, eval), not asserted here by matching strings in a skill
body.
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
GITHUB_PR_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "manage-github-pr" / "SKILL.md"
GITHUB_PR_COMMAND_FILE = SPEC_TREE_PLUGIN / "commands" / "manage-github-pr.md"
OPEN_PR_COMMAND_FILE = SPEC_TREE_PLUGIN / "commands" / "open-pr.md"
OPENING_PR_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "open-pr" / "SKILL.md"
MANAGING_PR_SKILL_FILE = SPEC_TREE_PLUGIN / "skills" / "manage-pr" / "SKILL.md"


def _frontmatter(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match is not None, (
        "the /manage-github-pr SKILL.md must begin with a YAML frontmatter block "
        "delimited by '---' lines"
    )
    return match.group(1)


class TestGithubPrPackaging:
    """The /manage-github-pr orchestration is a portable, user-invocable skill."""

    def test_skill_file_exists(self) -> None:
        assert GITHUB_PR_SKILL_FILE.is_file(), (
            "the /manage-github-pr orchestration must ship as a skill at "
            f"{GITHUB_PR_SKILL_FILE.relative_to(MARKETPLACE_ROOT)}"
        )

    def test_is_a_skill_not_a_command(self) -> None:
        # Slash commands are Claude Code-only; a skill activates on both runtimes.
        assert not GITHUB_PR_COMMAND_FILE.exists(), (
            "the /manage-github-pr orchestration must be a skill, not a command; "
            f"{GITHUB_PR_COMMAND_FILE.relative_to(MARKETPLACE_ROOT)} must not exist"
        )

    def test_skill_is_user_invocable(self) -> None:
        frontmatter = _frontmatter(GITHUB_PR_SKILL_FILE.read_text(encoding="utf-8"))
        assert not re.search(
            r"^user-invocable:\s*false\b", frontmatter, re.MULTILINE
        ), "the /manage-github-pr skill must be user-invocable (no 'user-invocable: false')"


class TestProtocolPackagingConstraints:
    """/open-pr stays internal; /manage-pr is user-invocable; no /open-pr wrapper."""

    def test_open_pr_command_wrapper_is_absent(self) -> None:
        assert not OPEN_PR_COMMAND_FILE.exists(), (
            "direct /open-pr command wrapper must not exist; "
            "route shipping through /manage-github-pr"
        )

    def test_opening_pr_protocol_is_internal(self) -> None:
        frontmatter = _frontmatter(OPENING_PR_SKILL_FILE.read_text(encoding="utf-8"))
        assert re.search(r"^user-invocable:\s*false\b", frontmatter, re.MULTILINE), (
            "/open-pr internal protocol must be 'user-invocable: false'"
        )

    def test_managing_pr_protocol_is_user_invocable(self) -> None:
        # /manage-pr is the direct open-PR management entry point, so it stays
        # user-invocable rather than hidden behind /manage-github-pr only.
        frontmatter = _frontmatter(MANAGING_PR_SKILL_FILE.read_text(encoding="utf-8"))
        assert not re.search(
            r"^user-invocable:\s*false\b", frontmatter, re.MULTILINE
        ), (
            "/manage-pr must be user-invocable (no 'user-invocable: false') because it is the direct open-PR management entry point"
        )
