"""Generated finite plugin selections for installation evidence."""

from collections.abc import Mapping, Sequence
from pathlib import Path

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_CATALOG_PATH,
    CODEX_CATALOG_PATH,
    SPEC_TREE_PLUGIN,
    catalog_plugin_names,
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


__all__ = ["generated_agent_subsets", "generated_catalog_subset"]
