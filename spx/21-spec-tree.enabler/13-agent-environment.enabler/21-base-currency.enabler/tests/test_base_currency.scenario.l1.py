"""Scenario tests for 21-base-currency.enabler (base-currency.md scenario).

L1: the real `session-start.py` hook is run as a subprocess against real git
repositories in pytest tmp_path directories, with no test doubles. Git fixtures
come from `outcomeeng_testing.harnesses.git_context`.

Assertion covered:
  - A worktree behind its resolved default branch yields a base-staleness
    directive on stdout naming the behind-count and the resolved default and
    instructing fetch+rebase, never reset.
"""

from outcomeeng_testing.harnesses.git_context import worktree_against_origin
from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_behind_default_emits_staleness_directive(tmp_path):
    behind = 2
    default_branch = "main"
    with worktree_against_origin(behind=behind, default_branch=default_branch) as repo:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(repo)},
            env_file=tmp_path / "claude.env",
            project_dir=repo,
        )
    assert result.returncode == 0
    assert "<SPEC-TREE_SESSION_START" in result.stdout
    assert f'behind="{behind}"' in result.stdout
    assert f'default="origin/{default_branch}"' in result.stdout
    assert "fetch" in result.stdout
    assert "rebase" in result.stdout
    assert "never" in result.stdout and "reset" in result.stdout
