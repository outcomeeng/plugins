"""Harness checks for handoff closeout compliance evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Final


REPO_ROOT: Final = Path(__file__).resolve().parents[2]
HANDOFF_DIR: Final = REPO_ROOT / "src/plugins/spec-tree/skills/handoff"
PICKUP_DIR: Final = REPO_ROOT / "src/plugins/spec-tree/skills/pickup"
DIST_HANDOFF_DIRS: Final = (
    REPO_ROOT / "dist/claude/spec-tree/skills/handoff",
    REPO_ROOT / "dist/codex/spec-tree/skills/handoff",
)
DIST_PICKUP_DIRS: Final = (
    REPO_ROOT / "dist/claude/spec-tree/skills/pickup",
    REPO_ROOT / "dist/codex/spec-tree/skills/pickup",
)
SESSIONS_SPEC: Final = (
    REPO_ROOT / "spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md"
)


def coordination_notes_block_closure_while_claude_can_act() -> bool:
    skill = _handoff_source("SKILL.md")
    reflect = _handoff_source("workflows/02-reflect.md")
    combined = "\n".join(
        [
            skill,
            reflect,
            _handoff_source("workflows/03-propose.md"),
            _handoff_source("workflows/04-execute.md"),
        ]
    )

    assert "Coordination notes block closure while Claude can act" in skill
    assert "A session file is not a disposal path for coordination notes" in skill
    assert "return to the governing implementation workflow" in reflect
    assert "never treat it as session-file-only context" in reflect
    for claim in (
        "Create a session file unless absolutely no unresolved continuation remains.",
        "Unfinished work needs a session file, even when the remaining steps are written",
        "both require a session file",
        "create the canonical continuation by default",
    ):
        assert claim not in combined
    return True


def handoff_searches_existing_sessions_before_new_continuation() -> bool:
    skill = _handoff_source("SKILL.md")
    reflect = _handoff_source("workflows/02-reflect.md")
    execute = _handoff_source("workflows/04-execute.md")

    assert "Search before adding any continuation" in skill
    assert "spx session list --status todo --json" in reflect
    assert "spx session list --status doing --json" in reflect
    assert (
        '<EXISTING_SESSION_RECONCILIATION status="none|same-owner-continuation|existing-owner|ambiguous">'
        in reflect
    )
    assert '`status="existing-owner"` blocks fresh-session creation' in reflect
    assert "If the marker is missing, STOP and return to workflow 02" in execute
    assert "fresh-session creation is forbidden" in execute
    for field in ("specs", "files", "goal", "next_step"):
        assert field in skill
        assert field in reflect
    return True


def existing_owner_allows_no_duplicate_session() -> bool:
    skill = _handoff_source("SKILL.md")
    execute = _handoff_source("workflows/04-execute.md")

    assert '<EXISTING_SESSION_RECONCILIATION status="existing-owner">' in skill
    assert "another session already owns the only remaining continuation" in skill
    assert (
        'status="existing-owner"` confirms another session already owns the only remaining continuation'
        in execute
    )
    assert "fresh-session creation is forbidden" in execute
    assert "no handoff file is created" in execute
    assert "After archiving, confirm through `<confirm>`" in execute
    assert (
        "Closed without continuation. All approved items persisted and committed."
        not in execute
    )
    return True


def transport_closeout_invokes_handoff_plain() -> bool:
    skill = _handoff_source("SKILL.md")
    sessions_spec = SESSIONS_SPEC.read_text()

    assert "merge lifecycle closeout" in skill
    assert "Merge lifecycle closeout uses this skill" in skill
    assert "transport's post-merge closure invokes `/handoff` plain" in sessions_spec
    assert "automation passes `--no-session`" in sessions_spec
    assert "without receiving `--no-session`" in skill
    return True


def plain_handoff_omits_session_when_no_continuation() -> bool:
    skill = _handoff_source("SKILL.md")
    execute = _handoff_source("workflows/04-execute.md")
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
    return True


def handoff_allows_branch_state_closeout_observations() -> bool:
    skill = _handoff_source("SKILL.md")

    for tool in (
        "Bash(spx session release:*)",
        "Bash(git fetch:*)",
        "Bash(git rev-parse:*)",
        "Bash(git worktree list:*)",
        "Bash(git show-ref:*)",
        "Bash(git ls-remote:*)",
        "Bash(git merge-base:*)",
        "Bash(git cherry:*)",
    ):
        assert tool in skill
    return True


def handoff_reconciles_wrong_notes() -> bool:
    skill = _handoff_source("SKILL.md")
    reflect = _handoff_source("workflows/02-reflect.md")

    assert "clearly wrong note outside the original scope" in skill
    assert "clearly wrong coordination note outside the original scope" in reflect
    assert "fix safe local corrections now" in reflect
    assert "ownership, scope, cost, or risk changes" in reflect
    return True


def handoff_final_confirmation_is_operator_useful() -> bool:
    sessions_spec = SESSIONS_SPEC.read_text()
    for execute in _handoff_surfaces("workflows/04-execute.md"):
        _assert_closeout_field_order(execute)
        _assert_closeout_surface_content(execute)
        assert "State:\n" not in execute[: execute.index("Product outcome")]

    for field in (
        "product outcome",
        "product spec when that context clarifies the result",
        "changed product surface",
        "human-readable change summary",
        "verification evidence",
        "inspection references when available",
        "delivered state",
        "remaining work when any exists",
        "compact Remaining Branches section",
        "small bug fixes and technical-debt cleanup remain describable at their natural scale",
    ):
        assert field in sessions_spec
    assert "operator-useful terms before mechanics" in sessions_spec
    return True


def pickup_proposal_and_no_node_anchor_use_portable_labels() -> bool:
    sessions_spec = SESSIONS_SPEC.read_text()
    for pickup in _pickup_surfaces("workflows/pickup.md"):
        assert "Changed product surface" in pickup
        assert "Inspection references" in pickup
        assert (
            "Branches, PRs, and session records are transport or lifecycle surfaces"
            in pickup
        )
        assert (
            "stop at the next safe checkpoint and present the delta before continuing"
            in pickup
        )
        assert "changed surface" not in pickup
        assert "Inspection surface" not in pickup

    for anchor in _handoff_surfaces("workflows/01-anchor-to-nodes.md"):
        assert "Product-level operations" in anchor
        assert (
            "Work changed operational state or product-wide guidance rather than a node-local spec."
            in anchor
        )
        assert "Plugin / methodology work" not in anchor

    assert "changed product surface" in sessions_spec
    assert "inspection references" in sessions_spec
    assert "Product-level operations" in sessions_spec
    assert "operational state or product-wide guidance" in sessions_spec
    assert "changed surface" not in sessions_spec
    assert "inspection surface" not in sessions_spec
    return True


def _handoff_source(relative_path: str) -> str:
    return (HANDOFF_DIR / relative_path).read_text()


def _handoff_surfaces(relative_path: str) -> tuple[str, ...]:
    return (_handoff_source(relative_path),) + tuple(
        (root / relative_path).read_text() for root in DIST_HANDOFF_DIRS
    )


def _pickup_surfaces(relative_path: str) -> tuple[str, ...]:
    return ((PICKUP_DIR / relative_path).read_text(),) + tuple(
        (root / relative_path).read_text() for root in DIST_PICKUP_DIRS
    )


def _assert_closeout_field_order(execute: str) -> None:
    product_outcome_index = execute.index("Product outcome")
    changed_surface_index = execute.index("Changed product surface")
    human_summary_index = execute.index("Human-readable change summary")
    verification_index = execute.index("Verification evidence")
    inspection_index = execute.index("Inspection references")
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


def _assert_closeout_surface_content(execute: str) -> None:
    for field in (
        "Product outcome",
        "Changed product surface",
        "Human-readable change summary",
        "Verification evidence",
        "Inspection references",
        "Delivered state",
        "Remaining work",
    ):
        assert field in execute

    for required in (
        "Remaining Branches",
        "**Deleted locally**",
        "**Deleted remotely**",
        "**Retained, with reason**",
        "**Needs operator decision, with exact evidence**",
        "Default-branch merge closeout includes the branch-state closeout record fields",
        "Merge lifecycle final output includes `Remaining Branches`",
        "git cherry -v --abbrev=40",
        "Never delete a branch checked out in another live worktree",
        "merge receipt",
        "PR URL",
        "running URL",
        "session mechanics only after the product summary",
        "<rejected_delivered_state_receipt>",
        "NEVER replace the product closeout with a section headed `Delivered state`",
        "Delivered state:\n- Merge commit: <full-sha>",
        "Confirmation output never uses a top-level `Delivered state` receipt",
        "Include whichever references apply; omit unavailable references rather than inventing one.",
        "Read the product spec when product intent is needed",
        "A small bug fix or technical-debt cleanup may be described plainly",
        "keeping the outcome proportional to the change",
    ):
        assert required in execute

    for receipt in (
        "State:\n",
        'State: "PR merged"',
        'State: "Archived"',
        "open with branch cleanup",
    ):
        assert receipt not in execute
