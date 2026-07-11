"""Level 2 evidence for project-scoped Codex runtime resolution."""

from outcomeeng_testing.harnesses.codex_project_runtime import (
    project_codex_runtime_resolves_worktree_artifacts,
)


def test_project_codex_runtime_resolves_worktree_artifacts() -> None:
    assert project_codex_runtime_resolves_worktree_artifacts()
