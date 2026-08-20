"""Generated finite plugin selections for installation evidence."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from outcomeeng.distribution.installation import (
    Agent,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    CLAUDE_CATALOG_PATH,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_USER_SCOPE,
    CODEX_CATALOG_PATH,
    CODEX_PLUGIN_ID_FIELD,
    CODEX_PLUGIN_MARKETPLACE_FIELD,
    InstallationMode,
    MARKETPLACE_NAME,
    Operation,
    SPEC_TREE_PLUGIN,
)


def catalog_plugin_names_from_bytes(payload: bytes) -> tuple[str, ...]:
    """Read catalog order from raw bytes independently of the production parser."""
    document = cast(
        "dict[str, list[dict[str, object]]]",
        json.loads(payload),
    )
    return tuple(
        cast("str", plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in document[CATALOG_PLUGINS_FIELD]
    )


def catalog_plugin_names_from_document(catalog_path: Path) -> tuple[str, ...]:
    """Read catalog order independently from the production catalog parser."""
    return catalog_plugin_names_from_bytes(catalog_path.read_bytes())


def generated_catalog_subset(
    catalog: Sequence[str],
    *,
    include_spec_tree: bool,
) -> frozenset[str]:
    """Select a nontrivial catalog-bounded subset with the requested validity."""
    selected = {
        plugin
        for index, plugin in enumerate(catalog)
        if index % 2 == 0 and plugin != SPEC_TREE_PLUGIN
    }
    if not selected:
        selected.update(plugin for plugin in catalog if plugin != SPEC_TREE_PLUGIN)
    if include_spec_tree:
        selected.add(SPEC_TREE_PLUGIN)
    else:
        selected.discard(SPEC_TREE_PLUGIN)
    return frozenset(selected)


def generated_agent_subsets(
    checkout: Path,
    *,
    include_spec_tree: bool,
) -> Mapping[Agent, frozenset[str]]:
    """Generate one catalog-bounded subset for every supported agent."""
    catalogs = {
        Agent.CLAUDE: catalog_plugin_names_from_document(
            checkout / CLAUDE_CATALOG_PATH
        ),
        Agent.CODEX: catalog_plugin_names_from_document(checkout / CODEX_CATALOG_PATH),
    }
    return {
        agent: generated_catalog_subset(
            catalog,
            include_spec_tree=include_spec_tree,
        )
        for agent, catalog in catalogs.items()
    }


def _catalog_window(
    optional: Sequence[str],
    start: int,
    size: int,
) -> tuple[str, ...]:
    """One deterministic rotating window over the optional catalog plugins."""
    return tuple(optional[(start + offset) % len(optional)] for offset in range(size))


def generated_valid_catalog_subsets(
    catalog: Sequence[str],
) -> tuple[frozenset[str], ...]:
    """Generate one valid subset per size class over rotating catalog windows.

    Size classes 0..n over the optional plugins keep every catalog member and
    every subset cardinality in the domain while the domain grows linearly with
    the catalog instead of exponentially.
    """
    if SPEC_TREE_PLUGIN not in catalog:
        raise ValueError("catalog must contain spec-tree")
    optional = tuple(plugin for plugin in catalog if plugin != SPEC_TREE_PLUGIN)
    return (
        frozenset((SPEC_TREE_PLUGIN,)),
        *(
            frozenset((SPEC_TREE_PLUGIN, *_catalog_window(optional, size - 1, size)))
            for size in range(1, len(optional) + 1)
        ),
    )


def generated_invalid_catalog_subsets(
    catalog: Sequence[str],
) -> tuple[frozenset[str], ...]:
    """Generate one nonempty invalid subset per size class over rotating windows."""
    optional = tuple(plugin for plugin in catalog if plugin != SPEC_TREE_PLUGIN)
    return tuple(
        frozenset(_catalog_window(optional, size - 1, size))
        for size in range(1, len(optional) + 1)
    )


def generated_persistent_catalog_selections(
    catalog: Sequence[str],
) -> tuple[frozenset[str], ...]:
    """Enumerate empty bootstrap state and every valid installed subset."""
    return (frozenset(), *generated_valid_catalog_subsets(catalog))


def generated_claude_listing_entries(
    catalog: Sequence[str],
    checkout: Path,
) -> tuple[tuple[dict[str, str], ...], frozenset[str]]:
    """Cycle Claude listing entries across scope cases, naming the in-scope set.

    Every third entry stays in the invocation checkout's project scope; the
    others rotate through a foreign project path and user scope, so scope
    filtering has both accepted and rejected members for every catalog window.
    """
    entries: list[dict[str, str]] = []
    in_scope: set[str] = set()
    for index, plugin in enumerate(catalog):
        entry = {
            CLAUDE_PLUGIN_ID_FIELD: f"{plugin}@{MARKETPLACE_NAME}",
            CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
            CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
        }
        if index % 3 == 1:
            entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD] = str(checkout.parent)
        elif index % 3 == 2:
            entry[CLAUDE_PLUGIN_SCOPE_FIELD] = CLAUDE_USER_SCOPE
            del entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]
        else:
            in_scope.add(plugin)
        entries.append(entry)
    return tuple(entries), frozenset(in_scope)


def generated_codex_listing_entries(
    catalog: Sequence[str],
) -> tuple[tuple[dict[str, str], ...], frozenset[str]]:
    """Alternate Codex listing entries across marketplaces, naming the in-scope set."""
    entries: list[dict[str, str]] = []
    in_scope: set[str] = set()
    for index, plugin in enumerate(catalog):
        if index % 2 == 0:
            in_scope.add(plugin)
        entries.append(
            {
                CODEX_PLUGIN_ID_FIELD: f"{plugin}@{MARKETPLACE_NAME}",
                CODEX_PLUGIN_MARKETPLACE_FIELD: (
                    MARKETPLACE_NAME if index % 2 == 0 else f"{MARKETPLACE_NAME}-other"
                ),
            }
        )
    return tuple(entries), frozenset(in_scope)


def generated_failure_classification_cases(
    operation_domains: Sequence[tuple[InstallationMode, str, Sequence[Operation]]],
) -> tuple[tuple[InstallationMode, str, Operation], ...]:
    """Compose each reachable mode-operation pair with a plan source.

    Several source configurations can reach the same operation.  Keep the
    first source that reaches each mode-operation pair so every finite mapping
    case appears exactly once.
    """
    reached: dict[tuple[InstallationMode, Operation], str] = {}
    for mode, source, operations in operation_domains:
        for operation in operations:
            reached.setdefault((mode, operation), source)
    return tuple(
        (mode, source, operation) for (mode, operation), source in reached.items()
    )


__all__ = [
    "catalog_plugin_names_from_bytes",
    "catalog_plugin_names_from_document",
    "generated_agent_subsets",
    "generated_catalog_subset",
    "generated_claude_listing_entries",
    "generated_codex_listing_entries",
    "generated_failure_classification_cases",
    "generated_invalid_catalog_subsets",
    "generated_persistent_catalog_selections",
    "generated_valid_catalog_subsets",
]
