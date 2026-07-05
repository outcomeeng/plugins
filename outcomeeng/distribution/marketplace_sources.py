"""Marketplace source discovery for maintainer refresh workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

DEFAULT_MARKETPLACE = "outcomeeng"
SOURCE_TYPE_GIT = "git"
SOURCE_TYPE_LOCAL = "local"
CLAUDE_MARKETPLACE_LIST_COMMAND = (
    "claude",
    "plugin",
    "marketplace",
    "list",
    "--json",
)
CLAUDE_MARKETPLACE_ADD_COMMAND = (
    "claude",
    "plugin",
    "marketplace",
    "add",
)
CLAUDE_MARKETPLACE_REMOVE_COMMAND = (
    "claude",
    "plugin",
    "marketplace",
    "remove",
)
CLAUDE_PLUGIN_LIST_COMMAND = (
    "claude",
    "plugin",
    "list",
    "--json",
)
CLAUDE_PLUGIN_INSTALL_COMMAND = (
    "claude",
    "plugin",
    "install",
)
CLAUDE_PLUGIN_ENABLE_COMMAND = (
    "claude",
    "plugin",
    "enable",
)
CLAUDE_PLUGIN_DISABLE_COMMAND = (
    "claude",
    "plugin",
    "disable",
)
CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT = "already installed"
CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT = "already enabled"
CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT = "already disabled"
CLAUDE_SCOPE_USER = "user"
CLAUDE_SCOPE_PROJECT = "project"
CLAUDE_SCOPE_LOCAL = "local"
CODEX_MARKETPLACE_LIST_COMMAND = (
    "codex",
    "plugin",
    "marketplace",
    "list",
    "--json",
)
CODEX_MARKETPLACE_ADD_COMMAND = (
    "codex",
    "plugin",
    "marketplace",
    "add",
)
CODEX_MARKETPLACE_REMOVE_COMMAND = (
    "codex",
    "plugin",
    "marketplace",
    "remove",
)
DIST_CODEX_PLUGINS_DIR = Path("dist") / "codex"
CODEX_PLUGIN_MANIFEST = Path(".codex-plugin") / "plugin.json"


class CommandRunner(Protocol):
    """Runs a runtime CLI command, optionally from a scoped working directory."""

    def __call__(
        self, command: list[str], *, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]: ...


class MarketplaceSourceError(RuntimeError):
    """Marketplace source discovery failed or reported an unsupported shape."""


@dataclass(frozen=True)
class MarketplaceSource:
    """Configured marketplace source reported by a runtime CLI."""

    name: str
    source_type: str
    path: Path | None = None
    url: str | None = None
    scope: str | None = None
    project_path: Path | None = None


@dataclass(frozen=True)
class CodexDistPlugin:
    """Plugin manifest discovered under ``dist/codex``."""

    name: str
    version: str
    root: Path


@dataclass(frozen=True)
class ClaudeInstalledPlugin:
    """Claude Code plugin selection that can be restored after source repair."""

    name: str
    marketplace: str
    scope: str
    enabled: bool
    project_path: Path | None = None
    restore_cwd: Path | None = None

    @property
    def ref(self) -> str:
        return f"{self.name}@{self.marketplace}"


@dataclass(frozen=True)
class ClaudeSettingsPaths:
    """Claude Code settings files that can declare marketplace sources."""

    user: Path
    project: Path
    local: Path


@dataclass(frozen=True)
class MarketplaceConfigRepairResult:
    """Result of reconciling runtime marketplace source configuration."""

    root: Path
    changed: bool
    commands: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ClaudeMarketplaceRepairTarget:
    """Claude marketplace declaration whose scope is being repaired."""

    scope: str | None
    source: MarketplaceSource | None
    project_path: Path | None = None


def run_command_capture(
    command: list[str], *, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True, cwd=cwd)


def parse_claude_marketplace_sources(payload: str) -> dict[str, MarketplaceSource]:
    """Parse ``claude plugin marketplace list --json`` output by marketplace name."""
    return _parse_marketplace_sources(payload, runtime="Claude Code")


def parse_claude_installed_plugins(
    payload: str, marketplace: str
) -> tuple[ClaudeInstalledPlugin, ...]:
    """Parse installed Claude Code plugin selections for one marketplace."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise MarketplaceSourceError(
            f"Claude Code plugin list output is not valid JSON: {exc}"
        ) from exc
    if not isinstance(data, list):
        raise MarketplaceSourceError("Claude Code plugin list output is not an array")
    plugins: list[ClaudeInstalledPlugin] = []
    for entry in data:
        if not isinstance(entry, dict):
            raise MarketplaceSourceError(
                "Claude Code plugin list entry is not an object"
            )
        plugin_id = entry.get("id")
        if not isinstance(plugin_id, str):
            raise MarketplaceSourceError(
                "Claude Code plugin list entry has no string id"
            )
        parsed = _parse_plugin_ref(plugin_id)
        if parsed is None:
            continue
        name, plugin_marketplace = parsed
        if plugin_marketplace != marketplace:
            continue
        scope = entry.get("scope")
        if not isinstance(scope, str):
            raise MarketplaceSourceError(
                f"Claude Code plugin `{plugin_id}` has no string scope"
            )
        enabled = entry.get("enabled")
        if not isinstance(enabled, bool):
            raise MarketplaceSourceError(
                f"Claude Code plugin `{plugin_id}` has no boolean enabled state"
            )
        project_path = _optional_path(entry.get("projectPath"))
        if scope in {"project", "local"} and project_path is None:
            raise MarketplaceSourceError(
                f"Claude Code plugin `{plugin_id}` with {scope} scope has no "
                "projectPath"
            )
        plugins.append(
            ClaudeInstalledPlugin(
                name=name,
                marketplace=plugin_marketplace,
                scope=scope,
                enabled=enabled,
                project_path=project_path,
            )
        )
    return tuple(plugins)


def parse_codex_marketplace_sources(payload: str) -> dict[str, MarketplaceSource]:
    """Parse ``codex plugin marketplace list --json`` output by marketplace name."""
    return _parse_marketplace_sources(payload, runtime="Codex")


def configured_local_marketplace_root(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    runner: CommandRunner = run_command_capture,
) -> Path:
    """Return the shared local marketplace root after validating both runtimes."""
    claude_result = _run_json_command(
        [*CLAUDE_MARKETPLACE_LIST_COMMAND],
        runner=runner,
    )
    codex_result = _run_json_command(
        [*CODEX_MARKETPLACE_LIST_COMMAND],
        runner=runner,
    )
    return require_matching_local_sources(
        marketplace,
        claude_sources=parse_claude_marketplace_sources(claude_result.stdout or ""),
        codex_sources=parse_codex_marketplace_sources(codex_result.stdout or ""),
    )


def ensure_local_marketplace_sources(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    source_root: Path | None = None,
    claude_project_root: Path | None = None,
    claude_settings_paths: ClaudeSettingsPaths | None = None,
    runner: CommandRunner = run_command_capture,
) -> MarketplaceConfigRepairResult:
    """Reconcile Claude Code and Codex to one local marketplace source."""
    claude_result = _run_json_command(
        [*CLAUDE_MARKETPLACE_LIST_COMMAND],
        runner=runner,
    )
    codex_result = _run_json_command(
        [*CODEX_MARKETPLACE_LIST_COMMAND],
        runner=runner,
    )
    claude_sources = parse_claude_marketplace_sources(claude_result.stdout or "")
    codex_sources = parse_codex_marketplace_sources(codex_result.stdout or "")
    root = _canonical_source_root(
        marketplace,
        explicit_root=source_root,
        claude_sources=claude_sources,
        codex_sources=codex_sources,
    )
    commands: list[tuple[str, ...]] = []
    commands.extend(
        _repair_claude_runtime_source(
            marketplace,
            source=claude_sources.get(marketplace),
            root=root,
            project_root=claude_project_root,
            settings_paths=claude_settings_paths,
            runner=runner,
        )
    )
    commands.extend(
        _repair_runtime_source(
            marketplace,
            source=codex_sources.get(marketplace),
            root=root,
            add_command=CODEX_MARKETPLACE_ADD_COMMAND,
            remove_command=CODEX_MARKETPLACE_REMOVE_COMMAND,
            runner=runner,
        )
    )
    return MarketplaceConfigRepairResult(
        root=root,
        changed=bool(commands),
        commands=tuple(commands),
    )


def require_matching_local_sources(
    marketplace: str,
    *,
    claude_sources: dict[str, MarketplaceSource],
    codex_sources: dict[str, MarketplaceSource],
) -> Path:
    """Validate that Claude Code and Codex share one local marketplace root."""
    claude = _required_source(claude_sources, marketplace, runtime="Claude Code")
    codex = _required_source(codex_sources, marketplace, runtime="Codex")
    if claude.source_type != SOURCE_TYPE_LOCAL or claude.path is None:
        raise MarketplaceSourceError(
            f"Claude Code marketplace `{marketplace}` must be a local Directory "
            f"source with a path; found {claude.source_type}"
        )
    if codex.source_type != SOURCE_TYPE_LOCAL or codex.path is None:
        raise MarketplaceSourceError(
            f"Codex marketplace `{marketplace}` must be registered as a local "
            f"source matching {claude.path}; found {codex.source_type}"
        )
    claude_path = _normalized_path(claude.path)
    codex_path = _normalized_path(codex.path)
    if claude_path != codex_path:
        raise MarketplaceSourceError(
            f"Codex marketplace `{marketplace}` local path {codex.path} does not "
            f"match Claude Code Directory source {claude.path}"
        )
    return claude_path


def available_codex_plugins(repo_root: Path) -> tuple[CodexDistPlugin, ...]:
    """Read addable Codex plugins from ``dist/codex`` manifests."""
    plugins_dir = repo_root / DIST_CODEX_PLUGINS_DIR
    if not plugins_dir.is_dir():
        return ()
    plugins: list[CodexDistPlugin] = []
    for child in sorted(plugins_dir.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        manifest = child / CODEX_PLUGIN_MANIFEST
        if not manifest.is_file():
            continue
        try:
            data = json.loads(manifest.read_text())
        except json.JSONDecodeError as exc:
            raise MarketplaceSourceError(
                f"invalid Codex plugin manifest JSON: {manifest}: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise MarketplaceSourceError(
                f"Codex plugin manifest is not a JSON object: {manifest}"
            )
        version = data.get("version")
        if not isinstance(version, str):
            raise MarketplaceSourceError(
                f"Codex plugin manifest has no string version: {manifest}"
            )
        plugins.append(CodexDistPlugin(name=child.name, version=version, root=child))
    return tuple(plugins)


def _parse_marketplace_sources(
    payload: str, *, runtime: str
) -> dict[str, MarketplaceSource]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise MarketplaceSourceError(
            f"{runtime} marketplace list output is not valid JSON: {exc}"
        ) from exc
    entries = tuple(_marketplace_entries(data, runtime=runtime))
    sources: dict[str, MarketplaceSource] = {}
    for entry in entries:
        name = entry.get("name")
        if not isinstance(name, str):
            raise MarketplaceSourceError(
                f"{runtime} marketplace entry has no string name"
            )
        source_entry = _source_entry(entry)
        source_type = _normalized_source_type(source_entry)
        sources[name] = MarketplaceSource(
            name=name,
            source_type=source_type,
            path=_path_field(source_entry, source_type),
            url=_url_field(source_entry, source_type),
            scope=_string_field(source_entry, ("scope",)),
            project_path=_optional_path(source_entry.get("projectPath")),
        )
    return sources


def _marketplace_entries(data: object, *, runtime: str) -> Iterable[dict[str, object]]:
    entries: object
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = _first_marketplace_array(data)
    else:
        raise MarketplaceSourceError(
            f"{runtime} marketplace list output is not an object or array"
        )
    if not isinstance(entries, list):
        raise MarketplaceSourceError(
            f"{runtime} marketplace list output has no marketplace array"
        )
    for entry in entries:
        if not isinstance(entry, dict):
            raise MarketplaceSourceError(
                f"{runtime} marketplace entry is not an object"
            )
        yield entry


def _first_marketplace_array(data: dict[str, object]) -> object:
    for key in ("marketplaces", "items", "entries", "configured"):
        if key in data:
            return data[key]
    return None


def _source_entry(entry: dict[str, object]) -> dict[str, object]:
    source = entry.get("marketplaceSource")
    if not isinstance(source, dict):
        return entry
    # Codex reports the marketplace name and installed root at the top level, with
    # the durable configured source nested under `marketplaceSource`.
    merged = dict(entry)
    merged.update(source)
    return merged


def _normalized_source_type(entry: dict[str, object]) -> str:
    raw = _string_field(entry, ("sourceType", "source_type", "source"))
    if raw is None:
        if _path_field(entry, SOURCE_TYPE_LOCAL) is not None:
            return SOURCE_TYPE_LOCAL
        return ""
    lowered = raw.strip().lower()
    if lowered.startswith("directory") or lowered in {"local", "path"}:
        return SOURCE_TYPE_LOCAL
    if lowered in {SOURCE_TYPE_GIT, "github"} or lowered.startswith("http"):
        return SOURCE_TYPE_GIT
    return lowered


def _path_field(entry: dict[str, object], source_type: str) -> Path | None:
    raw = _string_field(entry, ("path", "directory", "localPath", "sourcePath"))
    if raw is None and source_type == SOURCE_TYPE_LOCAL:
        raw = _string_field(entry, ("source",))
    if raw is None:
        return None
    return Path(raw).expanduser()


def _path_field_relative_to(
    entry: dict[str, object], source_type: str, base: Path
) -> Path | None:
    path = _path_field(entry, source_type)
    if path is None or path.is_absolute():
        return path
    return base / path


def _url_field(entry: dict[str, object], source_type: str) -> str | None:
    raw = _string_field(entry, ("url", "repo", "repository"))
    if raw is not None:
        return raw
    source = _string_field(entry, ("source",))
    if source is not None and (
        source_type == SOURCE_TYPE_GIT or source.strip().lower().startswith("http")
    ):
        return source
    return None


def _string_field(entry: dict[str, object], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = entry.get(name)
        if isinstance(value, str):
            return value
    return None


def _optional_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    return Path(value).expanduser()


def _parse_plugin_ref(plugin_id: str) -> tuple[str, str] | None:
    if "@" not in plugin_id:
        return None
    name, marketplace = plugin_id.rsplit("@", maxsplit=1)
    if not name or not marketplace:
        return None
    return name, marketplace


def _required_source(
    sources: dict[str, MarketplaceSource], marketplace: str, *, runtime: str
) -> MarketplaceSource:
    try:
        return sources[marketplace]
    except KeyError as exc:
        raise MarketplaceSourceError(
            f"{runtime} marketplace `{marketplace}` is not configured"
        ) from exc


def _normalized_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _canonical_source_root(
    marketplace: str,
    *,
    explicit_root: Path | None,
    claude_sources: dict[str, MarketplaceSource],
    codex_sources: dict[str, MarketplaceSource],
) -> Path:
    if explicit_root is not None:
        return _normalized_path(explicit_root)
    claude = claude_sources.get(marketplace)
    if (
        claude is not None
        and claude.source_type == SOURCE_TYPE_LOCAL
        and claude.path is not None
    ):
        return _normalized_path(claude.path)
    codex = codex_sources.get(marketplace)
    if (
        codex is not None
        and codex.source_type == SOURCE_TYPE_LOCAL
        and codex.path is not None
    ):
        return _normalized_path(codex.path)
    return _normalized_path(Path.cwd())


def _repair_runtime_source(
    marketplace: str,
    *,
    source: MarketplaceSource | None,
    root: Path,
    add_command: tuple[str, ...],
    remove_command: tuple[str, ...],
    runner: CommandRunner,
) -> tuple[tuple[str, ...], ...]:
    if _source_matches(source, root):
        return ()
    commands: list[tuple[str, ...]] = []
    if source is not None:
        remove = (*remove_command, marketplace)
        _run_json_command(list(remove), runner=runner)
        commands.append(remove)
    add = (*add_command, str(root))
    _run_json_command(list(add), runner=runner)
    commands.append(add)
    return tuple(commands)


def _repair_claude_runtime_source(
    marketplace: str,
    *,
    source: MarketplaceSource | None,
    root: Path,
    project_root: Path | None,
    settings_paths: ClaudeSettingsPaths | None,
    runner: CommandRunner,
) -> tuple[tuple[str, ...], ...]:
    resolved_project_root = _normalized_path(project_root or root)
    resolved_settings_paths = (
        _default_claude_settings_paths(resolved_project_root)
        if settings_paths is None
        else settings_paths
    )
    scoped_sources = _claude_marketplace_sources_from_settings(
        marketplace,
        resolved_settings_paths,
        project_root=resolved_project_root,
    )
    if _claude_runtime_source_matches(source, root, resolved_project_root) and all(
        _scoped_claude_source_matches(scoped_source, root, resolved_project_root)
        for scoped_source in scoped_sources
    ):
        return ()
    repair_targets = _claude_repair_targets(
        source=source,
        scoped_sources=scoped_sources,
        root=root,
        project_root=resolved_project_root,
    )
    preserved = _claude_plugins_to_preserve(
        marketplace,
        repair_targets=repair_targets,
        runner=runner,
    )
    commands: list[tuple[str, ...]] = []
    for target in repair_targets:
        cwd = _claude_repair_cwd(target)
        if target.source is not None:
            remove = _claude_marketplace_repair_command(
                CLAUDE_MARKETPLACE_REMOVE_COMMAND,
                target=target,
                argument=marketplace,
            )
            _run_json_command(list(remove), runner=runner, cwd=cwd)
            commands.append(remove)
        add = _claude_marketplace_repair_command(
            CLAUDE_MARKETPLACE_ADD_COMMAND,
            target=target,
            argument=str(root),
        )
        _run_json_command(list(add), runner=runner, cwd=cwd)
        commands.append(add)
    commands.extend(_restore_claude_plugins(preserved, runner=runner))
    return tuple(commands)


def _claude_plugins_to_preserve(
    marketplace: str,
    *,
    repair_targets: tuple[ClaudeMarketplaceRepairTarget, ...],
    runner: CommandRunner,
) -> tuple[ClaudeInstalledPlugin, ...]:
    if not repair_targets:
        return ()
    snapshot_cwd = _claude_plugin_snapshot_cwd(repair_targets)
    result = _run_json_command(
        [*CLAUDE_PLUGIN_LIST_COMMAND],
        runner=runner,
        cwd=snapshot_cwd,
    )
    return tuple(
        preserved
        for plugin in parse_claude_installed_plugins(result.stdout or "", marketplace)
        if (
            preserved := _claude_plugin_preserved_for_repair_targets(
                plugin, repair_targets
            )
        )
        is not None
    )


def _claude_repair_targets(
    *,
    source: MarketplaceSource | None,
    scoped_sources: tuple[MarketplaceSource, ...],
    root: Path,
    project_root: Path,
) -> tuple[ClaudeMarketplaceRepairTarget, ...]:
    targets: list[ClaudeMarketplaceRepairTarget] = []
    runtime_source_matches = _claude_runtime_source_matches(source, root, project_root)
    unscoped_runtime_repair = (
        source is not None
        and not runtime_source_matches
        and source.scope
        not in {
            CLAUDE_SCOPE_USER,
            CLAUDE_SCOPE_PROJECT,
            CLAUDE_SCOPE_LOCAL,
        }
    )
    for scoped_source in scoped_sources:
        target = ClaudeMarketplaceRepairTarget(
            scope=scoped_source.scope or CLAUDE_SCOPE_PROJECT,
            source=scoped_source,
            project_path=scoped_source.project_path or project_root,
        )
        if not _scoped_claude_source_matches(scoped_source, root, project_root):
            targets.append(target)
        elif source is None or unscoped_runtime_repair:
            targets.append(
                ClaudeMarketplaceRepairTarget(
                    scope=target.scope,
                    source=None,
                    project_path=target.project_path,
                )
            )
    if runtime_source_matches:
        return _unique_claude_repair_targets(targets)
    if source is not None and source.scope in {
        CLAUDE_SCOPE_USER,
        CLAUDE_SCOPE_PROJECT,
        CLAUDE_SCOPE_LOCAL,
    }:
        targets.append(
            ClaudeMarketplaceRepairTarget(
                scope=source.scope,
                source=source,
                project_path=project_root,
            ),
        )
        return _unique_claude_repair_targets(targets)
    if source is not None:
        targets.insert(
            0,
            ClaudeMarketplaceRepairTarget(
                scope=None,
                source=source,
                project_path=None,
            ),
        )
        return _unique_claude_repair_targets(targets)
    if targets:
        return _unique_claude_repair_targets(targets)
    return (
        ClaudeMarketplaceRepairTarget(
            scope=None,
            source=None,
            project_path=None,
        ),
    )


def _unique_claude_repair_targets(
    targets: list[ClaudeMarketplaceRepairTarget],
) -> tuple[ClaudeMarketplaceRepairTarget, ...]:
    unique: list[ClaudeMarketplaceRepairTarget] = []
    seen: set[tuple[str | None, Path | None]] = set()
    for target in targets:
        key = (
            target.scope,
            _normalized_path(target.project_path) if target.project_path else None,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(target)
    return tuple(unique)


def _claude_plugin_belongs_to_repair_targets(
    plugin: ClaudeInstalledPlugin,
    repair_targets: tuple[ClaudeMarketplaceRepairTarget, ...],
) -> bool:
    return (
        _claude_plugin_preserved_for_repair_targets(plugin, repair_targets) is not None
    )


def _claude_plugin_preserved_for_repair_targets(
    plugin: ClaudeInstalledPlugin,
    repair_targets: tuple[ClaudeMarketplaceRepairTarget, ...],
) -> ClaudeInstalledPlugin | None:
    if plugin.scope == CLAUDE_SCOPE_USER:
        if any(target.scope in {None, CLAUDE_SCOPE_USER} for target in repair_targets):
            return plugin
        for target in repair_targets:
            if target.scope in {CLAUDE_SCOPE_PROJECT, CLAUDE_SCOPE_LOCAL}:
                return replace(plugin, restore_cwd=_claude_repair_cwd(target))
        return None
    for target in repair_targets:
        if target.scope is None:
            continue
        if target.scope == CLAUDE_SCOPE_USER and plugin.scope in {
            CLAUDE_SCOPE_PROJECT,
            CLAUDE_SCOPE_LOCAL,
        }:
            if plugin.project_path is None or target.project_path is None:
                continue
            if _normalized_path(plugin.project_path) == _normalized_path(
                target.project_path
            ):
                return plugin
            continue
        if target.scope in {
            CLAUDE_SCOPE_PROJECT,
            CLAUDE_SCOPE_LOCAL,
        } and plugin.scope in {
            CLAUDE_SCOPE_PROJECT,
            CLAUDE_SCOPE_LOCAL,
        }:
            if plugin.project_path is None or target.project_path is None:
                continue
            if _normalized_path(plugin.project_path) == _normalized_path(
                target.project_path
            ):
                return plugin
            continue
    return None


def _claude_marketplace_repair_command(
    base_command: tuple[str, ...],
    *,
    target: ClaudeMarketplaceRepairTarget,
    argument: str,
) -> tuple[str, ...]:
    if target.scope is None:
        return (*base_command, argument)
    return (*base_command, "--scope", target.scope, argument)


def _restore_claude_plugins(
    plugins: tuple[ClaudeInstalledPlugin, ...],
    *,
    runner: CommandRunner,
) -> tuple[tuple[str, ...], ...]:
    commands: list[tuple[str, ...]] = []
    for plugin in plugins:
        cwd = _claude_restore_cwd(plugin)
        install = (*CLAUDE_PLUGIN_INSTALL_COMMAND, "--scope", plugin.scope, plugin.ref)
        _run_claude_plugin_restore_command(
            install,
            runner=runner,
            cwd=cwd,
            already_satisfied_fragment=CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT,
            plugin_ref=plugin.ref,
            plugin_scope=plugin.scope,
        )
        commands.append(install)
        state_command = (
            CLAUDE_PLUGIN_ENABLE_COMMAND
            if plugin.enabled
            else CLAUDE_PLUGIN_DISABLE_COMMAND
        )
        restore_state = (*state_command, "--scope", plugin.scope, plugin.ref)
        _run_claude_plugin_restore_command(
            restore_state,
            runner=runner,
            cwd=cwd,
            already_satisfied_fragment=(
                CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT
                if plugin.enabled
                else CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT
            ),
            plugin_ref=plugin.ref,
            plugin_scope=plugin.scope,
        )
        commands.append(restore_state)
    return tuple(commands)


def _claude_plugin_snapshot_cwd(
    repair_targets: tuple[ClaudeMarketplaceRepairTarget, ...],
) -> Path | None:
    for target in repair_targets:
        if target.project_path is not None:
            return target.project_path
    return None


def _claude_restore_cwd(plugin: ClaudeInstalledPlugin) -> Path | None:
    if plugin.restore_cwd is not None:
        return plugin.restore_cwd
    if plugin.scope in {"project", "local"}:
        return plugin.project_path
    return None


def _claude_repair_cwd(target: ClaudeMarketplaceRepairTarget) -> Path | None:
    if target.scope in {CLAUDE_SCOPE_PROJECT, CLAUDE_SCOPE_LOCAL}:
        return target.project_path
    return None


def _source_matches(source: MarketplaceSource | None, root: Path) -> bool:
    return (
        source is not None
        and source.source_type == SOURCE_TYPE_LOCAL
        and source.path is not None
        and _normalized_path(source.path) == root
    )


def _scoped_claude_source_matches(
    source: MarketplaceSource,
    root: Path,
    project_root: Path,
) -> bool:
    if not _source_matches(source, root):
        return False
    if source.scope == CLAUDE_SCOPE_USER:
        return True
    if source.scope in {CLAUDE_SCOPE_PROJECT, CLAUDE_SCOPE_LOCAL}:
        return (
            source.project_path is not None
            and _normalized_path(source.project_path) == project_root
        )
    return False


def _claude_runtime_source_matches(
    source: MarketplaceSource | None,
    root: Path,
    project_root: Path,
) -> bool:
    if source is None:
        return False
    if source.scope in {CLAUDE_SCOPE_PROJECT, CLAUDE_SCOPE_LOCAL}:
        return _scoped_claude_source_matches(source, root, project_root)
    return _source_matches(source, root)


def _default_claude_settings_paths(project_root: Path) -> ClaudeSettingsPaths:
    return ClaudeSettingsPaths(
        user=Path.home() / ".claude" / "settings.json",
        project=project_root / ".claude" / "settings.json",
        local=project_root / ".claude" / "settings.local.json",
    )


def _claude_marketplace_sources_from_settings(
    marketplace: str,
    settings_paths: ClaudeSettingsPaths,
    *,
    project_root: Path,
) -> tuple[MarketplaceSource, ...]:
    sources = (
        _claude_marketplace_source_from_settings(
            marketplace,
            settings_paths.user,
            scope=CLAUDE_SCOPE_USER,
            project_root=None,
        ),
        _claude_marketplace_source_from_settings(
            marketplace,
            settings_paths.project,
            scope=CLAUDE_SCOPE_PROJECT,
            project_root=project_root,
        ),
        _claude_marketplace_source_from_settings(
            marketplace,
            settings_paths.local,
            scope=CLAUDE_SCOPE_LOCAL,
            project_root=project_root,
        ),
    )
    return tuple(source for source in sources if source is not None)


def _claude_marketplace_source_from_settings(
    marketplace: str,
    path: Path,
    *,
    scope: str,
    project_root: Path | None,
) -> MarketplaceSource | None:
    settings_file = _claude_settings_file_path(path, project_root=project_root)
    if not settings_file.is_file():
        return None
    try:
        data = json.loads(settings_file.read_text())
    except json.JSONDecodeError as exc:
        raise MarketplaceSourceError(
            f"Claude Code settings file is not valid JSON: {settings_file}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise MarketplaceSourceError(
            f"Claude Code settings file is not an object: {settings_file}"
        )
    marketplaces = data.get("extraKnownMarketplaces")
    if not isinstance(marketplaces, dict):
        return None
    entry = marketplaces.get(marketplace)
    if not isinstance(entry, dict):
        return None
    source = entry.get("source")
    if not isinstance(source, dict):
        return None
    source_type = _normalized_source_type(source)
    path_base = project_root or path.parent
    return MarketplaceSource(
        name=marketplace,
        source_type=source_type,
        path=_path_field_relative_to(source, source_type, path_base),
        url=_url_field(source, source_type),
        scope=scope,
        project_path=project_root,
    )


def _claude_settings_file_path(path: Path, *, project_root: Path | None) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute() or project_root is None:
        return expanded
    return project_root / expanded


def _run_json_command(
    command: list[str],
    *,
    runner: CommandRunner,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if cwd is None:
        result = runner(command)
    else:
        result = runner(command, cwd=cwd)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        raise MarketplaceSourceError(
            f"{' '.join(command)} exited {result.returncode}{detail}"
        )
    return result


def _run_claude_plugin_restore_command(
    command: tuple[str, ...],
    *,
    runner: CommandRunner,
    cwd: Path | None,
    already_satisfied_fragment: str,
    plugin_ref: str,
    plugin_scope: str,
) -> subprocess.CompletedProcess[str]:
    if cwd is None:
        result = runner(list(command))
    else:
        result = runner(list(command), cwd=cwd)
    if result.returncode == 0:
        return result
    stderr = (result.stderr or "").strip()
    if _is_claude_plugin_already_satisfied_error(
        command,
        stderr=stderr,
        already_satisfied_fragment=already_satisfied_fragment,
        plugin_ref=plugin_ref,
        plugin_scope=plugin_scope,
    ):
        return result
    detail = f": {stderr}" if stderr else ""
    raise MarketplaceSourceError(
        f"{' '.join(command)} exited {result.returncode}{detail}"
    )


def _is_claude_plugin_already_satisfied_error(
    command: tuple[str, ...],
    *,
    stderr: str,
    already_satisfied_fragment: str,
    plugin_ref: str,
    plugin_scope: str,
) -> bool:
    action = command[2]
    idempotent_message = (
        f'Plugin "{plugin_ref}" is {already_satisfied_fragment} at {plugin_scope} scope'
    )
    plain = f'Failed to {action} plugin "{plugin_ref}": {idempotent_message}'
    decorated = f"\u2718 {plain}"
    return stderr in {plain, decorated}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect configured marketplace source paths",
    )
    parser.add_argument(
        "command",
        choices=("root", "ensure"),
        help="Inspect or reconcile the shared local marketplace root",
    )
    parser.add_argument(
        "marketplace",
        nargs="?",
        default=DEFAULT_MARKETPLACE,
        help="Marketplace name",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print reconciliation result as JSON",
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "root":
            root = configured_local_marketplace_root(args.marketplace)
            print(root)
            return 0
        result = ensure_local_marketplace_sources(args.marketplace)
    except MarketplaceSourceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(
            json.dumps(
                {
                    "root": str(result.root),
                    "changed": result.changed,
                    "commands": [list(command) for command in result.commands],
                }
            )
        )
    else:
        status = "repaired" if result.changed else "already configured"
        print(f"{result.root} ({status})")
    return 0


__all__ = [
    "CLAUDE_MARKETPLACE_ADD_COMMAND",
    "CLAUDE_MARKETPLACE_LIST_COMMAND",
    "CLAUDE_MARKETPLACE_REMOVE_COMMAND",
    "CLAUDE_PLUGIN_ALREADY_DISABLED_FRAGMENT",
    "CLAUDE_PLUGIN_ALREADY_ENABLED_FRAGMENT",
    "CLAUDE_PLUGIN_ALREADY_INSTALLED_FRAGMENT",
    "CLAUDE_PLUGIN_DISABLE_COMMAND",
    "CLAUDE_PLUGIN_ENABLE_COMMAND",
    "CLAUDE_PLUGIN_INSTALL_COMMAND",
    "CLAUDE_PLUGIN_LIST_COMMAND",
    "CLAUDE_SCOPE_LOCAL",
    "CLAUDE_SCOPE_PROJECT",
    "CLAUDE_SCOPE_USER",
    "CODEX_MARKETPLACE_ADD_COMMAND",
    "CODEX_MARKETPLACE_LIST_COMMAND",
    "CODEX_MARKETPLACE_REMOVE_COMMAND",
    "CODEX_PLUGIN_MANIFEST",
    "DEFAULT_MARKETPLACE",
    "DIST_CODEX_PLUGINS_DIR",
    "SOURCE_TYPE_GIT",
    "SOURCE_TYPE_LOCAL",
    "ClaudeInstalledPlugin",
    "ClaudeMarketplaceRepairTarget",
    "ClaudeSettingsPaths",
    "CodexDistPlugin",
    "CommandRunner",
    "MarketplaceConfigRepairResult",
    "MarketplaceSource",
    "MarketplaceSourceError",
    "available_codex_plugins",
    "configured_local_marketplace_root",
    "ensure_local_marketplace_sources",
    "main",
    "parse_claude_marketplace_sources",
    "parse_claude_installed_plugins",
    "parse_codex_marketplace_sources",
    "require_matching_local_sources",
    "run_command_capture",
]


if __name__ == "__main__":
    raise SystemExit(main())
