"""Scenario test for 19-worktree-occupancy.enabler (worktree-occupancy.md scenarios).

L1: runs ``spx hooks session-start`` and ``spx hooks pre-tool-use`` as subprocesses
and asserts the observable contract boundary — the ``CLAUDE_WORKTREE_CLAIMED`` env
export and the ``PreToolUse`` decision plus model-visible repair context — parsing
the JSON document rather than scanning stdout. The internal claim sequencing is
owned and verified by ``@outcomeeng/spx``.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start`` /
``spx hooks pre-tool-use`` (``spx/EXCLUDE``).
"""

from __future__ import annotations

import json
from pathlib import Path

from outcomeeng_testing.harnesses.hooks import (
    hook_document,
    make_spec_tree,
    run_pretool_gate,
    run_session_start,
)


def _transcript(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "text": "<SPEC_TREE_FOUNDATION>\nLoaded\n</SPEC_TREE_FOUNDATION>",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _pretool_payload(
    project: Path, transcript: Path, *, session_id: str
) -> dict[str, object]:
    return {
        "session_id": session_id,
        "transcript_path": str(transcript),
        "cwd": str(project),
        "tool_name": "Read",
        "tool_input": {"file_path": "spx/thing.product.md"},
    }


def test_session_start_exports_worktree_claim_status(tmp_path: Path) -> None:
    project = tmp_path / "worktree"
    project.mkdir()
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"session_id": "sess-claim", "cwd": str(project)},
        env_file=env_file,
        project_dir=project,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8")
    assert "CLAUDE_WORKTREE_CLAIMED" in content


def test_pretool_allows_when_already_claimed(tmp_path: Path) -> None:
    project = tmp_path / "worktree"
    make_spec_tree(project)
    transcript = _transcript(tmp_path / "t.jsonl")
    result = run_pretool_gate(
        _pretool_payload(project, transcript, session_id="sess-claimed"),
        project_dir=project,
        env_overrides={"CLAUDE_WORKTREE_CLAIMED": "1"},
    )
    assert result.returncode == 0
    assert hook_document(result)["hookSpecificOutput"]["permissionDecision"] == "allow"


def test_pretool_surfaces_claim_repair_context(tmp_path: Path) -> None:
    # With no prior claim marker, the gate attempts occupancy repair and surfaces
    # model-visible context about the attempt; the tool call still proceeds.
    project = tmp_path / "worktree"
    make_spec_tree(project)
    transcript = _transcript(tmp_path / "t.jsonl")
    result = run_pretool_gate(
        _pretool_payload(project, transcript, session_id="sess-repair"),
        project_dir=project,
    )
    assert result.returncode == 0
    document = hook_document(result)
    assert "hookSpecificOutput" in document
