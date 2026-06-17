"""Scenario test for 54-load-gating.enabler (load-gating.md scenarios).

L1: runs ``spx hooks pre-tool-use`` as a subprocess against a seeded transcript and
a spec-tree project, and parses the ``PreToolUse`` permission decision plus the
``specTree`` descriptor — never by scanning stdout for substrings.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks pre-tool-use``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

import json
from pathlib import Path

from outcomeeng_testing.harnesses.hooks import hook_document, run_pretool_gate


def _spec_tree_project(tmp_path: Path) -> Path:
    project = tmp_path / "worktree"
    (project / "spx").mkdir(parents=True)
    (project / "spx" / "thing.product.md").write_text("# Product\n", encoding="utf-8")
    return project


def _transcript(path: Path, *, foundation: bool) -> Path:
    line = (
        {
            "type": "assistant",
            "text": "<SPEC_TREE_FOUNDATION>\nLoaded\n</SPEC_TREE_FOUNDATION>",
        }
        if foundation
        else {"type": "user", "text": "start"}
    )
    path.write_text(json.dumps(line) + "\n", encoding="utf-8")
    return path


def _payload(
    project: Path,
    transcript_path: Path,
    *,
    tool_name: str | None = "Read",
    file_path: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "session_id": "sess-1",
        "transcript_path": str(transcript_path),
        "cwd": str(project),
        "tool_input": {} if file_path is None else {"file_path": file_path},
    }
    if tool_name is not None:
        payload["tool_name"] = tool_name
    return payload


def _decision(result) -> dict[str, object]:
    return hook_document(result)["hookSpecificOutput"]


def test_denies_first_tool_call_without_foundation_marker(tmp_path: Path) -> None:
    project = _spec_tree_project(tmp_path)
    transcript = _transcript(tmp_path / "t.jsonl", foundation=False)
    result = run_pretool_gate(_payload(project, transcript), project_dir=project)
    assert result.returncode == 0
    decision = _decision(result)
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert hook_document(result)["specTree"]["gate"] == "foundation"


def test_allows_when_foundation_marker_present(tmp_path: Path) -> None:
    project = _spec_tree_project(tmp_path)
    transcript = _transcript(tmp_path / "t.jsonl", foundation=True)
    result = run_pretool_gate(_payload(project, transcript), project_dir=project)
    assert result.returncode == 0
    assert _decision(result)["permissionDecision"] == "allow"


def test_no_tool_name_allows(tmp_path: Path) -> None:
    project = _spec_tree_project(tmp_path)
    transcript = _transcript(tmp_path / "t.jsonl", foundation=False)
    result = run_pretool_gate(
        _payload(project, transcript, tool_name=None), project_dir=project
    )
    assert result.returncode == 0
    assert _decision(result)["permissionDecision"] == "allow"


def test_non_spec_tree_repo_allows(tmp_path: Path) -> None:
    project = tmp_path / "plain"
    project.mkdir()
    transcript = _transcript(tmp_path / "t.jsonl", foundation=False)
    result = run_pretool_gate(_payload(project, transcript), project_dir=project)
    assert result.returncode == 0
    assert _decision(result)["permissionDecision"] == "allow"
