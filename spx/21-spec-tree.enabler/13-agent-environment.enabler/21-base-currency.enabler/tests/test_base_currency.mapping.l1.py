"""Mapping tests for 21-base-currency.enabler (base-currency.md mapping).

L1: the real `session-start.py` hook is run as a subprocess against real git
repositories and real filesystem I/O in pytest tmp_path directories, with no test
doubles.

Assertion covered:
  - A worktree base state maps to the hook's staleness output: behind by N>0 maps
    to a directive carrying N; current maps to no directive; a non-git directory
    or an unresolvable default maps to no directive and a zero exit.
"""

import subprocess

import pytest

from outcomeeng_testing.harnesses.git_context import worktree_against_origin
from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

MARKER = "<SPEC-TREE_SESSION_START"


@pytest.mark.parametrize("behind", [3, 0])
def test_base_state_maps_to_staleness_output(behind, tmp_path):
    with worktree_against_origin(behind=behind) as repo:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(repo)},
            env_file=tmp_path / "claude.env",
            project_dir=repo,
        )
    assert result.returncode == 0
    if behind > 0:
        assert MARKER in result.stdout
        assert f'behind="{behind}"' in result.stdout
    else:
        assert MARKER not in result.stdout


def test_non_git_directory_maps_to_no_directive(tmp_path):
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert MARKER not in result.stdout


def test_git_repo_without_resolvable_default_maps_to_no_directive(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", "-b", "main", str(repo)],
        check=True,
        capture_output=True,
    )
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(repo)},
        env_file=tmp_path / "claude.env",
        project_dir=repo,
    )
    assert result.returncode == 0
    assert MARKER not in result.stdout
