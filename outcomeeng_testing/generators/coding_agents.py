"""Generated public-Prowl identity domains for coding-agent evidence."""

from __future__ import annotations

from types import ModuleType


def agent_item(
    module: ModuleType,
    *,
    ordinal: int,
    worktree_ordinal: int | None = None,
) -> dict[str, object]:
    worktree_index = ordinal if worktree_ordinal is None else worktree_ordinal
    suffix = str(ordinal)
    worktree = f"/repo-{worktree_index}"
    return {
        module.ID_FIELD: f"agent-{suffix}",
        module.PANE_FIELD: {
            module.ID_FIELD: f"33333333-3333-4333-8333-{suffix.zfill(12)}"
        },
        module.WORKTREE_FIELD: {
            module.ID_FIELD: worktree,
            module.PATH_FIELD: worktree,
            module.ROOT_PATH_FIELD: f"{worktree}.git",
        },
        module.PROJECT_FIELD: {
            module.PATH_FIELD: worktree,
            module.BRANCH_FIELD: f"work/branch-{suffix}",
        },
        module.RUN_FIELD: {module.ID_FIELD: f"run-{suffix}"},
    }


def mutation_target(
    module: ModuleType,
    identity: dict[str, str],
    *,
    ordinal: int,
) -> dict[str, str]:
    return {
        module.PANE_FIELD: identity[module.PANE_FIELD],
        module.WORKTREE_FIELD: identity[module.WORKTREE_FIELD],
        module.BRANCH_FIELD: identity[module.BRANCH_FIELD],
        module.REPOSITORY_FIELD: identity[module.REPOSITORY_FIELD],
        module.HEAD_FIELD: f"{ordinal:040x}",
        module.STATUS_FIELD: "",
    }


def observed_mutation_state(
    module: ModuleType,
    identity: dict[str, str],
    *,
    ordinal: int,
) -> dict[str, str]:
    return {
        module.WORKTREE_FIELD: identity[module.WORKTREE_FIELD],
        module.BRANCH_FIELD: identity[module.BRANCH_FIELD],
        module.REPOSITORY_FIELD: identity[module.REPOSITORY_FIELD],
        module.HEAD_FIELD: f"{ordinal:040x}",
        module.STATUS_FIELD: "",
    }
