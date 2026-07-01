"""Compliance tests for the handoff closure policy.

These tests cover the prompt-level contract in ``../sessions.md``. The
behavior under test is the shipped handoff skill text, so the evidence reads the
authored source files directly and rejects instructions that convert
actionable coordination notes into additional queued sessions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


REPO_ROOT: Final = Path(__file__).resolve().parents[4]
HANDOFF_DIR: Final = REPO_ROOT / "src/plugins/spec-tree/skills/handoff"
CLAUDE_HANDOFF_DIR: Final = REPO_ROOT / "dist/claude/spec-tree/skills/handoff"
CODEX_HANDOFF_DIR: Final = REPO_ROOT / "dist/codex/spec-tree/skills/handoff"
SESSIONS_SPEC: Final = (
    REPO_ROOT / "spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md"
)


def _read(relative_path: str) -> str:
    return (HANDOFF_DIR / relative_path).read_text()


def _read_handoff_surface(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text()


def test_coordination_notes_block_closure_while_claude_can_act() -> None:
    skill = _read("SKILL.md")
    reflect = _read("workflows/02-reflect.md")

    assert "Coordination notes block closure while Claude can act" in skill
    assert "A session file is not a disposal path for coordination notes" in skill
    assert "return to the governing implementation workflow" in reflect
    assert "never treat it as session-file-only context" in reflect

    forbidden_claims = (
        "Create a session file unless absolutely no unresolved continuation remains.",
        "Unfinished work needs a session file, even when the remaining steps are written",
        "both require a session file",
        "create the canonical continuation by default",
    )
    combined = "\n".join(
        [
            skill,
            reflect,
            _read("workflows/03-propose.md"),
            _read("workflows/04-execute.md"),
        ]
    )
    for claim in forbidden_claims:
        assert claim not in combined


def test_handoff_searches_existing_sessions_before_new_continuation() -> None:
    skill = _read("SKILL.md")
    reflect = _read("workflows/02-reflect.md")
    execute = _read("workflows/04-execute.md")

    assert "Search before adding any continuation" in skill
    assert "spx session list --status todo --json" in reflect
    assert "spx session list --status doing --json" in reflect
    assert (
        '<EXISTING_SESSION_RECONCILIATION status="none|same-owner-continuation|existing-owner|ambiguous">'
        in reflect
    )
    assert '`status="existing-owner"` blocks Path C' in reflect
    assert "If the marker is missing, STOP and return to workflow 02" in execute
    assert "Path C is forbidden" in execute

    required_comparison_fields = ("specs", "files", "goal", "next_step")
    for field in required_comparison_fields:
        assert field in skill
        assert field in reflect


def test_existing_owner_allows_no_duplicate_session() -> None:
    skill = _read("SKILL.md")
    execute = _read("workflows/04-execute.md")

    assert '<EXISTING_SESSION_RECONCILIATION status="existing-owner">' in skill
    assert "another session already owns the only remaining continuation" in skill
    assert (
        'status="existing-owner"` confirms another session already owns the only remaining continuation'
        in execute
    )
    assert "Path C is forbidden" in execute
    assert "no handoff file is created" in execute
    assert "After archiving, confirm through `<confirm>`" in execute
    assert (
        "Closed without continuation. All approved items persisted and committed."
        not in execute
    )


def test_transport_closeout_invokes_handoff_plain() -> None:
    skill = _read("SKILL.md")
    sessions_spec = SESSIONS_SPEC.read_text()

    assert "merge lifecycle closeout" in skill
    assert "Merge lifecycle closeout uses this skill" in skill
    assert "transport's post-merge closure invokes `/handoff` plain" in sessions_spec
    assert "automation passes `--no-session`" in sessions_spec
    assert "without receiving `--no-session`" in skill


def test_plain_handoff_omits_session_when_no_continuation() -> None:
    skill = _read("SKILL.md")
    execute = _read("workflows/04-execute.md")
    sessions_spec = SESSIONS_SPEC.read_text()

    assert (
        "when `/handoff` runs plain and no unresolved continuation remains"
        in sessions_spec
    )
    assert (
        "merge lifecycle automation does not need `--no-session` to reach zero-handoff closeout"
        in sessions_spec
    )
    assert (
        "When the continuation signal is `absent`, omit the session file even for a plain merge lifecycle invocation"
        in skill
    )
    assert (
        "Plain merge lifecycle invocations use this path when the signal is `absent`; `--no-session` is not required"
        in execute
    )
    assert (
        "Workflow 04 persists all work and coordination notes and, unless `--no-session`, writes the session file"
        not in skill
    )
    assert "**Path A — `--no-session` (zero handoffs)**" not in execute


def test_handoff_allows_branch_state_closeout_observations() -> None:
    skill = _read("SKILL.md")

    required_tools = (
        "Bash(spx session release:*)",
        "Bash(git rev-parse:*)",
        "Bash(git worktree list:*)",
        "Bash(git show-ref:*)",
        "Bash(git ls-remote:*)",
        "Bash(git merge-base:*)",
        "Bash(git cherry:*)",
    )
    for tool in required_tools:
        assert tool in skill


def test_handoff_reconciles_out_of_scope_wrong_notes() -> None:
    skill = _read("SKILL.md")
    reflect = _read("workflows/02-reflect.md")

    assert "clearly wrong note outside the original scope" in skill
    assert "clearly wrong coordination note outside the original scope" in reflect
    assert "fix safe local corrections now" in reflect
    assert "ownership, scope, cost, or risk changes" in reflect


def test_handoff_final_confirmation_is_operator_useful() -> None:
    source_execute = _read("workflows/04-execute.md")
    claude_execute = _read_handoff_surface(
        CLAUDE_HANDOFF_DIR, "workflows/04-execute.md"
    )
    codex_execute = _read_handoff_surface(CODEX_HANDOFF_DIR, "workflows/04-execute.md")
    sessions_spec = SESSIONS_SPEC.read_text()
    surfaces = (source_execute, claude_execute, codex_execute)

    required_summary_fields = (
        "Product outcome",
        "Changed surface",
        "Human-readable change summary",
        "Verification evidence",
        "Inspection surface",
        "Delivered state",
        "Remaining work",
    )
    for execute in surfaces:
        product_outcome_index = execute.index("Product outcome")
        changed_surface_index = execute.index("Changed surface")
        human_summary_index = execute.index("Human-readable change summary")
        verification_index = execute.index("Verification evidence")
        inspection_index = execute.index("Inspection surface")
        delivered_state_index = execute.index("Delivered state")
        remaining_work_index = execute.index("Remaining work")
        mechanics_index = execute.index(
            "Put session mechanics only after the product summary"
        )
        canonical_continuation_index = execute.index("Canonical continuation")

        assert product_outcome_index < changed_surface_index
        assert changed_surface_index < human_summary_index
        assert human_summary_index < verification_index
        assert verification_index < inspection_index
        assert inspection_index < delivered_state_index
        assert delivered_state_index < remaining_work_index
        assert remaining_work_index < mechanics_index
        assert mechanics_index < canonical_continuation_index

        for field in required_summary_fields:
            assert field in execute

        assert "Remaining Branches" in execute
        assert "**Deleted locally**" in execute
        assert "**Deleted remotely**" in execute
        assert "**Retained, with reason**" in execute
        assert "**Needs operator decision, with exact evidence**" in execute
        assert (
            "Default-branch merge closeout includes the branch-state closeout record fields"
            in execute
        )
        assert "Merge lifecycle final output includes `Remaining Branches`" in execute
        assert "git cherry -v --abbrev=40" in execute
        assert "Never delete a branch checked out in another live worktree" in execute
        assert "merge receipt" in execute
        assert "PR URL" in execute
        assert "running URL" in execute
        assert "session mechanics only after the product summary" in execute
        assert (
            "Include whichever surfaces apply; omit unavailable surfaces rather than inventing one."
            in execute
        )
        assert "State:\n" not in execute[:product_outcome_index]

    for spec_field in (
        "product outcome",
        "changed surface",
        "human-readable change summary",
        "verification evidence",
        "inspection surface when available",
        "delivered state",
        "remaining work when any exists",
        "compact Remaining Branches section",
    ):
        assert spec_field in sessions_spec
    assert "operator-useful terms before mechanics" in sessions_spec

    weak_receipts = (
        "State:\n",
        'State: "PR merged"',
        'State: "Archived"',
        "open with branch cleanup",
    )
    for execute in surfaces:
        for receipt in weak_receipts:
            assert receipt not in execute
