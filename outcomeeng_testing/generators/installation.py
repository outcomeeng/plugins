"""Generated finite plugin selections for installation evidence."""

import json
from collections.abc import Mapping, Sequence
from enum import StrEnum
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
    CLAUDE_PLUGIN_VERSION_FIELD,
    CLAUDE_LOCAL_SCOPE,
    CLAUDE_MANAGED_SCOPE,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_USER_SCOPE,
    CODEX_CATALOG_PATH,
    CODEX_PLUGIN_ID_FIELD,
    CODEX_PLUGIN_MARKETPLACE_FIELD,
    CLAUDE_DIRECTORY_FIELD,
    CLAUDE_DIRECTORY_SOURCE_TYPE,
    CLAUDE_GITHUB_SOURCE_TYPE,
    CLAUDE_GIT_SOURCE_TYPE,
    CLAUDE_URL_FIELD,
    CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD,
    CLAUDE_MARKETPLACE_NAME_FIELD,
    CLAUDE_REPOSITORY_FIELD,
    CLAUDE_SOURCE_FIELD,
    InstallationMode,
    Operation,
    SPEC_TREE_PLUGIN,
    SourceAction,
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
    marketplace: str,
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
            CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(plugin, marketplace),
            CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
            CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
            CLAUDE_PLUGIN_VERSION_FIELD: recorded_version(index),
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
FOREIGN_MARKETPLACE_SUFFIX = "-other"
"""Appended to the marketplace name to form a name whose records every reader skips."""


def foreign_marketplace_name(marketplace: str) -> str:
    """A marketplace name other than the product's, whose records every reader skips."""
    return f"{marketplace}{FOREIGN_MARKETPLACE_SUFFIX}"


class RecordDisposition(StrEnum):
    """What one generated Claude Code install record should map to."""

    INVOCATION_NATIVE = "invocation-native"
    """A record of the invocation checkout: one native update there."""
    FILE_REWRITE = "file-rewrite"
    """A record of another existing checkout: its install-record entry is rewritten."""
    MISSING_DIRECTORY = "missing-directory"
    """A record whose project path is gone or not a directory: rewritten the same way."""
    OUT_OF_SCOPE = "out-of-scope"
    PATHLESS_OUT_OF_SCOPE = "pathless-out-of-scope"
    PATHLESS_DEFECT = "pathless-defect"
    """A refresh-scope entry naming no project path: a listing defect, reported."""
    UNCATALOGED = "uncataloged"
    EXCLUDED = "excluded"


MOVED_DISPOSITIONS: frozenset[RecordDisposition] = frozenset(
    {
        RecordDisposition.INVOCATION_NATIVE,
        RecordDisposition.FILE_REWRITE,
        RecordDisposition.MISSING_DIRECTORY,
    }
)
"""The dispositions whose record ends the run at the target."""


def recorded_version(ordinal: int) -> str:
    """The version a generated preflight listing entry carries.

    Every entry receives its own value, so two records of one plugin never
    share a version before a refresh and a report that names the wrong
    record's version is caught.
    """
    return f"0.{ordinal}.0"


def served_version(entry_count: int) -> str:
    """The version a generated closing listing serves to every moved record.

    Derived from the listing size, so it differs from every recorded version.
    """
    return f"1.{entry_count}.0"


class ClosingDisposition(StrEnum):
    """What one closing-listing entry says happened to its record during the run."""

    MOVED = "moved"
    STALE = "stale"
    KEPT = "kept"
    APPEARED = "appeared"


def generated_closing_listing(
    cases: Sequence[tuple[dict[str, str], RecordDisposition]],
    appearing_checkout: Path,
) -> tuple[tuple[dict[str, str], ClosingDisposition], ...]:
    """Derive the listing a run reads after execution from its preflight cases.

    Every record the plan updates is listed at the served version, except the
    last such record, which keeps its recorded version so a report that
    assumes the update moved it is caught. Every record the plan left
    unchanged is kept as listed. One record the preflight listing did not
    carry — the first cataloged plugin at project scope in a checkout no
    preflight entry names, at its own recorded version rather than the served
    one — is appended, the record another agent session writes between the
    two listing reads.
    """
    served = served_version(len(cases))
    updates = [
        index
        for index, (_, disposition) in enumerate(cases)
        if disposition in MOVED_DISPOSITIONS
    ]
    stale_index = updates[-1] if updates else None
    closing: list[tuple[dict[str, str], ClosingDisposition]] = []
    for index, (entry, disposition) in enumerate(cases):
        if disposition not in MOVED_DISPOSITIONS:
            closing.append((dict(entry), ClosingDisposition.KEPT))
        elif index == stale_index:
            closing.append((dict(entry), ClosingDisposition.STALE))
        else:
            closing.append(
                (
                    {**entry, CLAUDE_PLUGIN_VERSION_FIELD: served},
                    ClosingDisposition.MOVED,
                )
            )
    first_update = cases[updates[0]][0] if updates else cases[0][0]
    closing.append(
        (
            {
                CLAUDE_PLUGIN_ID_FIELD: first_update[CLAUDE_PLUGIN_ID_FIELD],
                CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(appearing_checkout),
                CLAUDE_PLUGIN_VERSION_FIELD: recorded_version(len(cases)),
            },
            ClosingDisposition.APPEARED,
        )
    )
    return tuple(closing)


def generated_claude_install_records(
    catalog: Sequence[str],
    marketplace: str,
    checkout: Path,
    other_checkout: Path,
    absent_path: Path,
    file_path: Path,
) -> tuple[tuple[tuple[dict[str, str], RecordDisposition], ...], ...]:
    """Cycle every catalog plugin through each install-record disposition.

    Each plugin yields one record per disposition: project and local scope in
    the invocation checkout, which move natively; project scope in another
    existing checkout, which the file rewrite moves; project scope at a path
    that no longer exists and at a path that is a regular file, which the
    rewrite moves the same way; a user-scope record carrying no path;
    managed-scope records at both checkouts; and an entry from another
    marketplace. The pathless refresh-scope entry, a listing defect, is
    generated separately because it fails the run it appears in. One
    uncataloged plugin record is appended so the catalog bound has a rejected
    member. Every entry receives its own recorded version.
    """
    groups: list[tuple[tuple[dict[str, str], RecordDisposition], ...]] = []
    for plugin in catalog:
        identifier = marketplace_plugin_identifier(plugin, marketplace)
        groups.append(
            (
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                    },
                    RecordDisposition.INVOCATION_NATIVE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_LOCAL_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                    },
                    RecordDisposition.INVOCATION_NATIVE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(other_checkout),
                    },
                    RecordDisposition.FILE_REWRITE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_LOCAL_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(other_checkout),
                    },
                    RecordDisposition.FILE_REWRITE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(absent_path),
                    },
                    RecordDisposition.MISSING_DIRECTORY,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(file_path),
                    },
                    RecordDisposition.MISSING_DIRECTORY,
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
                        CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(
                            plugin, foreign_marketplace_name(marketplace)
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
                        UNCATALOGED_PLUGIN, marketplace
                    ),
                    CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                    CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                },
                RecordDisposition.UNCATALOGED,
            ),
        )
    )
    ordinal = 0
    versioned: list[tuple[tuple[dict[str, str], RecordDisposition], ...]] = []
    for group in groups:
        members: list[tuple[dict[str, str], RecordDisposition]] = []
        for entry, disposition in group:
            members.append(
                (
                    {**entry, CLAUDE_PLUGIN_VERSION_FIELD: recorded_version(ordinal)},
                    disposition,
                )
            )
            ordinal += 1
        versioned.append(tuple(members))
    return tuple(versioned)


class RegistryShape(StrEnum):
    """The shapes a Claude Code marketplace registry entry takes for one name."""

    GITHUB = "github"
    GIT = "git"
    DIRECTORY = "directory"
    ABSENT = "absent"


def generated_marketplace_registry_entries(
    marketplace: str, clone: Path, checkout: Path
) -> tuple[tuple[str, RegistryShape, str | None, SourceAction], ...]:
    """Every registry-entry shape with the source the run must use for it.

    Each row carries the listing payload, its shape, the source rendering the
    run must report — the `owner/repo` of a GitHub entry, the URL of a git
    entry, the path of a directory entry, and None when no entry exists — and
    whether the plan refreshes or adds the marketplace. The construction law
    is Claude Code's own `marketplace add` argument grammar, which takes
    exactly those three forms, independent of the installer.
    """
    github_repository = f"{marketplace}-org/{marketplace}-plugins"
    git_url = f"https://git.example/{marketplace}.git"
    return (
        (
            json.dumps(
                [
                    {
                        CLAUDE_MARKETPLACE_NAME_FIELD: marketplace,
                        CLAUDE_SOURCE_FIELD: CLAUDE_GITHUB_SOURCE_TYPE,
                        CLAUDE_REPOSITORY_FIELD: github_repository,
                        CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD: str(clone),
                    }
                ]
            ),
            RegistryShape.GITHUB,
            github_repository,
            SourceAction.REFRESH,
        ),
        (
            json.dumps(
                [
                    {
                        CLAUDE_MARKETPLACE_NAME_FIELD: marketplace,
                        CLAUDE_SOURCE_FIELD: CLAUDE_DIRECTORY_SOURCE_TYPE,
                        CLAUDE_DIRECTORY_FIELD: str(checkout),
                        CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD: str(clone),
                    }
                ]
            ),
            RegistryShape.DIRECTORY,
            str(checkout),
            SourceAction.REFRESH,
        ),
        (
            json.dumps(
                [
                    {
                        CLAUDE_MARKETPLACE_NAME_FIELD: marketplace,
                        CLAUDE_SOURCE_FIELD: CLAUDE_GIT_SOURCE_TYPE,
                        CLAUDE_URL_FIELD: git_url,
                        CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD: str(clone),
                    }
                ]
            ),
            RegistryShape.GIT,
            git_url,
            SourceAction.REFRESH,
        ),
        (
            json.dumps(
                [
                    {
                        CLAUDE_MARKETPLACE_NAME_FIELD: foreign_marketplace_name(
                            marketplace
                        ),
                        CLAUDE_SOURCE_FIELD: CLAUDE_GITHUB_SOURCE_TYPE,
                        CLAUDE_REPOSITORY_FIELD: github_repository,
                    }
                ]
            ),
            RegistryShape.ABSENT,
            None,
            SourceAction.ADD,
        ),
    )


def generated_codex_listing_entries(
    catalog: Sequence[str],
    marketplace: str,
) -> tuple[tuple[dict[str, str], ...], frozenset[str]]:
    """Alternate Codex listing entries across marketplaces, naming the in-scope set."""
    entries: list[dict[str, str]] = []
    in_scope: set[str] = set()
    for index, plugin in enumerate(catalog):
        if index % 2 == 0:
            in_scope.add(plugin)
        entries.append(
            {
                CODEX_PLUGIN_ID_FIELD: marketplace_plugin_identifier(
                    plugin, marketplace
                ),
                CODEX_PLUGIN_MARKETPLACE_FIELD: (
                    marketplace
                    if index % 2 == 0
                    else foreign_marketplace_name(marketplace)
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
    "generated_marketplace_registry_entries",
    "foreign_marketplace_name",
    "MOVED_DISPOSITIONS",
    "RecordDisposition",
    "RegistryShape",
    "UNCATALOGED_PLUGIN",
    "generated_codex_listing_entries",
    "generated_failure_classification_cases",
    "generated_invalid_catalog_subsets",
    "generated_persistent_catalog_selections",
    "generated_valid_catalog_subsets",
]
