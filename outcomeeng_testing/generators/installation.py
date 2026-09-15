"""Generated finite plugin selections for installation evidence."""

import json
from collections.abc import Mapping, Sequence
from enum import StrEnum
from itertools import combinations
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
    CLAUDE_LOCAL_SCOPE,
    CLAUDE_MANAGED_SCOPE,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_USER_SCOPE,
    CODEX_CATALOG_PATH,
    CODEX_PLUGIN_ID_FIELD,
    CODEX_PLUGIN_MARKETPLACE_FIELD,
    InstallationMode,
    MARKETPLACE_NAME,
    Operation,
    SPEC_TREE_PLUGIN,
    marketplace_plugin_identifier,
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


def generated_claude_listing_entries(
    catalog: Sequence[str],
    checkout: Path,
) -> tuple[tuple[dict[str, str], ...], frozenset[str]]:
    """Cycle Claude listing entries across scope cases, naming the in-scope set.

    Entries rotate through five cases: project scope and local scope in the
    invocation checkout, which the inventory admits, and a foreign project
    path, user scope, and managed scope in the checkout, which it rejects, so
    scope filtering has accepted and rejected members for every catalog window.
    """
    entries: list[dict[str, str]] = []
    in_scope: set[str] = set()
    for index, plugin in enumerate(catalog):
        entry = {
            CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(plugin),
            CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
            CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
        }
        case = index % 5
        if case == 1:
            entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD] = str(checkout.parent)
        elif case == 2:
            entry[CLAUDE_PLUGIN_SCOPE_FIELD] = CLAUDE_USER_SCOPE
            del entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]
        elif case == 3:
            entry[CLAUDE_PLUGIN_SCOPE_FIELD] = CLAUDE_LOCAL_SCOPE
            in_scope.add(plugin)
        elif case == 4:
            entry[CLAUDE_PLUGIN_SCOPE_FIELD] = CLAUDE_MANAGED_SCOPE
        else:
            in_scope.add(plugin)
        entries.append(entry)
    return tuple(entries), frozenset(in_scope)


UNCATALOGED_PLUGIN = "retired-plugin"
"""A plugin name no committed catalog carries, used as the catalog bound's rejected member."""
FOREIGN_MARKETPLACE_NAME = f"{MARKETPLACE_NAME}-other"
"""A marketplace name other than the product's, whose records every reader skips."""


class RecordDisposition(StrEnum):
    """What one generated Claude Code install record should map to."""

    UPDATE = "update"
    NO_DIRECTORY_PATH = "no-directory-path"
    OUT_OF_SCOPE = "out-of-scope"
    PATHLESS_OUT_OF_SCOPE = "pathless-out-of-scope"
    UNCATALOGED = "uncataloged"
    NONCANONICAL_SOURCE = "noncanonical-source"
    UNREADABLE_SETTINGS = "unreadable-settings"
    EXCLUDED = "excluded"


def generated_claude_install_records(
    catalog: Sequence[str],
    checkout: Path,
    other_checkout: Path,
    absent_path: Path,
    file_path: Path,
    forked_checkout: Path,
    forked_local_checkout: Path,
    local_forked_checkout: Path,
    local_canonical_checkout: Path,
    malformed_checkout: Path,
    denied_checkout: Path,
) -> tuple[tuple[tuple[dict[str, str], RecordDisposition], ...], ...]:
    """Cycle every catalog plugin through each install-record disposition.

    Each plugin yields one record per disposition: an update at project scope
    in the invocation checkout, an update at project scope in another existing
    checkout, an update at local scope in the invocation checkout, a record
    whose project path is absent, a record whose project path is a regular
    file, a user-scope record carrying no path,
    managed-scope records at the invocation checkout and at the other existing
    checkout, a record in a checkout whose project settings register the
    marketplace from a noncanonical source, a record in a checkout whose local
    settings alone do so, a record in a checkout whose local settings register
    a noncanonical source over a canonical project declaration, a record in a
    checkout whose local settings register the canonical source over a
    noncanonical project declaration, a record in a checkout whose settings
    cannot be parsed, a record in a checkout whose settings directory denies
    reading, and an entry from another marketplace. The two
    conflicting checkouts are the precedence boundary: Claude Code lets the
    local document override the project document. One uncataloged plugin
    record is appended so the catalog bound has a rejected member.
    """
    groups: list[tuple[tuple[dict[str, str], RecordDisposition], ...]] = []
    for plugin in catalog:
        identifier = marketplace_plugin_identifier(plugin)
        groups.append(
            (
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                    },
                    RecordDisposition.UPDATE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(other_checkout),
                    },
                    RecordDisposition.UPDATE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_LOCAL_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                    },
                    RecordDisposition.UPDATE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(absent_path),
                    },
                    RecordDisposition.NO_DIRECTORY_PATH,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(file_path),
                    },
                    RecordDisposition.NO_DIRECTORY_PATH,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_USER_SCOPE,
                    },
                    RecordDisposition.PATHLESS_OUT_OF_SCOPE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_MANAGED_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                    },
                    RecordDisposition.OUT_OF_SCOPE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_MANAGED_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(other_checkout),
                    },
                    RecordDisposition.OUT_OF_SCOPE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(malformed_checkout),
                    },
                    RecordDisposition.UNREADABLE_SETTINGS,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(denied_checkout),
                    },
                    RecordDisposition.UNREADABLE_SETTINGS,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(forked_checkout),
                    },
                    RecordDisposition.NONCANONICAL_SOURCE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_LOCAL_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(forked_local_checkout),
                    },
                    RecordDisposition.NONCANONICAL_SOURCE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(local_forked_checkout),
                    },
                    RecordDisposition.NONCANONICAL_SOURCE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(local_canonical_checkout),
                    },
                    RecordDisposition.UPDATE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(
                            plugin, FOREIGN_MARKETPLACE_NAME
                        ),
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                    },
                    RecordDisposition.EXCLUDED,
                ),
            )
        )
    groups.append(
        (
            (
                {
                    CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(
                        UNCATALOGED_PLUGIN
                    ),
                    CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                    CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                },
                RecordDisposition.UNCATALOGED,
            ),
        )
    )
    return tuple(groups)


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
                CODEX_PLUGIN_ID_FIELD: marketplace_plugin_identifier(plugin),
                CODEX_PLUGIN_MARKETPLACE_FIELD: (
                    MARKETPLACE_NAME if index % 2 == 0 else f"{MARKETPLACE_NAME}-other"
                ),
            }
        )
    return tuple(entries), frozenset(in_scope)


def generated_failure_classification_cases(
    operation_domains: Sequence[
        tuple[InstallationMode, str | None, Sequence[Operation]]
    ],
) -> tuple[tuple[InstallationMode, str | None, Operation], ...]:
    """Compose each reachable mode-operation pair with a plan source.

    Several source configurations can reach the same operation.  Keep the
    first source that reaches each mode-operation pair so every finite mapping
    case appears exactly once.
    """
    reached: dict[tuple[InstallationMode, Operation], str | None] = {}
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
    "generated_claude_install_records",
    "generated_claude_listing_entries",
    "RecordDisposition",
    "UNCATALOGED_PLUGIN",
    "generated_codex_listing_entries",
    "generated_failure_classification_cases",
    "generated_invalid_catalog_subsets",
    "generated_persistent_catalog_selections",
    "generated_valid_catalog_subsets",
]
