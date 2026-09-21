"""Generated finite plugin selections for installation evidence."""

import json
import errno
import hashlib
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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
    PLUGIN_OPERATIONS,
    RecordWarningReason,
    SPEC_TREE_PLUGIN,
    marketplace_plugin_identifier,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "installation"


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
    """Select a canonical boundary subset with the requested validity."""
    if SPEC_TREE_PLUGIN not in catalog:
        raise ValueError("catalog must contain spec-tree")
    if include_spec_tree:
        return frozenset({SPEC_TREE_PLUGIN})
    selected = frozenset(plugin for plugin in catalog if plugin != SPEC_TREE_PLUGIN)
    if not selected:
        raise ValueError("catalog must contain a plugin other than spec-tree")
    return selected


def marketplace_source_from_fixture(filename: str) -> str:
    """Read a marketplace repository from a complete settings fixture."""
    document = cast(
        "dict[str, dict[str, dict[str, dict[str, str]]]]",
        json.loads((FIXTURE_ROOT / filename).read_text(encoding="utf-8")),
    )
    return document["extraKnownMarketplaces"][MARKETPLACE_NAME]["source"]["repo"]


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


@dataclass(frozen=True)
class CatalogRetirement:
    """One catalog member removed from the remaining committed order."""

    active: tuple[str, ...]
    retired: str


def generated_catalog_retirements(
    catalog: Sequence[str],
) -> tuple[CatalogRetirement, ...]:
    """Enumerate every optional catalog member as the retired member."""
    if SPEC_TREE_PLUGIN not in catalog:
        raise ValueError("catalog must contain spec-tree")
    return tuple(
        CatalogRetirement(
            active=tuple(candidate for candidate in catalog if candidate != retired),
            retired=retired,
        )
        for retired in catalog
        if retired != SPEC_TREE_PLUGIN
    )


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


FOREIGN_MARKETPLACE_NAME = f"{MARKETPLACE_NAME}-other"
"""A marketplace name other than the product's, whose records every reader skips."""


class RecordDisposition(StrEnum):
    """What one generated Claude Code install record should map to."""

    UPDATE = "update"
    EXCLUDED = "excluded"


RecordCaseDisposition = RecordDisposition | RecordWarningReason


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
    uncataloged_plugins: Sequence[str],
) -> tuple[tuple[tuple[dict[str, str], RecordCaseDisposition], ...], ...]:
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
    local document override the project document. Each supplied uncataloged
    plugin receives one record so a source-derived retired catalog member
    exercises the catalog bound.
    """
    groups: list[tuple[tuple[dict[str, str], RecordCaseDisposition], ...]] = []
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
                    RecordWarningReason.NO_DIRECTORY_PATH,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(file_path),
                    },
                    RecordWarningReason.NO_DIRECTORY_PATH,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_USER_SCOPE,
                    },
                    RecordWarningReason.PATHLESS_OUT_OF_SCOPE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_MANAGED_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                    },
                    RecordWarningReason.OUT_OF_SCOPE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_MANAGED_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(other_checkout),
                    },
                    RecordWarningReason.OUT_OF_SCOPE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(malformed_checkout),
                    },
                    RecordWarningReason.UNREADABLE_SETTINGS,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(denied_checkout),
                    },
                    RecordWarningReason.UNREADABLE_SETTINGS,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(forked_checkout),
                    },
                    RecordWarningReason.NONCANONICAL_SOURCE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_LOCAL_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(forked_local_checkout),
                    },
                    RecordWarningReason.NONCANONICAL_SOURCE,
                ),
                (
                    {
                        CLAUDE_PLUGIN_ID_FIELD: identifier,
                        CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                        CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(local_forked_checkout),
                    },
                    RecordWarningReason.NONCANONICAL_SOURCE,
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
    groups.extend(
        (
            (
                {
                    CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(plugin),
                    CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                    CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout),
                },
                RecordWarningReason.UNCATALOGED,
            ),
        )
        for plugin in uncataloged_plugins
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


def generated_command_failure_stderr() -> tuple[str, ...]:
    """Enumerate OS error diagnostics independently of CLI failure classification."""
    return tuple(dict.fromkeys(os.strerror(code) for code in errno.errorcode))


@dataclass(frozen=True)
class FailureClassificationCase:
    """One reachable command failure with an independently owned expectation."""

    mode: InstallationMode
    source: str | None
    agent: Agent
    operation: Operation
    plugin: str | None
    stderr: str
    pending_publication: bool


def _unpublished_capture_entries() -> tuple[dict[str, object], ...]:
    document = cast(
        "dict[str, object]",
        json.loads(
            (FIXTURE_ROOT / "unpublished_plugin" / "provenance.json").read_text(
                encoding="utf-8"
            )
        ),
    )
    return tuple(cast("list[dict[str, object]]", document["captures"]))


def _unpublished_capture(
    agent: Agent, operation: Operation
) -> dict[str, object] | None:
    return next(
        (
            entry
            for entry in _unpublished_capture_entries()
            if entry["agent"] == agent.value and entry["operation"] == operation.value
        ),
        None,
    )


def captured_unpublished_plugin_stderr(
    agent: Agent, operation: Operation, plugin: str
) -> str:
    """Render one exact agent-operation capture for another catalog plugin."""
    entry = _unpublished_capture(agent, operation)
    if entry is None:
        raise ValueError(
            f"no unpublished-plugin capture for {agent.value}/{operation.value}"
        )
    root = FIXTURE_ROOT / "unpublished_plugin"
    path = root / cast("str", entry["file"])
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
        raise ValueError(f"capture digest mismatch: {path}")
    document = cast(
        "dict[str, object]",
        json.loads((root / "provenance.json").read_text(encoding="utf-8")),
    )
    return (
        payload.decode("utf-8")
        .replace(cast("str", document["plugin"]), plugin)
        .replace(cast("str", document["marketplace"]), MARKETPLACE_NAME)
        .rstrip("\n")
    )


def generated_failure_classification_cases(
    operation_domains: Sequence[
        tuple[InstallationMode, str | None, Sequence[tuple[Agent, Operation]]]
    ],
    catalog: Sequence[str],
) -> tuple[FailureClassificationCase, ...]:
    """Compose every reachable mode-agent-operation with an independent failure.

    Several source configurations can reach the same command. Keep the first
    source for each complete key. Exact agent-operation captures supply
    publication-absence cases; the independent operating-system error domain
    supplies every other terminal failure.
    """
    reached: dict[tuple[InstallationMode, Agent, Operation], str | None] = {}
    for mode, source, commands in operation_domains:
        for agent, operation in commands:
            reached.setdefault((mode, agent, operation), source)
    plugins = tuple(sorted(catalog))
    if not plugins:
        raise ValueError("failure cases require a nonempty catalog")
    ordinary_errors = generated_command_failure_stderr()
    cases: list[FailureClassificationCase] = []
    for index, ((mode, agent, operation), source) in enumerate(reached.items()):
        plugin = (
            plugins[index % len(plugins)] if operation in PLUGIN_OPERATIONS else None
        )
        capture = _unpublished_capture(agent, operation)
        if capture is not None and plugin is not None:
            stderr = captured_unpublished_plugin_stderr(agent, operation, plugin)
            pending = mode is InstallationMode.PERSISTENT
        else:
            stderr = ordinary_errors[index % len(ordinary_errors)]
            pending = False
        cases.append(
            FailureClassificationCase(
                mode, source, agent, operation, plugin, stderr, pending
            )
        )
    return tuple(cases)


__all__ = [
    "catalog_plugin_names_from_bytes",
    "catalog_plugin_names_from_document",
    "generated_agent_subsets",
    "CatalogRetirement",
    "generated_catalog_retirements",
    "generated_catalog_subset",
    "generated_claude_install_records",
    "generated_claude_listing_entries",
    "RecordDisposition",
    "RecordCaseDisposition",
    "FailureClassificationCase",
    "generated_codex_listing_entries",
    "generated_failure_classification_cases",
    "generated_command_failure_stderr",
    "captured_unpublished_plugin_stderr",
    "generated_invalid_catalog_subsets",
    "generated_persistent_catalog_selections",
    "generated_valid_catalog_subsets",
]
