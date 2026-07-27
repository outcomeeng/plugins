"""Install committed marketplace catalogs into caller-selected agent homes."""

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
from tempfile import TemporaryDirectory
from typing import cast
from typing import Protocol

MARKETPLACE_NAME = "outcomeeng"
CODEX_CATALOG_PATH = Path(".agents/plugins/marketplace.json")
CLAUDE_CATALOG_PATH = Path(".claude-plugin/marketplace.json")
CODEX_CONFIG_PATH = Path(".codex/config.toml")
CODEX_AGENTS_PATH = Path(".codex/agents")
CATALOG_PLUGINS_FIELD = "plugins"
CATALOG_PLUGIN_NAME_FIELD = "name"
CLAUDE_PLUGIN_ID_FIELD = "id"
CLAUDE_PLUGIN_ENABLED_FIELD = "enabled"
CODEX_INSTALLED_FIELD = "installed"
CODEX_PLUGIN_ID_FIELD = "pluginId"
CODEX_PLUGIN_ENABLED_FIELD = "enabled"
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
CLAUDE_LIST_COMMAND: tuple[str, ...] = (
    CLAUDE_EXECUTABLE,
    "plugin",
    "list",
    "--json",
)
CODEX_LIST_COMMAND: tuple[str, ...] = (
    CODEX_EXECUTABLE,
    "plugin",
    "list",
    "--json",
)
PLACEMENT_SCRIPT_RELATIVE_PATH = Path("scripts/place_agents.py")
CLAUDE_ALREADY_ENABLED_FRAGMENT = "is already enabled at user scope"


class Agent(StrEnum):
    """Agent harnesses supported by repository installation."""

    CLAUDE = "claude"
    CODEX = "codex"


class Operation(StrEnum):
    """Installation operations exposed in reports and diagnostics."""

    MARKETPLACE_ADD = "marketplace-add"
    PLUGIN_INSTALL = "plugin-install"
    PLUGIN_ENABLE = "plugin-enable"
    LIFECYCLE_PLACE = "lifecycle-place"
    PLUGIN_LIST = "plugin-list"


@dataclass(frozen=True)
class InstallationRoots:
    """Explicit checkout and disposable agent-state roots."""

    checkout: Path
    state: Path
    home: Path
    claude_config: Path
    codex_home: Path
    codex_sqlite_home: Path


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
class InstallationPlan:
    """Immutable catalog-derived installation plan."""

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

    agent: Agent

    def commands(
        self,
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
    """Translate a Claude catalog into user-scoped CLI operations."""

    agent: Agent = Agent.CLAUDE

    def commands(
        self,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        plugins: Sequence[str],
    ) -> tuple[InstallationCommand, ...]:
        commands = [
            _command(
                self.agent,
                Operation.MARKETPLACE_ADD,
                None,
                (
                    CLAUDE_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "add",
                    str(roots.checkout),
                    "--scope",
                    "user",
                ),
                roots,
                environment,
            )
        ]
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
                            "user",
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
                            "user",
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
        if (
            command.operation is Operation.PLUGIN_ENABLE
            and result.exit_code != 0
            and CLAUDE_ALREADY_ENABLED_FRAGMENT in result.stderr
        ):
            return CommandResult(
                argv=result.argv,
                exit_code=0,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        return result


@dataclass(frozen=True)
class CodexInstallationAdapter:
    """Translate a Codex catalog into install and lifecycle operations."""

    agent: Agent = Agent.CODEX

    def commands(
        self,
        roots: InstallationRoots,
        environment: tuple[tuple[str, str], ...],
        plugins: Sequence[str],
    ) -> tuple[InstallationCommand, ...]:
        commands = [
            _command(
                self.agent,
                Operation.MARKETPLACE_ADD,
                None,
                (
                    CODEX_EXECUTABLE,
                    "plugin",
                    "marketplace",
                    "add",
                    str(roots.checkout),
                    "--json",
                ),
                roots,
                environment,
            )
        ]
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
        for plugin in plugins:
            script = (
                roots.checkout
                / "dist"
                / self.agent.value
                / plugin
                / "skills"
                / f"{plugin}-plugin"
                / PLACEMENT_SCRIPT_RELATIVE_PATH
            )
            if script.is_file():
                commands.append(
                    _command(
                        self.agent,
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


def build_installation_plan(
    checkout: Path,
    state_root: Path,
    base_environment: Mapping[str, str],
) -> InstallationPlan:
    """Build an immutable plan from the checkout's committed catalogs."""
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
    claude_plugins = catalog_plugin_names(resolved_checkout / CLAUDE_CATALOG_PATH)
    codex_plugins = catalog_plugin_names(resolved_checkout / CODEX_CATALOG_PATH)
    environment = installation_environment(roots, base_environment)
    plugins_by_agent = {
        Agent.CLAUDE: claude_plugins,
        Agent.CODEX: codex_plugins,
    }
    commands = tuple(
        command
        for adapter in AGENT_ADAPTERS
        for command in adapter.commands(
            roots,
            environment,
            plugins_by_agent[adapter.agent],
        )
    )
    return InstallationPlan(
        roots=roots,
        claude_plugins=claude_plugins,
        codex_plugins=codex_plugins,
        commands=commands,
    )


def catalog_plugin_names(catalog_path: Path) -> tuple[str, ...]:
    """Read and validate the ordered plugin names in one catalog."""
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


def installed_plugin_names(agent: Agent, payload: str) -> frozenset[str]:
    """Parse installed and enabled marketplace plugin names from CLI JSON."""
    try:
        document = cast(object, json.loads(payload))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid {agent.value} plugin listing: {error}") from error
    entries: object
    if agent is Agent.CLAUDE:
        entries = document
    else:
        if not isinstance(document, dict):
            raise ValueError("Codex plugin listing must be a JSON object")
        entries = document.get(CODEX_INSTALLED_FIELD)
    if not isinstance(entries, list):
        raise ValueError(f"{agent.value} plugin listing must contain an array")
    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"{agent.value} plugin listing contains a non-object")
        plugin_id_field = (
            CLAUDE_PLUGIN_ID_FIELD if agent is Agent.CLAUDE else CODEX_PLUGIN_ID_FIELD
        )
        enabled_field = (
            CLAUDE_PLUGIN_ENABLED_FIELD
            if agent is Agent.CLAUDE
            else CODEX_PLUGIN_ENABLED_FIELD
        )
        plugin_id = entry.get(plugin_id_field)
        enabled = entry.get(enabled_field)
        if not isinstance(plugin_id, str) or not isinstance(enabled, bool):
            raise ValueError(
                f"{agent.value} plugin listing entry lacks typed identity or state"
            )
        suffix = f"@{MARKETPLACE_NAME}"
        if enabled and plugin_id.endswith(suffix):
            names.add(plugin_id.removesuffix(suffix))
    return frozenset(names)


def installation_environment(
    roots: InstallationRoots,
    base_environment: Mapping[str, str],
) -> tuple[tuple[str, str], ...]:
    """Return the explicit environment for every agent command."""
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


def execute_installation(
    plan: InstallationPlan,
    runner: CommandRunner,
) -> InstallationReport:
    """Execute commands in plan order and stop at the first failure."""
    for root in (
        plan.roots.state,
        plan.roots.home,
        plan.roots.claude_config,
        plan.roots.codex_home,
        plan.roots.codex_sqlite_home,
    ):
        root.mkdir(parents=True, exist_ok=True)
    completed: list[CommandResult] = []
    for command in plan.commands:
        result = runner(command)
        if result.argv != command.argv:
            raise ValueError(
                f"runner returned an argv different from {command.operation.value}"
            )
        result = _agent_adapter(command.agent).normalize_result(command, result)
        if result.exit_code != 0:
            raise InstallationFailure(command, result, tuple(completed))
        completed.append(result)
    return InstallationReport(plan=plan, results=tuple(completed))


def main(argv: Sequence[str] | None = None) -> int:
    """Run repository installation in a disposable or caller-selected home."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path.cwd())
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    arguments = parser.parse_args(argv)
    if arguments.state_root is not None:
        return _run_cli_installation(
            arguments.checkout,
            arguments.state_root,
            arguments.json_output,
        )
    with TemporaryDirectory(prefix="outcomeeng-install-") as temporary_directory:
        return _run_cli_installation(
            arguments.checkout,
            Path(temporary_directory),
            arguments.json_output,
        )


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


def _run_cli_installation(checkout: Path, state_root: Path, json_output: bool) -> int:
    try:
        plan = build_installation_plan(checkout, state_root, os.environ)
        report = execute_installation(plan, _real_runner)
    except InstallationFailure as failure:
        print(json.dumps(_failure_document(failure), sort_keys=True), file=sys.stderr)
        return failure.result.exit_code
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, sort_keys=True), file=sys.stderr)
        return 1
    if json_output:
        print(json.dumps(_report_document(report), sort_keys=True))
    else:
        print(f"installed {len(report.plan.claude_plugins)} Claude plugins")
        print(f"installed {len(report.plan.codex_plugins)} Codex plugins")
    return 0


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
        "claude_plugins": list(report.plan.claude_plugins),
        "codex_plugins": list(report.plan.codex_plugins),
        "completed_operations": len(report.results),
        "state_root": str(report.plan.roots.state),
        "checkout": str(report.plan.roots.checkout),
    }


__all__ = [
    "AGENT_ADAPTERS",
    "Agent",
    "AgentAdapter",
    "CATALOG_PLUGIN_NAME_FIELD",
    "CATALOG_PLUGINS_FIELD",
    "CLAUDE_EXECUTABLE",
    "CLAUDE_CATALOG_PATH",
    "CLAUDE_ALREADY_ENABLED_FRAGMENT",
    "CLAUDE_CONFIG_ENV",
    "CLAUDE_LIST_COMMAND",
    "CLAUDE_PLUGIN_ENABLED_FIELD",
    "CLAUDE_PLUGIN_ID_FIELD",
    "ClaudeInstallationAdapter",
    "CODEX_AGENTS_PATH",
    "CODEX_CATALOG_PATH",
    "CODEX_CONFIG_PATH",
    "CODEX_EXECUTABLE",
    "CODEX_HOME_ENV",
    "CODEX_INSTALLED_FIELD",
    "CODEX_PLUGIN_ENABLED_FIELD",
    "CODEX_PLUGIN_ID_FIELD",
    "CODEX_LIST_COMMAND",
    "CODEX_SQLITE_HOME_ENV",
    "CodexInstallationAdapter",
    "CommandResult",
    "CommandRunner",
    "HOME_ENV",
    "InstallationCommand",
    "InstallationFailure",
    "InstallationPlan",
    "InstallationReport",
    "InstallationRoots",
    "MARKETPLACE_NAME",
    "Operation",
    "STATE_ENV_NAMES",
    "build_installation_plan",
    "catalog_plugin_names",
    "execute_installation",
    "installation_environment",
    "installed_plugin_names",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
