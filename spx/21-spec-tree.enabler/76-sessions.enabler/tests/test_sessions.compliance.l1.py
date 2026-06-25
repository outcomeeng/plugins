"""Compliance tests for session skill runtime-claim handling."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
HANDOFF_WORKFLOW_FILES = [
    REPO_ROOT / "src/plugins/spec-tree/skills/handoff/workflows/04-execute.md",
    REPO_ROOT / "dist/claude/spec-tree/skills/handoff/workflows/04-execute.md",
    REPO_ROOT / "dist/codex/spec-tree/skills/handoff/workflows/04-execute.md",
]
FORBIDDEN_WORKTREE_RELEASE_COMMAND = "spx worktree release"


class TestHandoffPreservesRuntimeWorktreeClaim:
    @pytest.mark.parametrize("workflow_file", HANDOFF_WORKFLOW_FILES)
    def test_handoff_workflow_never_releases_worktree_claim(
        self,
        workflow_file: Path,
    ) -> None:
        assert workflow_file.exists(), f"workflow file not found: {workflow_file}"
        assert FORBIDDEN_WORKTREE_RELEASE_COMMAND not in workflow_file.read_text()
