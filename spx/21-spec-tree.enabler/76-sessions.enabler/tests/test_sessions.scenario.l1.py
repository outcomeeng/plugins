"""
Scenario tests for 76-sessions.enabler (sessions.md scenario assertions).

All tests run at L1 using the real `spx` binary, the real `post-compact` hook,
real git repositories, and real filesystem I/O in pytest tmp_path directories,
with no test doubles.

`spx session handoff` only creates a session from a git work context it accepts
(see `outcomeeng_testing.harnesses.git_context`). Every test that invokes a
session subcommand therefore runs the subprocess with `cwd` set to a
provisioned, accepted context, so the outcome does not depend on the runner's
ambient git state.

Assertions covered:
  - handoff creates a session file in .spx/sessions/todo/ carrying the active
    node path (and the rest of the handoff body).
  - pickup moves that file from todo/ to doing/ and emits its content to stdout.
  - release moves one or more sessions from doing/ back to todo/ without
    modifying content.
  - coordination-note content (PLAN.md / ISSUES.md excerpts) in the handoff
    payload survives into the session file unchanged.
  - pre-compact delegates to `spx compact store` (forwarding session id
    and transcript path); post-compact re-anchors from `spx compact
    retrieve`, prefixing <SPEC-TREE_RESUMED> with the active node and, when
    a foundation was active, instructing the agent to re-invoke
    /spec-tree:understand and /spec-tree:contextualize <node>. When the spx
    CLI returns no stash, post-compact falls back to parsing the active node and
    foundation marker out of the compact summary.
"""

import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "scripts"
POST_COMPACT = SCRIPTS_DIR / "post-compact.py"
PRE_COMPACT = SCRIPTS_DIR / "pre-compact.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handoff(
    sessions_dir: Path,
    body: str,
    *,
    cwd: Path,
    priority: str = "medium",
    goal: str = "Verify handoff behavior",
    next_step: str = "Inspect the session file",
    git_ref: str | None = None,
) -> subprocess.CompletedProcess:
    # spx session handoff takes the JSON-prefix wire format: a single JSON
    # object of caller-supplied fields on the first line, then the body bytes
    # verbatim. It is run from an spx-accepted git context (cwd) so the result
    # does not depend on the runner's ambient git state. When git_ref is set it
    # names the work branch the CLI records after verifying it exists on origin;
    # omitted, the CLI derives git_ref from the git context.
    fields: dict[str, str] = {
        "priority": priority,
        "goal": goal,
        "next_step": next_step,
    }
    if git_ref is not None:
        fields["git_ref"] = git_ref
    header = json.dumps(fields)
    return subprocess.run(
        ["spx", "session", "handoff", "--sessions-dir", str(sessions_dir)],
        input=f"{header}\n{body}",
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def _pickup(
    sessions_dir: Path, session_id: str, *, cwd: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["spx", "session", "pickup", "--sessions-dir", str(sessions_dir), session_id],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


# The hooks delegate to the spx CLI via $SPX_BIN. Tests default it to a missing
# binary so the spx call fails and the hook takes its degraded path (post-compact
# falls back to summary parsing; pre-compact no-ops); the delegation tests point
# it at a fake spx that records argv and emits canned output.
_MISSING_SPX = "/nonexistent/spx"


def _post_compact(
    project_dir: Path, session_id: str, summary: str, *, spx_bin: str = _MISSING_SPX
) -> subprocess.CompletedProcess:
    payload = json.dumps(
        {"session_id": session_id, "compact_summary": summary, "cwd": str(project_dir)}
    )
    return subprocess.run(
        ["python3", str(POST_COMPACT)],
        input=payload,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "CLAUDE_PROJECT_DIR": str(project_dir),
            "SPX_BIN": spx_bin,
        },
    )


def _pre_compact(
    project_dir: Path, session_id: str, transcript: Path, *, spx_bin: str = _MISSING_SPX
) -> subprocess.CompletedProcess:
    payload = json.dumps(
        {
            "session_id": session_id,
            "transcript_path": str(transcript),
            "cwd": str(project_dir),
        }
    )
    return subprocess.run(
        ["python3", str(PRE_COMPACT)],
        input=payload,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "CLAUDE_PROJECT_DIR": str(project_dir),
            "SPX_BIN": spx_bin,
        },
    )


def _fake_spx(bindir: Path, *, stdout: str = "", returncode: int = 0) -> Path:
    """Write a fake `spx` executable that records its argv and emits canned output.

    The recorded argv (everything after `spx`) is written to `<spx>.argv` as a
    JSON list so a test can assert how the hook invoked the CLI.
    """
    bindir.mkdir(parents=True, exist_ok=True)
    spx = bindir / "spx"
    spx.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        'pathlib.Path(__file__ + ".argv").write_text(json.dumps(sys.argv[1:]))\n'
        f"sys.stdout.write({stdout!r})\n"
        f"sys.exit({returncode})\n"
    )
    spx.chmod(0o755)
    return spx


def _parse_handoff_id(stdout: str) -> str:
    m = re.search(r"<HANDOFF_ID>(.+?)</HANDOFF_ID>", stdout)
    assert m, f"no <HANDOFF_ID> in: {stdout}"
    return m.group(1)


def _parse_session_file(stdout: str) -> Path:
    m = re.search(r"<SESSION_FILE>(.+?)</SESSION_FILE>", stdout)
    assert m, f"no <SESSION_FILE> in: {stdout}"
    return Path(m.group(1))


def _read_git_ref(session_file: Path) -> str:
    # Match the git_ref frontmatter line whether the serializer quotes the key
    # and value (current spx output) or emits them bare.
    m = re.search(
        r'^\s*"?git_ref"?:\s*"?([^"\n]+?)"?\s*$',
        session_file.read_text(),
        re.MULTILINE,
    )
    assert m, f"no git_ref in frontmatter of {session_file}"
    return m.group(1)


# ---------------------------------------------------------------------------
# Assertion 1 — handoff creates a session file in todo/ with node path
# ---------------------------------------------------------------------------


class TestHandoffCreatesTodoSession:
    def test_file_appears_in_todo(self, tmp_path):
        with accepted_git_context() as repo:
            result = _handoff(
                tmp_path / "sessions",
                textwrap.dedent("""\
                    # Test session

                    Active node: spx/21-spec-tree.enabler/76-sessions.enabler/
                """),
                cwd=repo,
                goal="Verify handoff writes a file to todo/",
                next_step="Inspect the todo directory listing",
            )
            assert result.returncode == 0, result.stderr
            todo_files = list((tmp_path / "sessions" / "todo").glob("*.md"))
            assert len(todo_files) == 1

    def test_session_file_contains_active_node_path(self, tmp_path):
        active_node = "spx/21-spec-tree.enabler/76-sessions.enabler/"
        with accepted_git_context() as repo:
            result = _handoff(
                tmp_path / "sessions",
                textwrap.dedent(f"""\
                    Active node: {active_node}
                """),
                cwd=repo,
                goal="Verify active node path survives the handoff write",
                next_step="Read the todo session file and assert path presence",
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
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                "# Session\n",
                cwd=repo,
                goal="Move a session out of todo",
                next_step="Confirm the file no longer exists in todo",
            )
            assert result.returncode == 0, result.stderr
            session_id = _parse_handoff_id(result.stdout)

            pickup_result = _pickup(sessions_dir, session_id, cwd=repo)
            assert pickup_result.returncode == 0, pickup_result.stderr

            assert not (sessions_dir / "todo" / f"{session_id}.md").exists()

    def test_pickup_places_in_doing(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                "# Session\n",
                cwd=repo,
                goal="Move a session into doing",
                next_step="Confirm the file exists in doing",
            )
            assert result.returncode == 0, result.stderr
            session_id = _parse_handoff_id(result.stdout)

            pickup_result = _pickup(sessions_dir, session_id, cwd=repo)
            assert pickup_result.returncode == 0, pickup_result.stderr

            assert (sessions_dir / "doing" / f"{session_id}.md").exists()

    def test_pickup_emits_session_content_to_stdout(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        body = "Active node: spx/21-spec-tree.enabler/76-sessions.enabler/"
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                f"{body}\n",
                cwd=repo,
                goal="Surface session content during pickup",
                next_step="Read pickup stdout and assert body presence",
            )
            assert result.returncode == 0, result.stderr
            session_id = _parse_handoff_id(result.stdout)

            pickup_result = _pickup(sessions_dir, session_id, cwd=repo)
            assert pickup_result.returncode == 0, pickup_result.stderr
            assert body in pickup_result.stdout


# ---------------------------------------------------------------------------
# Assertion 3 — release moves session from doing/ back to todo/
# ---------------------------------------------------------------------------


def _release(
    sessions_dir: Path, session_id: str, *, cwd: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["spx", "session", "release", "--sessions-dir", str(sessions_dir), session_id],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


class TestReleaseMovesToTodo:
    def test_release_removes_from_doing(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                "# Session\n",
                cwd=repo,
                goal="Test release removes from doing",
                next_step="Run release and check doing/",
            )
            assert result.returncode == 0, result.stderr
            session_id = _parse_handoff_id(result.stdout)

            pickup_result = _pickup(sessions_dir, session_id, cwd=repo)
            assert pickup_result.returncode == 0, pickup_result.stderr

            release_result = _release(sessions_dir, session_id, cwd=repo)
            assert release_result.returncode == 0, release_result.stderr
            assert not (sessions_dir / "doing" / f"{session_id}.md").exists()

    def test_release_places_back_in_todo(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                "# Session\n",
                cwd=repo,
                goal="Test release places back in todo",
                next_step="Run release and check todo/",
            )
            assert result.returncode == 0, result.stderr
            session_id = _parse_handoff_id(result.stdout)

            pickup_result = _pickup(sessions_dir, session_id, cwd=repo)
            assert pickup_result.returncode == 0, pickup_result.stderr

            release_result = _release(sessions_dir, session_id, cwd=repo)
            assert release_result.returncode == 0, release_result.stderr
            assert (sessions_dir / "todo" / f"{session_id}.md").exists()

    def test_release_does_not_modify_content(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        body = "# Session with specific content\n\nKeep this intact."
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                body,
                cwd=repo,
                goal="Test release preserves content",
                next_step="Compare content before and after release",
            )
            assert result.returncode == 0, result.stderr
            session_id = _parse_handoff_id(result.stdout)

            pickup_result = _pickup(sessions_dir, session_id, cwd=repo)
            assert pickup_result.returncode == 0, pickup_result.stderr
            content_in_doing = (sessions_dir / "doing" / f"{session_id}.md").read_text()

            release_result = _release(sessions_dir, session_id, cwd=repo)
            assert release_result.returncode == 0, release_result.stderr
            content_in_todo = (sessions_dir / "todo" / f"{session_id}.md").read_text()
            assert content_in_doing == content_in_todo

    def test_release_multiple_ids_in_single_invocation(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with accepted_git_context() as repo:
            ids = []
            for i in range(2):
                result = _handoff(
                    sessions_dir,
                    f"# Session {i}\n",
                    cwd=repo,
                    goal=f"Multi-release test session {i}",
                    next_step="Verify multi-ID release",
                )
                assert result.returncode == 0, result.stderr
                sid = _parse_handoff_id(result.stdout)
                pickup_result = _pickup(sessions_dir, sid, cwd=repo)
                assert pickup_result.returncode == 0, pickup_result.stderr
                ids.append(sid)

            release_result = subprocess.run(
                ["spx", "session", "release", "--sessions-dir", str(sessions_dir)]
                + ids,
                capture_output=True,
                text=True,
                cwd=str(repo),
            )
            assert release_result.returncode == 0, release_result.stderr

            for sid in ids:
                assert not (sessions_dir / "doing" / f"{sid}.md").exists()
                assert (sessions_dir / "todo" / f"{sid}.md").exists()


# ---------------------------------------------------------------------------
# Assertion 4 — coordination-note content (PLAN.md / ISSUES.md) in session file
# ---------------------------------------------------------------------------


class TestCoordinationNoteContentInSession:
    def test_plan_md_excerpt_preserved(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        plan_text = "## PLAN: Wire the spx CLI half of the session-scope accumulator"
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                textwrap.dedent(f"""\
                    # Session with PLAN.md

                    {plan_text}
                """),
                cwd=repo,
                goal="Preserve PLAN.md excerpt through handoff",
                next_step="Read the todo session file and assert excerpt presence",
            )
            assert result.returncode == 0, result.stderr
            todo_files = list((sessions_dir / "todo").glob("*.md"))
            assert todo_files
            assert plan_text in todo_files[0].read_text()

    def test_issues_md_excerpt_preserved(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        issues_text = "## 12. Repo-wide evidence links still contain legacy test naming"
        with accepted_git_context() as repo:
            result = _handoff(
                sessions_dir,
                textwrap.dedent(f"""\
                    # Session with ISSUES.md

                    {issues_text}
                """),
                cwd=repo,
                goal="Preserve ISSUES.md excerpt through handoff",
                next_step="Read the todo session file and assert excerpt presence",
            )
            assert result.returncode == 0, result.stderr
            todo_files = list((sessions_dir / "todo").glob("*.md"))
            assert todo_files
            assert issues_text in todo_files[0].read_text()


# ---------------------------------------------------------------------------
# Worktree-state assertions — git_ref derivation and linked-worktree refusal
# ---------------------------------------------------------------------------


class TestHandoffGitContext:
    def test_root_checkout_on_branch_records_branch_name(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with handoff_git_env() as env:
            result = _handoff(sessions_dir, "# Session\n", cwd=env.root)
            assert result.returncode == 0, result.stderr
            git_ref = _read_git_ref(_parse_session_file(result.stdout))
            assert git_ref == env.default_branch

    def test_root_checkout_detached_head_records_head_sha(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with handoff_git_env() as env:
            env.detach_root()
            result = _handoff(sessions_dir, "# Session\n", cwd=env.root)
            assert result.returncode == 0, result.stderr
            git_ref = _read_git_ref(_parse_session_file(result.stdout))
            assert git_ref == env.head_sha()

    def test_linked_worktree_at_origin_tip_records_tip_sha(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with handoff_git_env() as env:
            worktree = env.linked_at_origin_tip()
            result = _handoff(sessions_dir, "# Session\n", cwd=worktree)
            assert result.returncode == 0, result.stderr
            git_ref = _read_git_ref(_parse_session_file(result.stdout))
            assert git_ref == env.origin_tip

    def test_linked_worktree_on_branch_is_refused(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with handoff_git_env() as env:
            worktree = env.linked_on_branch()
            result = _handoff(sessions_dir, "# Session\n", cwd=worktree)
            assert result.returncode != 0
            assert "SessionHandoffBaseError" in result.stderr
            assert not list(sessions_dir.rglob("*.md"))

    def test_linked_worktree_detached_off_tip_is_refused(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        with handoff_git_env() as env:
            worktree = env.linked_detached_off_tip()
            result = _handoff(sessions_dir, "# Session\n", cwd=worktree)
            assert result.returncode != 0
            assert "SessionHandoffBaseError" in result.stderr
            assert not list(sessions_dir.rglob("*.md"))

    def test_explicit_work_branch_ref_records_branch_name(self, tmp_path):
        # From a linked worktree at the origin tip — the accepted pool-worktree
        # state whose gate-derived git_ref is the tip SHA — an explicit ref
        # naming a branch on origin records the branch name instead, so the
        # handoff anchors at the feature branch rather than the base.
        sessions_dir = tmp_path / "sessions"
        with handoff_git_env() as env:
            work_branch = env.push_work_branch("work/feature")
            worktree = env.linked_at_origin_tip()
            result = _handoff(
                sessions_dir, "# Session\n", cwd=worktree, git_ref=work_branch
            )
            assert result.returncode == 0, result.stderr
            git_ref = _read_git_ref(_parse_session_file(result.stdout))
            assert git_ref == work_branch
            assert git_ref != env.origin_tip

    def test_explicit_work_branch_ref_absent_from_origin_is_refused(self, tmp_path):
        # An explicit ref the CLI cannot resolve on origin is refused rather than
        # recorded, so a handoff never anchors at a branch a cold agent cannot fetch.
        sessions_dir = tmp_path / "sessions"
        with handoff_git_env() as env:
            worktree = env.linked_at_origin_tip()
            result = _handoff(
                sessions_dir, "# Session\n", cwd=worktree, git_ref="work/absent"
            )
            assert result.returncode != 0
            assert "SessionWorkBranchNotOnOriginError" in result.stderr
            assert not list(sessions_dir.rglob("*.md"))


# ---------------------------------------------------------------------------
# Assertion 4 — post-compact emits re-anchoring directives from payload
# ---------------------------------------------------------------------------

_COMPACT_WITH_FOUNDATION = textwrap.dedent("""\
    1. Primary Request: Testing post-compact directive emission.

    ### Pre-compact markers

    <SPEC_TREE_FOUNDATION>
    <SPEC_TREE_CONTEXT target="spx/21-spec-tree.enabler/76-sessions.enabler/">
    <CLAIMED_SESSIONS ids="2026-05-04_11-08-33">

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

# A summarizer that follows the compactPrompt's own examples renders the marker
# and node path inside backticks and list bullets — the hook must still parse them.
_COMPACT_BACKTICKED = textwrap.dedent("""\
    1. Primary Request: Tolerant post-compact parsing.

    ### Pre-compact markers

    - `<SPEC_TREE_FOUNDATION>`
    - `<SPEC_TREE_CONTEXT target="spx/21-spec-tree.enabler/76-sessions.enabler/">`

    ### Active spec-tree node

    `spx/21-spec-tree.enabler/76-sessions.enabler/`
""")

# The markers section records `none`, but the marker token is quoted in another
# section — detection must stay scoped so this does not trigger re-anchoring.
_COMPACT_MARKER_OUTSIDE_SECTION = textwrap.dedent("""\
    1. Primary Request: Discussion of the compaction mechanism.

    ### Pre-compact markers

    none

    ### Active spec-tree node

    none

    ### Last user request

    The user asked how <SPEC_TREE_FOUNDATION> is detected after compaction.
""")


class TestPostCompactEmitsReanchoringDirective:
    def test_resumed_marker_always_emitted(self, tmp_path):
        result = _post_compact(tmp_path, "sess-x", _COMPACT_WITHOUT_FOUNDATION)
        assert result.returncode == 0, result.stderr
        assert "<SPEC-TREE_RESUMED" in result.stdout

    def test_active_node_attribute_present_when_node_known(self, tmp_path):
        result = _post_compact(tmp_path, "sess-y", _COMPACT_WITH_FOUNDATION)
        assert result.returncode == 0, result.stderr
        assert (
            'active-node="spx/21-spec-tree.enabler/76-sessions.enabler/"'
            in result.stdout
        )

    def test_no_active_node_attribute_when_node_absent(self, tmp_path):
        result = _post_compact(tmp_path, "sess-z", _COMPACT_WITHOUT_FOUNDATION)
        assert result.returncode == 0, result.stderr
        assert "active-node=" not in result.stdout

    def test_foundation_present_emits_reanchoring_skills(self, tmp_path):
        result = _post_compact(tmp_path, "sess-a", _COMPACT_WITH_FOUNDATION)
        assert result.returncode == 0, result.stderr
        assert "/spec-tree:understand" in result.stdout
        assert "/spec-tree:contextualize" in result.stdout

    def test_contextualizing_carries_node_argument(self, tmp_path):
        result = _post_compact(tmp_path, "sess-b", _COMPACT_WITH_FOUNDATION)
        assert result.returncode == 0, result.stderr
        node = "spx/21-spec-tree.enabler/76-sessions.enabler/"
        assert f"/spec-tree:contextualize {node}" in result.stdout

    def test_backticked_section_still_extracts_node(self, tmp_path):
        result = _post_compact(tmp_path, "sess-c", _COMPACT_BACKTICKED)
        assert result.returncode == 0, result.stderr
        node = "spx/21-spec-tree.enabler/76-sessions.enabler/"
        assert f'active-node="{node}"' in result.stdout
        assert f"/spec-tree:contextualize {node}" in result.stdout

    def test_marker_outside_markers_section_does_not_trigger(self, tmp_path):
        result = _post_compact(tmp_path, "sess-d", _COMPACT_MARKER_OUTSIDE_SECTION)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "<SPEC-TREE_RESUMED/>"
        assert "/spec-tree:understand" not in result.stdout

    def test_foundation_absent_omits_reanchoring_skills(self, tmp_path):
        result = _post_compact(tmp_path, "sess-b", _COMPACT_WITHOUT_FOUNDATION)
        assert result.returncode == 0, result.stderr
        assert "/spec-tree:understand" not in result.stdout
        assert "/spec-tree:contextualize" not in result.stdout

    def test_no_compact_summary_produces_no_output(self, tmp_path):
        payload = json.dumps({"session_id": "sess-c", "cwd": str(tmp_path)})
        result = subprocess.run(
            ["python3", str(POST_COMPACT)],
            input=payload,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "CLAUDE_PROJECT_DIR": str(tmp_path),
                "SPX_BIN": _MISSING_SPX,
            },
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_no_file_written_to_disk(self, tmp_path):
        _post_compact(tmp_path, "sess-d", _COMPACT_WITH_FOUNDATION)
        written = list(tmp_path.rglob("*")) if tmp_path.exists() else []
        assert not written, f"unexpected files written: {written}"

    def test_foundation_in_code_block_not_treated_as_marker(self, tmp_path):
        # <SPEC_TREE_FOUNDATION> quoted or indented in another section must not
        # trigger re-anchoring — only an occurrence within ### Pre-compact markers counts.
        summary_with_indented_marker = textwrap.dedent("""\
            ### Pre-compact markers

            none

            ### Active spec-tree node

            none

            ### In-flight observations

            Discussed `<SPEC_TREE_FOUNDATION>` marker behavior in code review.
                <SPEC_TREE_FOUNDATION>
        """)
        result = _post_compact(tmp_path, "sess-e", summary_with_indented_marker)
        assert result.returncode == 0, result.stderr
        assert "/spec-tree:understand" not in result.stdout


# ---------------------------------------------------------------------------
# Assertion 5 — the hooks delegate stash management to the spx CLI. The stash
# mechanics (transcript parse, .spx/ resolution across a worktree pool,
# placement, numbering) are owned and tested in the spx repo, not here; these
# tests pin only the hook's contract with the CLI and its degraded paths.
# ---------------------------------------------------------------------------


class TestPreCompactDelegatesToSpx:
    def test_invokes_compact_store_with_session_and_transcript(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text("{}\n")
        spx = _fake_spx(tmp_path / "bin")
        result = _pre_compact(tmp_path, "sess-p", transcript, spx_bin=str(spx))
        assert result.returncode == 0, result.stderr
        argv = json.loads((spx.parent / "spx.argv").read_text())
        assert argv == [
            "compact",
            "store",
            "--session-id",
            "sess-p",
            "--transcript",
            str(transcript),
        ]

    def test_missing_session_or_transcript_does_not_invoke_spx(self, tmp_path):
        spx = _fake_spx(tmp_path / "bin")
        payload = json.dumps({"session_id": "", "cwd": str(tmp_path)})
        result = subprocess.run(
            ["python3", str(PRE_COMPACT)],
            input=payload,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "CLAUDE_PROJECT_DIR": str(tmp_path),
                "SPX_BIN": str(spx),
            },
        )
        assert result.returncode == 0, result.stderr
        assert not (spx.parent / "spx.argv").exists()

    def test_missing_spx_is_a_silent_noop(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text("{}\n")
        result = _pre_compact(tmp_path, "sess-p", transcript)  # _MISSING_SPX
        assert result.returncode == 0, result.stderr
        assert result.stdout == ""

    def test_writes_no_filesystem_path_itself(self, tmp_path):
        # The PreCompact hook reaches state only through the spx CLI; it writes
        # nothing itself. With the CLI absent it no-ops, so the filesystem is
        # untouched — the only file present is the transcript the test created.
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text("{}\n")
        before = set(tmp_path.rglob("*"))
        result = _pre_compact(tmp_path, "sess-p", transcript)  # _MISSING_SPX
        assert result.returncode == 0, result.stderr
        after = set(tmp_path.rglob("*"))
        assert after == before, f"PreCompact wrote: {after - before}"


class TestPostCompactUsesSpxRetrieve:
    _NODE = "spx/21-spec-tree.enabler/76-sessions.enabler"

    def test_reanchors_from_spx_retrieve_over_summary(self, tmp_path):
        # spx returns a node; the hook re-anchors from it and ignores the summary.
        stash = json.dumps({"active_node": self._NODE, "has_foundation": True})
        spx = _fake_spx(tmp_path / "bin", stdout=stash)
        result = _post_compact(
            tmp_path, "sess-q", "summary lacking any markers", spx_bin=str(spx)
        )
        assert result.returncode == 0, result.stderr
        assert f'active-node="{self._NODE}"' in result.stdout
        assert f"/spec-tree:contextualize {self._NODE}" in result.stdout
        argv = json.loads((spx.parent / "spx.argv").read_text())
        assert argv == ["compact", "retrieve", "--session-id", "sess-q"]

    def test_falls_back_to_summary_when_spx_returns_nothing(self, tmp_path):
        # spx exits non-zero (no stash); the hook parses the node from the summary.
        spx = _fake_spx(tmp_path / "bin", returncode=1)
        result = _post_compact(
            tmp_path, "sess-q", _COMPACT_WITH_FOUNDATION, spx_bin=str(spx)
        )
        assert result.returncode == 0, result.stderr
        assert "/spec-tree:understand" in result.stdout
        assert (
            "/spec-tree:contextualize spx/21-spec-tree.enabler/76-sessions.enabler"
            in result.stdout
        )
