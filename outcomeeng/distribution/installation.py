"""Install committed marketplace catalogs into selected agent state."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol, cast

MARKETPLACE_NAME = "outcomeeng"
CANONICAL_MARKETPLACE_SOURCE = "outcomeeng/plugins"
CANONICAL_CODEX_SOURCE = "https://github.com/outcomeeng/plugins"
CODEX_CATALOG_PATH = Path(".agents/plugins/marketplace.json")
CLAUDE_CATALOG_PATH = Path(".claude-plugin/marketplace.json")
VERIFICATION_TEST = (
    "spx/32-distribution.enabler/21-installation.enabler/"
    "21-repository-installation.enabler/tests/"
    "test_repository_installation.scenario.l2.py"
)
CLAUDE_PROJECT_SETTINGS_PATH = Path(".claude/settings.json")
CODEX_CONFIG_PATH = Path(".codex/config.toml")
CODEX_AGENTS_PATH = Path(".codex/agents")
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
PYTHON_EXECUTABLE = "python3"
CLAUDE_LIST_COMMAND = (CLAUDE_EXECUTABLE, "plugin", "list", "--json")
CODEX_LIST_COMMAND = (CODEX_EXECUTABLE, "plugin", "list", "--json")
CODEX_MARKETPLACE_LIST_COMMAND = (
    CODEX_EXECUTABLE,
    "plugin",
    "marketplace",
    "list",
    "--json",
)
PLACEMENT_SCRIPT_RELATIVE_PATH = Path("scripts/place_agents.py")
CLAUDE_ALREADY_INSTALLED_FRAGMENT = "already installed"
CLAUDE_ALREADY_ENABLED_FRAGMENT = "already enabled"
EXTRA_MARKETPLACES_FIELD = "extraKnownMarketplaces"
CLAUDE_SOURCE_FIELD = "source"
CLAUDE_REPOSITORY_FIELD = "repo"


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
    MARKETPLACE_REMOVE = "marketplace-remove"
    MARKETPLACE_ADD = "marketplace-add"
    MARKETPLACE_REFRESH = "marketplace-refresh"
    PLUGIN_INSTALL = "plugin-install"
    PLUGIN_ENABLE = "plugin-enable"
    LIFECYCLE_PLACE = "lifecycle-place"
    PLUGIN_LIST = "plugin-list"


class SourceAction(StrEnum):
    """Reconciliation required for one configured marketplace source."""

    ADD = "add"
    REFRESH = "refresh"
    REPLACE = "replace"


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


@dataclass(frozen=True)
class PersistentPreflight:
    """Validated persistent inputs before Codex source inspection."""

    roots: InstallationRoots
    environment: tuple[tuple[str, str], ...]
    claude_plugins: tuple[str, ...]
    codex_plugins: tuple[str, ...]
    claude_source_action: SourceAction
    codex_inspection: InstallationCommand


@dataclass(frozen=True)
class InstallationPlan:
    """Immutable catalog-derived installation plan."""

    mode: InstallationMode
    roots: InstallationRoots
    claude_plugins: tuple[str, ...]
    codex_plugins: tuple[str, ...]
    commands: tuple[InstallationCommand, ...]


@dataclass(frozen=True)
class InstallationReport:
    """Completed commands from one successful installation."""

    plan: InstallationPlan
    results: tuple[CommandResult, ...]


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
        scope = "project" if mode is InstallationMode.PERSISTENT else "user"
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
            commands.extend(
                (
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
                    ),
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
                    ),
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
    """Translate a Codex catalog into install and lifecycle operations."""

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
        commands.extend(_lifecycle_commands(roots, environment, plugins))
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
    return _build_plan(
        InstallationMode.ISOLATED,
        roots,
        environment,
        SourceAction.ADD,
        SourceAction.ADD,
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
            "Claude Code user-scope marketplace collision: "
            f"{user_settings} declares `{MARKETPLACE_NAME}`; remove that user-scope "
            "registration before project-scoped installation"
        )
    project_document = _settings_document(roots.checkout / CLAUDE_PROJECT_SETTINGS_PATH)
    claude_source_action = _claude_source_action(project_document)
    environment = persistent_environment(roots, base_environment)
    inspection = _command(
        Agent.CODEX,
        Operation.MARKETPLACE_INSPECT,
        None,
        CODEX_MARKETPLACE_LIST_COMMAND,
        roots,
        environment,
    )
    return PersistentPreflight(
        roots=roots,
        environment=environment,
        claude_plugins=catalog_plugin_names(roots.checkout / CLAUDE_CATALOG_PATH),
        codex_plugins=catalog_plugin_names(roots.checkout / CODEX_CATALOG_PATH),
        claude_source_action=claude_source_action,
        codex_inspection=inspection,
    )


def build_persistent_installation_plan(
    preflight: PersistentPreflight,
    codex_marketplace_payload: str,
) -> InstallationPlan:
    """Build a persistent plan from validated inputs and Codex CLI state."""
    codex_action = codex_source_action(codex_marketplace_payload)
    return _build_plan(
        InstallationMode.PERSISTENT,
        preflight.roots,
        preflight.environment,
        preflight.claude_source_action,
        codex_action,
        claude_plugins=preflight.claude_plugins,
        codex_plugins=preflight.codex_plugins,
    )


def execute_persistent_installation(
    checkout: Path,
    base_environment: Mapping[str, str],
    runner: CommandRunner,
) -> InstallationReport:
    """Inspect selected persistent state, then reconcile and install it."""
    preflight = build_persistent_preflight(checkout, base_environment)
    inspection_result = _checked_result(
        preflight.codex_inspection,
        runner(preflight.codex_inspection),
    )
    if inspection_result.exit_code != 0:
        raise InstallationFailure(
            preflight.codex_inspection,
            inspection_result,
            (),
        )
    plan = build_persistent_installation_plan(preflight, inspection_result.stdout)
    return execute_installation(plan, runner, completed=(inspection_result,))


def _build_plan(
    mode: InstallationMode,
    roots: InstallationRoots,
    environment: tuple[tuple[str, str], ...],
    claude_action: SourceAction,
    codex_action: SourceAction,
    *,
    claude_plugins: tuple[str, ...] | None = None,
    codex_plugins: tuple[str, ...] | None = None,
) -> InstallationPlan:
    selected_claude_plugins = claude_plugins or catalog_plugin_names(
        roots.checkout / CLAUDE_CATALOG_PATH
    )
    selected_codex_plugins = codex_plugins or catalog_plugin_names(
        roots.checkout / CODEX_CATALOG_PATH
    )
    plugins_by_agent = {
        Agent.CLAUDE: selected_claude_plugins,
        Agent.CODEX: selected_codex_plugins,
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
    return InstallationPlan(
        mode=mode,
        roots=roots,
        claude_plugins=selected_claude_plugins,
        codex_plugins=selected_codex_plugins,
        commands=commands,
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


def codex_source_action(payload: str) -> SourceAction:
    """Classify the selected Codex home's configured marketplace source."""
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid Codex marketplace listing: {error}") from error
    if not isinstance(document, dict):
        raise ValueError("Codex marketplace listing must be a JSON object")
    marketplaces = document.get("marketplaces")
    if not isinstance(marketplaces, list):
        raise ValueError("Codex marketplace listing must contain a marketplaces array")
    for entry in marketplaces:
        if not isinstance(entry, dict):
            raise ValueError("Codex marketplace listing contains a non-object")
        if entry.get("name") != MARKETPLACE_NAME:
            continue
        source = entry.get("marketplaceSource")
        if not isinstance(source, dict):
            return SourceAction.REPLACE
        source_value = source.get("source")
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
    for command in plan.commands:
        result = _checked_result(command, runner(command))
        result = _agent_adapter(command.agent).normalize_result(command, result)
        if result.exit_code != 0:
            raise InstallationFailure(command, result, tuple(results))
        results.append(result)
    return InstallationReport(plan=plan, results=tuple(results))


def main(argv: Sequence[str] | None = None) -> int:
    """Install persistently by default or verify in an explicit isolated root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path.cwd())
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    arguments = parser.parse_args(argv)
    try:
        if arguments.state_root is None:
            report = execute_persistent_installation(
                arguments.checkout,
                os.environ,
                _real_runner,
            )
        else:
            plan = build_isolated_installation_plan(
                arguments.checkout,
                arguments.state_root,
                os.environ,
            )
            report = execute_installation(plan, _real_runner)
    except InstallationFailure as failure:
        print(json.dumps(_failure_document(failure), sort_keys=True), file=sys.stderr)
        return failure.result.exit_code
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, sort_keys=True), file=sys.stderr)
        return 1
    if arguments.json_output:
        print(json.dumps(_report_document(report), sort_keys=True))
    else:
        print(f"installed {len(report.plan.claude_plugins)} Claude plugins")
        print(f"installed {len(report.plan.codex_plugins)} Codex plugins")
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


def _lifecycle_commands(
    roots: InstallationRoots,
    environment: tuple[tuple[str, str], ...],
    plugins: Sequence[str],
) -> tuple[InstallationCommand, ...]:
    commands: list[InstallationCommand] = []
    for plugin in plugins:
        script = (
            roots.checkout
            / "dist"
            / Agent.CODEX.value
            / plugin
            / "skills"
            / f"{plugin}-plugin"
            / PLACEMENT_SCRIPT_RELATIVE_PATH
        )
        if script.is_file():
            commands.append(
                _command(
                    Agent.CODEX,
                    Operation.LIFECYCLE_PLACE,
                    plugin,
                    (
                        PYTHON_EXECUTABLE,
                        str(script),
                        "--checkout",
                        str(roots.checkout),
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


def _claude_source_action(document: Mapping[str, object]) -> SourceAction:
    entry = _marketplace_entry(document)
    if entry is None:
        return SourceAction.ADD
    if not isinstance(entry, dict):
        return SourceAction.REPLACE
    source = entry.get(CLAUDE_SOURCE_FIELD)
    if not isinstance(source, dict):
        return SourceAction.REPLACE
    if (
        source.get(CLAUDE_SOURCE_FIELD) == "github"
        and source.get(CLAUDE_REPOSITORY_FIELD) == CANONICAL_MARKETPLACE_SOURCE
    ):
        return SourceAction.REFRESH
    return SourceAction.REPLACE


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
        "agent": failure.command.agent.value,
        "plugin": failure.command.plugin,
        "operation": failure.command.operation.value,
        "argv": list(failure.result.argv),
        "exit_code": failure.result.exit_code,
        "stdout": failure.result.stdout,
        "stderr": failure.result.stderr,
        "completed_operations": len(failure.completed),
    }


def _report_document(report: InstallationReport) -> dict[str, object]:
    return {
        "mode": report.plan.mode.value,
        "claude_plugins": list(report.plan.claude_plugins),
        "codex_plugins": list(report.plan.codex_plugins),
        "completed_operations": len(report.results),
        "state_root": (
            str(report.plan.roots.state) if report.plan.roots.state else None
        ),
        "checkout": str(report.plan.roots.checkout),
        "codex_home": str(report.plan.roots.codex_home),
    }


__all__ = [
    "AGENT_ADAPTERS",
    "Agent",
    "AgentAdapter",
    "CANONICAL_MARKETPLACE_SOURCE",
    "CATALOG_PLUGIN_NAME_FIELD",
    "CATALOG_PLUGINS_FIELD",
    "CLAUDE_CATALOG_PATH",
    "CLAUDE_CONFIG_ENV",
    "CLAUDE_PROJECT_SETTINGS_PATH",
    "CODEX_AGENTS_PATH",
    "CODEX_CATALOG_PATH",
    "CODEX_CONFIG_PATH",
    "CODEX_HOME_ENV",
    "CODEX_SQLITE_HOME_ENV",
    "CommandResult",
    "CommandRunner",
    "HOME_ENV",
    "InstallationCommand",
    "InstallationFailure",
    "InstallationMode",
    "InstallationPlan",
    "InstallationReport",
    "InstallationRoots",
    "MARKETPLACE_NAME",
    "Operation",
    "PersistentPreflight",
    "PYTHON_EXECUTABLE",
    "SourceAction",
    "STATE_ENV_NAMES",
    "VERIFICATION_TEST",
    "build_isolated_installation_plan",
    "build_persistent_installation_plan",
    "build_persistent_preflight",
    "catalog_plugin_names",
    "codex_source_action",
    "execute_installation",
    "execute_persistent_installation",
    "isolated_environment",
    "main",
    "persistent_environment",
    "persistent_roots",
]


if __name__ == "__main__":
    sys.exit(main())
