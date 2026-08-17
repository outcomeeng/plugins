"""Generated finite plugin selections for installation evidence."""

import json
from collections.abc import Mapping, Sequence
from itertools import combinations
from pathlib import Path
from typing import cast

from outcomeeng.distribution.installation import (
    Agent,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    CLAUDE_CATALOG_PATH,
    CODEX_CATALOG_PATH,
    InstallationMode,
    Operation,
    SPEC_TREE_PLUGIN,
    catalog_plugin_names,
)


def catalog_plugin_names_from_document(catalog_path: Path) -> tuple[str, ...]:
    """Read catalog order independently from the production catalog parser."""
    document = cast(
        "dict[str, list[dict[str, object]]]",
        json.loads(catalog_path.read_bytes()),
    )
    return tuple(
        cast("str", plugin[CATALOG_PLUGIN_NAME_FIELD])
        for plugin in document[CATALOG_PLUGINS_FIELD]
    )


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
        Agent.CLAUDE: catalog_plugin_names(checkout / CLAUDE_CATALOG_PATH),
        Agent.CODEX: catalog_plugin_names(checkout / CODEX_CATALOG_PATH),
    }
    return {
        agent: generated_catalog_subset(
            catalog,
            include_spec_tree=include_spec_tree,
        )
        for agent, catalog in catalogs.items()
    }


def generated_valid_catalog_subsets(
    catalog: Sequence[str],
) -> tuple[frozenset[str], ...]:
    """Enumerate every catalog subset containing the required plugin."""
    if SPEC_TREE_PLUGIN not in catalog:
        raise ValueError("catalog must contain spec-tree")
    optional = tuple(plugin for plugin in catalog if plugin != SPEC_TREE_PLUGIN)
    return tuple(
        frozenset((SPEC_TREE_PLUGIN, *selected))
        for size in range(len(optional) + 1)
        for selected in combinations(optional, size)
    )


def generated_invalid_catalog_subsets(
    catalog: Sequence[str],
) -> tuple[frozenset[str], ...]:
    """Enumerate every nonempty catalog subset omitting the required plugin."""
    optional = tuple(plugin for plugin in catalog if plugin != SPEC_TREE_PLUGIN)
    return tuple(
        frozenset(selected)
        for size in range(1, len(optional) + 1)
        for selected in combinations(optional, size)
    )


def generated_persistent_catalog_selections(
    catalog: Sequence[str],
) -> tuple[frozenset[str], ...]:
    """Enumerate empty bootstrap state and every valid installed subset."""
    return (frozenset(), *generated_valid_catalog_subsets(catalog))


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
    "catalog_plugin_names_from_document",
    "generated_agent_subsets",
    "generated_catalog_subset",
    "generated_failure_classification_cases",
    "generated_invalid_catalog_subsets",
    "generated_persistent_catalog_selections",
    "generated_valid_catalog_subsets",
]
