"""Install committed marketplace catalogs into selected agent state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from typing import Protocol, cast

from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    DIST_DIR_NAME,
    SKILLS_SUBDIR_NAME,
)

MARKETPLACE_IDENTIFIER_JOINER = "@"
"""The character both agent CLIs place between a plugin name and its marketplace name."""
CATALOG_MARKETPLACE_NAME_FIELD = "name"
"""The committed catalog field that names the marketplace; no constant names it."""
CATALOG_PLUGIN_SOURCE_FIELD = "source"
"""The committed catalog field naming where one plugin's tree lives, relative to the catalog root."""
PLUGIN_MANIFEST_RELATIVE = Path(".claude-plugin") / "plugin.json"
PLUGIN_MANIFEST_VERSION_FIELD = "version"
GIT_EXECUTABLE = "git"
GIT_HEAD_ARGUMENTS: tuple[str, ...] = ("rev-parse", "HEAD")
"""How the run reads the registered clone's head commit, the target every record moves to."""
CODEX_CATALOG_PATH = Path(".agents/plugins/marketplace.json")
CLAUDE_CATALOG_PATH = Path(".claude-plugin/marketplace.json")
CLAUDE_PROJECT_SETTINGS_PATH = Path(".claude/settings.json")
CLAUDE_LOCAL_SETTINGS_PATH = Path(".claude/settings.local.json")
CODEX_CONFIG_PATH = Path(".codex/config.toml")
CODEX_AGENTS_PATH = Path(".codex/agents")
CODEX_HOME_AGENTS_PATH = Path("agents")
AGENT_OWNERSHIP_FILENAME = ".outcomeeng-marketplace-ownership.json"
AGENT_OWNERSHIP_SCHEMA_VERSION = 1
AGENT_OWNERSHIP_SCHEMA_FIELD = "schema_version"
AGENT_OWNERSHIP_ENTRIES_FIELD = "entries"
AGENT_OWNERSHIP_DESTINATION_FIELD = "destination"
AGENT_OWNERSHIP_PLUGIN_FIELD = "plugin"
AGENT_OWNERSHIP_DIGEST_FIELD = "digest"
AGENT_SKILLS_FIELD = "skills"
AGENT_SKILLS_CONFIG_FIELD = "config"
AGENT_SKILL_NAME_FIELD = "name"
CATALOG_PLUGINS_FIELD = "plugins"
CATALOG_PLUGIN_NAME_FIELD = "name"
HOME_ENV = "HOME"
CLAUDE_CONFIG_ENV = "CLAUDE_CONFIG_DIR"
CODEX_HOME_ENV = "CODEX_HOME"
CODEX_SQLITE_HOME_ENV = "CODEX_SQLITE_HOME"
STATE_ENV_NAMES: tuple[str, ...] = (
    HOME_ENV,
    CLAUDE_CONFIG_ENV,
    CODEX_HOME_ENV,
    CODEX_SQLITE_HOME_ENV,
)
CLAUDE_EXECUTABLE = "claude"
CODEX_EXECUTABLE = "codex"
CODEX_EXEC_SUBCOMMAND = "exec"
"""The Codex subcommand that runs one non-interactive session."""
CLAUDE_LIST_COMMAND = (CLAUDE_EXECUTABLE, "plugin", "list", "--json")


def codex_list_command(marketplace: str) -> tuple[str, ...]:
    """The Codex listing of one marketplace's installed plugins."""
    return (CODEX_EXECUTABLE, "plugin", "list", "--marketplace", marketplace, "--json")


CODEX_MARKETPLACE_LIST_COMMAND = (
    CODEX_EXECUTABLE,
    "plugin",
    "marketplace",
    "list",
    "--json",
)
CLAUDE_MARKETPLACE_LIST_COMMAND = (
    CLAUDE_EXECUTABLE,
    "plugin",
    "marketplace",
    "list",
    "--json",
)
CLAUDE_ALREADY_INSTALLED_FRAGMENT = "already installed"
UNPUBLISHED_PLUGIN_FRAGMENT = "not found in marketplace"
CLAUDE_ALREADY_ENABLED_FRAGMENT = "already enabled"
EXTRA_MARKETPLACES_FIELD = "extraKnownMarketplaces"
CLAUDE_SOURCE_FIELD = "source"
CLAUDE_REPOSITORY_FIELD = "repo"
CLAUDE_DIRECTORY_FIELD = "path"
CLAUDE_GITHUB_SOURCE_TYPE = "github"
CLAUDE_DIRECTORY_SOURCE_TYPE = "directory"
CLAUDE_GIT_SOURCE_TYPE = "git"
CLAUDE_URL_FIELD = "url"
CODEX_MARKETPLACES_FIELD = "marketplaces"
CODEX_MARKETPLACE_NAME_FIELD = "name"
CODEX_MARKETPLACE_SOURCE_FIELD = "marketplaceSource"
CODEX_SOURCE_TYPE_FIELD = "sourceType"
CODEX_SOURCE_FIELD = "source"
CODEX_GIT_SOURCE_TYPE = "git"
CODEX_LOCAL_SOURCE_TYPE = "local"
CLAUDE_MARKETPLACE_NAME_FIELD = "name"
CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD = "installLocation"
"""The registry listing field naming the clone Claude Code keeps for a marketplace."""
CLAUDE_PLUGIN_CACHE_RELATIVE = Path("plugins") / "cache"
"""Where Claude Code caches plugin trees beneath its configuration directory: `<marketplace>/<plugin>/<version>`."""
CLAUDE_PLUGIN_ID_FIELD = "id"
CLAUDE_PLUGIN_ENABLED_FIELD = "enabled"
CLAUDE_PLUGIN_SCOPE_FIELD = "scope"
CLAUDE_PLUGIN_PROJECT_PATH_FIELD = "projectPath"
CLAUDE_PLUGIN_VERSION_FIELD = "version"
CLAUDE_INSTALLED_PLUGINS_RELATIVE = Path("plugins") / "installed_plugins.json"
"""Where Claude Code keeps its install-record document beneath its configuration directory.

The installer reads records through the agent's listing and rewrites, in this
document, the entries of every project- or local-scope record outside the
invocation checkout; the path and the field names below are the agent's own
vocabulary, owned here so no other module spells them.
"""
CLAUDE_INSTALLED_PLUGINS_FIELD = "plugins"
CLAUDE_INSTALLED_RECORD_VERSION_FIELD = "version"
CLAUDE_INSTALLED_RECORD_COMMIT_FIELD = "gitCommitSha"
CLAUDE_INSTALLED_RECORD_PATH_FIELD = "installPath"
CLAUDE_PROJECT_SCOPE = "project"
CLAUDE_LOCAL_SCOPE = "local"
CLAUDE_USER_SCOPE = "user"
CLAUDE_MANAGED_SCOPE = "managed"
CLAUDE_REFRESH_SCOPES: frozenset[str] = frozenset(
    {CLAUDE_PROJECT_SCOPE, CLAUDE_LOCAL_SCOPE}
)
"""Claude Code scopes whose install records persistent refresh brings to the target."""
CLAUDE_ENABLED_PLUGINS_FIELD = "enabledPlugins"
CODEX_PLUGIN_ENTRIES_FIELD = "installed"
CODEX_PLUGIN_ID_FIELD = "pluginId"
CODEX_PLUGIN_ENABLED_FIELD = "enabled"
CODEX_PLUGIN_MARKETPLACE_FIELD = "marketplaceName"
SPEC_TREE_PLUGIN = "spec-tree"
FIRST_INSTALL_WARNING = (
    "No {marketplace} plugins are installed for {agent}; installing only "
    "{plugin}. You probably want to install more plugins."
)
UNREFRESHABLE_RECORD_WARNING = (
    "Claude Code records {plugin} at {scope} scope for {project_path}, but the "
    "plugin cache carries no directory for the target version {version}; the "
    "record is left unchanged."
)
UNWRITTEN_RECORD_WARNING = (
    "Claude Code's install-record document carries no {scope}-scope entry for "
    "{plugin} at {project_path} that the rewrite could address, so the record "
    "the run planned to move is left unchanged."
)
UNREADABLE_HEAD_RECORD_WARNING = (
    "Claude Code records {plugin} at {scope} scope for {project_path}, but the "
    "location the registry records for the marketplace resolves no head commit "
    "— it is no git working tree, or the read of it failed; the run reaches no "
    "target."
)
"""The absent-head disposition, worded for every record the run carries.

The head read presupposes a git working tree, which a directory registration
added from a plain directory is not. No target exists for any plugin, so the
drift comparison judges nothing and this warning is the whole domain's path to
the exit code; the message claims nothing about a record's version, because the
invocation checkout's own records have already received their native update
while every other record is left where the rewrite found it.
"""
UNRESOLVED_TARGET_RECORD_WARNING = (
    "Claude Code records {plugin} at {scope} scope for {project_path}, but the "
    "registered clone resolves no target version for {plugin} — its catalog "
    "names no source, or the manifest that source names carries no readable "
    "version; the record reaches no target."
)
"""The unresolved-target disposition, worded for every record it covers.

A record outside the invocation checkout is left where it was, because the
rewrite is what would have moved it; the invocation checkout's own record has
already received its native update by the time the clone is read. Neither
reaches a target, which is what the warning says and what makes the exit
nonzero, so the message claims nothing about the record's version.
"""
OUT_OF_SCOPE_RECORD_WARNING = (
    "Claude Code records {plugin} at {scope} scope for {project_path}; persistent "
    "installation refreshes only project and local scope, so the record is left "
    "unchanged."
)
PATHLESS_OUT_OF_SCOPE_RECORD_WARNING = (
    "Claude Code records {plugin} at {scope} scope with no project path; "
    "persistent installation refreshes only project and local scope, so the "
    "record is left unchanged."
)
UNCATALOGED_RECORD_WARNING = (
    "Claude Code records {plugin} at {scope} scope for {project_path}, but the "
    "committed catalog does not carry it; the record is left unchanged."
)
UNREGISTERED_TARGET_WARNING = (
    "Claude Code records {plugin} at {scope} scope for {project_path} at version "
    "{version}, but this run registers the marketplace itself, so no target "
    "exists yet; the record is left unchanged and the next run refreshes it."
)
WITHHELD_TARGET_RECORD_WARNING = (
    "Claude Code records {plugin} at {scope} scope for {project_path} at version "
    "{version}, but this run withholds the registration a target would be read "
    "from; the record is left unchanged."
)
PATHLESS_LISTING_ENTRY_WARNING = (
    "Claude Code lists {plugin} at {scope} scope with no project path; the entry "
    "is a listing defect and is left unchanged."
)
VERSIONLESS_LISTING_ENTRY_WARNING = (
    "Claude Code lists {plugin} at {scope} scope for {project_path} with no "
    "version; the entry is a listing defect and is left unchanged."
)
UNREADABLE_SETTINGS_DIAGNOSTIC = "invalid Claude Code settings"
UNREADABLE_SETTINGS_WARNING = (
    "{diagnostic}; bootstrap of the invocation checkout is skipped, and no "
    "other operation reads those settings."
)
"""The unreadable-settings disposition, worded for the condition's own reach.

The message names what the settings decide — the bootstrap alone — rather
than what the rest of the run goes on to do, because a run that also
withholds the registration performs nothing else either. Each record's own
disposition is reported beside this warning.
"""
UNDECLARED_SOURCE_DIAGNOSTIC = "the invocation checkout declares no marketplace source"
WITHHELD_REGISTRATION_WARNING = (
    "{diagnostic}; this agent registers no {marketplace} marketplace and the "
    "invocation checkout declares no readable source for one, so that "
    "registration and every operation depending on it are withheld."
)
"""The withheld-registration disposition, worded for what the plan withholds.

Every operation naming the marketplace goes with the registration, which for
Claude Code is the native update of each record the invocation checkout
holds, so the message claims no refresh. Each record the run leaves where it
found it carries its own warning.
"""
UNLOCATED_REGISTRY_DIAGNOSTIC = "the marketplace registry entry names no clone"
OFF_TARGET_DIAGNOSTIC = "install records off the target after refresh"
CHECKOUT_OPTION = "--checkout"
"""The installer option naming the invocation checkout."""
STATE_ROOT_OPTION = "--state-root"
"""The installer option selecting isolated mode's disposable state root."""
JSON_OUTPUT_OPTION = "--json"
"""The installer option requesting the JSON report on stdout."""


def marketplace_plugin_identifier(plugin: str, marketplace: str) -> str:
    """Compose the identifier an agent CLI gives one plugin of one marketplace."""
    return f"{plugin}{MARKETPLACE_IDENTIFIER_JOINER}{marketplace}"


def marketplace_plugin_name(identifier: str, marketplace: str) -> str | None:
    """Return the plugin name an identifier carries for the marketplace, or None.

    An identifier from another marketplace yields None, so a reader skips it.
    """
    suffix = f"{MARKETPLACE_IDENTIFIER_JOINER}{marketplace}"
    if not identifier.endswith(suffix):
        return None
    return identifier.removesuffix(suffix)


def catalog_marketplace_name(catalog_path: Path) -> str:
    """Read the marketplace's own name from one committed catalog."""
    try:
        document = cast(object, json.loads(catalog_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"invalid marketplace catalog {catalog_path}: {error}"
        ) from error
    if not isinstance(document, dict):
        raise ValueError(f"marketplace catalog {catalog_path} must be a JSON object")
    name = document.get(CATALOG_MARKETPLACE_NAME_FIELD)
    if not isinstance(name, str) or not name:
        raise ValueError(f"marketplace catalog {catalog_path} names no marketplace")
    return name


class Agent(StrEnum):
    """Agent harnesses supported by marketplace installation."""

    CLAUDE = "claude"
    CODEX = "codex"


class InstallationMode(StrEnum):
    """Persistent installation or isolated verification."""

    PERSISTENT = "persistent"
    ISOLATED = "isolated"


class Operation(StrEnum):
    """External operations exposed in reports and diagnostics."""

    MARKETPLACE_INSPECT = "marketplace-inspect"
    PLUGIN_INSPECT = "plugin-inspect"
    MARKETPLACE_ADD = "marketplace-add"
    MARKETPLACE_REFRESH = "marketplace-refresh"
    MARKETPLACE_HEAD = "marketplace-head"
    """Read the registered clone's head commit after the marketplace refresh."""
    PLUGIN_INSTALL = "plugin-install"
    PLUGIN_ENABLE = "plugin-enable"
    PLUGIN_UPDATE = "plugin-update"
    PLUGIN_LIST = "plugin-list"


class ReportField(StrEnum):
    """Public JSON fields emitted by repository installation."""

    AGENT = "agent"
    PLUGIN = "plugin"
    OPERATION = "operation"
    ARGV = "argv"
    EXIT_CODE = "exit_code"
    STDOUT = "stdout"
    STDERR = "stderr"
    COMPLETED_OPERATIONS = "completed_operations"
    MODE = "mode"
    CLAUDE_PLUGINS = "claude_plugins"
    CLAUDE_RECORDS = "claude_records"
    CODEX_PLUGINS = "codex_plugins"
    STATE_ROOT = "state_root"
    CHECKOUT = "checkout"
    CODEX_HOME = "codex_home"
    PENDING_PUBLICATION = "pending_publication"
    WARNINGS = "warnings"
    MESSAGE = "message"
    AGENT_HOME = "agent_home"
    WRITTEN = "written"
    PRUNED = "pruned"
    COLLISIONS = "collisions"
    DESTINATION = "destination"
    REASON = "reason"
    SCOPE = "scope"
    PROJECT_PATH = "project_path"
    VERSION = "version"
    VERSION_BEFORE = "version_before"
    VERSION_AFTER = "version_after"
    UNREFRESHED_RECORDS = "unrefreshed_records"
    OFF_TARGET_RECORDS = "off_target_records"
    TARGET = "target"
    COMMIT = "commit"
    VERSIONS = "versions"
    MARKETPLACE = "marketplace"
    SOURCE = "source"
    COMMANDS = "commands"
    CWD = "cwd"


PLUGIN_OPERATIONS: frozenset[Operation] = frozenset(
    {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE, Operation.PLUGIN_UPDATE}
)
"""Operations that name one plugin, as opposed to a marketplace or the checkout."""

CLAUDE_SCOPE_BEARING_OPERATIONS: frozenset[Operation] = frozenset(
    {
        Operation.MARKETPLACE_ADD,
        Operation.PLUGIN_INSTALL,
        Operation.PLUGIN_ENABLE,
        Operation.PLUGIN_UPDATE,
    }
)
"""Claude operations whose public CLI accepts an explicit installation scope.

`_claude_argv` appends the scope exactly for these operations and for no other
operation it builds; the marketplace refresh it builds takes none. The
marketplace and plugin inspections and the closing plugin listing are the fixed
tuples `CLAUDE_MARKETPLACE_LIST_COMMAND` and `CLAUDE_LIST_COMMAND`, which carry
no scope.
"""
REPORTED_FAILURE_OPERATIONS: frozenset[Operation] = frozenset(
    {Operation.MARKETPLACE_HEAD}
)
"""Planned operations whose nonzero exit is a reported disposition, not a failure.

The head read is the run's only non-agent command and the only one whose
failure names a machine state the decision already gives a disposition: a run
with no head reaches no target, exactly as a bootstrap run and a withheld
registration do. Raising there would abandon the machine-wide refresh with
nothing reported about any record on the machine, so the run continues, plans
no rewrite, and reports every record it carries against no target.
"""
CLAUDE_SCOPELESS_OPERATIONS: frozenset[Operation] = frozenset(
    {Operation.MARKETPLACE_REFRESH, Operation.MARKETPLACE_HEAD, Operation.PLUGIN_LIST}
)
"""Claude plan operations whose public CLI takes no installation scope.

With `CLAUDE_SCOPE_BEARING_OPERATIONS` this partitions every Claude operation a
plan carries; the preflight inspections run outside any plan.
"""
CLAUDE_SCOPE_FLAG = "--scope"


class SourceAction(StrEnum):
    """What one agent's marketplace registration requires of the run.

    An absent registration is added from the invocation checkout's own
    declaration; a present one is refreshed as registered. The registry is the
    source of truth for where plugins come from, so no source is compared
    against a constant.
    """

    ADD = "add"
    REFRESH = "refresh"


@dataclass(frozen=True)
class RegisteredMarketplace:
    """One agent's registry entry for the marketplace: its rendered source and clone."""

    source: str
    install_location: Path | None


class AgentHomeAction(StrEnum):
    """One digest-guarded mutation in the selected Codex agent home."""

    CREATE = "create"
    REPLACE = "replace"
    PRUNE = "prune"


@dataclass(frozen=True)
class InstallationRoots:
    """Checkout, marketplace name, and explicitly selected agent-state roots."""

    checkout: Path
    marketplace: str
    """The marketplace's name as the checkout's committed catalog declares it."""
    state: Path | None
    home: Path
    claude_config: Path
    codex_home: Path
    codex_sqlite_home: Path | None


@dataclass(frozen=True, order=True)
class ClaudeInstallRecord:
    """One Claude Code install record: a plugin at one scope for one project path.

    Claude Code keys its install records by scope and project path. Persistent
    refresh moves the invocation checkout's own records through the native
    plugin update and every other project- or local-scope record of a cataloged
    plugin by rewriting its entry in the install-record document, so every
    record on the machine reaches the target without a command in its checkout.
    """

    plugin: str
    scope: str
    project_path: Path
    version: str = field(compare=False)
    """The version the listing reports for the record.

    Excluded from identity and ordering: Claude Code keys the record by plugin,
    scope, and project path, and the version is what a refresh moves.
    """


@dataclass(frozen=True, order=True)
class RecordRefresh:
    """One planned install record with the version it held before and after.

    Both versions come from the agent's own listings — the preflight listing
    the plan was built from and the closing listing the run reads after
    execution. An absent closing version means the record was no longer
    listed after execution.
    """

    record: ClaudeInstallRecord
    version_before: str
    version_after: str | None


@dataclass(frozen=True)
class RecordDrift:
    """What one run's closing listing says about the records it planned.

    `refreshed` pairs every planned record with its before and after versions;
    `unrefreshed` is every project- or local-scope record the closing listing
    reports that the plan did not carry — written by another agent session
    between the two reads, or left by a warning; `off_target` is every
    project- or local-scope record of a cataloged plugin the closing listing
    reports at a version other than the target, planned or not, which is the
    run's failure condition.
    """

    refreshed: tuple[RecordRefresh, ...]
    unrefreshed: tuple[ClaudeInstallRecord, ...]
    off_target: tuple[ClaudeInstallRecord, ...]


@dataclass(frozen=True)
class MarketplaceTarget:
    """The head every install record moves to: one commit and each plugin's version there."""

    commit: str
    versions: Mapping[str, str]


@dataclass(frozen=True, order=True)
class RecordRewrite:
    """One install-record entry the run rewrites to the target."""

    record: ClaudeInstallRecord
    install_path: Path
    version: str
    commit: str


@dataclass(frozen=True, order=True)
class PathlessInstallRecord:
    """A Claude Code install record that names no project path.

    A record at a scope outside project and local scope carries none — user
    scope today — and a refresh-scope entry that carries none is a listing
    defect the run reports as a blocking warning. Neither is refreshed,
    because a rewrite addresses an entry by scope and project path.
    """

    plugin: str
    scope: str


@dataclass(frozen=True, order=True)
class VersionlessInstallRecord:
    """A Claude Code install record whose listing entry reports no version.

    The entry names a scope and a project path, so a rewrite could address
    it, but the listing is the only source for what a record holds, so an
    entry reporting no version is a listing defect the run reports as a
    blocking warning and leaves unchanged — the same disposition a
    refresh-scope entry with no project path receives.
    """

    plugin: str
    scope: str
    project_path: Path


type ListedInstallRecord = (
    ClaudeInstallRecord | PathlessInstallRecord | VersionlessInstallRecord
)
"""One entry of Claude Code's install-record listing, defects included."""


@dataclass(frozen=True)
class InstallationCommand:
    """One ordered external operation in an installation plan."""

    agent: Agent
    operation: Operation
    plugin: str | None
    argv: tuple[str, ...]
    cwd: Path
    environment: tuple[tuple[str, str], ...]
    scope: str | None = None
    """The install-record scope the command addresses, where the agent keys one.

    Claude Code keys its records by scope, so a scope-bearing command names it
    here rather than leaving a reader to recover it from a position in `argv`.
    """
    source: str | None = None
    """The marketplace source a registration command carries, where it carries one."""


@dataclass(frozen=True)
class CommandResult:
    """Structured external-command result."""

    argv: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True, order=True)
class AgentDefinition:
    """One generated Codex agent definition selected by the committed catalog."""

    plugin: str
    source: Path
    destination: Path
    digest: str
    content: bytes


@dataclass(frozen=True, order=True)
class AgentOwnership:
    """One marketplace ownership claim over a selected-home destination."""

    destination: Path
    plugin: str
    digest: str


@dataclass(frozen=True, order=True)
class AgentHomeMutation:
    """One planned home mutation guarded by its preflight observation."""

    action: AgentHomeAction
    destination: Path
    plugin: str
    digest: str
    expected_digest: str | None
    content: bytes | None


@dataclass(frozen=True, order=True)
class AgentHomeCollision:
    """One destination preserved because marketplace ownership is insufficient."""

    destination: Path
    plugin: str
    reason: str


@dataclass(frozen=True)
class AgentHomePlan:
    """Immutable marketplace-wide reconciliation for one selected Codex home."""

    ownership_path: Path
    ownership_expected_digest: str | None
    mutations: tuple[AgentHomeMutation, ...]
    collisions: tuple[AgentHomeCollision, ...]
    ownership_after: tuple[AgentOwnership, ...]


@dataclass(frozen=True)
class AgentHomeResult:
    """Applied home mutations and preserved collisions from one installation."""

    written: tuple[Path, ...]
    pruned: tuple[Path, ...]
    collisions: tuple[AgentHomeCollision, ...]


class ScopeSplitClassification(StrEnum):
    """How one checkout definition relates to the selected home's shipped copy."""

    DIRECTED_REMOVAL = "directed-removal"
    SHADOWING_COLLISION = "shadowing-collision"


@dataclass(frozen=True, order=True)
class ScopeSplitEntry:
    """One checkout definition shadowing a selected-home plugin definition."""

    path: Path
    classification: ScopeSplitClassification


class ScopeSplitError(ValueError):
    """Checkout agent definitions shadow skills installed in the selected home."""

    def __init__(self, entries: tuple[ScopeSplitEntry, ...]) -> None:
        self.entries = entries
        removals = tuple(
            str(entry.path)
            for entry in entries
            if entry.classification is ScopeSplitClassification.DIRECTED_REMOVAL
        )
        collisions = tuple(
            str(entry.path)
            for entry in entries
            if entry.classification is ScopeSplitClassification.SHADOWING_COLLISION
        )
        super().__init__(
            "Codex agent scope split: selected-home plugin skills are shadowed; "
            f"remove byte-identical plugin copies {removals}; inspect changed or "
            f"unrecognized collisions {collisions}"
        )


class AgentHomeCollisionError(ValueError):
    """Selected-home destinations block complete marketplace reconciliation."""

    def __init__(self, collisions: tuple[AgentHomeCollision, ...]) -> None:
        self.collisions = collisions
        details = tuple(
            f"{collision.destination} ({collision.reason})" for collision in collisions
        )
        super().__init__(f"Codex agent-home collisions: {details}")


@dataclass(frozen=True)
class PersistentPreflight:
    """Validated persistent inputs and read-only inspection commands."""

    roots: InstallationRoots
    environment: tuple[tuple[str, str], ...]
    claude_plugins: tuple[str, ...]
    codex_plugins: tuple[str, ...]
    codex_agents: tuple[AgentDefinition, ...]
    inspections: tuple[InstallationCommand, ...]


@dataclass(frozen=True, order=True)
class InstallationWarning:
    """One non-terminal warning produced while selecting plugins or records.

    A blocking warning names a record the run could not bring to the target
    or could not judge — a listing defect, a plugin with no cached target, a
    bootstrap the invocation checkout's unreadable settings withhold — and
    fails the run's exit code without stopping its other work.
    """

    agent: Agent
    message: str
    blocking: bool = False


@dataclass(frozen=True)
class InstallationPlan:
    """Immutable catalog-derived installation plan."""

    mode: InstallationMode
    roots: InstallationRoots
    claude_plugins: tuple[str, ...]
    codex_plugins: tuple[str, ...]
    commands: tuple[InstallationCommand, ...]
    agent_home: AgentHomePlan
    warnings: tuple[InstallationWarning, ...] = ()
    claude_records: tuple[ClaudeInstallRecord, ...] = ()
    """The invocation checkout's own records, moved through the native update."""
    rewrite_records: tuple[ClaudeInstallRecord, ...] = ()
    """Every other project- or local-scope record of a cataloged plugin, moved by file rewrite."""
    closing: tuple[InstallationCommand, ...] = ()
    """The listing commands executed after every mutation, the run's postcondition read."""
    claude_clone: Path | None = None
    """The registered marketplace clone Claude Code keeps, where the target is read."""
    claude_source: str | None = None
    """The Claude marketplace source the run refreshes from or registers, as reported."""
    claude_catalog: tuple[str, ...] = ()
    """Every plugin the committed Claude catalog carries; the rewrite's target ranges over it."""


@dataclass(frozen=True, order=True)
class PendingPublication:
    """One plugin the agent's own refreshed marketplace has not published.

    The agent is carried because the two marketplaces refresh separately: the
    canonical branch can advance between them, leaving a plugin absent from one
    and installed by the other. A plugin name alone cannot say which.
    """

    agent: Agent
    plugin: str


@dataclass(frozen=True)
class InstallationReport:
    """Completed commands from one successful installation."""

    plan: InstallationPlan
    results: tuple[CommandResult, ...]
    pending_publication: tuple[PendingPublication, ...] = ()
    agent_home: AgentHomeResult | None = None
    record_drift: RecordDrift | None = None
    """The closing-listing comparison; None when the plan issued no closing listing."""
    rewrites: tuple[RecordRewrite, ...] = ()
    """The install-record entries the run rewrote to the target."""
    rewrite_warnings: tuple[InstallationWarning, ...] = ()
    """Records the run could not bring to the target, each named with its reason."""
    target: MarketplaceTarget | None = None
    """The head commit and per-plugin versions every record moves to; None without a registered clone."""

    def pending_for(self, agent: Agent) -> frozenset[str]:
        """The plugins this agent could not install because they are unpublished."""
        return frozenset(
            entry.plugin for entry in self.pending_publication if entry.agent is agent
        )

    def installed_for(self, agent: Agent) -> frozenset[str]:
        """The plugins this agent installed: what its plan carries, less what is pending.

        The selection says which plugins the run means to reach; the install
        and native-update commands its plan carries say which it does reach.
        The two part wherever a later condition withholds an agent's
        operations — unreadable invocation settings, or a registration this
        run cannot make — so this answers from the commands. Every reader of
        this report, the text summary and the JSON document alike, answers
        from here, so the two cannot disagree about whether a plugin was
        installed.
        """
        return frozenset(
            command.plugin
            for command in self.plan.commands
            if command.agent is agent
            and command.plugin is not None
            and command.operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_UPDATE}
        ) - self.pending_for(agent)

    def refreshed_claude_records(self) -> tuple[ClaudeInstallRecord, ...]:
        """The Claude install records this run moved: natively, then by rewrite.

        A record whose plugin the marketplace has not published is pending,
        so its update did not refresh it; a record the rewrite could not
        reach is reported in `rewrite_warnings`.
        """
        pending = self.pending_for(Agent.CLAUDE)
        rewritten = frozenset(rewrite.record for rewrite in self.rewrites)
        return tuple(
            record
            for record in (*self.plan.claude_records, *self.plan.rewrite_records)
            if record.plugin not in pending
            and (record in rewritten or record in self.plan.claude_records)
        )


class InstallationFailure(RuntimeError):
    """The first failed installation command and completed prefix."""

    def __init__(
        self,
        command: InstallationCommand,
        result: CommandResult,
        completed: tuple[CommandResult, ...],
    ) -> None:
        self.command = command
        self.result = result
        self.completed = completed
        super().__init__(
            f"{command.agent.value} {command.operation.value} failed for "
            f"{command.plugin or command.operation.value} with exit {result.exit_code}"
        )


class CommandRunner(Protocol):
    """Execute one command without shell interpretation."""

    def __call__(self, command: InstallationCommand) -> CommandResult: ...


class AgentAdapter(Protocol):
    """Build and normalize commands for one supported agent harness."""

    @property
    def agent(self) -> Agent: ...

    def commands(
        self,
        mode: InstallationMode,
        source_action: SourceAction,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        plugins: Sequence[str],
        records: Sequence[ClaudeInstallRecord] = (),
        recorded: frozenset[str] = frozenset(),
        clone: Path | None = None,
        bootstrap: bool = True,
        bootstrap_source: str | None = None,
    ) -> tuple[InstallationCommand, ...]: ...

    def closing(
        self,
        mode: InstallationMode,
        source_action: SourceAction,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        bootstrap_source: str | None = None,
    ) -> tuple[InstallationCommand, ...]: ...

    def normalize_result(
        self,
        command: InstallationCommand,
        result: CommandResult,
    ) -> CommandResult: ...


@dataclass(frozen=True)
class ClaudeInstallationAdapter:
    """Translate a Claude catalog into scoped CLI operations."""

    agent: Agent = Agent.CLAUDE

    def commands(
        self,
        mode: InstallationMode,
        source_action: SourceAction,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        plugins: Sequence[str],
        records: Sequence[ClaudeInstallRecord] = (),
        recorded: frozenset[str] = frozenset(),
        clone: Path | None = None,
        bootstrap: bool = True,
        bootstrap_source: str | None = None,
    ) -> tuple[InstallationCommand, ...]:
        scope = (
            CLAUDE_PROJECT_SCOPE
            if mode is InstallationMode.PERSISTENT
            else CLAUDE_USER_SCOPE
        )
        registering = (
            mode is InstallationMode.PERSISTENT and source_action is SourceAction.ADD
        )
        source = bootstrap_source if registering else str(roots.checkout)
        if source is None:
            # The registration this run would perform has no source, and every
            # command below names the marketplace that registration would
            # carry: the source commands, the bootstrap install and enable,
            # and the native update of each record the invocation checkout
            # holds. The whole Claude plan is therefore withheld and the
            # caller reports it. The install-record rewrite and the closing
            # listing name no marketplace, so the machine-wide refresh runs
            # on without them.
            return ()
        commands: list[InstallationCommand] = list(
            _claude_source_commands(source_action, source, scope, roots, environment)
        )
        for plugin in plugins:
            if plugin in recorded or not bootstrap:
                continue
            plugin_id = marketplace_plugin_identifier(plugin, roots.marketplace)
            commands.append(
                _command(
                    self.agent,
                    Operation.PLUGIN_INSTALL,
                    plugin,
                    _claude_argv(
                        Operation.PLUGIN_INSTALL,
                        "plugin",
                        "install",
                        plugin_id,
                        scope=scope,
                    ),
                    roots,
                    environment,
                    scope=scope,
                )
            )
            commands.append(
                _command(
                    self.agent,
                    Operation.PLUGIN_ENABLE,
                    plugin,
                    _claude_argv(
                        Operation.PLUGIN_ENABLE,
                        "plugin",
                        "enable",
                        plugin_id,
                        scope=scope,
                    ),
                    roots,
                    environment,
                    scope=scope,
                )
            )
        for record in records:
            commands.append(
                _command(
                    self.agent,
                    Operation.PLUGIN_UPDATE,
                    record.plugin,
                    _claude_argv(
                        Operation.PLUGIN_UPDATE,
                        "plugin",
                        "update",
                        marketplace_plugin_identifier(record.plugin, roots.marketplace),
                        scope=record.scope,
                    ),
                    roots,
                    environment,
                    scope=record.scope,
                )
            )
        if clone is not None:
            commands.append(
                _command(
                    self.agent,
                    Operation.MARKETPLACE_HEAD,
                    None,
                    (GIT_EXECUTABLE, "-C", str(clone), *GIT_HEAD_ARGUMENTS),
                    roots,
                    environment,
                )
            )
        return tuple(commands)

    def closing(
        self,
        mode: InstallationMode,
        source_action: SourceAction,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        bootstrap_source: str | None = None,
    ) -> tuple[InstallationCommand, ...]:
        # The install-record listing is the machine-wide refresh's
        # postcondition read over records this run never registered, so a
        # withheld registration never withholds it.
        del mode, source_action, bootstrap_source
        return (
            _command(
                self.agent,
                Operation.PLUGIN_LIST,
                None,
                CLAUDE_LIST_COMMAND,
                roots,
                environment,
            ),
        )

    def normalize_result(
        self,
        command: InstallationCommand,
        result: CommandResult,
    ) -> CommandResult:
        already_satisfied = (
            command.operation is Operation.PLUGIN_INSTALL
            and CLAUDE_ALREADY_INSTALLED_FRAGMENT in result.stderr.lower()
        ) or (
            command.operation is Operation.PLUGIN_ENABLE
            and CLAUDE_ALREADY_ENABLED_FRAGMENT in result.stderr.lower()
        )
        if result.exit_code != 0 and already_satisfied:
            return CommandResult(result.argv, 0, result.stdout, result.stderr)
        return result


@dataclass(frozen=True)
class CodexInstallationAdapter:
    """Translate a Codex catalog into selected-home CLI operations."""

    agent: Agent = Agent.CODEX

    def commands(
        self,
        mode: InstallationMode,
        source_action: SourceAction,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        plugins: Sequence[str],
        records: Sequence[ClaudeInstallRecord] = (),
        recorded: frozenset[str] = frozenset(),
        clone: Path | None = None,
        bootstrap: bool = True,
        bootstrap_source: str | None = None,
    ) -> tuple[InstallationCommand, ...]:
        # Codex keys no install record by project path, so the shared
        # signature's Claude records, clone, and bootstrap switch carry
        # nothing for this adapter.
        del records, recorded, clone, bootstrap
        source = self._source(mode, source_action, roots, bootstrap_source)
        if source is None:
            # The registration this run would perform has no source, and every
            # Codex plugin operation installs from that registration, so the
            # whole Codex plan is withheld and the caller reports it.
            return ()
        commands = list(
            _codex_source_commands(source_action, source, roots, environment)
        )
        for plugin in plugins:
            commands.append(
                _command(
                    self.agent,
                    Operation.PLUGIN_INSTALL,
                    plugin,
                    (
                        CODEX_EXECUTABLE,
                        "plugin",
                        "add",
                        marketplace_plugin_identifier(plugin, roots.marketplace),
                        "--json",
                    ),
                    roots,
                    environment,
                )
            )
        return tuple(commands)

    def closing(
        self,
        mode: InstallationMode,
        source_action: SourceAction,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        bootstrap_source: str | None = None,
    ) -> tuple[InstallationCommand, ...]:
        if self._source(mode, source_action, roots, bootstrap_source) is None:
            # The listing names the marketplace this run withheld, so it fails
            # the same way every withheld operation would; the withheld plan's
            # blocking warning is what the run reports instead.
            return ()
        return (
            _command(
                self.agent,
                Operation.PLUGIN_LIST,
                None,
                codex_list_command(roots.marketplace),
                roots,
                environment,
            ),
        )

    @staticmethod
    def _source(
        mode: InstallationMode,
        source_action: SourceAction,
        roots: InstallationRoots,
        bootstrap_source: str | None,
    ) -> str | None:
        """The source this run's Codex operations resolve against, or None.

        A persistent run that registers the marketplace installs from the
        source the invocation checkout declares; every other run installs
        from the checkout itself. A registering run with no declared source
        resolves nothing, and every Codex operation — the plan's and the
        closing listing's alike — names a marketplace that run never
        registered.
        """
        registering = (
            mode is InstallationMode.PERSISTENT and source_action is SourceAction.ADD
        )
        return bootstrap_source if registering else str(roots.checkout)

    def normalize_result(
        self,
        command: InstallationCommand,
        result: CommandResult,
    ) -> CommandResult:
        return result


AGENT_ADAPTERS: tuple[AgentAdapter, ...] = (
    ClaudeInstallationAdapter(),
    CodexInstallationAdapter(),
)


def build_isolated_installation_plan(
    checkout: Path,
    state_root: Path,
    base_environment: Mapping[str, str],
    *,
    claude_plugins: Sequence[str] | None = None,
    codex_plugins: Sequence[str] | None = None,
) -> InstallationPlan:
    """Build an isolated plan rooted beneath caller-selected disposable state."""
    resolved_checkout = checkout.resolve(strict=True)
    resolved_state = state_root.resolve()
    roots = InstallationRoots(
        checkout=resolved_checkout,
        marketplace=catalog_marketplace_name(resolved_checkout / CLAUDE_CATALOG_PATH),
        state=resolved_state,
        home=resolved_state / "home",
        claude_config=resolved_state / "claude",
        codex_home=resolved_state / "codex",
        codex_sqlite_home=resolved_state / "codex-sqlite",
    )
    environment = isolated_environment(roots, base_environment)
    claude_catalog = catalog_plugin_names(roots.checkout / CLAUDE_CATALOG_PATH)
    codex_catalog = catalog_plugin_names(roots.checkout / CODEX_CATALOG_PATH)
    selected_claude = _isolated_selection(
        Agent.CLAUDE,
        claude_catalog,
        claude_plugins,
    )
    selected_codex = _isolated_selection(
        Agent.CODEX,
        codex_catalog,
        codex_plugins,
    )
    return _build_plan(
        InstallationMode.ISOLATED,
        roots,
        environment,
        SourceAction.ADD,
        SourceAction.ADD,
        claude_plugins=selected_claude,
        codex_plugins=selected_codex,
    )


def build_persistent_preflight(
    checkout: Path,
    base_environment: Mapping[str, str],
) -> PersistentPreflight:
    """Validate persistent state boundaries before any state-changing command."""
    roots = persistent_roots(checkout, base_environment)
    environment = persistent_environment(roots, base_environment)
    codex_plugins = catalog_plugin_names(roots.checkout / CODEX_CATALOG_PATH)
    codex_agents = generated_codex_agent_definitions(
        roots.checkout,
        roots.codex_home,
        codex_plugins,
    )
    _reject_scope_split(roots.checkout, codex_plugins, codex_agents)
    inspections = (
        _command(
            Agent.CLAUDE,
            Operation.MARKETPLACE_INSPECT,
            None,
            CLAUDE_MARKETPLACE_LIST_COMMAND,
            roots,
            environment,
        ),
        _command(
            Agent.CLAUDE,
            Operation.PLUGIN_INSPECT,
            None,
            CLAUDE_LIST_COMMAND,
            roots,
            environment,
        ),
        _command(
            Agent.CODEX,
            Operation.MARKETPLACE_INSPECT,
            None,
            CODEX_MARKETPLACE_LIST_COMMAND,
            roots,
            environment,
        ),
        _command(
            Agent.CODEX,
            Operation.PLUGIN_INSPECT,
            None,
            codex_list_command(roots.marketplace),
            roots,
            environment,
        ),
    )
    return PersistentPreflight(
        roots=roots,
        environment=environment,
        claude_plugins=catalog_plugin_names(roots.checkout / CLAUDE_CATALOG_PATH),
        codex_plugins=codex_plugins,
        codex_agents=codex_agents,
        inspections=inspections,
    )


def _unmoved_record_warnings(
    records: Sequence[ClaudeInstallRecord],
    template: str,
) -> tuple[InstallationWarning, ...]:
    """One blocking warning per install record the run leaves where it found it."""
    return tuple(
        InstallationWarning(
            agent=Agent.CLAUDE,
            message=template.format(
                plugin=record.plugin,
                scope=record.scope,
                project_path=record.project_path,
                version=record.version,
            ),
            blocking=True,
        )
        for record in records
    )


def build_persistent_installation_plan(
    preflight: PersistentPreflight,
    *,
    claude_marketplace_payload: str,
    claude_plugins_payload: str,
    codex_marketplace_payload: str,
    codex_plugins_payload: str,
) -> InstallationPlan:
    """Build a persistent plan from validated inputs and live agent CLI state.

    The checkout's committed settings declare the marketplace source, but a
    fresh agent home has no marketplace to refresh: the declared action holds
    only where the live listing carries the marketplace, and an absent live
    marketplace is added regardless of the declaration. Those settings are a
    bootstrap input alone: a document that cannot be read, or that declares no
    source, withholds the registration that needs it and is reported, while
    every other install record on the machine is still refreshed.
    """
    marketplace = preflight.roots.marketplace
    claude_registered = claude_registered_marketplace(
        claude_marketplace_payload, marketplace
    )
    claude_action = (
        SourceAction.ADD if claude_registered is None else SourceAction.REFRESH
    )
    if claude_registered is not None and claude_registered.install_location is None:
        raise ValueError(
            f"{UNLOCATED_REGISTRY_DIAGNOSTIC}: Claude Code registers `{marketplace}` "
            f"from {claude_registered.source} but names no install location"
        )
    codex_registered = codex_registered_marketplace(
        codex_marketplace_payload, marketplace
    )
    codex_action = (
        SourceAction.ADD if codex_registered is None else SourceAction.REFRESH
    )
    declared_source, declared_source_error = _declared_bootstrap_source(
        preflight.roots.checkout,
        marketplace,
        needed=claude_registered is None or codex_registered is None,
    )
    claude_source = (
        declared_source if claude_registered is None else claude_registered.source
    )
    codex_bootstrap_source = (
        None if declared_source is None else codex_source_form(declared_source)
    )
    withheld_warnings = tuple(
        InstallationWarning(
            agent=agent,
            message=WITHHELD_REGISTRATION_WARNING.format(
                diagnostic=declared_source_error,
                marketplace=marketplace,
            ),
            blocking=True,
        )
        for agent, registered in (
            (Agent.CLAUDE, claude_registered),
            (Agent.CODEX, codex_registered),
        )
        if declared_source_error is not None and registered is None
    )
    claude_installed = installed_plugin_names(
        Agent.CLAUDE,
        claude_plugins_payload,
        checkout=preflight.roots.checkout,
        marketplace=marketplace,
    )
    claude_selection, claude_bootstrapping = _persistent_selection(
        Agent.CLAUDE,
        preflight.claude_plugins,
        claude_installed,
        marketplace,
    )
    codex_selection, codex_bootstrapping = _persistent_selection(
        Agent.CODEX,
        preflight.codex_plugins,
        installed_plugin_names(
            Agent.CODEX,
            codex_plugins_payload,
            checkout=preflight.roots.checkout,
            marketplace=marketplace,
        ),
        marketplace,
    )
    native_records, rewrite_records, record_warnings = claude_refresh_records(
        claude_install_records(claude_plugins_payload, marketplace),
        preflight.claude_plugins,
        preflight.roots.checkout,
    )
    if claude_source is None:
        # The withheld registration withholds the native update of every
        # record the invocation checkout holds, because that command names
        # the marketplace this run never registers; with no registration
        # there is also no clone to read a target from, so no record moves.
        record_warnings = (
            *record_warnings,
            *_unmoved_record_warnings(
                (*native_records, *rewrite_records), WITHHELD_TARGET_RECORD_WARNING
            ),
        )
        native_records = ()
        rewrite_records = ()
    elif claude_registered is None:
        record_warnings = (
            *record_warnings,
            *_unmoved_record_warnings(rewrite_records, UNREGISTERED_TARGET_WARNING),
        )
        rewrite_records = ()
    settings_error = invocation_settings_error(preflight.roots.checkout)
    settings_warning = (
        None
        if settings_error is None
        else InstallationWarning(
            agent=Agent.CLAUDE,
            message=UNREADABLE_SETTINGS_WARNING.format(diagnostic=settings_error),
            blocking=any(plugin not in claude_installed for plugin in claude_selection),
        )
    )
    plan = _build_plan(
        InstallationMode.PERSISTENT,
        preflight.roots,
        preflight.environment,
        claude_action,
        codex_action,
        claude_plugins=claude_selection,
        codex_plugins=codex_selection,
        codex_agents=tuple(
            agent for agent in preflight.codex_agents if agent.plugin in codex_selection
        ),
        warnings=tuple(
            warning
            for warning in (
                settings_warning,
                *withheld_warnings,
                *record_warnings,
            )
            if warning is not None
        ),
        claude_records=native_records,
        claude_recorded=claude_installed,
        claude_bootstrap=settings_error is None,
        rewrite_records=rewrite_records,
        claude_clone=(
            None if claude_registered is None else claude_registered.install_location
        ),
        claude_source=claude_source,
        claude_catalog=preflight.claude_plugins,
        claude_bootstrap_source=declared_source,
        codex_bootstrap_source=codex_bootstrap_source,
    )
    first_install = _first_install_warnings(
        plan,
        {Agent.CLAUDE: claude_bootstrapping, Agent.CODEX: codex_bootstrapping},
        marketplace,
    )
    if not first_install:
        return plan
    return replace(plan, warnings=(*first_install, *plan.warnings))


def execute_persistent_installation(
    checkout: Path,
    base_environment: Mapping[str, str],
    runner: CommandRunner,
) -> InstallationReport:
    """Inspect selected persistent state, then reconcile and install it.

    The checkout's committed plugin selection is read before installing and
    re-applied afterwards, on a successful run and on one that fails partway.
    Installing a plugin activates it in the scope, so the selection would
    otherwise widen to the whole catalog. Only the selection is re-applied:
    the marketplace source the run reconciles lives in the same document and
    must survive.
    """
    preflight = build_persistent_preflight(checkout, base_environment)
    inspection_results: list[CommandResult] = []
    inspection_payloads: dict[tuple[Agent, Operation], str] = {}
    for inspection in preflight.inspections:
        result = _checked_result(inspection, runner(inspection))
        if result.exit_code != 0:
            raise InstallationFailure(
                inspection,
                result,
                tuple(inspection_results),
            )
        inspection_results.append(result)
        inspection_payloads[(inspection.agent, inspection.operation)] = result.stdout
    plan = build_persistent_installation_plan(
        preflight,
        claude_marketplace_payload=inspection_payloads[
            (Agent.CLAUDE, Operation.MARKETPLACE_INSPECT)
        ],
        claude_plugins_payload=inspection_payloads[
            (Agent.CLAUDE, Operation.PLUGIN_INSPECT)
        ],
        codex_marketplace_payload=inspection_payloads[
            (Agent.CODEX, Operation.MARKETPLACE_INSPECT)
        ],
        codex_plugins_payload=inspection_payloads[
            (Agent.CODEX, Operation.PLUGIN_INSPECT)
        ],
    )
    settings = checkout / CLAUDE_PROJECT_SETTINGS_PATH
    # Unreadable settings withhold the bootstrap install that would widen the
    # selection, so there is nothing to re-apply for such a checkout.
    declared = (
        None
        if invocation_settings_error(checkout) is not None
        else _declared_plugin_selection(settings)
    )
    try:
        return execute_installation(plan, runner, completed=tuple(inspection_results))
    finally:
        _restore_plugin_selection(settings, declared)


@dataclass(frozen=True)
class DeclaredSelection:
    """A checkout's plugin selection, and whether the checkout declares one."""

    present: bool
    value: object


def _selection_of(document: Mapping[str, object]) -> DeclaredSelection:
    return DeclaredSelection(
        present=CLAUDE_ENABLED_PLUGINS_FIELD in document,
        value=document.get(CLAUDE_ENABLED_PLUGINS_FIELD),
    )


def _declared_plugin_selection(settings: Path) -> DeclaredSelection | None:
    """Read the plugin selection a checkout's project settings declare."""
    if not settings.exists():
        return None
    return _selection_of(_settings_document(settings))


def _restore_plugin_selection(
    settings: Path,
    declared: DeclaredSelection | None,
) -> None:
    """Re-apply a declared plugin selection, leaving the rest of the document.

    The checkout's settings document belongs to the operator and the agent,
    not to this run, so the selection is applied to the document as it stands
    at the write boundary and the file is replaced atomically: a reader never
    observes a truncated settings document, and every field written while the
    run was in flight survives.
    """
    if declared is None or not settings.exists():
        return
    document = _settings_document(settings)
    if _selection_of(document) == declared:
        return
    if declared.present:
        document[CLAUDE_ENABLED_PLUGINS_FIELD] = declared.value
    else:
        document.pop(CLAUDE_ENABLED_PLUGINS_FIELD, None)
    _atomic_write(settings, (json.dumps(document, indent=2) + "\n").encode("utf-8"))


def _build_plan(
    mode: InstallationMode,
    roots: InstallationRoots,
    environment: tuple[tuple[str, str], ...],
    claude_action: SourceAction,
    codex_action: SourceAction,
    *,
    claude_plugins: tuple[str, ...],
    codex_plugins: tuple[str, ...],
    codex_agents: tuple[AgentDefinition, ...] | None = None,
    warnings: tuple[InstallationWarning, ...] = (),
    claude_records: tuple[ClaudeInstallRecord, ...] = (),
    claude_recorded: frozenset[str] = frozenset(),
    claude_bootstrap: bool = True,
    rewrite_records: tuple[ClaudeInstallRecord, ...] = (),
    claude_clone: Path | None = None,
    claude_source: str | None = None,
    claude_catalog: tuple[str, ...] = (),
    claude_bootstrap_source: str | None = None,
    codex_bootstrap_source: str | None = None,
) -> InstallationPlan:
    selected_codex_agents = (
        generated_codex_agent_definitions(
            roots.checkout,
            roots.codex_home,
            codex_plugins,
        )
        if codex_agents is None
        else codex_agents
    )
    _reject_scope_split(roots.checkout, codex_plugins, selected_codex_agents)
    plugins_by_agent = {
        Agent.CLAUDE: claude_plugins,
        Agent.CODEX: codex_plugins,
    }
    actions = {Agent.CLAUDE: claude_action, Agent.CODEX: codex_action}
    bootstrap_sources = {
        Agent.CLAUDE: claude_bootstrap_source,
        Agent.CODEX: codex_bootstrap_source,
    }
    commands = tuple(
        command
        for adapter in AGENT_ADAPTERS
        for command in adapter.commands(
            mode,
            actions[adapter.agent],
            roots,
            environment,
            plugins_by_agent[adapter.agent],
            claude_records,
            claude_recorded,
            claude_clone,
            claude_bootstrap,
            bootstrap_sources[adapter.agent],
        )
    )
    closing = tuple(
        command
        for adapter in AGENT_ADAPTERS
        for command in adapter.closing(
            mode,
            actions[adapter.agent],
            roots,
            environment,
            bootstrap_sources[adapter.agent],
        )
    )
    agent_home = build_agent_home_plan(
        roots.codex_home,
        selected_codex_agents,
    )
    if agent_home.collisions:
        raise AgentHomeCollisionError(agent_home.collisions)
    return InstallationPlan(
        mode=mode,
        roots=roots,
        claude_plugins=claude_plugins,
        codex_plugins=codex_plugins,
        commands=commands,
        agent_home=agent_home,
        warnings=warnings,
        claude_records=claude_records,
        rewrite_records=rewrite_records,
        closing=closing,
        claude_clone=claude_clone,
        claude_source=claude_source,
        claude_catalog=claude_catalog,
    )


def claude_install_records(
    payload: str, marketplace: str
) -> tuple[ListedInstallRecord, ...]:
    """Parse every install record of the marketplace one Claude Code listing reports.

    A project- or local-scope entry that names no project path, and an entry
    that reports no version, are listing defects; each is kept as its own
    record kind so the run reports it and continues with every other record.
    """
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid claude plugin listing: {error}") from error
    if not isinstance(document, list):
        raise ValueError("claude plugin listing must contain an array")
    records: list[ListedInstallRecord] = []
    for index, entry in enumerate(document):
        record = _claude_install_record(index, entry, marketplace)
        if record is not None:
            records.append(record)
    return tuple(records)


def _claude_install_record(
    index: int, entry: object, marketplace: str
) -> ListedInstallRecord | None:
    """Parse one listing entry; None for an entry from another marketplace.

    A defect the run can report and continue past — an entry with no project
    path, or one with no version — becomes the record kind that carries that
    defect; only an entry whose plugin identity, scope, or project-path type
    the listing contract itself breaks stops the parse.
    """
    if not isinstance(entry, dict):
        raise ValueError(f"claude plugin listing entry {index} must be an object")
    identifier = entry.get(CLAUDE_PLUGIN_ID_FIELD)
    if not isinstance(identifier, str):
        raise ValueError(f"claude plugin listing entry {index} has no typed identity")
    plugin = marketplace_plugin_name(identifier, marketplace)
    if plugin is None:
        return None
    scope = entry.get(CLAUDE_PLUGIN_SCOPE_FIELD)
    if not isinstance(scope, str):
        raise ValueError(f"claude plugin listing entry {index} has no typed scope")
    project_path = entry.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD)
    if project_path is None:
        return PathlessInstallRecord(plugin=plugin, scope=scope)
    if not isinstance(project_path, str):
        raise ValueError(
            f"claude plugin listing entry {index} has an untyped project path"
        )
    resolved_path = Path(project_path).expanduser().resolve()
    version = entry.get(CLAUDE_PLUGIN_VERSION_FIELD)
    if not isinstance(version, str):
        return VersionlessInstallRecord(
            plugin=plugin, scope=scope, project_path=resolved_path
        )
    return ClaudeInstallRecord(
        plugin=plugin,
        scope=scope,
        project_path=resolved_path,
        version=version,
    )


def compare_install_listings(
    refreshed: Sequence[ClaudeInstallRecord],
    after: Sequence[ListedInstallRecord],
    target: MarketplaceTarget | None,
) -> RecordDrift:
    """Pair every refreshed record with its closing version and judge the rest.

    A pure comparison over typed records: each refreshed record's version
    before is the one its preflight listing entry carried, its version after
    is the one the closing listing carries for the same plugin, scope, and
    project path; every project- or local-scope record the closing listing
    reports outside the refreshed set is unrefreshed — a record the plan
    warned about, one whose plugin turned out pending publication, or one
    another agent session wrote between the two reads; and every project- or
    local-scope record of a plugin the target names whose closing version is
    not the target's is off target, whatever the plan did with it. A run that
    registers the marketplace itself has no target, so nothing is off one:
    every record it left unmoved is still reported as unrefreshed, and the
    blocking warning that run raises is what makes its exit nonzero. The
    comparison reads nothing but its arguments.
    """
    closing = {
        record: record for record in after if isinstance(record, ClaudeInstallRecord)
    }
    refreshes = tuple(
        RecordRefresh(
            record=record,
            version_before=record.version,
            version_after=(closing[record].version if record in closing else None),
        )
        for record in refreshed
    )
    refreshed_identities = frozenset(refreshed)
    unrefreshed = tuple(
        record
        for record in closing
        if record.scope in CLAUDE_REFRESH_SCOPES and record not in refreshed_identities
    )
    off_target = (
        ()
        if target is None
        else tuple(
            record
            for record in closing
            if record.scope in CLAUDE_REFRESH_SCOPES
            and record.plugin in target.versions
            and record.version != target.versions[record.plugin]
        )
    )
    return RecordDrift(
        refreshed=refreshes, unrefreshed=unrefreshed, off_target=off_target
    )


def claude_refresh_records(
    records: Sequence[ListedInstallRecord],
    catalog: Sequence[str],
    checkout: Path,
) -> tuple[
    tuple[ClaudeInstallRecord, ...],
    tuple[ClaudeInstallRecord, ...],
    tuple[InstallationWarning, ...],
]:
    """Split Claude install records into native updates, file rewrites, and warnings.

    A project- or local-scope record of a cataloged plugin in the invocation
    checkout moves through the native update, which fetches the target into
    the shared cache; every other project- or local-scope record of a
    cataloged plugin moves by a rewrite of its install-record entry, whether
    or not its project directory still exists, so no command runs in another
    checkout. A record outside the catalog, or outside project and local
    scope, is reported and left unchanged; a refresh-scope entry with no
    project path, and an entry the listing reports with no version, are
    listing defects reported the same way. Both moved sets follow catalog
    order, then project path, then scope, so the plan is stable across
    listings.
    """
    resolved_checkout = checkout.resolve()
    native: list[ClaudeInstallRecord] = []
    rewrites: list[ClaudeInstallRecord] = []
    warnings: list[InstallationWarning] = []
    for record in records:
        if isinstance(record, VersionlessInstallRecord):
            if record.scope in CLAUDE_REFRESH_SCOPES:
                warnings.append(
                    InstallationWarning(
                        agent=Agent.CLAUDE,
                        message=VERSIONLESS_LISTING_ENTRY_WARNING.format(
                            plugin=record.plugin,
                            scope=record.scope,
                            project_path=record.project_path,
                        ),
                        blocking=True,
                    )
                )
                continue
            warnings.append(
                InstallationWarning(
                    agent=Agent.CLAUDE,
                    message=OUT_OF_SCOPE_RECORD_WARNING.format(
                        plugin=record.plugin,
                        scope=record.scope,
                        project_path=record.project_path,
                    ),
                )
            )
            continue
        if isinstance(record, PathlessInstallRecord):
            if record.scope in CLAUDE_REFRESH_SCOPES:
                warnings.append(
                    InstallationWarning(
                        agent=Agent.CLAUDE,
                        message=PATHLESS_LISTING_ENTRY_WARNING.format(
                            plugin=record.plugin, scope=record.scope
                        ),
                        blocking=True,
                    )
                )
                continue
            message = PATHLESS_OUT_OF_SCOPE_RECORD_WARNING.format(
                plugin=record.plugin, scope=record.scope
            )
        elif record.scope not in CLAUDE_REFRESH_SCOPES:
            message = OUT_OF_SCOPE_RECORD_WARNING.format(
                plugin=record.plugin,
                scope=record.scope,
                project_path=record.project_path,
            )
        elif record.plugin not in catalog:
            message = UNCATALOGED_RECORD_WARNING.format(
                plugin=record.plugin,
                scope=record.scope,
                project_path=record.project_path,
            )
        elif record.project_path == resolved_checkout:
            native.append(record)
            continue
        else:
            rewrites.append(record)
            continue
        warnings.append(InstallationWarning(agent=Agent.CLAUDE, message=message))

    def order(record: ClaudeInstallRecord) -> tuple[int, str, str]:
        return (
            catalog.index(record.plugin),
            str(record.project_path),
            record.scope,
        )

    native.sort(key=order)
    rewrites.sort(key=order)
    return tuple(native), tuple(rewrites), tuple(warnings)


def installed_plugin_names(
    agent: Agent,
    payload: str,
    *,
    checkout: Path,
    marketplace: str,
) -> frozenset[str]:
    """Parse one agent's installed inventory of the marketplace for its scope.

    Claude Code's inventory is every record at project or local scope for the
    invocation checkout, the two scopes persistent refresh updates natively,
    read through the same record parser the refresh consumes; Codex's is the
    selected home's marketplace entries.
    """
    if agent is Agent.CLAUDE:
        resolved_checkout = checkout.resolve()
        return frozenset(
            record.plugin
            for record in claude_install_records(payload, marketplace)
            if isinstance(record, ClaudeInstallRecord)
            and record.scope in CLAUDE_REFRESH_SCOPES
            and record.project_path == resolved_checkout
        )
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid {agent.value} plugin listing: {error}") from error
    if not isinstance(document, dict):
        raise ValueError("Codex plugin listing must be a JSON object")
    entries = document.get(CODEX_PLUGIN_ENTRIES_FIELD)
    if not isinstance(entries, list):
        raise ValueError(f"{agent.value} plugin listing must contain an array")

    installed: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{agent.value} plugin listing entry {index} must be an object"
            )
        identifier = entry.get(CODEX_PLUGIN_ID_FIELD)
        if not isinstance(identifier, str):
            raise ValueError(
                f"{agent.value} plugin listing entry {index} has no typed identity"
            )
        plugin = marketplace_plugin_name(identifier, marketplace)
        if plugin is None:
            continue
        listed_marketplace = entry.get(CODEX_PLUGIN_MARKETPLACE_FIELD)
        if not isinstance(listed_marketplace, str):
            raise ValueError(
                f"Codex plugin listing entry {index} has no typed marketplace"
            )
        if listed_marketplace != marketplace:
            continue
        installed.add(plugin)
    return frozenset(installed)


def _isolated_selection(
    agent: Agent,
    catalog: tuple[str, ...],
    requested: Sequence[str] | None,
) -> tuple[str, ...]:
    selection = catalog if requested is None else tuple(requested)
    unknown = frozenset(selection) - frozenset(catalog)
    if unknown:
        raise ValueError(
            f"invalid {agent.value} isolated selection: plugins absent from the "
            f"committed catalog: {', '.join(sorted(unknown))}"
        )
    if SPEC_TREE_PLUGIN not in selection:
        raise ValueError(
            f"invalid {agent.value} isolated selection: `{SPEC_TREE_PLUGIN}` is required"
        )
    selected = frozenset(selection)
    return tuple(plugin for plugin in catalog if plugin in selected)


def _persistent_selection(
    agent: Agent,
    catalog: tuple[str, ...],
    installed: frozenset[str],
    marketplace: str,
) -> tuple[tuple[str, ...], bool]:
    """One agent's selection and whether an empty inventory proposed the bootstrap.

    The empty inventory proposes the bootstrap; it does not decide it. A
    later condition — unreadable invocation settings, or a registration this
    run cannot make — can withhold the install that proposal names, so the
    flag travels to the plan and the first-install warning is raised from
    what the plan carries rather than from the inventory read here.
    """
    if SPEC_TREE_PLUGIN not in catalog:
        raise ValueError(
            f"invalid {agent.value} catalog: `{SPEC_TREE_PLUGIN}` is required"
        )
    if not installed:
        return (SPEC_TREE_PLUGIN,), True
    if SPEC_TREE_PLUGIN not in installed:
        raise ValueError(
            f"invalid {agent.value} installed selection: nonempty {marketplace} "
            f"inventory must include `{SPEC_TREE_PLUGIN}`"
        )
    return tuple(plugin for plugin in catalog if plugin in installed), False


def _first_install_warnings(
    plan: InstallationPlan,
    bootstrapping: Mapping[Agent, bool],
    marketplace: str,
) -> tuple[InstallationWarning, ...]:
    """One first-install warning per agent whose plan carries the bootstrap install.

    The warning announces an install, so it reads the install commands the
    plan carries. An agent whose bootstrap the run withholds issues none of
    them and announces nothing; the condition that withheld the bootstrap
    carries its own warning.
    """
    installing = frozenset(
        command.agent
        for command in plan.commands
        if command.operation is Operation.PLUGIN_INSTALL
    )
    return tuple(
        InstallationWarning(
            agent=agent,
            message=FIRST_INSTALL_WARNING.format(
                marketplace=marketplace,
                agent=agent.value,
                plugin=SPEC_TREE_PLUGIN,
            ),
        )
        for agent in Agent
        if bootstrapping.get(agent, False) and agent in installing
    )


def persistent_roots(
    checkout: Path,
    base_environment: Mapping[str, str],
) -> InstallationRoots:
    """Resolve persistent roots from the active environment."""
    home = _required_environment_path(base_environment, HOME_ENV)
    codex_home = _required_environment_path(base_environment, CODEX_HOME_ENV)
    claude_config = Path(
        base_environment.get(CLAUDE_CONFIG_ENV, str(home / ".claude"))
    ).expanduser()
    sqlite_value = base_environment.get(CODEX_SQLITE_HOME_ENV)
    resolved_checkout = checkout.resolve(strict=True)
    return InstallationRoots(
        checkout=resolved_checkout,
        marketplace=catalog_marketplace_name(resolved_checkout / CLAUDE_CATALOG_PATH),
        state=None,
        home=home.resolve(),
        claude_config=claude_config.resolve(),
        codex_home=codex_home.resolve(),
        codex_sqlite_home=(
            Path(sqlite_value).expanduser().resolve() if sqlite_value else None
        ),
    )


def catalog_plugin_names(catalog_path: Path) -> tuple[str, ...]:
    """Read and validate ordered plugin names from one committed catalog."""
    try:
        document = cast(object, json.loads(catalog_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"invalid marketplace catalog {catalog_path}: {error}"
        ) from error
    if not isinstance(document, dict):
        raise ValueError(f"marketplace catalog {catalog_path} must be a JSON object")
    plugins = document.get(CATALOG_PLUGINS_FIELD)
    if not isinstance(plugins, list):
        raise ValueError(
            f"marketplace catalog {catalog_path} must contain a plugins array"
        )
    names: list[str] = []
    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            raise ValueError(
                f"marketplace catalog {catalog_path} plugin {index} must be an object"
            )
        name = plugin.get(CATALOG_PLUGIN_NAME_FIELD)
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"marketplace catalog {catalog_path} plugin {index} has no name"
            )
        names.append(name)
    if len(set(names)) != len(names):
        raise ValueError(f"marketplace catalog {catalog_path} contains duplicate names")
    return tuple(names)


def generated_codex_agent_definitions(
    checkout: Path,
    codex_home: Path,
    plugins: Sequence[str],
) -> tuple[AgentDefinition, ...]:
    """Read every catalog plugin's generated Codex agent definitions."""
    agents_root = codex_home / CODEX_HOME_AGENTS_PATH
    definitions: list[AgentDefinition] = []
    destinations: dict[Path, Path] = {}
    for plugin in plugins:
        source_root = (
            checkout
            / DIST_DIR_NAME
            / Agent.CODEX.value
            / plugin
            / SKILLS_SUBDIR_NAME
            / f"{plugin}-plugin"
            / AGENTS_SUBDIR_NAME
        )
        for source in sorted(source_root.glob("*.toml")):
            destination = agents_root / source.name
            prior = destinations.get(destination)
            if prior is not None:
                raise ValueError(
                    "generated Codex agent destination collision: "
                    f"{prior} and {source} both claim {destination}"
                )
            destinations[destination] = source
            content = source.read_bytes()
            definitions.append(
                AgentDefinition(
                    plugin=plugin,
                    source=source,
                    destination=destination,
                    digest=_digest(content),
                    content=content,
                )
            )
    return tuple(sorted(definitions))


def _reject_scope_split(
    checkout: Path,
    plugins: Sequence[str],
    definitions: Sequence[AgentDefinition],
) -> None:
    entries = checkout_scope_split_entries(checkout, plugins, definitions)
    if entries:
        raise ScopeSplitError(entries)


def checkout_scope_split_entries(
    checkout: Path,
    plugins: Sequence[str],
    definitions: Sequence[AgentDefinition],
) -> tuple[ScopeSplitEntry, ...]:
    """Classify checkout definitions that shadow selected-home plugin skills."""
    shipped_content = {definition.content for definition in definitions}
    plugin_names = frozenset(plugins)
    entries: list[ScopeSplitEntry] = []
    for path in sorted((checkout / CODEX_AGENTS_PATH).glob("*.toml")):
        if path.is_symlink():
            entries.append(
                ScopeSplitEntry(path, ScopeSplitClassification.SHADOWING_COLLISION)
            )
            continue
        content = path.read_bytes()
        if content in shipped_content:
            entries.append(
                ScopeSplitEntry(path, ScopeSplitClassification.DIRECTED_REMOVAL)
            )
            continue
        if _checkout_agent_mentions_plugin(path, content, plugin_names):
            entries.append(
                ScopeSplitEntry(path, ScopeSplitClassification.SHADOWING_COLLISION)
            )
    return tuple(entries)


def _checkout_agent_mentions_plugin(
    path: Path,
    content: bytes,
    plugins: frozenset[str],
) -> bool:
    if any(
        path.stem.startswith(f"{plugin}_") or path.stem.startswith(f"{plugin}-")
        for plugin in plugins
    ):
        return True
    try:
        document = tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    skills = document.get(AGENT_SKILLS_FIELD)
    if not isinstance(skills, dict):
        return False
    config = skills.get(AGENT_SKILLS_CONFIG_FIELD)
    if not isinstance(config, list):
        return False
    return any(
        isinstance(entry, dict)
        and isinstance(name := entry.get(AGENT_SKILL_NAME_FIELD), str)
        and name.partition(":")[0] in plugins
        for entry in config
    )


def build_agent_home_plan(
    codex_home: Path,
    definitions: Sequence[AgentDefinition],
) -> AgentHomePlan:
    """Plan catalog-wide reconciliation from digest-bound ownership."""
    agents_root = codex_home / CODEX_HOME_AGENTS_PATH
    if agents_root.is_symlink():
        raise ValueError(
            f"selected Codex agent directory must not be a symlink: {agents_root}"
        )
    ownership_path = agents_root / AGENT_OWNERSHIP_FILENAME
    if ownership_path.is_symlink():
        raise ValueError(
            f"agent ownership record must be a regular file: {ownership_path}"
        )
    ownership_expected_digest = (
        _digest(ownership_path.read_bytes()) if ownership_path.is_file() else None
    )
    ownership = {
        entry.destination: entry for entry in _read_agent_ownership(codex_home)
    }
    desired = {definition.destination: definition for definition in definitions}
    mutations: list[AgentHomeMutation] = []
    collisions: list[AgentHomeCollision] = []
    ownership_after: dict[Path, AgentOwnership] = dict(ownership)

    for destination, definition in desired.items():
        recorded = ownership.get(destination)
        destination_present = destination.exists() or destination.is_symlink()
        current_digest = _path_digest(destination)
        if not destination_present:
            mutations.append(
                AgentHomeMutation(
                    action=AgentHomeAction.CREATE,
                    destination=destination,
                    plugin=definition.plugin,
                    digest=definition.digest,
                    expected_digest=None,
                    content=definition.content,
                )
            )
            ownership_after[destination] = AgentOwnership(
                destination,
                definition.plugin,
                definition.digest,
            )
            continue
        if current_digest is None:
            collisions.append(
                AgentHomeCollision(
                    destination,
                    definition.plugin,
                    "destination exists but is not a regular file",
                )
            )
            continue
        if recorded is None:
            if current_digest == definition.digest:
                ownership_after[destination] = AgentOwnership(
                    destination,
                    definition.plugin,
                    definition.digest,
                )
                continue
            collisions.append(
                AgentHomeCollision(
                    destination,
                    definition.plugin,
                    "destination is occupied without marketplace ownership",
                )
            )
            continue
        if current_digest != recorded.digest:
            collisions.append(
                AgentHomeCollision(
                    destination,
                    recorded.plugin,
                    "destination bytes differ from the recorded installed digest",
                )
            )
            continue
        if current_digest != definition.digest:
            mutations.append(
                AgentHomeMutation(
                    action=AgentHomeAction.REPLACE,
                    destination=destination,
                    plugin=definition.plugin,
                    digest=definition.digest,
                    expected_digest=current_digest,
                    content=definition.content,
                )
            )
        ownership_after[destination] = AgentOwnership(
            destination,
            definition.plugin,
            definition.digest,
        )

    for destination, recorded in ownership.items():
        if destination in desired:
            continue
        destination_present = destination.exists() or destination.is_symlink()
        current_digest = _path_digest(destination)
        if not destination_present:
            ownership_after.pop(destination, None)
            continue
        if current_digest is None:
            collisions.append(
                AgentHomeCollision(
                    destination,
                    recorded.plugin,
                    "retired destination exists but is not a regular file",
                )
            )
            continue
        if current_digest != recorded.digest:
            collisions.append(
                AgentHomeCollision(
                    destination,
                    recorded.plugin,
                    "retired destination bytes differ from the recorded installed digest",
                )
            )
            continue
        mutations.append(
            AgentHomeMutation(
                action=AgentHomeAction.PRUNE,
                destination=destination,
                plugin=recorded.plugin,
                digest=recorded.digest,
                expected_digest=current_digest,
                content=None,
            )
        )
        ownership_after.pop(destination, None)

    return AgentHomePlan(
        ownership_path=ownership_path,
        ownership_expected_digest=ownership_expected_digest,
        mutations=tuple(sorted(mutations)),
        collisions=tuple(sorted(collisions)),
        ownership_after=tuple(sorted(ownership_after.values())),
    )


def apply_agent_home_plan(plan: AgentHomePlan) -> AgentHomeResult:
    """Apply one preflighted home reconciliation without widening ownership."""
    if plan.collisions:
        raise AgentHomeCollisionError(plan.collisions)
    ownership_present = plan.ownership_path.exists() or plan.ownership_path.is_symlink()
    if plan.ownership_expected_digest is None and ownership_present:
        raise ValueError(
            f"agent ownership changed after preflight: {plan.ownership_path}"
        )
    if (
        plan.ownership_expected_digest is not None
        and _path_digest(plan.ownership_path) != plan.ownership_expected_digest
    ):
        raise ValueError(
            f"agent ownership changed after preflight: {plan.ownership_path}"
        )
    for mutation in plan.mutations:
        destination_present = (
            mutation.destination.exists() or mutation.destination.is_symlink()
        )
        if mutation.expected_digest is None and destination_present:
            raise ValueError(
                f"agent destination changed after preflight: {mutation.destination}"
            )
        if (
            mutation.expected_digest is not None
            and _path_digest(mutation.destination) != mutation.expected_digest
        ):
            raise ValueError(
                f"agent destination changed after preflight: {mutation.destination}"
            )

    written: list[Path] = []
    pruned: list[Path] = []
    for mutation in plan.mutations:
        if mutation.action is AgentHomeAction.PRUNE:
            mutation.destination.unlink()
            pruned.append(mutation.destination)
            continue
        if mutation.content is None:
            raise ValueError(f"agent write has no content: {mutation.destination}")
        _atomic_write(mutation.destination, mutation.content)
        written.append(mutation.destination)

    ownership_content = _agent_ownership_content(
        plan.ownership_path.parent.parent,
        plan.ownership_after,
    )
    if _path_bytes(plan.ownership_path) != ownership_content:
        _atomic_write(plan.ownership_path, ownership_content)
    return AgentHomeResult(
        written=tuple(written),
        pruned=tuple(pruned),
        collisions=plan.collisions,
    )


def _read_agent_ownership(codex_home: Path) -> tuple[AgentOwnership, ...]:
    ownership_path = codex_home / CODEX_HOME_AGENTS_PATH / AGENT_OWNERSHIP_FILENAME
    if not ownership_path.exists() and not ownership_path.is_symlink():
        return ()
    if ownership_path.is_symlink():
        raise ValueError(
            f"agent ownership record must be a regular file: {ownership_path}"
        )
    try:
        document = cast(
            object,
            json.loads(ownership_path.read_text(encoding="utf-8")),
        )
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"invalid agent ownership record {ownership_path}: {error}"
        ) from error
    if not isinstance(document, dict):
        raise ValueError(f"agent ownership record {ownership_path} must be an object")
    if document.get(AGENT_OWNERSHIP_SCHEMA_FIELD) != AGENT_OWNERSHIP_SCHEMA_VERSION:
        raise ValueError(
            f"agent ownership record {ownership_path} has an unsupported schema"
        )
    values = document.get(AGENT_OWNERSHIP_ENTRIES_FIELD)
    if not isinstance(values, list):
        raise ValueError(
            f"agent ownership record {ownership_path} must contain an entries array"
        )
    entries: list[AgentOwnership] = []
    seen: set[Path] = set()
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise ValueError(
                f"agent ownership record {ownership_path} entry {index} must be an object"
            )
        destination_value = value.get(AGENT_OWNERSHIP_DESTINATION_FIELD)
        plugin = value.get(AGENT_OWNERSHIP_PLUGIN_FIELD)
        digest = value.get(AGENT_OWNERSHIP_DIGEST_FIELD)
        if not isinstance(destination_value, str):
            raise ValueError(
                f"agent ownership record {ownership_path} entry {index} has no destination"
            )
        relative_destination = Path(destination_value)
        if (
            relative_destination.is_absolute()
            or len(relative_destination.parts) != 2
            or relative_destination.parts[0] != CODEX_HOME_AGENTS_PATH.name
            or relative_destination.suffix != ".toml"
        ):
            raise ValueError(
                f"agent ownership record {ownership_path} entry {index} has an invalid destination"
            )
        destination = codex_home / relative_destination
        if not isinstance(plugin, str) or not plugin:
            raise ValueError(
                f"agent ownership record {ownership_path} entry {index} has no plugin"
            )
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(
                f"agent ownership record {ownership_path} entry {index} has an invalid digest"
            )
        if destination in seen:
            raise ValueError(
                f"agent ownership record {ownership_path} repeats {destination}"
            )
        seen.add(destination)
        entries.append(AgentOwnership(destination, plugin, digest))
    return tuple(sorted(entries))


def _agent_ownership_content(
    codex_home: Path,
    entries: Sequence[AgentOwnership],
) -> bytes:
    document = {
        AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
        AGENT_OWNERSHIP_ENTRIES_FIELD: [
            {
                AGENT_OWNERSHIP_DESTINATION_FIELD: str(
                    entry.destination.relative_to(codex_home)
                ),
                AGENT_OWNERSHIP_PLUGIN_FIELD: entry.plugin,
                AGENT_OWNERSHIP_DIGEST_FIELD: entry.digest,
            }
            for entry in entries
        ],
    }
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _path_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() and not path.is_symlink() else None


def _path_digest(path: Path) -> str | None:
    content = _path_bytes(path)
    return _digest(content) if content is not None else None


def codex_registered_marketplace(
    payload: str, marketplace: str
) -> RegisteredMarketplace | None:
    """Read the selected Codex home's registry entry for the marketplace, or None."""
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid Codex marketplace listing: {error}") from error
    if not isinstance(document, dict):
        raise ValueError("Codex marketplace listing must be a JSON object")
    marketplaces = document.get(CODEX_MARKETPLACES_FIELD)
    if not isinstance(marketplaces, list):
        raise ValueError("Codex marketplace listing must contain a marketplaces array")
    for entry in marketplaces:
        if not isinstance(entry, dict):
            raise ValueError("Codex marketplace listing contains a non-object")
        if entry.get(CODEX_MARKETPLACE_NAME_FIELD) != marketplace:
            continue
        source = entry.get(CODEX_MARKETPLACE_SOURCE_FIELD)
        if not isinstance(source, dict):
            raise ValueError(
                f"Codex marketplace listing entry `{marketplace}` has no typed source"
            )
        source_value = source.get(CODEX_SOURCE_FIELD)
        if not isinstance(source_value, str):
            raise ValueError(
                f"Codex marketplace listing entry `{marketplace}` has no typed source"
            )
        return RegisteredMarketplace(source=source_value, install_location=None)
    return None


def isolated_environment(
    roots: InstallationRoots,
    base_environment: Mapping[str, str],
) -> tuple[tuple[str, str], ...]:
    """Redirect every state-bearing environment variable beneath isolated state."""
    if roots.state is None or roots.codex_sqlite_home is None:
        raise ValueError("isolated installation requires disposable state roots")
    environment = {
        name: value
        for name, value in base_environment.items()
        if name not in STATE_ENV_NAMES
    }
    environment.update(
        {
            HOME_ENV: str(roots.home),
            CLAUDE_CONFIG_ENV: str(roots.claude_config),
            CODEX_HOME_ENV: str(roots.codex_home),
            CODEX_SQLITE_HOME_ENV: str(roots.codex_sqlite_home),
        }
    )
    return tuple(sorted(environment.items()))


def persistent_environment(
    roots: InstallationRoots,
    base_environment: Mapping[str, str],
) -> tuple[tuple[str, str], ...]:
    """Carry the selected persistent roots explicitly to every command."""
    environment = dict(base_environment)
    environment.update(
        {
            HOME_ENV: str(roots.home),
            CLAUDE_CONFIG_ENV: str(roots.claude_config),
            CODEX_HOME_ENV: str(roots.codex_home),
        }
    )
    if roots.codex_sqlite_home is not None:
        environment[CODEX_SQLITE_HOME_ENV] = str(roots.codex_sqlite_home)
    return tuple(sorted(environment.items()))


def _is_pending_publication(
    plan: InstallationPlan,
    command: InstallationCommand,
    result: CommandResult,
) -> bool:
    """Whether a failed plugin operation names a plugin the source has not published.

    A persistent run installs from the canonical marketplace, so a checkout whose
    committed catalog is ahead of that marketplace declares plugins it cannot yet
    install — every changeset that adds a plugin is in exactly that state until it
    merges. That is the checkout leading its published source, not a failure.

    An isolated run registers the checkout itself as the marketplace, so the same
    message there means the catalog and the built tree disagree, which is a defect
    and stays terminal.
    """
    return (
        plan.mode is InstallationMode.PERSISTENT
        and command.operation in PLUGIN_OPERATIONS
        and command.plugin is not None
        and UNPUBLISHED_PLUGIN_FRAGMENT in result.stderr.lower()
    )


def execute_installation(
    plan: InstallationPlan,
    runner: CommandRunner,
    *,
    completed: tuple[CommandResult, ...] = (),
) -> InstallationReport:
    """Execute plan order and stop at the first failed operation."""
    if plan.mode is InstallationMode.ISOLATED:
        _create_isolated_roots(plan.roots)
    results = list(completed)
    pending: list[PendingPublication] = []
    head: str | None = None
    for command in plan.commands:
        result = _run_command(plan, command, runner, results, pending)
        if command.operation is Operation.MARKETPLACE_HEAD:
            head = result.stdout.strip() if result.exit_code == 0 else None
    target: MarketplaceTarget | None = None
    rewrites: tuple[RecordRewrite, ...] = ()
    rewrite_warnings: tuple[InstallationWarning, ...] = ()
    if plan.mode is InstallationMode.PERSISTENT:
        target, rewrites, rewrite_warnings = _rewrite_records(plan, head, pending)
    closing_results: list[CommandResult] = []
    for command in plan.closing:
        closing_results.append(_run_command(plan, command, runner, results, pending))
    agent_home = apply_agent_home_plan(plan.agent_home)
    return InstallationReport(
        plan=plan,
        results=tuple(results),
        pending_publication=tuple(pending),
        agent_home=agent_home,
        record_drift=_record_drift(plan, closing_results, rewrites, pending, target),
        rewrites=rewrites,
        rewrite_warnings=rewrite_warnings,
        target=target,
    )


def _run_command(
    plan: InstallationPlan,
    command: InstallationCommand,
    runner: CommandRunner,
    results: list[CommandResult],
    pending: list[PendingPublication],
) -> CommandResult:
    result = _checked_result(command, runner(command))
    result = _agent_adapter(command.agent).normalize_result(command, result)
    if result.exit_code != 0 and command.operation not in REPORTED_FAILURE_OPERATIONS:
        if not _is_pending_publication(plan, command, result):
            raise InstallationFailure(command, result, tuple(results))
        if command.plugin is not None:
            entry = PendingPublication(command.agent, command.plugin)
            if entry not in pending:
                pending.append(entry)
    results.append(result)
    return result


def _rewrite_records(
    plan: InstallationPlan,
    head: str | None,
    pending: Sequence[PendingPublication],
) -> tuple[
    MarketplaceTarget | None,
    tuple[RecordRewrite, ...],
    tuple[InstallationWarning, ...],
]:
    """Bring every planned rewrite record to the target in the install-record file.

    The target is read from the registered clone at the head the run just
    read; the rewrite is planned as a pure function and written once at this
    edge. A plan with no clone — the bootstrap case, where nothing was
    registered before this run — carries no target and no rewrite record, so
    the drift comparison reports every record that run left unmoved as
    unrefreshed and the plan's blocking warning names each of them.

    A plugin the clone resolves no target version for is reported over every
    record the run carries, the invocation checkout's native records
    included, because the supply defect is the plugin's rather than one
    record's. A plugin whose absence from the registered source is
    established is pending publication instead — one of the two conditions
    this run continues past — so its records stay out of every disposition.

    The other is a head the read resolved nothing for: the registered
    location is no git working tree, or the read failed. That leaves the
    whole run without a target rather than one plugin without a version, so
    every carried record is reported against no target and none is rewritten.
    """
    if plan.claude_clone is None:
        return None, (), ()
    unpublished = frozenset(
        entry.plugin for entry in pending if entry.agent is Agent.CLAUDE
    )
    if head is None:
        return (
            None,
            (),
            unreadable_head_warnings(
                tuple(
                    record
                    for record in (*plan.claude_records, *plan.rewrite_records)
                    if record.plugin not in unpublished
                )
            ),
        )
    target = marketplace_target(plan.claude_clone, head, plan.claude_catalog)
    cache_root = (
        plan.roots.claude_config / CLAUDE_PLUGIN_CACHE_RELATIVE / plan.roots.marketplace
    )
    carried = tuple(
        record
        for record in (*plan.claude_records, *plan.rewrite_records)
        if record.plugin not in unpublished
    )
    candidates = tuple(
        record for record in plan.rewrite_records if record.plugin not in unpublished
    )
    unresolved = unresolved_target_warnings(carried, target)
    rewrites, warnings = plan_install_record_rewrite(
        candidates,
        target,
        cache_root,
        cached_plugin_versions(cache_root, plan.claude_catalog),
    )
    written, write_warnings = rewrite_install_records(
        plan.roots.claude_config / CLAUDE_INSTALLED_PLUGINS_RELATIVE,
        rewrites,
        plan.roots.marketplace,
    )
    return target, written, (*unresolved, *warnings, *write_warnings)


def _record_drift(
    plan: InstallationPlan,
    closing_results: Sequence[CommandResult],
    rewrites: Sequence[RecordRewrite],
    pending: Sequence[PendingPublication],
    target: MarketplaceTarget | None,
) -> RecordDrift | None:
    """Compare a persistent plan against the Claude closing listing.

    The closing listing is the persistent machine-wide refresh's postcondition
    read, so an isolated plan carries no drift; its result sits at the same
    offset among the closing results as its command among the plan's closing
    commands. A planned native record whose plugin is pending publication
    received no refresh, and a rewrite record the run could not rewrite is
    unrefreshed; both are judged against the target like every other record.
    A run that registers the marketplace itself reaches no target, and it
    reports its drift too: every record it left unmoved is unrefreshed, and
    each record it did move carries the version it held and the version the
    closing listing carries.
    """
    if plan.mode is not InstallationMode.PERSISTENT:
        return None
    unpublished = frozenset(
        entry.plugin for entry in pending if entry.agent is Agent.CLAUDE
    )
    refreshed = (
        *(record for record in plan.claude_records if record.plugin not in unpublished),
        *(rewrite.record for rewrite in rewrites),
    )
    for offset, command in enumerate(plan.closing):
        if command.agent is Agent.CLAUDE and command.operation is Operation.PLUGIN_LIST:
            return compare_install_listings(
                refreshed,
                claude_install_records(
                    closing_results[offset].stdout, plan.roots.marketplace
                ),
                target,
            )
    return None


def installation_exit_code(report: InstallationReport) -> int:
    """The exit code one completed run reports, as a pure function of its report.

    Two sources between them cover every condition the run reports: the drift
    comparison names each record left off the target, and the blocking
    warnings the plan and the rewrite raise name every condition no record
    carries. Either one makes the run's exit nonzero.
    """
    off_target = report.record_drift.off_target if report.record_drift else ()
    blocking = any(
        warning.blocking
        for warning in (*report.plan.warnings, *report.rewrite_warnings)
    )
    return 1 if off_target or blocking else 0


def main(
    argv: Sequence[str] | None = None,
    *,
    base_environment: Mapping[str, str] | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Install persistently by default or verify in an explicit isolated root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(CHECKOUT_OPTION, type=Path, default=Path.cwd())
    parser.add_argument(STATE_ROOT_OPTION, type=Path)
    parser.add_argument(JSON_OUTPUT_OPTION, action="store_true", dest="json_output")
    arguments = parser.parse_args(argv)
    environment = os.environ if base_environment is None else base_environment
    command_runner = _real_runner if runner is None else runner
    try:
        if arguments.state_root is None:
            report = execute_persistent_installation(
                arguments.checkout,
                environment,
                command_runner,
            )
        else:
            plan = build_isolated_installation_plan(
                arguments.checkout,
                arguments.state_root,
                environment,
            )
            report = execute_installation(plan, command_runner)
    except InstallationFailure as failure:
        print(json.dumps(_failure_document(failure), sort_keys=True), file=sys.stderr)
        return failure.result.exit_code
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, sort_keys=True), file=sys.stderr)
        return 1
    for warning in (*report.plan.warnings, *report.rewrite_warnings):
        print(f"warning: {warning.message}", file=sys.stderr)
    off_target = report.record_drift.off_target if report.record_drift else ()
    if arguments.json_output:
        print(json.dumps(report_document(report), sort_keys=True))
    else:
        print(f"installed {len(report.installed_for(Agent.CLAUDE))} Claude plugins")
        print(
            f"refreshed {len(report.refreshed_claude_records())} Claude Code "
            "install records"
        )
        print(f"installed {len(report.installed_for(Agent.CODEX))} Codex plugins")
        for entry in report.pending_publication:
            print(
                f"pending publication, not installed: {entry.plugin} ({entry.agent.value})"
            )
    for record in off_target:
        print(
            f"error: {OFF_TARGET_DIAGNOSTIC}: {record.plugin} at {record.scope} scope "
            f"for {record.project_path} lists {record.version}",
            file=sys.stderr,
        )
    return installation_exit_code(report)


def _claude_argv(operation: Operation, *words: str, scope: str) -> tuple[str, ...]:
    """Build one Claude CLI argv, appending the scope only where the CLI takes it."""
    argv = (CLAUDE_EXECUTABLE, *words)
    if operation in CLAUDE_SCOPE_BEARING_OPERATIONS:
        return (*argv, CLAUDE_SCOPE_FLAG, scope)
    if operation not in CLAUDE_SCOPELESS_OPERATIONS:
        raise ValueError(f"{operation.value} has no Claude Code scope disposition")
    return argv


def _claude_source_commands(
    action: SourceAction,
    source: str,
    scope: str,
    roots: InstallationRoots,
    environment: tuple[tuple[str, str], ...],
) -> tuple[InstallationCommand, ...]:
    commands: list[InstallationCommand] = []
    if action is SourceAction.ADD:
        commands.append(
            _command(
                Agent.CLAUDE,
                Operation.MARKETPLACE_ADD,
                None,
                _claude_argv(
                    Operation.MARKETPLACE_ADD,
                    "plugin",
                    "marketplace",
                    "add",
                    source,
                    scope=scope,
                ),
                roots,
                environment,
                scope=scope,
                source=source,
            )
        )
    else:
        commands.append(
            _command(
                Agent.CLAUDE,
                Operation.MARKETPLACE_REFRESH,
                None,
                _claude_argv(
                    Operation.MARKETPLACE_REFRESH,
                    "plugin",
                    "marketplace",
                    "update",
                    roots.marketplace,
                    scope=scope,
                ),
                roots,
                environment,
                scope=scope,
            )
        )
    return tuple(commands)


def _codex_source_commands(
    action: SourceAction,
    source: str,
    roots: InstallationRoots,
    environment: tuple[tuple[str, str], ...],
) -> tuple[InstallationCommand, ...]:
    commands: list[InstallationCommand] = []
    if action is SourceAction.ADD:
        commands.append(
            _command(
                Agent.CODEX,
                Operation.MARKETPLACE_ADD,
                None,
                (
                    CODEX_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "add",
                    source,
                    "--json",
                ),
                roots,
                environment,
                source=source,
            )
        )
    else:
        commands.append(
            _command(
                Agent.CODEX,
                Operation.MARKETPLACE_REFRESH,
                None,
                (
                    CODEX_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "upgrade",
                    roots.marketplace,
                    "--json",
                ),
                roots,
                environment,
            )
        )
    return tuple(commands)


def _settings_document(path: Path) -> dict[str, object]:
    """Read one settings document; a missing document is empty, any other failure unreadable."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise ValueError(f"{UNREADABLE_SETTINGS_DIAGNOSTIC} {path}: {error}") from error
    try:
        document = cast(object, json.loads(text))
    except json.JSONDecodeError as error:
        raise ValueError(f"{UNREADABLE_SETTINGS_DIAGNOSTIC} {path}: {error}") from error
    if not isinstance(document, dict):
        raise ValueError(
            f"{UNREADABLE_SETTINGS_DIAGNOSTIC} {path}: must be a JSON object"
        )
    return document


def _marketplace_entry(
    document: Mapping[str, object], marketplace: str
) -> object | None:
    marketplaces = document.get(EXTRA_MARKETPLACES_FIELD)
    if marketplaces is None:
        return None
    if not isinstance(marketplaces, dict):
        raise ValueError(f"{EXTRA_MARKETPLACES_FIELD} must be a JSON object")
    return marketplaces.get(marketplace)


CLAUDE_SETTINGS_PRECEDENCE: tuple[Path, ...] = (
    CLAUDE_LOCAL_SETTINGS_PATH,
    CLAUDE_PROJECT_SETTINGS_PATH,
)
"""A checkout's Claude Code settings documents, highest precedence first.

Claude Code lets the local document override the shared project document, so
a marketplace the local document declares is the one a session in that
checkout resolves against.
"""


def claude_registered_marketplace(
    payload: str, marketplace: str
) -> RegisteredMarketplace | None:
    """Read the machine registry's entry for the marketplace from one listing, or None.

    The entry is the source the run refreshes from and reports; its install
    location is the clone whose head becomes the target every record moves to.
    """
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid claude marketplace listing: {error}") from error
    if not isinstance(document, list):
        raise ValueError("claude marketplace listing must be a JSON array")
    for entry in document:
        if not isinstance(entry, dict):
            raise ValueError("claude marketplace listing contains a non-object")
        name = entry.get(CLAUDE_MARKETPLACE_NAME_FIELD)
        if not isinstance(name, str):
            raise ValueError("claude marketplace listing entry lacks a typed name")
        if name != marketplace:
            continue
        location = entry.get(CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD)
        return RegisteredMarketplace(
            source=render_claude_source(entry),
            install_location=(
                Path(location).expanduser() if isinstance(location, str) else None
            ),
        )
    return None


def render_claude_source(entry: Mapping[str, object]) -> str:
    """Render a Claude marketplace source as the CLI's `marketplace add` argument.

    A GitHub source is its `owner/repo`, a git source its URL, a directory
    source its path — the three forms `claude plugin marketplace add` takes —
    and any other shape its JSON, so the report names the source in the form
    the registry carries.
    """
    source_type = entry.get(CLAUDE_SOURCE_FIELD)
    repository = entry.get(CLAUDE_REPOSITORY_FIELD)
    url = entry.get(CLAUDE_URL_FIELD)
    directory = entry.get(CLAUDE_DIRECTORY_FIELD)
    if source_type == CLAUDE_GITHUB_SOURCE_TYPE and isinstance(repository, str):
        return repository
    if source_type == CLAUDE_GIT_SOURCE_TYPE and isinstance(url, str):
        return url
    if source_type == CLAUDE_DIRECTORY_SOURCE_TYPE and isinstance(directory, str):
        return directory
    return json.dumps(
        {
            key: value
            for key, value in entry.items()
            if key
            not in (
                CLAUDE_MARKETPLACE_NAME_FIELD,
                CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD,
            )
        },
        sort_keys=True,
    )


def invocation_settings_error(checkout: Path) -> str | None:
    """The diagnostic for the first invocation-checkout settings document that cannot be read.

    Only bootstrap reads those documents: a source to register and a selection
    to re-apply after the install that widens it. Every other record on the
    machine is refreshed without them, so an unreadable document is reported
    and withholds the bootstrap alone.
    """
    for relative in CLAUDE_SETTINGS_PRECEDENCE:
        try:
            _settings_document(checkout / relative)
        except ValueError as error:
            return str(error)
    return None


def declared_claude_source(checkout: Path, marketplace: str) -> str:
    """The marketplace source the invocation checkout's own settings declare.

    Read in Claude Code's precedence order, local before project; the first
    declaration decides. Bootstrap registers this source, so a checkout that
    declares none cannot bootstrap.
    """
    for relative in CLAUDE_SETTINGS_PRECEDENCE:
        entry = _marketplace_entry(_settings_document(checkout / relative), marketplace)
        if isinstance(entry, dict):
            source = entry.get(CLAUDE_SOURCE_FIELD)
            if isinstance(source, dict):
                return render_claude_source(source)
    raise ValueError(f"{UNDECLARED_SOURCE_DIAGNOSTIC}: {checkout}")


def codex_source_form(source: str) -> str:
    """The Codex spelling of one Claude Code marketplace source.

    A GitHub `owner/repo` becomes its HTTPS URL; a directory or git URL is used as is.
    """
    if claude_source_type(source) == CLAUDE_GITHUB_SOURCE_TYPE:
        return f"https://github.com/{source}"
    return source


def declared_codex_source(checkout: Path, marketplace: str) -> str:
    """The Codex form of the source the invocation checkout declares for Claude Code."""
    return codex_source_form(declared_claude_source(checkout, marketplace))


def _declared_bootstrap_source(
    checkout: Path,
    marketplace: str,
    *,
    needed: bool,
) -> tuple[str | None, str | None]:
    """The source a bootstrap registration would use, or the diagnostic withholding it.

    The invocation checkout's settings are a bootstrap input alone. A document
    that cannot be read, or that declares no source for this marketplace,
    withholds the registration that needs it rather than stopping the run: the
    machine-wide refresh of every other install record reads no settings and
    stays performable. A run that needs no registration reads nothing.
    """
    if not needed:
        return None, None
    try:
        return declared_claude_source(checkout, marketplace), None
    except ValueError as error:
        return None, str(error)


GIT_URL_SCHEMES = ("http", "https", "ssh", "git")
"""The schemes a registered marketplace source may name.

Recognition, not selection: the run classifies a string the agent's own
registry carries and fetches nothing over any of them. Each is spelled as
its scheme alone and joined to its separator below, so no line here reads
as a URL this module uses.
"""
GIT_SCHEME_SEPARATOR = "://"
GIT_HOST_PREFIX = "git@"
GIT_URL_PREFIXES = (
    *(f"{scheme}{GIT_SCHEME_SEPARATOR}" for scheme in GIT_URL_SCHEMES),
    GIT_HOST_PREFIX,
)
GIT_URL_SUFFIX = ".git"
PATH_PREFIXES = ("/", ".", "~")


def claude_source_type(source: str) -> str:
    """Classify one `marketplace add` argument as the source type Claude Code records.

    One grammar for every reader: a URL scheme, `git@` host, or `.git` suffix
    is a git source; an `owner/repo` shorthand is a GitHub source; anything
    else — a path, whatever its prefix — is a directory source.
    """
    if source.startswith(GIT_URL_PREFIXES) or source.endswith(GIT_URL_SUFFIX):
        return CLAUDE_GIT_SOURCE_TYPE
    if "/" in source and not source.startswith(PATH_PREFIXES):
        return CLAUDE_GITHUB_SOURCE_TYPE
    return CLAUDE_DIRECTORY_SOURCE_TYPE


def marketplace_target(
    clone: Path, commit: str, catalog: Sequence[str]
) -> MarketplaceTarget:
    """Read the target every record moves to from the registered clone at `commit`.

    Each cataloged plugin's version is the one its manifest carries in the
    clone, found through the clone's own catalog entry for that plugin. A
    plugin the clone's catalog names no source for, or whose manifest the
    clone cannot supply or does not version, resolves to no target version
    and is left out; every project- or local-scope record of it — the
    invocation checkout's own included — is reported as unresolved and the
    run continues, because one plugin's supply defect settles nothing about
    the rest of the machine's records. A clone catalog the run cannot read at
    all resolves no plugin, so it stops the run.
    """
    catalog_path = clone / CLAUDE_CATALOG_PATH
    try:
        catalog_document = cast(
            object, json.loads(catalog_path.read_text(encoding="utf-8"))
        )
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"invalid marketplace clone catalog {catalog_path}: {error}"
        ) from error
    if not isinstance(catalog_document, dict):
        raise ValueError(
            f"marketplace clone catalog {catalog_path} must be a JSON object"
        )
    sources: dict[str, str] = {}
    plugins = catalog_document.get(CATALOG_PLUGINS_FIELD)
    for plugin in plugins if isinstance(plugins, list) else ():
        if isinstance(plugin, dict):
            name = plugin.get(CATALOG_PLUGIN_NAME_FIELD)
            source = plugin.get(CATALOG_PLUGIN_SOURCE_FIELD)
            if isinstance(name, str) and isinstance(source, str):
                sources[name] = source
    versions: dict[str, str] = {}
    for plugin in catalog:
        source = sources.get(plugin)
        if source is None:
            continue
        manifest_path = clone / source / PLUGIN_MANIFEST_RELATIVE
        try:
            manifest = cast(
                object, json.loads(manifest_path.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError):
            continue
        version = (
            manifest.get(PLUGIN_MANIFEST_VERSION_FIELD)
            if isinstance(manifest, dict)
            else None
        )
        if not isinstance(version, str):
            continue
        versions[plugin] = version
    return MarketplaceTarget(commit=commit, versions=versions)


def unreadable_head_warnings(
    records: Sequence[ClaudeInstallRecord],
) -> tuple[InstallationWarning, ...]:
    """One blocking warning per record a run whose head read resolved nothing carries.

    The domain is every project- or local-scope record of a cataloged plugin
    the run carries — the invocation checkout's own, which the native update
    has already moved, beside every record the rewrite would have moved —
    because no head means no target for any plugin rather than a defect in
    one plugin's supply.

    This is the whole domain's only path to the exit code. The drift
    comparison judges a record against its plugin's target version, and this
    run has none for any plugin, so a run that left the disposition to the
    comparison would exit zero having refreshed nothing.
    """
    return tuple(
        InstallationWarning(
            agent=Agent.CLAUDE,
            message=UNREADABLE_HEAD_RECORD_WARNING.format(
                plugin=record.plugin,
                scope=record.scope,
                project_path=record.project_path,
            ),
            blocking=True,
        )
        for record in records
    )


def unresolved_target_warnings(
    records: Sequence[ClaudeInstallRecord],
    target: MarketplaceTarget,
) -> tuple[InstallationWarning, ...]:
    """One blocking warning per record whose plugin resolves to no target version.

    The domain is every project- or local-scope record of a cataloged plugin
    the run carries — the invocation checkout's own, which the native update
    moves, beside every record the rewrite would have moved — because the
    condition belongs to the plugin's supply in the registered clone rather
    than to the way one record would have moved.

    This is the only path such a record has to the exit code. The drift
    comparison judges a record against the target version of its plugin, and
    for these records there is none, so a run that left the disposition to
    the comparison would exit zero on a plugin it could not resolve.
    """
    return tuple(
        InstallationWarning(
            agent=Agent.CLAUDE,
            message=UNRESOLVED_TARGET_RECORD_WARNING.format(
                plugin=record.plugin,
                scope=record.scope,
                project_path=record.project_path,
            ),
            blocking=True,
        )
        for record in records
        if record.plugin not in target.versions
    )


def plan_install_record_rewrite(
    records: Sequence[ClaudeInstallRecord],
    target: MarketplaceTarget,
    cache_root: Path,
    cached_versions: Mapping[str, frozenset[str]],
) -> tuple[tuple[RecordRewrite, ...], tuple[InstallationWarning, ...]]:
    """Plan the install-record entries to rewrite to the target, as a pure function.

    `cached_versions` names, per plugin, the versions the plugin cache holds;
    a record whose plugin has no cached target version cannot be pointed at
    a tree the session could load, so it is reported instead of rewritten.

    A record whose plugin resolves to no target version is passed over
    without a warning here: its disposition covers a domain wider than the
    rewrite's, so `unresolved_target_warnings` raises it over every record
    the run carries rather than this function over the subset it plans.
    """
    rewrites: list[RecordRewrite] = []
    warnings: list[InstallationWarning] = []
    for record in records:
        version = target.versions.get(record.plugin)
        if version is None:
            continue
        if version not in cached_versions.get(record.plugin, frozenset()):
            warnings.append(
                InstallationWarning(
                    agent=Agent.CLAUDE,
                    message=UNREFRESHABLE_RECORD_WARNING.format(
                        plugin=record.plugin,
                        scope=record.scope,
                        project_path=record.project_path,
                        version=version,
                    ),
                    blocking=True,
                )
            )
            continue
        rewrites.append(
            RecordRewrite(
                record=record,
                install_path=cache_root / record.plugin / version,
                version=version,
                commit=target.commit,
            )
        )
    return tuple(rewrites), tuple(warnings)


def apply_install_record_writes(
    text: str,
    rewrites: Sequence[RecordRewrite],
    marketplace: str,
    document_path: Path,
) -> tuple[str, tuple[RecordRewrite, ...], tuple[InstallationWarning, ...]]:
    """Apply the planned write set to one install-record document text.

    A pure function from document text and write set to the replacement text:
    each planned entry — matched by plugin, scope, and project path — receives
    the target install path, version, and commit, and every other entry and
    field of the text it is given is carried through unchanged.

    A planned record the text does not carry is one condition with two forms:
    the plugin's identifier is absent, or its entries name no match for the
    record's scope and project path. Both return the record as unwritten with
    one blocking warning, so the run reports what it moved and what it could
    not rather than claiming the whole plan.

    `document_path` names the document in the diagnostics a malformed text
    raises; nothing here reads or writes it.
    """
    document = cast(object, json.loads(text))
    if not isinstance(document, dict):
        raise ValueError(f"{document_path} must be a JSON object")
    plugins = document.get(CLAUDE_INSTALLED_PLUGINS_FIELD)
    if not isinstance(plugins, dict):
        raise ValueError(f"{document_path} carries no plugin records")
    written: list[RecordRewrite] = []
    warnings: list[InstallationWarning] = []
    for rewrite in rewrites:
        identifier = marketplace_plugin_identifier(rewrite.record.plugin, marketplace)
        entries = plugins.get(identifier)
        matched = False
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                project_path = entry.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD)
                if (
                    entry.get(CLAUDE_PLUGIN_SCOPE_FIELD) == rewrite.record.scope
                    and isinstance(project_path, str)
                    and Path(project_path).expanduser().resolve()
                    == rewrite.record.project_path
                ):
                    entry[CLAUDE_INSTALLED_RECORD_PATH_FIELD] = str(
                        rewrite.install_path
                    )
                    entry[CLAUDE_INSTALLED_RECORD_VERSION_FIELD] = rewrite.version
                    entry[CLAUDE_INSTALLED_RECORD_COMMIT_FIELD] = rewrite.commit
                    matched = True
        if matched:
            written.append(rewrite)
            continue
        warnings.append(
            InstallationWarning(
                agent=Agent.CLAUDE,
                message=UNWRITTEN_RECORD_WARNING.format(
                    plugin=rewrite.record.plugin,
                    scope=rewrite.record.scope,
                    project_path=rewrite.record.project_path,
                ),
                blocking=True,
            )
        )
    indent = 2 if "\n  " in text else None
    rendered = json.dumps(document, indent=indent)
    if text.endswith("\n"):
        rendered += "\n"
    return rendered, tuple(written), tuple(warnings)


def read_install_record_document(document_path: Path) -> str:
    """Read one install-record document whole; the writer's default reader."""
    return document_path.read_text(encoding="utf-8")


def rewrite_install_records(
    document_path: Path,
    rewrites: Sequence[RecordRewrite],
    marketplace: str,
    *,
    read_document: Callable[[Path], str] = read_install_record_document,
) -> tuple[tuple[RecordRewrite, ...], tuple[InstallationWarning, ...]]:
    """Rewrite the planned entries in Claude Code's install-record document.

    The run does not own this document. Other agent sessions write into it
    while the run is in flight, and the agent admits no lock over it, so the
    replacement is built from the document as it stands at the write boundary
    rather than from a copy read before it: the writer reads the document,
    applies the planned set, reads the document once more immediately before
    the replace, and applies the same set again when the store moved under the
    first read. A record another session wrote in that interval is therefore
    carried into the replacement with every field the plan does not set, and
    reaches the closing listing comparison, which reports it.

    That second read is one read at the write boundary, not a lock, a wait, or
    a loop: the writer makes no further observation of the store, waits for no
    other session, and chases no record it sees.

    `read_document` is the reader boundary. Production binds the file reader;
    evidence binds a reader that schedules another session's write into the
    interval the two reads span.
    """
    if not rewrites:
        return (), ()
    text = read_document(document_path)
    rendered, written, warnings = apply_install_record_writes(
        text, rewrites, marketplace, document_path
    )
    current = read_document(document_path)
    if current != text:
        rendered, written, warnings = apply_install_record_writes(
            current, rewrites, marketplace, document_path
        )
    _atomic_write(document_path, rendered.encode("utf-8"))
    return written, warnings


def cached_plugin_versions(
    cache_root: Path, plugins: Sequence[str]
) -> dict[str, frozenset[str]]:
    """Observe, per plugin, the version directories the plugin cache holds."""
    observed: dict[str, frozenset[str]] = {}
    for plugin in plugins:
        directory = cache_root / plugin
        observed[plugin] = (
            frozenset(entry.name for entry in directory.iterdir() if entry.is_dir())
            if directory.is_dir()
            else frozenset()
        )
    return observed


SOURCE_VALUE_FIELDS = {
    CLAUDE_GITHUB_SOURCE_TYPE: CLAUDE_REPOSITORY_FIELD,
    CLAUDE_GIT_SOURCE_TYPE: CLAUDE_URL_FIELD,
    CLAUDE_DIRECTORY_SOURCE_TYPE: CLAUDE_DIRECTORY_FIELD,
}
"""The field each Claude source type carries its value in; the inverse of `render_claude_source`."""


def claude_marketplace_source(source: str) -> dict[str, str]:
    """Build the Claude source object for one `marketplace add` argument."""
    source_type = claude_source_type(source)
    return {
        CLAUDE_SOURCE_FIELD: source_type,
        SOURCE_VALUE_FIELDS[source_type]: source,
    }


def claude_marketplace_listing_payload(
    source: str, marketplace: str, install_location: Path | None = None
) -> str:
    """Build one Claude marketplace-listing payload at its public boundary."""
    entry: dict[str, object] = {
        CLAUDE_MARKETPLACE_NAME_FIELD: marketplace,
        **claude_marketplace_source(source),
    }
    if install_location is not None:
        entry[CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD] = str(install_location)
    return json.dumps([entry])


def claude_marketplace_settings(source: str, marketplace: str) -> dict[str, object]:
    """Build one Claude project settings document declaring the marketplace."""
    return {
        EXTRA_MARKETPLACES_FIELD: {
            marketplace: {
                CLAUDE_SOURCE_FIELD: claude_marketplace_source(source),
            }
        }
    }


def codex_marketplace_listing_payload(source: str, marketplace: str) -> str:
    """Build one Codex marketplace-listing payload at its public boundary."""
    source_type = (
        CODEX_LOCAL_SOURCE_TYPE
        if claude_source_type(source) == CLAUDE_DIRECTORY_SOURCE_TYPE
        else CODEX_GIT_SOURCE_TYPE
    )
    return json.dumps(
        {
            CODEX_MARKETPLACES_FIELD: [
                {
                    CODEX_MARKETPLACE_NAME_FIELD: marketplace,
                    CODEX_MARKETPLACE_SOURCE_FIELD: {
                        CODEX_SOURCE_TYPE_FIELD: source_type,
                        CODEX_SOURCE_FIELD: source,
                    },
                }
            ]
        }
    )


def _required_environment_path(
    environment: Mapping[str, str],
    name: str,
) -> Path:
    value = environment.get(name)
    if not value:
        raise ValueError(f"persistent installation requires active ${name}")
    return Path(value).expanduser()


def _create_isolated_roots(roots: InstallationRoots) -> None:
    if roots.state is None or roots.codex_sqlite_home is None:
        raise ValueError("isolated installation requires disposable state roots")
    for root in (
        roots.state,
        roots.home,
        roots.claude_config,
        roots.codex_home,
        roots.codex_sqlite_home,
    ):
        root.mkdir(parents=True, exist_ok=True)


def _agent_adapter(agent: Agent) -> AgentAdapter:
    for adapter in AGENT_ADAPTERS:
        if adapter.agent is agent:
            return adapter
    raise ValueError(f"unsupported installation agent: {agent.value}")


def _command(
    agent: Agent,
    operation: Operation,
    plugin: str | None,
    argv: tuple[str, ...],
    roots: InstallationRoots,
    environment: tuple[tuple[str, str], ...],
    *,
    scope: str | None = None,
    source: str | None = None,
) -> InstallationCommand:
    return InstallationCommand(
        agent=agent,
        operation=operation,
        plugin=plugin,
        argv=argv,
        cwd=roots.checkout,
        environment=environment,
        scope=scope,
        source=source,
    )


def _checked_result(
    command: InstallationCommand,
    result: CommandResult,
) -> CommandResult:
    if result.argv != command.argv:
        raise ValueError(
            f"runner returned an argv different from {command.operation.value}"
        )
    return result


def _real_runner(command: InstallationCommand) -> CommandResult:
    result = subprocess.run(
        command.argv,
        cwd=command.cwd,
        env=dict(command.environment),
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        argv=command.argv,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _failure_document(failure: InstallationFailure) -> dict[str, object]:
    return {
        ReportField.AGENT: failure.command.agent.value,
        ReportField.PLUGIN: failure.command.plugin,
        ReportField.OPERATION: failure.command.operation.value,
        ReportField.ARGV: list(failure.result.argv),
        ReportField.EXIT_CODE: failure.result.exit_code,
        ReportField.STDOUT: failure.result.stdout,
        ReportField.STDERR: failure.result.stderr,
        ReportField.COMPLETED_OPERATIONS: len(failure.completed),
    }


def report_document(report: InstallationReport) -> dict[str, object]:
    agent_home = report.agent_home
    return {
        ReportField.MODE: report.plan.mode.value,
        ReportField.CLAUDE_PLUGINS: sorted(report.installed_for(Agent.CLAUDE)),
        ReportField.CLAUDE_RECORDS: [
            {
                ReportField.PLUGIN: record.plugin,
                ReportField.SCOPE: record.scope,
                ReportField.PROJECT_PATH: str(record.project_path),
                ReportField.VERSION_BEFORE: record.version,
                ReportField.VERSION_AFTER: _version_after(report, record),
            }
            for record in report.refreshed_claude_records()
        ],
        ReportField.UNREFRESHED_RECORDS: [
            {
                ReportField.PLUGIN: record.plugin,
                ReportField.SCOPE: record.scope,
                ReportField.PROJECT_PATH: str(record.project_path),
                ReportField.VERSION: record.version,
            }
            for record in (
                report.record_drift.unrefreshed if report.record_drift else ()
            )
        ],
        ReportField.OFF_TARGET_RECORDS: [
            {
                ReportField.PLUGIN: record.plugin,
                ReportField.SCOPE: record.scope,
                ReportField.PROJECT_PATH: str(record.project_path),
                ReportField.VERSION: record.version,
            }
            for record in (
                report.record_drift.off_target if report.record_drift else ()
            )
        ],
        ReportField.TARGET: (
            None
            if report.target is None
            else {
                ReportField.COMMIT: report.target.commit,
                ReportField.VERSIONS: dict(report.target.versions),
            }
        ),
        ReportField.MARKETPLACE: report.plan.roots.marketplace,
        ReportField.SOURCE: report.plan.claude_source,
        ReportField.COMMANDS: [
            {
                ReportField.AGENT: command.agent.value,
                ReportField.OPERATION: command.operation.value,
                ReportField.PLUGIN: command.plugin,
                ReportField.CWD: str(command.cwd),
            }
            for command in (*report.plan.commands, *report.plan.closing)
        ],
        ReportField.CODEX_PLUGINS: sorted(report.installed_for(Agent.CODEX)),
        ReportField.COMPLETED_OPERATIONS: len(report.results),
        ReportField.STATE_ROOT: (
            str(report.plan.roots.state) if report.plan.roots.state else None
        ),
        ReportField.CHECKOUT: str(report.plan.roots.checkout),
        ReportField.CODEX_HOME: str(report.plan.roots.codex_home),
        ReportField.PENDING_PUBLICATION: [
            {ReportField.AGENT: entry.agent.value, ReportField.PLUGIN: entry.plugin}
            for entry in report.pending_publication
        ],
        ReportField.WARNINGS: [
            {
                ReportField.AGENT: warning.agent.value,
                ReportField.MESSAGE: warning.message,
            }
            for warning in (*report.plan.warnings, *report.rewrite_warnings)
        ],
        ReportField.AGENT_HOME: (
            {
                ReportField.WRITTEN: [str(path) for path in agent_home.written],
                ReportField.PRUNED: [str(path) for path in agent_home.pruned],
                ReportField.COLLISIONS: [
                    {
                        ReportField.DESTINATION: str(collision.destination),
                        ReportField.PLUGIN: collision.plugin,
                        ReportField.REASON: collision.reason,
                    }
                    for collision in agent_home.collisions
                ],
            }
            if agent_home is not None
            else None
        ),
    }


def _refresh_of(
    report: InstallationReport, record: ClaudeInstallRecord
) -> RecordRefresh | None:
    if report.record_drift is None:
        return None
    for refresh in report.record_drift.refreshed:
        if refresh.record == record:
            return refresh
    return None


def _version_after(
    report: InstallationReport, record: ClaudeInstallRecord
) -> str | None:
    refresh = _refresh_of(report, record)
    return None if refresh is None else refresh.version_after


__all__ = [
    "AGENT_ADAPTERS",
    "CATALOG_MARKETPLACE_NAME_FIELD",
    "CATALOG_PLUGIN_SOURCE_FIELD",
    "CLAUDE_MARKETPLACE_INSTALL_LOCATION_FIELD",
    "CLAUDE_PLUGIN_CACHE_RELATIVE",
    "GIT_EXECUTABLE",
    "GIT_HEAD_ARGUMENTS",
    "MarketplaceTarget",
    "OFF_TARGET_DIAGNOSTIC",
    "PATHLESS_LISTING_ENTRY_WARNING",
    "VERSIONLESS_LISTING_ENTRY_WARNING",
    "PLUGIN_MANIFEST_RELATIVE",
    "PLUGIN_MANIFEST_VERSION_FIELD",
    "RecordRewrite",
    "RegisteredMarketplace",
    "UNDECLARED_SOURCE_DIAGNOSTIC",
    "UNLOCATED_REGISTRY_DIAGNOSTIC",
    "UNREFRESHABLE_RECORD_WARNING",
    "UNREADABLE_HEAD_RECORD_WARNING",
    "UNRESOLVED_TARGET_RECORD_WARNING",
    "UNWRITTEN_RECORD_WARNING",
    "cached_plugin_versions",
    "catalog_marketplace_name",
    "claude_marketplace_source",
    "claude_source_type",
    "claude_registered_marketplace",
    "codex_list_command",
    "codex_registered_marketplace",
    "declared_claude_source",
    "declared_codex_source",
    "codex_source_form",
    "marketplace_target",
    "apply_install_record_writes",
    "plan_install_record_rewrite",
    "read_install_record_document",
    "unreadable_head_warnings",
    "unresolved_target_warnings",
    "render_claude_source",
    "rewrite_install_records",
    "AGENT_OWNERSHIP_FILENAME",
    "AGENT_SKILL_NAME_FIELD",
    "AGENT_SKILLS_CONFIG_FIELD",
    "AGENT_SKILLS_FIELD",
    "AGENT_OWNERSHIP_SCHEMA_VERSION",
    "Agent",
    "AgentAdapter",
    "AgentDefinition",
    "AgentHomeAction",
    "AgentHomeCollision",
    "AgentHomeCollisionError",
    "AgentHomeMutation",
    "AgentHomePlan",
    "AgentHomeResult",
    "AgentOwnership",
    "PLUGIN_OPERATIONS",
    "REPORTED_FAILURE_OPERATIONS",
    "UNPUBLISHED_PLUGIN_FRAGMENT",
    "CATALOG_PLUGIN_NAME_FIELD",
    "CATALOG_PLUGINS_FIELD",
    "CLAUDE_CATALOG_PATH",
    "CLAUDE_CONFIG_ENV",
    "CLAUDE_DIRECTORY_FIELD",
    "CLAUDE_DIRECTORY_SOURCE_TYPE",
    "CLAUDE_GIT_SOURCE_TYPE",
    "CLAUDE_URL_FIELD",
    "CLAUDE_GITHUB_SOURCE_TYPE",
    "CLAUDE_PLUGIN_ENABLED_FIELD",
    "CLAUDE_PLUGIN_ID_FIELD",
    "CLAUDE_PLUGIN_PROJECT_PATH_FIELD",
    "CLAUDE_PLUGIN_SCOPE_FIELD",
    "CLAUDE_LOCAL_SCOPE",
    "CLAUDE_PROJECT_SCOPE",
    "CLAUDE_REFRESH_SCOPES",
    "CLAUDE_SCOPE_BEARING_OPERATIONS",
    "CLAUDE_SCOPELESS_OPERATIONS",
    "CLAUDE_SCOPE_FLAG",
    "CLAUDE_USER_SCOPE",
    "CLAUDE_ENABLED_PLUGINS_FIELD",
    "EXTRA_MARKETPLACES_FIELD",
    "CLAUDE_PROJECT_SETTINGS_PATH",
    "CHECKOUT_OPTION",
    "STATE_ROOT_OPTION",
    "JSON_OUTPUT_OPTION",
    "CLAUDE_SOURCE_FIELD",
    "CODEX_AGENTS_PATH",
    "CODEX_CATALOG_PATH",
    "CODEX_CONFIG_PATH",
    "CODEX_GIT_SOURCE_TYPE",
    "CODEX_HOME_ENV",
    "CODEX_HOME_AGENTS_PATH",
    "CODEX_LOCAL_SOURCE_TYPE",
    "CODEX_MARKETPLACES_FIELD",
    "CLAUDE_MARKETPLACE_LIST_COMMAND",
    "CLAUDE_MARKETPLACE_NAME_FIELD",
    "CODEX_MARKETPLACE_LIST_COMMAND",
    "CODEX_MARKETPLACE_NAME_FIELD",
    "CODEX_MARKETPLACE_SOURCE_FIELD",
    "CODEX_PLUGIN_ENABLED_FIELD",
    "CODEX_PLUGIN_ENTRIES_FIELD",
    "CODEX_PLUGIN_ID_FIELD",
    "CODEX_PLUGIN_MARKETPLACE_FIELD",
    "CODEX_SQLITE_HOME_ENV",
    "CODEX_SOURCE_FIELD",
    "CODEX_SOURCE_TYPE_FIELD",
    "CommandResult",
    "CommandRunner",
    "HOME_ENV",
    "InstallationCommand",
    "InstallationFailure",
    "InstallationMode",
    "InstallationPlan",
    "InstallationReport",
    "InstallationRoots",
    "InstallationWarning",
    "FIRST_INSTALL_WARNING",
    "OUT_OF_SCOPE_RECORD_WARNING",
    "PATHLESS_OUT_OF_SCOPE_RECORD_WARNING",
    "UNCATALOGED_RECORD_WARNING",
    "CLAUDE_INSTALLED_PLUGINS_FIELD",
    "CLAUDE_INSTALLED_PLUGINS_RELATIVE",
    "CLAUDE_INSTALLED_RECORD_COMMIT_FIELD",
    "CLAUDE_INSTALLED_RECORD_PATH_FIELD",
    "CLAUDE_INSTALLED_RECORD_VERSION_FIELD",
    "CLAUDE_PLUGIN_VERSION_FIELD",
    "ClaudeInstallRecord",
    "ListedInstallRecord",
    "PathlessInstallRecord",
    "VersionlessInstallRecord",
    "RecordDrift",
    "RecordRefresh",
    "compare_install_listings",
    "installation_exit_code",
    "claude_install_records",
    "claude_refresh_records",
    "MARKETPLACE_IDENTIFIER_JOINER",
    "Operation",
    "PersistentPreflight",
    "ReportField",
    "ScopeSplitClassification",
    "ScopeSplitEntry",
    "ScopeSplitError",
    "SourceAction",
    "STATE_ENV_NAMES",
    "SPEC_TREE_PLUGIN",
    "apply_agent_home_plan",
    "build_agent_home_plan",
    "build_isolated_installation_plan",
    "build_persistent_installation_plan",
    "build_persistent_preflight",
    "catalog_plugin_names",
    "checkout_scope_split_entries",
    "claude_marketplace_listing_payload",
    "CLAUDE_LOCAL_SETTINGS_PATH",
    "CLAUDE_MANAGED_SCOPE",
    "UNREADABLE_SETTINGS_DIAGNOSTIC",
    "UNREADABLE_SETTINGS_WARNING",
    "WITHHELD_REGISTRATION_WARNING",
    "UNREGISTERED_TARGET_WARNING",
    "WITHHELD_TARGET_RECORD_WARNING",
    "marketplace_plugin_identifier",
    "marketplace_plugin_name",
    "CODEX_EXEC_SUBCOMMAND",
    "CLAUDE_SETTINGS_PRECEDENCE",
    "claude_marketplace_settings",
    "codex_marketplace_listing_payload",
    "generated_codex_agent_definitions",
    "execute_installation",
    "execute_persistent_installation",
    "isolated_environment",
    "installed_plugin_names",
    "invocation_settings_error",
    "main",
    "persistent_environment",
    "persistent_roots",
]


if __name__ == "__main__":
    sys.exit(main())
