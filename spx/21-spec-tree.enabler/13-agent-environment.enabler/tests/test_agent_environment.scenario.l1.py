"""Scenario tests for 13-agent-environment.enabler (agent-environment.md scenarios).

L1: the real `session-start.py` hook is run as a subprocess against real git
repositories and real filesystem I/O in pytest tmp_path directories, with no test
doubles. Git fixtures come from `outcomeeng_testing.harnesses.git_context`; the
hook invocation comes from `outcomeeng_testing.harnesses.hooks`.

Assertions covered:
  - SessionStart writes $CLAUDE_SESSION_ID to the harness env file.
  - SessionStart in a directory containing .spx/ creates no per-runtime session
    directory (lazy creation is spx session pickup's job).
  - A worktree behind its resolved default branch yields a base-staleness
    directive on stdout naming the behind-count and instructing fetch+rebase,
    never reset.
"""

from outcomeeng_testing.harnesses.git_context import worktree_against_origin
from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_session_start_writes_session_id_to_env_file(tmp_path):
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert f"export CLAUDE_SESSION_ID={SESSION_ID}" in env_file.read_text(
        encoding="utf-8"
    )


def test_session_start_creates_no_per_runtime_session_directory(tmp_path):
    (tmp_path / ".spx" / "sessions").mkdir(parents=True)
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert not (tmp_path / ".spx" / "sessions" / SESSION_ID).exists()
    assert list((tmp_path / ".spx" / "sessions").iterdir()) == []


def test_behind_default_emits_staleness_directive(tmp_path):
    with worktree_against_origin(behind=2) as repo:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(repo)},
            env_file=tmp_path / "claude.env",
            project_dir=repo,
        )
    assert result.returncode == 0
    assert "<SPEC-TREE_SESSION_START" in result.stdout
    assert 'behind="2"' in result.stdout
    assert "rebase" in result.stdout
    assert "never" in result.stdout and "reset" in result.stdout
