"""Harness checks for session CLI scenario evidence."""

from __future__ import annotations

import json
import re
import subprocess
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)


def _handoff(
    sessions_dir: Path,
    body: str,
    *,
    cwd: Path,
    priority: str = "medium",
    goal: str = "Verify handoff behavior",
    next_step: str = "Inspect the session file",
    git_ref: str | None = None,
) -> subprocess.CompletedProcess[str]:
    fields: dict[str, str] = {
        "priority": priority,
        "goal": goal,
        "next_step": next_step,
    }
    if git_ref is not None:
        fields["git_ref"] = git_ref
    return subprocess.run(
        ["spx", "session", "handoff", "--sessions-dir", str(sessions_dir)],
        input=f"{json.dumps(fields)}\n{body}",
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )


def _pickup(
    sessions_dir: Path, session_id: str, *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["spx", "session", "pickup", "--sessions-dir", str(sessions_dir), session_id],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )


def _release(
    sessions_dir: Path, session_id: str, *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "spx",
            "session",
            "release",
            "--sessions-dir",
            str(sessions_dir),
            session_id,
        ],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )


def _archive(
    sessions_dir: Path, session_id: str, *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "spx",
            "session",
            "archive",
            "--sessions-dir",
            str(sessions_dir),
            session_id,
        ],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )


def _parse_handoff_id(stdout: str) -> str:
    match = re.search(r"<HANDOFF_ID>(.+?)</HANDOFF_ID>", stdout)
    assert match, f"no <HANDOFF_ID> in: {stdout}"
    return match.group(1)


def _parse_session_file(stdout: str) -> Path:
    match = re.search(r"<SESSION_FILE>(.+?)</SESSION_FILE>", stdout)
    assert match, f"no <SESSION_FILE> in: {stdout}"
    return Path(match.group(1))


def _read_git_ref(session_file: Path) -> str:
    lines = session_file.read_text().splitlines()
    assert lines and lines[0] == "---", f"no YAML frontmatter in {session_file}"
    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line == "---"),
        None,
    )
    assert closing_index is not None, (
        f"no closing YAML frontmatter fence in {session_file}"
    )
    frontmatter = "\n".join(lines[1:closing_index])
    match = re.search(
        r'^\s*"?git_ref"?:\s*"?([^"\n]+?)"?\s*$',
        frontmatter,
        re.MULTILINE,
    )
    assert match, f"no git_ref in frontmatter of {session_file}"
    return match.group(1)


def _single_todo_file(sessions_dir: Path) -> Path:
    todo_files = list((sessions_dir / "todo").glob("*.md"))
    assert len(todo_files) == 1
    return todo_files[0]


def handoff_file_appears_in_todo() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        result = _handoff(
            sessions_dir,
            textwrap.dedent(
                """\
                # Test session

                Active node: spx/21-spec-tree.enabler/76-sessions.enabler/
                """
            ),
            cwd=repo,
            goal="Verify handoff writes a file to todo/",
            next_step="Inspect the todo directory listing",
        )
        assert result.returncode == 0, result.stderr
        _single_todo_file(sessions_dir)
        return True


def session_file_contains_active_node_path() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        active_node = "spx/21-spec-tree.enabler/76-sessions.enabler/"
        result = _handoff(
            sessions_dir,
            f"Active node: {active_node}\n",
            cwd=repo,
            goal="Verify active node path survives the handoff write",
            next_step="Read the todo session file and assert path presence",
        )
        assert result.returncode == 0, result.stderr
        assert active_node in _single_todo_file(sessions_dir).read_text()
        return True


def session_file_records_current_git_ref() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        result = _handoff(
            Path(directory) / "sessions",
            "Active node: spx/21-spec-tree.enabler/76-sessions.enabler/\n",
            cwd=repo,
            goal="Verify handoff records the current git ref",
            next_step="Read the todo session file and assert git_ref",
        )
        assert result.returncode == 0, result.stderr
        assert _read_git_ref(_parse_session_file(result.stdout)) == "main"
        return True


def handoff_preserves_full_body_payload() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        body = textwrap.dedent(
            """\
            # Session payload round trip

            ## PLAN: Carry exact coordination note content

            - preserve punctuation: []{}(),;:!?
            - preserve indentation:
                nested line one
                nested line two
            """
        )
        result = _handoff(
            sessions_dir,
            body,
            cwd=repo,
            goal="Verify handoff preserves the full body payload",
            next_step="Read the todo session file and compare the stored body",
        )
        assert result.returncode == 0, result.stderr
        assert body in _single_todo_file(sessions_dir).read_text()
        return True


def pickup_removes_from_todo() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
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
        return True


def pickup_places_in_doing() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
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
        return True


def pickup_emits_session_content_to_stdout() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        body = "Active node: spx/21-spec-tree.enabler/76-sessions.enabler/"
        result = _handoff(
            sessions_dir,
            f"{body}\n",
            cwd=repo,
            goal="Surface session content during pickup",
            next_step="Read pickup stdout and assert body presence",
        )
        assert result.returncode == 0, result.stderr
        pickup_result = _pickup(
            sessions_dir, _parse_handoff_id(result.stdout), cwd=repo
        )
        assert pickup_result.returncode == 0, pickup_result.stderr
        assert body in pickup_result.stdout
        return True


def release_removes_from_doing() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        session_id = _handoff_then_pickup(sessions_dir, repo)
        release_result = _release(sessions_dir, session_id, cwd=repo)
        assert release_result.returncode == 0, release_result.stderr
        assert not (sessions_dir / "doing" / f"{session_id}.md").exists()
        return True


def release_places_back_in_todo() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        session_id = _handoff_then_pickup(sessions_dir, repo)
        release_result = _release(sessions_dir, session_id, cwd=repo)
        assert release_result.returncode == 0, release_result.stderr
        assert (sessions_dir / "todo" / f"{session_id}.md").exists()
        return True


def release_does_not_modify_content() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        body = "# Session with specific content\n\nKeep this intact."
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
        return True


def release_multiple_ids_in_single_invocation() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        first_id = _handoff_then_pickup(sessions_dir, repo)
        second_id = _handoff_then_pickup(sessions_dir, repo)
        release_result = subprocess.run(
            [
                "spx",
                "session",
                "release",
                "--sessions-dir",
                str(sessions_dir),
                first_id,
                second_id,
            ],
            capture_output=True,
            text=True,
            cwd=str(repo),
            check=False,
        )
        assert release_result.returncode == 0, release_result.stderr
        for session_id in (first_id, second_id):
            assert not (sessions_dir / "doing" / f"{session_id}.md").exists()
            assert (sessions_dir / "todo" / f"{session_id}.md").exists()
        return True


def archive_moves_todo_session_to_archive() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        result = _handoff(
            sessions_dir,
            "# Session to archive\n",
            cwd=repo,
            goal="Verify archive moves a todo session",
            next_step="Archive the created session",
        )
        assert result.returncode == 0, result.stderr
        session_id = _parse_handoff_id(result.stdout)
        archive_result = _archive(sessions_dir, session_id, cwd=repo)
        assert archive_result.returncode == 0, archive_result.stderr

        assert not (sessions_dir / "todo" / f"{session_id}.md").exists()
        assert (sessions_dir / "archive" / f"{session_id}.md").exists()
        return True


def handoff_preserves_incorporated_session_reference() -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        prior = _handoff(
            sessions_dir,
            "# Prior session\n",
            cwd=repo,
            goal="Create prior session reference",
            next_step="Use the emitted id in a replacement session",
        )
        assert prior.returncode == 0, prior.stderr
        prior_id = _parse_handoff_id(prior.stdout)
        replacement_body = textwrap.dedent(
            f"""\
            # Canonical continuation

            <incorporated_sessions>
            - {prior_id}
            </incorporated_sessions>
            """
        )
        result = _handoff(
            sessions_dir,
            replacement_body,
            cwd=repo,
            goal="Verify incorporated-session body preservation",
            next_step="Read the created replacement session",
        )
        assert result.returncode == 0, result.stderr
        assert replacement_body in _parse_session_file(result.stdout).read_text()
        return True


def plan_md_excerpt_preserved() -> bool:
    return _coordination_excerpt_preserved(
        heading="Session with PLAN.md",
        excerpt="## PLAN: Wire the spx CLI half of the session-scope accumulator",
        goal="Preserve PLAN.md excerpt through handoff",
    )


def issues_md_excerpt_preserved() -> bool:
    return _coordination_excerpt_preserved(
        heading="Session with ISSUES.md",
        excerpt="## 12. Repo-wide evidence links still contain legacy test naming",
        goal="Preserve ISSUES.md excerpt through handoff",
    )


def root_checkout_on_branch_records_branch_name() -> bool:
    with TemporaryDirectory() as directory, handoff_git_env() as env:
        result = _handoff(Path(directory) / "sessions", "# Session\n", cwd=env.root)
        assert result.returncode == 0, result.stderr
        assert _read_git_ref(_parse_session_file(result.stdout)) == env.default_branch
        return True


def root_checkout_detached_head_records_head_sha() -> bool:
    with TemporaryDirectory() as directory, handoff_git_env() as env:
        env.detach_root()
        result = _handoff(Path(directory) / "sessions", "# Session\n", cwd=env.root)
        assert result.returncode == 0, result.stderr
        assert _read_git_ref(_parse_session_file(result.stdout)) == env.head_sha()
        return True


def linked_worktree_at_origin_tip_records_tip_sha() -> bool:
    with TemporaryDirectory() as directory, handoff_git_env() as env:
        result = _handoff(
            Path(directory) / "sessions",
            "# Session\n",
            cwd=env.linked_at_origin_tip(),
        )
        assert result.returncode == 0, result.stderr
        assert _read_git_ref(_parse_session_file(result.stdout)) == env.origin_tip
        return True


def linked_worktree_on_branch_is_refused() -> bool:
    with TemporaryDirectory() as directory, handoff_git_env() as env:
        sessions_dir = Path(directory) / "sessions"
        result = _handoff(sessions_dir, "# Session\n", cwd=env.linked_on_branch())
        assert result.returncode != 0
        assert "SessionHandoffBaseError" in result.stderr
        assert not list(sessions_dir.rglob("*.md"))
        return True


def linked_worktree_detached_off_tip_is_refused() -> bool:
    with TemporaryDirectory() as directory, handoff_git_env() as env:
        sessions_dir = Path(directory) / "sessions"
        result = _handoff(
            sessions_dir,
            "# Session\n",
            cwd=env.linked_detached_off_tip(),
        )
        assert result.returncode != 0
        assert "SessionHandoffBaseError" in result.stderr
        assert not list(sessions_dir.rglob("*.md"))
        return True


def explicit_work_branch_ref_records_branch_name() -> bool:
    with TemporaryDirectory() as directory, handoff_git_env() as env:
        work_branch = env.push_work_branch("work/feature")
        result = _handoff(
            Path(directory) / "sessions",
            "# Session\n",
            cwd=env.linked_at_origin_tip(),
            git_ref=work_branch,
        )
        assert result.returncode == 0, result.stderr
        git_ref = _read_git_ref(_parse_session_file(result.stdout))
        assert git_ref == work_branch
        assert git_ref != env.origin_tip
        return True


def explicit_work_branch_ref_absent_from_origin_is_refused() -> bool:
    with TemporaryDirectory() as directory, handoff_git_env() as env:
        sessions_dir = Path(directory) / "sessions"
        result = _handoff(
            sessions_dir,
            "# Session\n",
            cwd=env.linked_at_origin_tip(),
            git_ref="work/absent",
        )
        assert result.returncode != 0
        assert "SessionWorkBranchNotOnOriginError" in result.stderr
        assert not list(sessions_dir.rglob("*.md"))
        return True


def _handoff_then_pickup(sessions_dir: Path, repo: Path) -> str:
    result = _handoff(
        sessions_dir,
        "# Session\n",
        cwd=repo,
        goal="Move a session through pickup",
        next_step="Run release and inspect queue state",
    )
    assert result.returncode == 0, result.stderr
    session_id = _parse_handoff_id(result.stdout)
    pickup_result = _pickup(sessions_dir, session_id, cwd=repo)
    assert pickup_result.returncode == 0, pickup_result.stderr
    return session_id


def _coordination_excerpt_preserved(*, heading: str, excerpt: str, goal: str) -> bool:
    with TemporaryDirectory() as directory, accepted_git_context() as repo:
        sessions_dir = Path(directory) / "sessions"
        result = _handoff(
            sessions_dir,
            textwrap.dedent(
                f"""\
                # {heading}

                {excerpt}
                """
            ),
            cwd=repo,
            goal=goal,
            next_step="Read the todo session file and assert excerpt presence",
        )
        assert result.returncode == 0, result.stderr
        assert excerpt in _single_todo_file(sessions_dir).read_text()
        return True
