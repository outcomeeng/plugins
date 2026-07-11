"""
Scenario tests for 76-sessions.enabler (sessions.md scenario assertions).

All tests run at L1 using the real `spx` binary, real git repositories, and real
filesystem I/O in pytest tmp_path directories, with no test doubles.

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
  - handoff git-ref derivation across root and linked worktree states.
"""

import json
import re
import subprocess
import textwrap
from pathlib import Path

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)


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


def _release(
    sessions_dir: Path, session_id: str, *, cwd: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["spx", "session", "release", "--sessions-dir", str(sessions_dir), session_id],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


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

    def test_session_file_records_current_git_ref(self, tmp_path):
        with accepted_git_context() as repo:
            result = _handoff(
                tmp_path / "sessions",
                "Active node: spx/21-spec-tree.enabler/76-sessions.enabler/\n",
                cwd=repo,
                goal="Verify handoff records the current git ref",
                next_step="Read the todo session file and assert git_ref",
            )
            assert result.returncode == 0, result.stderr
            session_file = _parse_session_file(result.stdout)
            assert _read_git_ref(session_file) == "main"


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
