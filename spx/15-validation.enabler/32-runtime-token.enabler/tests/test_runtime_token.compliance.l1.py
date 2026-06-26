"""Compliance evidence: the runtime-token validator's enforcement contract.

Spec: spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md

The validator never passes a raw runtime-divergent name in a non-ignored file, derives
its forbidden-name set from the guard-enforced kinds (tool, field, file) of the
build's runtime-token registry while excluding the review-only term kind, and enforces
every file under src/plugins/ by default — a file not on the ignore-list is checked
without opt-in.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution.build import RuntimeTokenKind
from outcomeeng.validation._steps import runtime_token_files
from outcomeeng.validation.runtime_tokens import (
    RUNTIME_TOKEN_IGNORE,
    compile_forbidden_pattern,
    find_raw_tokens,
    forbidden_names,
    is_ignored,
    scan_file,
    scan_paths,
)

# The names the live registry's guard-enforced kinds (tool, field, file) own — the
# single source of truth the validator forbids raw. Sourced through the same
# derivation the validator uses, so the test restates no copied literal.
_FORBIDDEN_NAMES = frozenset(forbidden_names())
_REPO_ROOT = Path(__file__).resolve().parents[4]


def test_never_passes_a_raw_registry_name_in_a_non_ignored_file(tmp_path: Path) -> None:
    # A non-ignored file (tmp_path resolves outside the repo, so never ignored)
    # carrying any registry name is reported.
    for name in _FORBIDDEN_NAMES:
        probe = tmp_path / "probe.md"
        probe.write_text(f"Use {name} here.\n", encoding="utf-8")
        violations = scan_file(probe)
        assert [v.token for v in violations] == [name]


def test_forbidden_set_derives_from_the_registry() -> None:
    # Every guard-enforced name is detected; a name not in the registry is not.
    for name in _FORBIDDEN_NAMES:
        assert find_raw_tokens(f"text {name} text") == [(1, name)]
    assert find_raw_tokens("text NotARegisteredTool text") == []


def test_forbidden_set_excludes_review_only_term_kind() -> None:
    # The forbidden set is derived only from guard-enforced kinds. A controlled
    # registry mixes enforced tool, field, and file names with a review-only
    # term: the derivation keeps the first three and drops the term, whose
    # common-word concept terms a whole-token match would flag in prose.
    registry = {
        "tool": RuntimeTokenKind(
            lint_enforced=True, names={"ask_user": {"claude": "AskUserQuestion"}}
        ),
        "field": RuntimeTokenKind(
            lint_enforced=True, names={"tools_list": {"codex": "tools"}}
        ),
        "file": RuntimeTokenKind(
            lint_enforced=True, names={"root_guide": {"claude": "CLAUDE.md"}}
        ),
        "term": RuntimeTokenKind(
            lint_enforced=False, names={"research_agent": {"codex": "agent"}}
        ),
    }
    forbidden = set(forbidden_names(registry=registry))
    assert "AskUserQuestion" in forbidden  # tool kind — guard-enforced
    assert "tools" in forbidden  # field kind — guard-enforced
    assert "CLAUDE.md" in forbidden  # file kind — guard-enforced
    assert "agent" not in forbidden  # term kind — review-covered, excluded


def test_empty_forbidden_set_matches_nothing() -> None:
    # A kind can be guard-enforced yet carry no entries (field starts empty), so
    # the enforced-name set can be empty. The compiled pattern must then match
    # nothing — an empty alternation would otherwise match the empty string at
    # every position and flag every line.
    registry = {
        "field": RuntimeTokenKind(lint_enforced=True, names={}),
        "term": RuntimeTokenKind(
            lint_enforced=False, names={"research_agent": {"codex": "agent"}}
        ),
    }
    assert forbidden_names(registry=registry) == ()
    pattern = compile_forbidden_pattern(())
    assert pattern.search("AskUserQuestion request_user_input any text") is None


def test_enforced_by_default_only_ignored_files_exempt(tmp_path: Path) -> None:
    # The ignore-list is the only exemption: an entry on it is exempt, every other
    # file under the root is enforced. Inject a controlled ignore-list and root so
    # the discrimination is exercised independently of the live (empty) set.
    relative = "plugins/wip/SKILL.md"
    ignore = frozenset({relative})
    assert is_ignored(
        tmp_path / "plugins" / "wip" / "SKILL.md", ignore=ignore, repo_root=tmp_path
    )
    assert not is_ignored(
        tmp_path / "plugins" / "live" / "SKILL.md", ignore=ignore, repo_root=tmp_path
    )

    # The live exemption set covers the guide-generation node files, which define
    # file-kind names as runtime data and cannot consume a build token, plus
    # review-changes neutral citation surfaces that name both guide filenames as
    # citation targets rather than runtime-resolved guide reads.
    assert RUNTIME_TOKEN_IGNORE == frozenset(
        {
            "src/plugins/spec-tree/skills/update-spx/scripts/update_spx.py",
            "src/plugins/spec-tree/skills/update-spx/SKILL.md",
            "src/plugins/spec-tree/agents/spx-updater.md",
            "src/plugins/spec-tree/skills/understand/templates/spx-claude.md",
            "src/plugins/spec-tree/skills/review-changes/references/review-prompt.md",
            "src/plugins/spec-tree/skills/review-changes/scripts/review_result.py",
        }
    )
    assert not is_ignored(
        _REPO_ROOT
        / "src"
        / "plugins"
        / "develop"
        / "skills"
        / "create-skills"
        / "SKILL.md"
    )


def test_real_tree_scan_passes() -> None:
    # End-to-end delegation over the real authored tree: scan_paths exercises
    # scan_file -> is_ignored across exactly the files the gate step feeds the
    # validator. It returns empty because every authored file is converted to
    # tokens, save the one tracked exemption the gate skips.
    gate_files = runtime_token_files()
    assert gate_files  # the gate scans a non-empty authored set
    assert scan_paths(gate_files) == []

    # The live exemptions are the guide-generation node files and the review-changes
    # neutral citation surfaces; every other gate file is checked.
    assert RUNTIME_TOKEN_IGNORE == frozenset(
        {
            "src/plugins/spec-tree/skills/update-spx/scripts/update_spx.py",
            "src/plugins/spec-tree/skills/update-spx/SKILL.md",
            "src/plugins/spec-tree/agents/spx-updater.md",
            "src/plugins/spec-tree/skills/understand/templates/spx-claude.md",
            "src/plugins/spec-tree/skills/review-changes/references/review-prompt.md",
            "src/plugins/spec-tree/skills/review-changes/scripts/review_result.py",
        }
    )
