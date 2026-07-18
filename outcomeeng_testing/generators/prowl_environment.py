"""Generated request domains for the Prowl environment adapter evidence."""

from __future__ import annotations

from types import ModuleType

from hypothesis import strategies as st


def coordination_references() -> st.SearchStrategy[str]:
    return st.uuids(version=4).map(str)


def result_forms() -> st.SearchStrategy[tuple[str | None, str | None, str | None]]:
    inline = st.text(min_size=1, max_size=200)
    reference = st.from_regex(r"result://[a-z0-9]{1,32}", fullmatch=True)
    projection = st.text(min_size=1, max_size=80)
    return st.one_of(
        inline.map(lambda value: (value, None, None)),
        st.tuples(st.none(), reference, projection),
        st.tuples(inline, reference, projection),
    )


def operation_requests(module: ModuleType) -> list[dict[str, object]]:
    pane = "11111111-1111-4111-8111-111111111111"
    tab = "22222222-2222-4222-8222-222222222222"
    worktree = "/repo/worktree"
    path = "/repo/worktree/subdirectory"
    return [
        module.operation_request(module.Operation.LIST),
        module.operation_request(module.Operation.AGENTS),
        module.operation_request(
            module.Operation.READ,
            pane=pane,
            last=37,
            wait_stable=True,
            stable_interval=250,
            stable_period=900,
            wait_timeout=12,
        ),
        module.operation_request(
            module.Operation.SEND,
            pane=pane,
            text="run the bounded task",
            no_enter=True,
            no_wait=True,
        ),
        module.operation_request(
            module.Operation.SEND,
            target=pane,
            text="run and capture",
            capture=True,
            timeout=45,
        ),
        module.operation_request(
            module.Operation.KEY,
            target=pane,
            key="enter",
            repeat=3,
            mutation_authorized=True,
        ),
        module.operation_request(
            module.Operation.FOCUS,
            worktree=worktree,
            mutation_authorized=True,
        ),
        module.operation_request(
            module.Operation.TAB_CREATE,
            worktree=worktree,
            path=path,
            mutation_authorized=True,
        ),
        module.operation_request(
            module.Operation.TAB_CLOSE,
            tab=tab,
            force=True,
            mutation_authorized=True,
        ),
        module.operation_request(
            module.Operation.PANE_CLOSE,
            pane=pane,
            force=True,
            mutation_authorized=True,
        ),
        module.operation_request(module.Operation.OPEN, path=path),
        module.operation_request(module.Operation.OPEN),
    ]


def public_agent_item(module: ModuleType, ordinal: int) -> dict[str, object]:
    identity = agent_identity(module, ordinal)
    return {
        module.ID_FIELD: identity[module.AGENT_FIELD],
        module.PANE_FIELD: {module.ID_FIELD: identity[module.PANE_FIELD]},
        module.WORKTREE_FIELD: {
            module.ID_FIELD: identity[module.WORKTREE_FIELD],
            module.PATH_FIELD: identity[module.WORKTREE_FIELD],
            module.ROOT_PATH_FIELD: identity[module.REPOSITORY_FIELD],
        },
        module.PROJECT_FIELD: {
            module.PATH_FIELD: identity[module.WORKTREE_FIELD],
            module.BRANCH_FIELD: identity[module.BRANCH_FIELD],
        },
        module.RUN_FIELD: {module.ID_FIELD: identity[module.RUN_FIELD]},
    }


def agent_identity(module: ModuleType, ordinal: int) -> dict[str, str]:
    suffix = str(ordinal)
    return {
        module.AGENT_FIELD: f"agent-{suffix}",
        module.PANE_FIELD: f"33333333-3333-4333-8333-{suffix.zfill(12)}",
        module.WORKTREE_FIELD: f"/repo-{suffix}",
        module.BRANCH_FIELD: f"work/branch-{suffix}",
        module.REPOSITORY_FIELD: "/repo.git",
        module.RUN_FIELD: f"run-{suffix}",
    }
