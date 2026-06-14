"""Compliance tests for 13-agent-environment.enabler (agent-environment.md compliance).

L1: the real `session-start.py` hook is run as a subprocess against real git
repositories in pytest tmp_path directories, with no test doubles.

Assertions covered:
  - The hook resolves the default branch from git's configured default
    (origin/HEAD), never a literal origin/main.
  - The base-staleness check is read-only: no git fetch, no state-mutating git
    command, and HEAD and refs are unchanged after the hook runs.
"""

import subprocess

from outcomeeng_testing.harnesses.git_context import worktree_against_origin
from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "cccccccc-dddd-eeee-ffff-000000000000"


def _git_out(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_default_branch_resolved_from_git_not_literal_main(tmp_path):
    # A non-main default: a hook that hardcoded origin/main would emit nothing
    # here, and one that resolves the configured default names this branch. The
    # expected branch is derived from the value provisioned, not hand-copied.
    default = "trunk"
    with worktree_against_origin(behind=1, default_branch=default) as repo:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(repo)},
            env_file=tmp_path / "claude.env",
            project_dir=repo,
        )
    assert result.returncode == 0
    assert f'default="origin/{default}"' in result.stdout
    assert "origin/main" not in result.stdout


def test_base_staleness_check_is_read_only(tmp_path):
    with worktree_against_origin(behind=2) as repo:
        head_before = _git_out(repo, "rev-parse", "HEAD")
        refs_before = _git_out(repo, "show-ref")
        fetch_head_before = (repo / ".git" / "FETCH_HEAD").exists()

        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(repo)},
            env_file=tmp_path / "claude.env",
            project_dir=repo,
        )

        head_after = _git_out(repo, "rev-parse", "HEAD")
        refs_after = _git_out(repo, "show-ref")
        fetch_head_after = (repo / ".git" / "FETCH_HEAD").exists()

    assert result.returncode == 0
    assert head_before == head_after
    assert refs_before == refs_after
    # A fetch would create .git/FETCH_HEAD; the harness only pushes, so it is
    # absent before and must stay absent — proving the check ran no fetch.
    assert fetch_head_before is False
    assert fetch_head_after is False
