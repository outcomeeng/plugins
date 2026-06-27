"""Compliance tests for session skill handoff handling."""

from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[4]
HANDOFF_SKILL_FILES: Final = [
    REPO_ROOT / "src/plugins/spec-tree/skills/handoff/SKILL.md",
    REPO_ROOT / "dist/claude/spec-tree/skills/handoff/SKILL.md",
    REPO_ROOT / "dist/codex/spec-tree/skills/handoff/SKILL.md",
]
HANDOFF_WORKFLOW_FILES: Final = [
    REPO_ROOT / "src/plugins/spec-tree/skills/handoff/workflows/04-execute.md",
    REPO_ROOT / "dist/claude/spec-tree/skills/handoff/workflows/04-execute.md",
    REPO_ROOT / "dist/codex/spec-tree/skills/handoff/workflows/04-execute.md",
]
FORBIDDEN_CONTEXT_SESSION_LIST: Final = "Current Sessions:"
FORBIDDEN_SESSION_LIST_COMMAND: Final = "!`spx session list"
FORBIDDEN_WORKTREE_RELEASE_COMMAND: Final = "spx worktree release"
REQUIRED_HANDOFF_ARGUMENT_BINDING: Final = "arguments: [session_mode, prune_mode]"
REQUIRED_HANDOFF_ARGUMENT_CONSUMPTION: Final = "$session_mode"
REQUIRED_HANDOFF_PRUNE_CONSUMPTION: Final = "$prune_mode"


class TestHandoffPreservesRuntimeWorktreeClaim:
    @pytest.mark.parametrize("workflow_file", HANDOFF_WORKFLOW_FILES)
    def test_handoff_workflow_never_releases_worktree_claim(
        self,
        workflow_file: Path,
    ) -> None:
        assert workflow_file.exists(), f"workflow file not found: {workflow_file}"
        assert FORBIDDEN_WORKTREE_RELEASE_COMMAND not in workflow_file.read_text()


class TestHandoffInvocationSurface:
    @pytest.mark.parametrize("skill_file", HANDOFF_SKILL_FILES)
    def test_handoff_context_omits_session_queue_listing(
        self,
        skill_file: Path,
    ) -> None:
        assert skill_file.exists(), f"skill file not found: {skill_file}"
        skill_text = skill_file.read_text()
        assert FORBIDDEN_CONTEXT_SESSION_LIST not in skill_text
        assert FORBIDDEN_SESSION_LIST_COMMAND not in skill_text

    @pytest.mark.parametrize("skill_file", HANDOFF_SKILL_FILES)
    def test_handoff_declares_and_consumes_structured_arguments(
        self,
        skill_file: Path,
    ) -> None:
        assert skill_file.exists(), f"skill file not found: {skill_file}"
        skill_text = skill_file.read_text()
        assert REQUIRED_HANDOFF_ARGUMENT_BINDING in skill_text
        assert REQUIRED_HANDOFF_ARGUMENT_CONSUMPTION in skill_text
        assert REQUIRED_HANDOFF_PRUNE_CONSUMPTION in skill_text
