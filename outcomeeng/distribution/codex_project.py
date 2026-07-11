"""Generate checkout-local Codex runtime configuration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, cast

from outcomeeng.distribution.agents import (
    AgentConversionError,
    CodexAgent,
    convert_agents,
    install_agents,
    render_toml_document,
)

PROJECT_CONFIG_RELATIVE_PATH: Final = Path(".codex/config.toml")
PROJECT_CODEX_HOME_RELATIVE_PATH: Final = Path(".codex/runtime")
CODEX_HOME_AGENTS_RELATIVE_PATH: Final = Path("agents")
CODEX_HOME_CONFIG_FILENAME: Final = "config.toml"
CODEX_DIST_RELATIVE_PATH: Final = Path("dist/codex")
CODEX_MARKETPLACE_RELATIVE_PATH: Final = Path(".agents/plugins/marketplace.json")
CODEX_LOCAL_RECIPE_NAME: Final = "codex-local"
CODEX_LOCAL_BUILD_ARGV: Final = ("just", "build-skills")
PROJECT_RUNTIME_BUILD_ARGV: Final = (
    "uv",
    "run",
    "--no-cache",
    "python",
    "-m",
    "outcomeeng.distribution.codex_project",
    ".",
)

ADDITIONAL_PROJECT_PLUGIN_ENABLEMENT: Final[dict[str, bool]] = {
    "taches-cc-resources@taches-cc-resources": True,
}

CONFIG_AGENTS_KEY: Final = "agents"
CONFIG_FILE_KEY: Final = "config_file"
CONFIG_PLUGINS_KEY: Final = "plugins"
DESCRIPTION_KEY: Final = "description"
ENABLED_KEY: Final = "enabled"
NAME_KEY: Final = "name"
PROJECTS_KEY: Final = "projects"
TRUST_LEVEL_KEY: Final = "trust_level"
TRUSTED_VALUE: Final = "trusted"

CODEX_COMMAND: Final = "codex"
CODEX_HOME_ENV: Final = "CODEX_HOME"
CODEX_LOCAL_LAUNCH_ARGV: Final = (
    f"{CODEX_HOME_ENV}=$PWD/{PROJECT_CODEX_HOME_RELATIVE_PATH.as_posix()}",
    CODEX_COMMAND,
    "{{args}}",
)
CODEX_MARKETPLACE_LIST_ARGS: Final = ("plugin", "marketplace", "list", "--json")
CODEX_MARKETPLACE_ADD_ARGS: Final = ("plugin", "marketplace", "add")
CODEX_PLUGIN_ADD_ARGS: Final = ("plugin", "add")
MARKETPLACE_NAME_KEY: Final = "name"
MARKETPLACE_ROOT_KEY: Final = "root"
MARKETPLACES_KEY: Final = "marketplaces"
PLUGINS_KEY: Final = "plugins"


class CommandRunner(Protocol):
    """Run one bounded Codex CLI command."""

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
    ) -> subprocess.CompletedProcess[str]: ...


@dataclass(frozen=True)
class ProjectRuntimePaths:
    """Filesystem locations for one generated project runtime."""

    project_root: Path
    source_root: Path
    dist_root: Path
    config_path: Path
    agents_root: Path
    codex_home: Path


@dataclass(frozen=True)
class Marketplace:
    """Checkout-local marketplace identity and plugin set."""

    name: str
    plugins: tuple[str, ...]


class ProjectRuntimeError(RuntimeError):
    """Raised when project runtime generation or verification fails."""


def project_runtime_paths(
    project_root: Path,
    *,
    source_root: Path | None = None,
    dist_root: Path | None = None,
    codex_home: Path | None = None,
) -> ProjectRuntimePaths:
    """Return normalized project-runtime paths."""
    root = project_root.resolve()
    source = (source_root or root).resolve()
    runtime_home = (codex_home or root / PROJECT_CODEX_HOME_RELATIVE_PATH).resolve()
    return ProjectRuntimePaths(
        project_root=root,
        source_root=source,
        dist_root=(dist_root or source / CODEX_DIST_RELATIVE_PATH).resolve(),
        config_path=root / PROJECT_CONFIG_RELATIVE_PATH,
        agents_root=runtime_home / CODEX_HOME_AGENTS_RELATIVE_PATH,
        codex_home=runtime_home,
    )


def render_project_config(paths: ProjectRuntimePaths) -> str:
    """Render project plugin enablement."""
    values: dict[str, object] = {
        CONFIG_PLUGINS_KEY: {
            plugin: {ENABLED_KEY: enabled}
            for plugin, enabled in _project_plugin_enablement(paths).items()
        },
    }
    return render_toml_document(values)


def build_project_runtime(
    project_root: Path,
    *,
    source_root: Path | None = None,
    codex_home: Path | None = None,
    command_runner: CommandRunner | None = None,
) -> tuple[Path, ...]:
    """Generate checkout-local Codex plugins, agents, and project config."""
    paths = project_runtime_paths(
        project_root,
        source_root=source_root,
        codex_home=codex_home,
    )
    _prepare_local_plugins(paths, command_runner or _run_command)
    installed = install_agents(paths.dist_root, paths.agents_root)
    _configure_local_runtime(paths, convert_agents(paths.dist_root))
    paths.config_path.parent.mkdir(parents=True, exist_ok=True)
    paths.config_path.write_text(render_project_config(paths), encoding="utf-8")
    return (paths.config_path, *installed)


def main(argv: Sequence[str] | None = None) -> int:
    """Generate checkout-local Codex runtime configuration."""
    arguments = tuple(argv or ())
    project_root = Path(arguments[0]) if arguments else Path.cwd()
    try:
        written = build_project_runtime(project_root)
    except (AgentConversionError, OSError, ProjectRuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"generated {len(written)} project-scoped Codex runtime file(s)")
    return 0


def _agent_bindings(agents: tuple[CodexAgent, ...]) -> dict[str, object]:
    bindings: dict[str, object] = {}
    for agent in agents:
        name = _required_string(agent.values, NAME_KEY)
        bindings[name] = {
            DESCRIPTION_KEY: _required_string(agent.values, DESCRIPTION_KEY),
            CONFIG_FILE_KEY: str(Path("agents") / agent.filename),
        }
    return bindings


def _required_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ProjectRuntimeError(f"converted agent has no string {key!r}")
    return value


def _project_plugin_enablement(paths: ProjectRuntimePaths) -> dict[str, bool]:
    marketplace = _load_marketplace(paths.source_root)
    local_plugins = {
        f"{plugin}@{marketplace.name}": True for plugin in marketplace.plugins
    }
    return {**local_plugins, **ADDITIONAL_PROJECT_PLUGIN_ENABLEMENT}


def _load_marketplace(source_root: Path) -> Marketplace:
    catalog_path = source_root / CODEX_MARKETPLACE_RELATIVE_PATH
    with catalog_path.open("rb") as stream:
        document = json.load(stream)
    catalog = _as_mapping(document)
    plugins = tuple(
        _required_string(plugin, NAME_KEY)
        for plugin in _required_list(catalog, PLUGINS_KEY)
    )
    return Marketplace(
        name=_required_string(catalog, NAME_KEY),
        plugins=plugins,
    )


def _prepare_local_plugins(
    paths: ProjectRuntimePaths,
    runner: CommandRunner,
) -> None:
    paths.codex_home.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, CODEX_HOME_ENV: str(paths.codex_home)}
    marketplace = _load_marketplace(paths.source_root)
    listed = _run_codex_json(
        (CODEX_COMMAND, *CODEX_MARKETPLACE_LIST_ARGS),
        cwd=paths.source_root,
        env=environment,
        runner=runner,
    )
    matching = tuple(
        entry
        for entry in _required_list(listed, MARKETPLACES_KEY)
        if entry.get(MARKETPLACE_NAME_KEY) == marketplace.name
    )
    if not matching:
        _run_codex_json(
            (
                CODEX_COMMAND,
                *CODEX_MARKETPLACE_ADD_ARGS,
                str(paths.source_root),
                "--json",
            ),
            cwd=paths.source_root,
            env=environment,
            runner=runner,
        )
    elif len(matching) != 1:
        raise ProjectRuntimeError(
            f"checkout-local Codex home has duplicate {marketplace.name!r} marketplaces"
        )
    else:
        configured_root = Path(
            _required_string(matching[0], MARKETPLACE_ROOT_KEY)
        ).resolve()
        if configured_root != paths.source_root:
            raise ProjectRuntimeError(
                f"checkout-local marketplace {marketplace.name!r} resolves to "
                f"{configured_root}, expected {paths.source_root}"
            )

    for plugin in marketplace.plugins:
        _run_codex_json(
            (
                CODEX_COMMAND,
                *CODEX_PLUGIN_ADD_ARGS,
                f"{plugin}@{marketplace.name}",
                "--json",
            ),
            cwd=paths.source_root,
            env=environment,
            runner=runner,
        )


def _configure_local_runtime(
    paths: ProjectRuntimePaths,
    agents: tuple[CodexAgent, ...],
) -> None:
    config_path = paths.codex_home / CODEX_HOME_CONFIG_FILENAME
    if config_path.is_file():
        with config_path.open("rb") as stream:
            loaded = tomllib.load(stream)
        values = dict(loaded)
    else:
        values = {}
    projects = dict(_optional_mapping(values.get(PROJECTS_KEY)))
    projects[str(paths.project_root)] = {TRUST_LEVEL_KEY: TRUSTED_VALUE}
    values[PROJECTS_KEY] = projects
    values[CONFIG_AGENTS_KEY] = _agent_bindings(agents)
    config_path.write_text(render_toml_document(values), encoding="utf-8")


def _run_codex_json(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    runner: CommandRunner,
) -> Mapping[str, object]:
    completed = runner(argv, cwd=cwd, env=env)
    if completed.returncode != 0:
        raise ProjectRuntimeError(completed.stderr.strip())
    try:
        return _as_mapping(json.loads(completed.stdout))
    except json.JSONDecodeError as exc:
        raise ProjectRuntimeError(
            f"Codex command returned invalid JSON: {' '.join(argv)}"
        ) from exc


def _run_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _required_mapping(
    values: Mapping[str, object],
    key: str,
) -> Mapping[str, object]:
    return _as_mapping(values.get(key))


def _as_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ProjectRuntimeError("Codex response field is not an object")
    return cast(Mapping[str, object], value)


def _optional_mapping(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    return _as_mapping(value)


def _required_list(
    values: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ProjectRuntimeError(f"Codex response field {key!r} is not an array")
    return tuple(_as_mapping(item) for item in value)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
