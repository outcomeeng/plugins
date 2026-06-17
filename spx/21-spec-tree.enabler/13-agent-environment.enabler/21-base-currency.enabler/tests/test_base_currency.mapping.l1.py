"""Mapping test for 21-base-currency.enabler (base-currency.md mapping).

L1: a worktree base state maps to the base-currency directive — present with
``behind_count`` and ``default_branch`` when behind by N>0, absent when current or
when the directory is non-git or has no resolvable default. Asserts on the parsed
JSON descriptor.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

import subprocess

import pytest

from outcomeeng_testing.harnesses.git_context import worktree_against_origin
from outcomeeng_testing.harnesses.hooks import (
    directive_of_kind,
    hook_document,
    run_session_start,
)

SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


@pytest.mark.parametrize("behind", [3, 0])
def test_base_state_maps_to_base_currency_directive(behind, tmp_path) -> None:
    with worktree_against_origin(behind=behind) as repo:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(repo)},
            env_file=tmp_path / "claude.env",
            project_dir=repo,
        )
    assert result.returncode == 0
    directive = directive_of_kind(hook_document(result), "base-currency")
    if behind > 0:
        assert directive is not None
        assert directive["behind_count"] == behind
    else:
        assert directive is None


def test_non_git_directory_maps_to_no_directive(tmp_path) -> None:
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert directive_of_kind(hook_document(result), "base-currency") is None


def test_git_repo_without_resolvable_default_maps_to_no_directive(tmp_path) -> None:
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
    assert directive_of_kind(hook_document(result), "base-currency") is None
