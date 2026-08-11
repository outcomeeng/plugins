"""Generated request domains for the Prowl environment adapter evidence."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from types import ModuleType

from hypothesis import strategies as st


@dataclass(frozen=True)
class DelegationTextCase:
    subject: str
    instruction: str
    inline_result: str
    result_reference: str
    projection: str


def delegation_text_case(ordinal: int) -> DelegationTextCase:
    suffix = str(ordinal)
    return DelegationTextCase(
        subject=f"bounded delegation {suffix}",
        instruction=f"return terminal evidence {suffix}",
        inline_result=f"terminal result {suffix}",
        result_reference=f"result://terminal-{suffix}",
        projection=f"bounded terminal projection {suffix}",
    )


def public_prowl_operation_names(module: ModuleType) -> tuple[str, ...]:
    return tuple(operation.value for operation in module.PUBLIC_PROWL_COMMAND_PREFIXES)


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


def _request_argument_value(
    module: ModuleType, field_name: str, ordinal: int
) -> object:
    if field_name in module.SELECTOR_FIELDS:
        return f"selector-{ordinal}-{field_name}"
    if field_name == module.PATH_FIELD:
        return f"/generated/{ordinal}"
    if field_name in module.TEXT_ARGUMENT_FIELDS:
        return f"generated-{field_name}-{ordinal}"
    if field_name in module.INTEGER_BOUNDS:
        return module.INTEGER_BOUNDS[field_name][0]
    if field_name in module.BOOLEAN_ARGUMENT_FIELDS:
        return True
    raise AssertionError(f"Source operation contract has no generator for {field_name}")


def operation_requests(module: ModuleType) -> list[dict[str, object]]:
    argument_names = {field: name for name, field in module.ARGUMENT_NAMES.items()}
    requests: list[dict[str, object]] = []
    ordinal = 0
    for operation_name in public_prowl_operation_names(module):
        operation = module.Operation(operation_name)
        contract = module.OPERATION_CONTRACTS[operation]
        for shape in contract.request_shapes:
            optional_fields = tuple(sorted(shape.optional_fields))
            for subset_size in range(len(optional_fields) + 1):
                for optional_subset in combinations(optional_fields, subset_size):
                    ordinal += 1
                    fields = shape.required_fields | frozenset(optional_subset)
                    arguments = {
                        argument_names[field_name]: _request_argument_value(
                            module, field_name, ordinal
                        )
                        for field_name in fields
                    }
                    requests.append(module.operation_request(operation, **arguments))
    return requests


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


def resolver_target_path(
    module: ModuleType,
    agents: list[dict[str, object]],
    cardinality: object,
) -> str:
    if cardinality is module.TargetMatchCardinality.ZERO:
        agent = agents[0]
        field_name = module.PATH_FIELD
    elif cardinality is module.TargetMatchCardinality.ONE:
        agent = agents[1]
        field_name = module.PATH_FIELD
    elif cardinality is module.TargetMatchCardinality.MULTIPLE:
        agent = agents[0]
        field_name = module.ROOT_PATH_FIELD
    else:
        raise AssertionError(f"Unknown target-match cardinality: {cardinality}")
    worktree = agent[module.WORKTREE_FIELD]
    if not isinstance(worktree, dict):
        raise AssertionError("Generated public agent has no worktree object")
    value = worktree[field_name]
    if not isinstance(value, str):
        raise AssertionError(f"Generated worktree {field_name} is not text")
    return value


def subprocess_input_text(ordinal: int) -> str:
    return f"generated subprocess input {ordinal}"


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
