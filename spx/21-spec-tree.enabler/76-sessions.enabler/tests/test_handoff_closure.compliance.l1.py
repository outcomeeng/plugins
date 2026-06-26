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


def _read(relative_path: str) -> str:
    return (HANDOFF_DIR / relative_path).read_text()


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
    assert "spx session list --json" in reflect
    assert '<EXISTING_SESSION_RECONCILIATION status="none|same-owner-continuation|existing-owner|ambiguous">' in reflect
    assert '`status="existing-owner"` blocks Path C' in reflect
    assert "If the marker is missing, STOP and return to workflow 02" in execute
    assert "Path C is forbidden" in execute

    required_comparison_fields = ("specs", "files", "goal", "next_step")
    for field in required_comparison_fields:
        assert field in skill
        assert field in reflect


def test_handoff_reconciles_out_of_scope_wrong_notes() -> None:
    skill = _read("SKILL.md")
    reflect = _read("workflows/02-reflect.md")

    assert "clearly wrong note outside the original scope" in skill
    assert "clearly wrong coordination note outside the original scope" in reflect
    assert "fix safe local corrections now" in reflect
    assert "ownership, scope, cost, or risk changes" in reflect
