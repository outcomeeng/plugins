"""Generated request and evidence domains for the herdr environment adapter."""

from __future__ import annotations

from itertools import combinations
from types import ModuleType

from hypothesis import strategies as st


class RequestContractError(RuntimeError):
    """The source operation contract names a field this generator cannot produce."""


def wait_timeouts(module: ModuleType) -> st.SearchStrategy[int]:
    """Millisecond bounds inside the adapter's declared timeout range."""
    minimum, maximum = module.INTEGER_BOUNDS[module.TIMEOUT_FIELD]
    return st.integers(min_value=minimum, max_value=maximum)


def agent_names() -> st.SearchStrategy[str]:
    """Live agent names herdr admits."""
    return st.from_regex(r"[a-z][a-z0-9_-]{0,31}", fullmatch=True)


def pane_ids() -> st.SearchStrategy[str]:
    return st.from_regex(r"w[1-9][0-9]{0,2}:p[1-9][0-9]{0,3}", fullmatch=True)


def agent_states(module: ModuleType) -> st.SearchStrategy[object]:
    return st.sampled_from(tuple(module.AgentState))


def unknown_operation_names(module: ModuleType) -> st.SearchStrategy[str]:
    known = {operation.value for operation in module.Operation}
    return st.from_regex(r"[a-z]+(?:-[a-z]+){0,2}", fullmatch=True).filter(
        lambda name: name not in known
    )


def agent_item_variant(
    module: ModuleType,
    template: dict[str, object],
    ordinal: int,
    state: object,
    *,
    name: str | None = None,
) -> dict[str, object]:
    """One hosted agent session varied from a captured inventory item.

    Only the fields the evidence quantifies over change: the server state and
    the identities that keep sessions distinct. Every other field keeps the
    value herdr emitted.
    """
    suffix = str(ordinal)
    return {
        **template,
        module.NAME_FIELD: name if name is not None else f"agent-{suffix}",
        module.AGENT_STATUS_FIELD: str(state),
        module.PANE_ID_FIELD: f"w1:p{suffix}",
        module.TAB_ID_FIELD: f"w1:t{suffix}",
    }


def inventories(
    module: ModuleType, template: dict[str, object]
) -> st.SearchStrategy[list[dict[str, object]]]:
    """Inventories of distinct agent sessions over every server state."""

    def build(states: list[object]) -> list[dict[str, object]]:
        return [
            agent_item_variant(module, template, ordinal, state)
            for ordinal, state in enumerate(states, start=1)
        ]

    return st.lists(agent_states(module), min_size=1, max_size=6).map(build)


def _request_argument_value(
    module: ModuleType, field_name: str, ordinal: int
) -> object:
    if field_name == module.SOURCE_FIELD:
        sources = tuple(module.ReadSource)
        return sources[ordinal % len(sources)].value
    if field_name == module.UNTIL_FIELD:
        states = tuple(module.AgentState)
        return [states[ordinal % len(states)].value]
    if field_name in module.TEXT_ARGUMENT_FIELDS:
        return f"generated-{field_name}-{ordinal}"
    if field_name in module.TEXT_LIST_ARGUMENT_FIELDS:
        return [f"generated-{field_name}-{ordinal}"]
    if field_name in module.INTEGER_BOUNDS:
        return module.INTEGER_BOUNDS[field_name][0]
    if field_name in module.BOOLEAN_ARGUMENT_FIELDS:
        return True
    raise RequestContractError(
        f"Source operation contract has no generator for {field_name}"
    )


def operation_requests(module: ModuleType) -> list[dict[str, object]]:
    """Every operation × request shape × optional subset the registry declares."""
    argument_names = {field: name for name, field in module.ARGUMENT_NAMES.items()}
    requests: list[dict[str, object]] = []
    ordinal = 0
    for operation in module.Operation:
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
