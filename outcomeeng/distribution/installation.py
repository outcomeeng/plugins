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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol, cast

from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    DIST_DIR_NAME,
    SKILLS_SUBDIR_NAME,
)

MARKETPLACE_NAME = "outcomeeng"
USER_SCOPE_COLLISION_DIAGNOSTIC = "Claude Code user-scope marketplace collision"
CANONICAL_MARKETPLACE_SOURCE = "outcomeeng/plugins"
CANONICAL_CODEX_SOURCE = "https://github.com/outcomeeng/plugins"
CODEX_CATALOG_PATH = Path(".agents/plugins/marketplace.json")
CLAUDE_CATALOG_PATH = Path(".claude-plugin/marketplace.json")
CLAUDE_PROJECT_SETTINGS_PATH = Path(".claude/settings.json")
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
CLAUDE_LIST_COMMAND = (CLAUDE_EXECUTABLE, "plugin", "list", "--json")
CODEX_LIST_COMMAND = (
    CODEX_EXECUTABLE,
    "plugin",
    "list",
    "--marketplace",
    MARKETPLACE_NAME,
    "--json",
)
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
CODEX_MARKETPLACES_FIELD = "marketplaces"
CODEX_MARKETPLACE_NAME_FIELD = "name"
CODEX_MARKETPLACE_SOURCE_FIELD = "marketplaceSource"
CODEX_SOURCE_TYPE_FIELD = "sourceType"
CODEX_SOURCE_FIELD = "source"
CODEX_GIT_SOURCE_TYPE = "git"
CODEX_LOCAL_SOURCE_TYPE = "local"
CLAUDE_MARKETPLACE_NAME_FIELD = "name"
CLAUDE_PLUGIN_ID_FIELD = "id"
CLAUDE_PLUGIN_ENABLED_FIELD = "enabled"
CLAUDE_PLUGIN_SCOPE_FIELD = "scope"
CLAUDE_PLUGIN_PROJECT_PATH_FIELD = "projectPath"
CLAUDE_PROJECT_SCOPE = "project"
CLAUDE_USER_SCOPE = "user"
CLAUDE_ENABLED_PLUGINS_FIELD = "enabledPlugins"
CODEX_PLUGIN_ENTRIES_FIELD = "installed"
CODEX_PLUGIN_ID_FIELD = "pluginId"
CODEX_PLUGIN_ENABLED_FIELD = "enabled"
CODEX_PLUGIN_MARKETPLACE_FIELD = "marketplaceName"
SPEC_TREE_PLUGIN = "spec-tree"
FIRST_INSTALL_WARNING = (
    "No outcomeeng plugins are installed for {agent}; installing only spec-tree. "
    "You probably want to install more plugins."
)


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
    MARKETPLACE_REMOVE = "marketplace-remove"
    MARKETPLACE_ADD = "marketplace-add"
    MARKETPLACE_REFRESH = "marketplace-refresh"
    PLUGIN_INSTALL = "plugin-install"
    PLUGIN_ENABLE = "plugin-enable"
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


PLUGIN_OPERATIONS: frozenset[Operation] = frozenset(
    {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
)
"""Operations that name one plugin, as opposed to a marketplace or the checkout."""

CLAUDE_SCOPE_BEARING_OPERATIONS: frozenset[Operation] = frozenset(
    {
        Operation.MARKETPLACE_REMOVE,
        Operation.MARKETPLACE_ADD,
        Operation.PLUGIN_INSTALL,
        Operation.PLUGIN_ENABLE,
    }
)
"""Claude operations whose public CLI accepts an explicit installation scope."""

CLAUDE_SCOPELESS_OPERATIONS: frozenset[Operation] = frozenset(
    {Operation.MARKETPLACE_REFRESH, Operation.PLUGIN_LIST}
)
"""Claude operations whose public CLI has no installation-scope argument."""


class SourceAction(StrEnum):
    """Reconciliation required for one configured marketplace source."""

    ADD = "add"
    REFRESH = "refresh"
    REPLACE = "replace"


class AgentHomeAction(StrEnum):
    """One digest-guarded mutation in the selected Codex agent home."""

    CREATE = "create"
    REPLACE = "replace"
    PRUNE = "prune"


@dataclass(frozen=True)
class InstallationRoots:
    """Checkout and explicitly selected agent-state roots."""

    checkout: Path
    state: Path | None
    home: Path
    claude_config: Path
    codex_home: Path
    codex_sqlite_home: Path | None


@dataclass(frozen=True)
class InstallationCommand:
    """One ordered external operation in an installation plan."""

    agent: Agent
    operation: Operation
    plugin: str | None
    argv: tuple[str, ...]
    cwd: Path
    environment: tuple[tuple[str, str], ...]


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
    claude_source_action: SourceAction
    inspections: tuple[InstallationCommand, ...]


@dataclass(frozen=True, order=True)
class InstallationWarning:
    """One non-terminal warning produced while selecting plugins."""

    agent: Agent
    message: str


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

    def pending_for(self, agent: Agent) -> frozenset[str]:
        """The plugins this agent could not install because they are unpublished."""
        return frozenset(
            entry.plugin for entry in self.pending_publication if entry.agent is agent
        )

    def installed_for(self, agent: Agent) -> frozenset[str]:
        """The plugins this agent installed: what it planned, less what is pending.

        The plan carries the committed catalog, which is what the run intended
        rather than what it achieved. Every reader of this report — the text
        summary and the JSON document alike — answers from here, so the two
        cannot disagree about whether a pending plugin was installed.
        """
        planned = (
            self.plan.claude_plugins
            if agent is Agent.CLAUDE
            else self.plan.codex_plugins
        )
        return frozenset(planned) - self.pending_for(agent)


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
            f"{command.plugin or MARKETPLACE_NAME} with exit {result.exit_code}"
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
    ) -> tuple[InstallationCommand, ...]:
        scope = (
            CLAUDE_PROJECT_SCOPE
            if mode is InstallationMode.PERSISTENT
            else CLAUDE_USER_SCOPE
        )
        source = (
            CANONICAL_MARKETPLACE_SOURCE
            if mode is InstallationMode.PERSISTENT
            else str(roots.checkout)
        )
        commands = list(
            _claude_source_commands(source_action, source, scope, roots, environment)
        )
        for plugin in plugins:
            plugin_id = f"{plugin}@{MARKETPLACE_NAME}"
            commands.append(
                _command(
                    self.agent,
                    Operation.PLUGIN_INSTALL,
                    plugin,
                    (
                        CLAUDE_EXECUTABLE,
                        "plugin",
                        "install",
                        plugin_id,
                        "--scope",
                        scope,
                    ),
                    roots,
                    environment,
                )
            )
            commands.append(
                _command(
                    self.agent,
                    Operation.PLUGIN_ENABLE,
                    plugin,
                    (
                        CLAUDE_EXECUTABLE,
                        "plugin",
                        "enable",
                        plugin_id,
                        "--scope",
                        scope,
                    ),
                    roots,
                    environment,
                )
            )
        commands.append(
            _command(
                self.agent,
                Operation.PLUGIN_LIST,
                None,
                CLAUDE_LIST_COMMAND,
                roots,
                environment,
            )
        )
        return tuple(commands)

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
    ) -> tuple[InstallationCommand, ...]:
        source = (
            CANONICAL_MARKETPLACE_SOURCE
            if mode is InstallationMode.PERSISTENT
            else str(roots.checkout)
        )
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
                        f"{plugin}@{MARKETPLACE_NAME}",
                        "--json",
                    ),
                    roots,
                    environment,
                )
            )
        commands.append(
            _command(
                self.agent,
                Operation.PLUGIN_LIST,
                None,
                CODEX_LIST_COMMAND,
                roots,
                environment,
            )
        )
        return tuple(commands)

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
    user_settings = roots.claude_config / "settings.json"
    user_document = _settings_document(user_settings)
    if _marketplace_entry(user_document) is not None:
        raise ValueError(
            f"{USER_SCOPE_COLLISION_DIAGNOSTIC}: "
            f"{user_settings} declares `{MARKETPLACE_NAME}`; remove that user-scope "
            "registration before project-scoped installation"
        )
    project_document = _settings_document(roots.checkout / CLAUDE_PROJECT_SETTINGS_PATH)
    project_source_action = claude_source_action(project_document)
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
            CODEX_LIST_COMMAND,
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
        claude_source_action=project_source_action,
        inspections=inspections,
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
    marketplace is added regardless of the declaration.
    """
    claude_action = (
        preflight.claude_source_action
        if MARKETPLACE_NAME in claude_marketplace_names(claude_marketplace_payload)
        else SourceAction.ADD
    )
    codex_action = codex_source_action(codex_marketplace_payload)
    claude_selection, claude_warning = _persistent_selection(
        Agent.CLAUDE,
        preflight.claude_plugins,
        installed_plugin_names(
            Agent.CLAUDE,
            claude_plugins_payload,
            checkout=preflight.roots.checkout,
        ),
    )
    codex_selection, codex_warning = _persistent_selection(
        Agent.CODEX,
        preflight.codex_plugins,
        installed_plugin_names(
            Agent.CODEX,
            codex_plugins_payload,
            checkout=preflight.roots.checkout,
        ),
    )
    return _build_plan(
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
            for warning in (claude_warning, codex_warning)
            if warning is not None
        ),
    )


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
    declared = _declared_plugin_selection(settings)
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
    """Re-apply a declared plugin selection, leaving the rest of the document."""
    if declared is None or not settings.exists():
        return
    document = _settings_document(settings)
    if _selection_of(document) == declared:
        return
    if declared.present:
        document[CLAUDE_ENABLED_PLUGINS_FIELD] = declared.value
    else:
        document.pop(CLAUDE_ENABLED_PLUGINS_FIELD, None)
    settings.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


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
    commands = tuple(
        command
        for adapter in AGENT_ADAPTERS
        for command in adapter.commands(
            mode,
            actions[adapter.agent],
            roots,
            environment,
            plugins_by_agent[adapter.agent],
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
    )


def installed_plugin_names(
    agent: Agent,
    payload: str,
    *,
    checkout: Path,
) -> frozenset[str]:
    """Parse one agent's installed outcomeeng inventory for its selected scope."""
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid {agent.value} plugin listing: {error}") from error
    entries: object = document
    if agent is Agent.CODEX:
        if not isinstance(document, dict):
            raise ValueError("Codex plugin listing must be a JSON object")
        entries = document.get(CODEX_PLUGIN_ENTRIES_FIELD)
    if not isinstance(entries, list):
        raise ValueError(f"{agent.value} plugin listing must contain an array")

    marketplace_suffix = f"@{MARKETPLACE_NAME}"
    resolved_checkout = checkout.resolve()
    installed: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{agent.value} plugin listing entry {index} must be an object"
            )
        identifier_field = (
            CLAUDE_PLUGIN_ID_FIELD if agent is Agent.CLAUDE else CODEX_PLUGIN_ID_FIELD
        )
        identifier = entry.get(identifier_field)
        if not isinstance(identifier, str):
            raise ValueError(
                f"{agent.value} plugin listing entry {index} has no typed identity"
            )
        if not identifier.endswith(marketplace_suffix):
            continue
        if agent is Agent.CLAUDE:
            scope = entry.get(CLAUDE_PLUGIN_SCOPE_FIELD)
            if not isinstance(scope, str):
                raise ValueError(
                    f"Claude plugin listing entry {index} has no typed scope"
                )
            if scope != CLAUDE_PROJECT_SCOPE:
                continue
            project_path = entry.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD)
            if not isinstance(project_path, str):
                raise ValueError(
                    f"Claude plugin listing entry {index} has no typed project path"
                )
            if Path(project_path).expanduser().resolve() != resolved_checkout:
                continue
        else:
            marketplace = entry.get(CODEX_PLUGIN_MARKETPLACE_FIELD)
            if not isinstance(marketplace, str):
                raise ValueError(
                    f"Codex plugin listing entry {index} has no typed marketplace"
                )
            if marketplace != MARKETPLACE_NAME:
                continue
        installed.add(identifier.removesuffix(marketplace_suffix))
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
) -> tuple[tuple[str, ...], InstallationWarning | None]:
    if SPEC_TREE_PLUGIN not in catalog:
        raise ValueError(
            f"invalid {agent.value} catalog: `{SPEC_TREE_PLUGIN}` is required"
        )
    if not installed:
        return (
            (SPEC_TREE_PLUGIN,),
            InstallationWarning(
                agent=agent,
                message=FIRST_INSTALL_WARNING.format(agent=agent.value),
            ),
        )
    if SPEC_TREE_PLUGIN not in installed:
        raise ValueError(
            f"invalid {agent.value} installed selection: nonempty outcomeeng "
            f"inventory must include `{SPEC_TREE_PLUGIN}`"
        )
    return (
        tuple(plugin for plugin in catalog if plugin in installed),
        None,
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
    return InstallationRoots(
        checkout=checkout.resolve(strict=True),
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


def codex_source_action(payload: str) -> SourceAction:
    """Classify the selected Codex home's configured marketplace source."""
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
        if entry.get(CODEX_MARKETPLACE_NAME_FIELD) != MARKETPLACE_NAME:
            continue
        source = entry.get(CODEX_MARKETPLACE_SOURCE_FIELD)
        if not isinstance(source, dict):
            return SourceAction.REPLACE
        source_value = source.get(CODEX_SOURCE_FIELD)
        if isinstance(source_value, str) and _canonical_codex_source(source_value):
            return SourceAction.REFRESH
        return SourceAction.REPLACE
    return SourceAction.ADD


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
    for command in plan.commands:
        result = _checked_result(command, runner(command))
        result = _agent_adapter(command.agent).normalize_result(command, result)
        if result.exit_code != 0:
            if not _is_pending_publication(plan, command, result):
                raise InstallationFailure(command, result, tuple(results))
            if command.plugin is not None:
                entry = PendingPublication(command.agent, command.plugin)
                if entry not in pending:
                    pending.append(entry)
        results.append(result)
    agent_home = apply_agent_home_plan(plan.agent_home)
    return InstallationReport(
        plan=plan,
        results=tuple(results),
        pending_publication=tuple(pending),
        agent_home=agent_home,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    base_environment: Mapping[str, str] | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Install persistently by default or verify in an explicit isolated root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path.cwd())
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
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
    for warning in report.plan.warnings:
        print(f"warning: {warning.message}", file=sys.stderr)
    if arguments.json_output:
        print(json.dumps(report_document(report), sort_keys=True))
    else:
        print(f"installed {len(report.installed_for(Agent.CLAUDE))} Claude plugins")
        print(f"installed {len(report.installed_for(Agent.CODEX))} Codex plugins")
        for entry in report.pending_publication:
            print(
                f"pending publication, not installed: {entry.plugin} ({entry.agent.value})"
            )
    return 0


def _claude_source_commands(
    action: SourceAction,
    source: str,
    scope: str,
    roots: InstallationRoots,
    environment: tuple[tuple[str, str], ...],
) -> tuple[InstallationCommand, ...]:
    commands: list[InstallationCommand] = []
    if action is SourceAction.REPLACE:
        commands.append(
            _command(
                Agent.CLAUDE,
                Operation.MARKETPLACE_REMOVE,
                None,
                (
                    CLAUDE_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "remove",
                    MARKETPLACE_NAME,
                    "--scope",
                    scope,
                ),
                roots,
                environment,
            )
        )
    if action in {SourceAction.ADD, SourceAction.REPLACE}:
        commands.append(
            _command(
                Agent.CLAUDE,
                Operation.MARKETPLACE_ADD,
                None,
                (
                    CLAUDE_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "add",
                    source,
                    "--scope",
                    scope,
                ),
                roots,
                environment,
            )
        )
    else:
        commands.append(
            _command(
                Agent.CLAUDE,
                Operation.MARKETPLACE_REFRESH,
                None,
                (
                    CLAUDE_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "update",
                    MARKETPLACE_NAME,
                ),
                roots,
                environment,
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
    if action is SourceAction.REPLACE:
        commands.append(
            _command(
                Agent.CODEX,
                Operation.MARKETPLACE_REMOVE,
                None,
                (
                    CODEX_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "remove",
                    MARKETPLACE_NAME,
                    "--json",
                ),
                roots,
                environment,
            )
        )
    if action in {SourceAction.ADD, SourceAction.REPLACE}:
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
                    MARKETPLACE_NAME,
                    "--json",
                ),
                roots,
                environment,
            )
        )
    return tuple(commands)


def _settings_document(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        document = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid Claude Code settings {path}: {error}") from error
    if not isinstance(document, dict):
        raise ValueError(f"Claude Code settings {path} must be a JSON object")
    return document


def _marketplace_entry(document: Mapping[str, object]) -> object | None:
    marketplaces = document.get(EXTRA_MARKETPLACES_FIELD)
    if marketplaces is None:
        return None
    if not isinstance(marketplaces, dict):
        raise ValueError(f"{EXTRA_MARKETPLACES_FIELD} must be a JSON object")
    return marketplaces.get(MARKETPLACE_NAME)


def claude_source_action(document: Mapping[str, object]) -> SourceAction:
    """Classify one Claude project settings marketplace source."""
    entry = _marketplace_entry(document)
    if entry is None:
        return SourceAction.ADD
    if not isinstance(entry, dict):
        return SourceAction.REPLACE
    source = entry.get(CLAUDE_SOURCE_FIELD)
    if not isinstance(source, dict):
        return SourceAction.REPLACE
    if (
        source.get(CLAUDE_SOURCE_FIELD) == CLAUDE_GITHUB_SOURCE_TYPE
        and source.get(CLAUDE_REPOSITORY_FIELD) == CANONICAL_MARKETPLACE_SOURCE
    ):
        return SourceAction.REFRESH
    return SourceAction.REPLACE


def claude_marketplace_names(payload: str) -> frozenset[str]:
    """Parse marketplace names from one Claude marketplace listing."""
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid claude marketplace listing: {error}") from error
    if not isinstance(document, list):
        raise ValueError("claude marketplace listing must be a JSON array")
    names: set[str] = set()
    for entry in document:
        if not isinstance(entry, dict):
            raise ValueError("claude marketplace listing contains a non-object")
        name = entry.get(CLAUDE_MARKETPLACE_NAME_FIELD)
        if not isinstance(name, str):
            raise ValueError("claude marketplace listing entry lacks a typed name")
        names.add(name)
    return frozenset(names)


def claude_marketplace_listing_payload(repository: str) -> str:
    """Build one Claude marketplace-listing payload at its public boundary."""
    return json.dumps(
        [
            {
                CLAUDE_MARKETPLACE_NAME_FIELD: MARKETPLACE_NAME,
                CLAUDE_SOURCE_FIELD: CLAUDE_GITHUB_SOURCE_TYPE,
                CLAUDE_REPOSITORY_FIELD: repository,
            }
        ]
    )


def claude_marketplace_settings(repository: str) -> dict[str, object]:
    """Build one Claude project settings document for the marketplace."""
    if repository == CANONICAL_MARKETPLACE_SOURCE:
        source = {
            CLAUDE_SOURCE_FIELD: CLAUDE_GITHUB_SOURCE_TYPE,
            CLAUDE_REPOSITORY_FIELD: repository,
        }
    else:
        source = {
            CLAUDE_SOURCE_FIELD: CLAUDE_DIRECTORY_SOURCE_TYPE,
            CLAUDE_DIRECTORY_FIELD: repository,
        }
    return {
        EXTRA_MARKETPLACES_FIELD: {
            MARKETPLACE_NAME: {
                CLAUDE_SOURCE_FIELD: source,
            }
        }
    }


def codex_marketplace_listing_payload(source: str) -> str:
    """Build one Codex marketplace-listing payload at its public boundary."""
    source_type = (
        CODEX_GIT_SOURCE_TYPE if source.startswith("http") else CODEX_LOCAL_SOURCE_TYPE
    )
    return json.dumps(
        {
            CODEX_MARKETPLACES_FIELD: [
                {
                    CODEX_MARKETPLACE_NAME_FIELD: MARKETPLACE_NAME,
                    CODEX_MARKETPLACE_SOURCE_FIELD: {
                        CODEX_SOURCE_TYPE_FIELD: source_type,
                        CODEX_SOURCE_FIELD: source,
                    },
                }
            ]
        }
    )


def _canonical_codex_source(source: str) -> bool:
    normalized = source.removesuffix(".git").rstrip("/")
    return normalized in {
        CANONICAL_MARKETPLACE_SOURCE,
        CANONICAL_CODEX_SOURCE,
        "git@github.com:outcomeeng/plugins",
    }


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
) -> InstallationCommand:
    return InstallationCommand(
        agent=agent,
        operation=operation,
        plugin=plugin,
        argv=argv,
        cwd=roots.checkout,
        environment=environment,
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
            for warning in report.plan.warnings
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


__all__ = [
    "AGENT_ADAPTERS",
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
    "CANONICAL_CODEX_SOURCE",
    "CANONICAL_MARKETPLACE_SOURCE",
    "PLUGIN_OPERATIONS",
    "UNPUBLISHED_PLUGIN_FRAGMENT",
    "CATALOG_PLUGIN_NAME_FIELD",
    "CATALOG_PLUGINS_FIELD",
    "CLAUDE_CATALOG_PATH",
    "CLAUDE_CONFIG_ENV",
    "CLAUDE_DIRECTORY_FIELD",
    "CLAUDE_DIRECTORY_SOURCE_TYPE",
    "CLAUDE_GITHUB_SOURCE_TYPE",
    "CLAUDE_PLUGIN_ENABLED_FIELD",
    "CLAUDE_PLUGIN_ID_FIELD",
    "CLAUDE_PLUGIN_PROJECT_PATH_FIELD",
    "CLAUDE_PLUGIN_SCOPE_FIELD",
    "CLAUDE_PROJECT_SCOPE",
    "CLAUDE_SCOPE_BEARING_OPERATIONS",
    "CLAUDE_SCOPELESS_OPERATIONS",
    "CLAUDE_USER_SCOPE",
    "CLAUDE_ENABLED_PLUGINS_FIELD",
    "EXTRA_MARKETPLACES_FIELD",
    "CLAUDE_PROJECT_SETTINGS_PATH",
    "USER_SCOPE_COLLISION_DIAGNOSTIC",
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
    "MARKETPLACE_NAME",
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
    "claude_marketplace_names",
    "claude_marketplace_settings",
    "claude_source_action",
    "codex_marketplace_listing_payload",
    "codex_source_action",
    "generated_codex_agent_definitions",
    "execute_installation",
    "execute_persistent_installation",
    "isolated_environment",
    "installed_plugin_names",
    "main",
    "persistent_environment",
    "persistent_roots",
]


if __name__ == "__main__":
    sys.exit(main())
