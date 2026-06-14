"""Mapping tests for 13-agent-environment.enabler (agent-environment.md mappings).

L1: the real `session-start.py` hook is run as a subprocess against real git
repositories and real filesystem I/O in pytest tmp_path directories, with no test
doubles.

Assertions covered:
  - A worktree base state maps to the hook's staleness output: behind by N>0 maps
    to a directive carrying N; current maps to no directive; a non-git directory
    or an unresolvable default maps to no directive and a zero exit.
  - A SessionStart payload maps to the identity write: distinct session UUIDs map
    to distinct $CLAUDE_SESSION_ID writes; a missing session_id maps to no export.
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


def test_distinct_session_ids_map_to_distinct_writes(tmp_path):
    first_env = tmp_path / "first.env"
    second_env = tmp_path / "second.env"
    run_session_start(
        {"session_id": "session-one", "cwd": str(tmp_path)},
        env_file=first_env,
        project_dir=tmp_path,
    )
    run_session_start(
        {"session_id": "session-two", "cwd": str(tmp_path)},
        env_file=second_env,
        project_dir=tmp_path,
    )
    assert "export CLAUDE_SESSION_ID=session-one" in first_env.read_text(
        encoding="utf-8"
    )
    assert "export CLAUDE_SESSION_ID=session-two" in second_env.read_text(
        encoding="utf-8"
    )


def test_missing_session_id_maps_to_no_export(tmp_path):
    env_file = tmp_path / "claude.env"
    result = run_session_start(
        {"cwd": str(tmp_path)},
        env_file=env_file,
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    assert "CLAUDE_SESSION_ID" not in content
