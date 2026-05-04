"""
Scenario tests for 76-sessions.enabler (sessions.md assertions 1–5).

All tests run at L1 using real subprocesses, real filesystem I/O in pytest
tmp_path directories, and no test doubles.

Assertions covered:
  1. spx session handoff creates a file in .spx/sessions/todo/ with the
     provided content (including the active node path).
  2. spx session pickup moves that file from todo/ to doing/.
  3. Escape hatch content (PLAN.md / ISSUES.md excerpts) in the handoff
     payload survives into the session file unchanged.
  4. post-compact writes the compact summary atomically to
     .spx/sessions/tmp/compact-<session_id>.md.
  5. session-resume claims that file, emits <SPEC-TREE_RESUMED> with the
     active node (when present), emits /spec-tree:understanding and
     /spec-tree:contextualizing (conditional on <SPEC_TREE_FOUNDATION>),
     and removes the claimed file afterward.
"""

import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
BIN_DIR = REPO_ROOT / "plugins" / "spec-tree" / "bin"
POST_COMPACT = BIN_DIR / "post-compact"
SESSION_RESUME = BIN_DIR / "session-resume"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handoff(sessions_dir: Path, content: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["spx", "session", "handoff", "--sessions-dir", str(sessions_dir)],
        input=content,
        capture_output=True,
        text=True,
    )


def _pickup(sessions_dir: Path, session_id: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["spx", "session", "pickup", "--sessions-dir", str(sessions_dir), session_id],
        capture_output=True,
        text=True,
    )


def _post_compact(
    project_dir: Path, session_id: str, summary: str
) -> subprocess.CompletedProcess:
    payload = json.dumps(
        {"session_id": session_id, "compact_summary": summary, "cwd": str(project_dir)}
    )
    return subprocess.run(
        ["bash", str(POST_COMPACT)],
        input=payload,
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)},
    )


def _session_resume(
    project_dir: Path, new_session_id: str
) -> subprocess.CompletedProcess:
    payload = json.dumps({"session_id": new_session_id, "cwd": str(project_dir)})
    return subprocess.run(
        ["bash", str(SESSION_RESUME)],
        input=payload,
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)},
    )


def _parse_handoff_id(stdout: str) -> str:
    m = re.search(r"<HANDOFF_ID>(.+?)</HANDOFF_ID>", stdout)
    assert m, f"no <HANDOFF_ID> in: {stdout}"
    return m.group(1)


def _write_compact_file(project_dir: Path, session_id: str, content: str) -> Path:
    tmp_dir = project_dir / ".spx" / "sessions" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    f = tmp_dir / f"compact-{session_id}.md"
    f.write_text(content)
    return f


# ---------------------------------------------------------------------------
# Assertion 1 — handoff creates a session file in todo/ with node path
# ---------------------------------------------------------------------------


class TestHandoffCreatesTodoSession:
    def test_file_appears_in_todo(self, tmp_path):
        result = _handoff(
            tmp_path / "sessions",
            textwrap.dedent("""\
                ---
                priority: medium
                tags: [sessions-test]
                ---
                # Test session

                Active node: spx/21-spec-tree.enabler/76-sessions.enabler/
            """),
        )
        assert result.returncode == 0, result.stderr
        todo_files = list((tmp_path / "sessions" / "todo").glob("*.md"))
        assert len(todo_files) == 1

    def test_session_file_contains_active_node_path(self, tmp_path):
        active_node = "spx/21-spec-tree.enabler/76-sessions.enabler/"
        result = _handoff(
            tmp_path / "sessions",
            textwrap.dedent(f"""\
                ---
                priority: medium
                ---
                Active node: {active_node}
            """),
        )
        assert result.returncode == 0, result.stderr
        todo_files = list((tmp_path / "sessions" / "todo").glob("*.md"))
        assert todo_files
        assert active_node in todo_files[0].read_text()


# ---------------------------------------------------------------------------
# Assertion 2 — pickup moves session from todo/ to doing/
# ---------------------------------------------------------------------------


class TestPickupMovesToDoing:
    def test_pickup_removes_from_todo(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        result = _handoff(sessions_dir, "---\npriority: medium\n---\n# Session\n")
        assert result.returncode == 0, result.stderr
        session_id = _parse_handoff_id(result.stdout)

        _pickup(sessions_dir, session_id)

        assert not (sessions_dir / "todo" / f"{session_id}.md").exists()

    def test_pickup_places_in_doing(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        result = _handoff(sessions_dir, "---\npriority: medium\n---\n# Session\n")
        assert result.returncode == 0, result.stderr
        session_id = _parse_handoff_id(result.stdout)

        pickup_result = _pickup(sessions_dir, session_id)
        assert pickup_result.returncode == 0, pickup_result.stderr

        assert (sessions_dir / "doing" / f"{session_id}.md").exists()

    def test_pickup_emits_session_content_to_stdout(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        body = "Active node: spx/21-spec-tree.enabler/76-sessions.enabler/"
        result = _handoff(sessions_dir, f"---\npriority: medium\n---\n{body}\n")
        assert result.returncode == 0, result.stderr
        session_id = _parse_handoff_id(result.stdout)

        pickup_result = _pickup(sessions_dir, session_id)
        assert pickup_result.returncode == 0, pickup_result.stderr
        assert body in pickup_result.stdout


# ---------------------------------------------------------------------------
# Assertion 3 — escape hatch content (PLAN.md / ISSUES.md) in session file
# ---------------------------------------------------------------------------


class TestEscapeHatchContentInSession:
    def test_plan_md_excerpt_preserved(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        plan_text = "## PLAN: Wire the spx CLI half of the session-scope accumulator"
        result = _handoff(
            sessions_dir,
            textwrap.dedent(f"""\
                ---
                priority: medium
                ---
                # Session with PLAN.md

                {plan_text}
            """),
        )
        assert result.returncode == 0, result.stderr
        todo_files = list((sessions_dir / "todo").glob("*.md"))
        assert todo_files
        assert plan_text in todo_files[0].read_text()

    def test_issues_md_excerpt_preserved(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        issues_text = "## 12. Repo-wide evidence links still contain legacy test naming"
        result = _handoff(
            sessions_dir,
            textwrap.dedent(f"""\
                ---
                priority: medium
                ---
                # Session with ISSUES.md

                {issues_text}
            """),
        )
        assert result.returncode == 0, result.stderr
        todo_files = list((sessions_dir / "todo").glob("*.md"))
        assert todo_files
        assert issues_text in todo_files[0].read_text()


# ---------------------------------------------------------------------------
# Assertion 4 — post-compact persists compact summary atomically
# ---------------------------------------------------------------------------


class TestPostCompactPersistsSummary:
    def test_compact_file_created_in_tmp(self, tmp_path):
        summary = "1. Primary Request: Testing post-compact behavior."
        result = _post_compact(tmp_path, "sess-aaa", summary)
        assert result.returncode == 0, result.stderr
        out = tmp_path / ".spx" / "sessions" / "tmp" / "compact-sess-aaa.md"
        assert out.exists()
        assert summary in out.read_text()

    def test_write_is_atomic_no_tmp_remnants(self, tmp_path):
        summary = "Atomic write test."
        _post_compact(tmp_path, "sess-bbb", summary)
        tmp_remnants = list(
            (tmp_path / ".spx" / "sessions" / "tmp").glob("compact-sess-bbb.md.tmp.*")
        )
        assert not tmp_remnants

    def test_missing_compact_summary_exits_cleanly(self, tmp_path):
        payload = json.dumps({"session_id": "no-summary", "cwd": str(tmp_path)})
        result = subprocess.run(
            ["bash", str(POST_COMPACT)],
            input=payload,
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)},
        )
        assert result.returncode == 0
        out = tmp_path / ".spx" / "sessions" / "tmp" / "compact-no-summary.md"
        assert not out.exists()


# ---------------------------------------------------------------------------
# Assertion 5 — session-resume conditional re-anchoring and cleanup
# ---------------------------------------------------------------------------

_COMPACT_WITH_FOUNDATION = textwrap.dedent("""\
    1. Primary Request: Testing session-resume conditional behavior.

    ### Pre-compact markers

    <SPEC_TREE_FOUNDATION>
    <SPEC_TREE_CONTEXT target="spx/21-spec-tree.enabler/76-sessions.enabler/">
    <SESSION_SCOPE ids="2026-05-04_11-08-33">

    ### Active spec-tree node

    spx/21-spec-tree.enabler/76-sessions.enabler/
""")

_COMPACT_WITHOUT_FOUNDATION = textwrap.dedent("""\
    1. Primary Request: Non-spec-tree work.

    ### Pre-compact markers

    none

    ### Active spec-tree node

    none
""")


class TestSessionResumeConditionalReanchoring:
    def test_foundation_present_emits_reanchoring_directive(self, tmp_path):
        _write_compact_file(tmp_path, "old-111", _COMPACT_WITH_FOUNDATION)
        result = _session_resume(tmp_path, "new-222")
        assert result.returncode == 0, result.stderr
        assert "/spec-tree:understanding" in result.stdout
        assert "/spec-tree:contextualizing" in result.stdout

    def test_foundation_absent_omits_reanchoring_directive(self, tmp_path):
        _write_compact_file(tmp_path, "old-333", _COMPACT_WITHOUT_FOUNDATION)
        result = _session_resume(tmp_path, "new-444")
        assert result.returncode == 0, result.stderr
        assert "/spec-tree:understanding" not in result.stdout
        assert "/spec-tree:contextualizing" not in result.stdout

    def test_resumed_marker_always_emitted(self, tmp_path):
        _write_compact_file(tmp_path, "old-555", _COMPACT_WITHOUT_FOUNDATION)
        result = _session_resume(tmp_path, "new-666")
        assert "<SPEC-TREE_RESUMED" in result.stdout

    def test_active_node_attribute_present_when_foundation(self, tmp_path):
        _write_compact_file(tmp_path, "old-556", _COMPACT_WITH_FOUNDATION)
        result = _session_resume(tmp_path, "new-667")
        assert (
            'active-node="spx/21-spec-tree.enabler/76-sessions.enabler/"'
            in result.stdout
        )

    def test_compact_file_removed_after_claim(self, tmp_path):
        _write_compact_file(tmp_path, "old-777", _COMPACT_WITH_FOUNDATION)
        _session_resume(tmp_path, "new-888")
        remaining = list(
            (tmp_path / ".spx" / "sessions" / "tmp").glob("compact-old-777*")
        )
        assert not remaining, f"unexpected files after claim: {remaining}"

    def test_no_compact_file_produces_empty_output(self, tmp_path):
        (tmp_path / ".spx" / "sessions" / "tmp").mkdir(parents=True, exist_ok=True)
        result = _session_resume(tmp_path, "new-aaa")
        assert result.returncode == 0
        assert result.stdout == ""
