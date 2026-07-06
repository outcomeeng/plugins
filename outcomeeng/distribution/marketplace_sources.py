"""Marketplace source discovery for maintainer refresh workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
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
CLAUDE_SCOPE_MANAGED = "managed"
_CLAUDE_PROJECT_PATH_SCOPES = frozenset({"project", "local"})
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
MARKETPLACE_FIELD_NAME = "name"
MARKETPLACE_FIELD_SOURCE = "source"
MARKETPLACE_FIELD_PATH = "path"
MARKETPLACE_FIELD_SOURCE_TYPE = "sourceType"
MARKETPLACE_FIELD_MARKETPLACES = "marketplaces"
MARKETPLACE_FIELD_ROOT = "root"
MARKETPLACE_FIELD_MARKETPLACE_SOURCE = "marketplaceSource"
MARKETPLACE_FIELD_URL = "url"
MARKETPLACE_FIELD_SCOPE = "scope"
MARKETPLACE_FIELD_PROJECT_PATH = "projectPath"
PLUGIN_FIELD_ID = "id"
PLUGIN_FIELD_ENABLED = "enabled"
PLUGIN_MANIFEST_FIELD_VERSION = "version"


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

    @property
    def ref(self) -> str:
        return f"{self.name}@{self.marketplace}"


@dataclass(frozen=True)
class MarketplaceConfigRepairResult:
    """Result of reconciling runtime marketplace source configuration."""

    root: Path
    changed: bool
    commands: tuple[tuple[str, ...], ...]


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
        plugin_id = entry.get(PLUGIN_FIELD_ID)
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
        scope = entry.get(MARKETPLACE_FIELD_SCOPE)
        if not isinstance(scope, str):
            raise MarketplaceSourceError(
                f"Claude Code plugin `{plugin_id}` has no string scope"
            )
        enabled = entry.get(PLUGIN_FIELD_ENABLED)
        if not isinstance(enabled, bool):
            raise MarketplaceSourceError(
                f"Claude Code plugin `{plugin_id}` has no boolean enabled state"
            )
        project_path = _optional_path(entry.get(MARKETPLACE_FIELD_PROJECT_PATH))
        if scope in _CLAUDE_PROJECT_PATH_SCOPES and project_path is None:
            raise MarketplaceSourceError(
                f"Claude Code plugin `{plugin_id}` with {scope} scope has no "
                f"{MARKETPLACE_FIELD_PROJECT_PATH}"
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
    claude_source_groups = _parse_marketplace_source_groups(
        claude_result.stdout or "",
        runtime="Claude Code",
    )
    codex_source_groups = _parse_marketplace_source_groups(
        codex_result.stdout or "",
        runtime="Codex",
    )
    shared_root = _shared_local_source_root(
        claude_source_groups.get(marketplace, ()),
        codex_source_groups.get(marketplace, ()),
    )
    if shared_root is not None:
        return shared_root
    claude_sources = _select_marketplace_sources(claude_source_groups)
    codex_sources = _select_marketplace_sources(codex_source_groups)
    return require_matching_local_sources(
        marketplace,
        claude_sources=claude_sources,
        codex_sources=codex_sources,
    )


def configured_claude_directory_marketplace_root(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    runner: CommandRunner = run_command_capture,
) -> Path:
    """Return the Claude Code Directory source root without validating Codex."""
    claude_result = _run_json_command(
        [*CLAUDE_MARKETPLACE_LIST_COMMAND],
        runner=runner,
    )
    claude_source_groups = _parse_marketplace_source_groups(
        claude_result.stdout or "",
        runtime="Claude Code",
    )
    root = _single_runtime_local_source_root(
        claude_source_groups.get(marketplace, ()),
        runtime="Claude Code",
    )
    if root is None:
        claude_sources = _select_marketplace_sources(claude_source_groups)
        claude = _required_source(claude_sources, marketplace, runtime="Claude Code")
        raise MarketplaceSourceError(
            f"Claude Code marketplace `{marketplace}` must be a local Directory "
            f"source with a path; found {claude.source_type}"
        )
    return root


def ensure_local_marketplace_sources(
    marketplace: str = DEFAULT_MARKETPLACE,
    *,
    source_root: Path | None = None,
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
    claude_source_groups = _parse_marketplace_source_groups(
        claude_result.stdout or "",
        runtime="Claude Code",
    )
    claude_sources = _select_marketplace_sources(claude_source_groups)
    codex_source_groups = _parse_marketplace_source_groups(
        codex_result.stdout or "",
        runtime="Codex",
    )
    codex_sources = _select_marketplace_sources(codex_source_groups)
    root = _canonical_source_root(
        marketplace,
        explicit_root=source_root,
        claude_sources=claude_sources,
        codex_sources=codex_sources,
        claude_source_groups=claude_source_groups,
        codex_source_groups=codex_source_groups,
    )
    commands: list[tuple[str, ...]] = []
    commands.extend(
        _repair_claude_runtime_source(
            marketplace,
            sources=claude_source_groups.get(marketplace, ()),
            root=root,
            runner=runner,
        )
    )
    commands.extend(
        _repair_runtime_source(
            marketplace,
            sources=codex_source_groups.get(marketplace, ()),
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
        version = data.get(PLUGIN_MANIFEST_FIELD_VERSION)
        if not isinstance(version, str):
            raise MarketplaceSourceError(
                f"Codex plugin manifest has no string version: {manifest}"
            )
        plugins.append(CodexDistPlugin(name=child.name, version=version, root=child))
    return tuple(plugins)


def _parse_marketplace_sources(
    payload: str, *, runtime: str
) -> dict[str, MarketplaceSource]:
    return _select_marketplace_sources(
        _parse_marketplace_source_groups(payload, runtime=runtime)
    )


def _parse_marketplace_source_groups(
    payload: str, *, runtime: str
) -> dict[str, tuple[MarketplaceSource, ...]]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise MarketplaceSourceError(
            f"{runtime} marketplace list output is not valid JSON: {exc}"
        ) from exc
    entries = tuple(_marketplace_entries(data, runtime=runtime))
    sources: dict[str, list[MarketplaceSource]] = {}
    for entry in entries:
        source = _marketplace_source_from_entry(entry, runtime=runtime)
        sources.setdefault(source.name, []).append(source)
    return {name: tuple(group) for name, group in sources.items()}


def _marketplace_source_from_entry(
    entry: dict[str, object], *, runtime: str
) -> MarketplaceSource:
    name = entry.get(MARKETPLACE_FIELD_NAME)
    if not isinstance(name, str):
        raise MarketplaceSourceError(f"{runtime} marketplace entry has no string name")
    source_entry = _source_entry(entry)
    source_type = _normalized_source_type(source_entry)
    scope = _string_field(source_entry, (MARKETPLACE_FIELD_SCOPE,))
    project_path = _optional_path(source_entry.get(MARKETPLACE_FIELD_PROJECT_PATH))
    path = _path_field(source_entry, source_type)
    if source_type == SOURCE_TYPE_LOCAL and path is None:
        raise MarketplaceSourceError(
            f"{runtime} marketplace `{name}` local source has no usable path"
        )
    if (
        runtime == "Claude Code"
        and scope in _CLAUDE_PROJECT_PATH_SCOPES
        and project_path is None
    ):
        raise MarketplaceSourceError(
            f"{runtime} marketplace `{name}` with {scope} scope has no "
            f"{MARKETPLACE_FIELD_PROJECT_PATH}"
        )
    return MarketplaceSource(
        name=name,
        source_type=source_type,
        path=path,
        url=_url_field(source_entry, source_type),
        scope=scope,
        project_path=project_path,
    )


def _select_marketplace_sources(
    grouped_sources: dict[str, tuple[MarketplaceSource, ...]],
) -> dict[str, MarketplaceSource]:
    return {
        name: selected
        for name, sources in grouped_sources.items()
        if (selected := _select_marketplace_source(sources)) is not None
    }


def _select_marketplace_source(
    sources: tuple[MarketplaceSource, ...],
) -> MarketplaceSource | None:
    selected: MarketplaceSource | None = None
    for source in sources:
        if selected is None or _source_selection_rank(source) > _source_selection_rank(
            selected
        ):
            selected = source
    return selected


def _source_selection_rank(source: MarketplaceSource) -> int:
    if source.source_type != SOURCE_TYPE_LOCAL:
        return 0
    if source.scope == CLAUDE_SCOPE_USER:
        return 5
    if source.scope is None:
        return 4
    if source.scope == CLAUDE_SCOPE_MANAGED:
        return 3
    return 2


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
    for key in (MARKETPLACE_FIELD_MARKETPLACES, "items", "entries", "configured"):
        if key in data:
            return data[key]
    return None


def _source_entry(entry: dict[str, object]) -> dict[str, object]:
    source = entry.get(MARKETPLACE_FIELD_MARKETPLACE_SOURCE)
    if not isinstance(source, dict):
        return entry
    # Codex reports the marketplace name and installed root at the top level, with
    # the durable configured source nested under `marketplaceSource`.
    merged = dict(entry)
    merged.update(source)
    return merged


def _normalized_source_type(entry: dict[str, object]) -> str:
    raw = _string_field(
        entry,
        (
            MARKETPLACE_FIELD_SOURCE_TYPE,
            "source_type",
            MARKETPLACE_FIELD_SOURCE,
        ),
    )
    if raw is None:
        if _path_field(entry, SOURCE_TYPE_LOCAL) is not None:
            return SOURCE_TYPE_LOCAL
        return ""
    lowered = raw.strip().lower()
    if _local_source_type_token(raw):
        return SOURCE_TYPE_LOCAL
    if lowered in {SOURCE_TYPE_GIT, "github"} or lowered.startswith("http"):
        return SOURCE_TYPE_GIT
    return lowered


def _path_field(entry: dict[str, object], source_type: str) -> Path | None:
    raw = _string_field(
        entry,
        (
            MARKETPLACE_FIELD_PATH,
            "directory",
            "localPath",
            "sourcePath",
        ),
    )
    if raw is None and source_type == SOURCE_TYPE_LOCAL:
        source = _string_field(entry, (MARKETPLACE_FIELD_SOURCE,))
        if source is not None and not _local_source_type_token(source):
            raw = source
    if raw is None:
        return None
    return Path(raw).expanduser()


def _url_field(entry: dict[str, object], source_type: str) -> str | None:
    raw = _string_field(entry, (MARKETPLACE_FIELD_URL, "repo", "repository"))
    if raw is not None:
        return raw
    source = _string_field(entry, (MARKETPLACE_FIELD_SOURCE,))
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


def _local_source_type_token(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered.startswith("directory") or lowered in {"local", "path"}


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
    claude_source_groups: dict[str, tuple[MarketplaceSource, ...]] | None = None,
    codex_source_groups: dict[str, tuple[MarketplaceSource, ...]] | None = None,
) -> Path:
    if explicit_root is not None:
        return _normalized_path(explicit_root)
    shared_root = _shared_local_source_root(
        claude_source_groups.get(marketplace, ())
        if claude_source_groups is not None
        else tuple(claude_sources.values()),
        codex_source_groups.get(marketplace, ())
        if codex_source_groups is not None
        else tuple(codex_sources.values()),
    )
    if shared_root is not None:
        return shared_root
    claude_group_root = _single_runtime_local_source_root(
        claude_source_groups.get(marketplace, ())
        if claude_source_groups is not None
        else tuple(claude_sources.values()),
        runtime="Claude Code",
    )
    if claude_group_root is not None:
        return claude_group_root
    codex_group_root = _single_runtime_local_source_root(
        codex_source_groups.get(marketplace, ())
        if codex_source_groups is not None
        else tuple(codex_sources.values()),
        runtime="Codex",
    )
    if codex_group_root is not None:
        return codex_group_root
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


def _shared_local_source_root(
    claude_sources: tuple[MarketplaceSource, ...],
    codex_sources: tuple[MarketplaceSource, ...],
) -> Path | None:
    codex_roots = set(_local_source_roots(codex_sources))
    shared_roots = tuple(
        root for root in _local_source_roots(claude_sources) if root in codex_roots
    )
    if not shared_roots:
        return None
    unique_roots = tuple(dict.fromkeys(shared_roots))
    if len(unique_roots) > 1:
        formatted = ", ".join(str(root) for root in unique_roots)
        raise MarketplaceSourceError(
            f"multiple shared local marketplace roots reported: {formatted}"
        )
    return next(iter(unique_roots))


def _single_runtime_local_source_root(
    sources: tuple[MarketplaceSource, ...],
    *,
    runtime: str,
) -> Path | None:
    roots = tuple(dict.fromkeys(_local_source_roots(sources)))
    if not roots:
        return None
    if len(roots) > 1:
        formatted = ", ".join(str(root) for root in roots)
        raise MarketplaceSourceError(
            f"{runtime} reported multiple local marketplace roots: {formatted}"
        )
    return next(iter(roots))


def _local_source_roots(sources: tuple[MarketplaceSource, ...]) -> tuple[Path, ...]:
    return tuple(
        _normalized_path(source.path)
        for source in sources
        if source.source_type == SOURCE_TYPE_LOCAL and source.path is not None
    )


def _repair_runtime_source(
    marketplace: str,
    *,
    sources: tuple[MarketplaceSource, ...],
    root: Path,
    add_command: tuple[str, ...],
    remove_command: tuple[str, ...],
    runner: CommandRunner,
) -> tuple[tuple[str, ...], ...]:
    canonical_source_exists = any(
        _user_registration_source_matches(source, root, accept_unscoped=True)
        for source in sources
    )
    stale_sources = (
        tuple(source for source in sources if not _source_matches(source, root))
        if canonical_source_exists
        else tuple(
            source
            for source in sources
            if not _user_registration_source_matches(source, root, accept_unscoped=True)
        )
    )
    if canonical_source_exists and not stale_sources:
        return ()
    commands: list[tuple[str, ...]] = []
    if sources:
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
    sources: tuple[MarketplaceSource, ...],
    root: Path,
    runner: CommandRunner,
) -> tuple[tuple[str, ...], ...]:
    stale_managed_sources = tuple(
        source
        for source in sources
        if source.scope == CLAUDE_SCOPE_MANAGED and not _source_matches(source, root)
    )
    if stale_managed_sources:
        source = stale_managed_sources[0]
        raise MarketplaceSourceError(
            f"Claude Code marketplace `{marketplace}` is managed at "
            f"{source.path or source.source_type} and cannot be repaired to {root}"
        )
    canonical_user_source_exists = any(
        _user_registration_source_matches(
            source,
            root,
            accept_unscoped=False,
        )
        for source in sources
    )
    editable_sources = tuple(
        source
        for source in sources
        if source.scope != CLAUDE_SCOPE_MANAGED
        and not _user_registration_source_matches(
            source,
            root,
            accept_unscoped=False,
        )
    )
    if canonical_user_source_exists and not editable_sources:
        return ()
    source_readd_required = not canonical_user_source_exists or any(
        _claude_source_removal_can_affect_user_plugins(source)
        for source in editable_sources
    )
    preserved = (
        _claude_user_plugins_to_preserve(
            marketplace,
            runner=runner,
        )
        if source_readd_required
        else ()
    )
    commands: list[tuple[str, ...]] = []
    seen_removals: set[tuple[tuple[str, ...], Path | None]] = set()
    for source in _claude_removal_order(editable_sources):
        remove = _claude_marketplace_remove_command(marketplace, source)
        remove_cwd = _claude_marketplace_remove_cwd(source)
        removal_key = (remove, remove_cwd)
        if removal_key in seen_removals:
            continue
        seen_removals.add(removal_key)
        _run_json_command(
            list(remove),
            runner=runner,
            cwd=remove_cwd,
        )
        commands.append(remove)
    if source_readd_required:
        add = (*CLAUDE_MARKETPLACE_ADD_COMMAND, str(root))
        _run_json_command(list(add), runner=runner)
        commands.append(add)
    commands.extend(_restore_claude_plugins(preserved, runner=runner))
    return tuple(commands)


def _claude_removal_order(
    sources: tuple[MarketplaceSource, ...],
) -> tuple[MarketplaceSource, ...]:
    return tuple(sorted(sources, key=lambda source: source.scope is None))


def _claude_source_removal_can_affect_user_plugins(source: MarketplaceSource) -> bool:
    return source.scope in {None, CLAUDE_SCOPE_USER}


def _claude_marketplace_remove_command(
    marketplace: str,
    source: MarketplaceSource,
) -> tuple[str, ...]:
    if source.scope is None:
        return (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, marketplace)
    return (*CLAUDE_MARKETPLACE_REMOVE_COMMAND, marketplace, "--scope", source.scope)


def _claude_marketplace_remove_cwd(source: MarketplaceSource) -> Path | None:
    if source.scope not in _CLAUDE_PROJECT_PATH_SCOPES:
        return None
    if source.project_path is None:
        raise MarketplaceSourceError(
            f"Claude Code marketplace `{source.name}` with {source.scope} scope has "
            f"no {MARKETPLACE_FIELD_PROJECT_PATH}"
        )
    return _normalized_path(source.project_path)


def _claude_user_plugins_to_preserve(
    marketplace: str,
    *,
    runner: CommandRunner,
) -> tuple[ClaudeInstalledPlugin, ...]:
    result = _run_json_command(
        [*CLAUDE_PLUGIN_LIST_COMMAND],
        runner=runner,
    )
    return tuple(
        plugin
        for plugin in parse_claude_installed_plugins(result.stdout or "", marketplace)
        if plugin.scope == CLAUDE_SCOPE_USER
    )


def _restore_claude_plugins(
    plugins: tuple[ClaudeInstalledPlugin, ...],
    *,
    runner: CommandRunner,
) -> tuple[tuple[str, ...], ...]:
    commands: list[tuple[str, ...]] = []
    for plugin in plugins:
        install = (*CLAUDE_PLUGIN_INSTALL_COMMAND, "--scope", plugin.scope, plugin.ref)
        _run_claude_plugin_restore_command(
            install,
            runner=runner,
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


def _source_matches(source: MarketplaceSource | None, root: Path) -> bool:
    return (
        source is not None
        and source.source_type == SOURCE_TYPE_LOCAL
        and source.path is not None
        and _normalized_path(source.path) == root
    )


def _user_registration_source_matches(
    source: MarketplaceSource | None,
    root: Path,
    *,
    accept_unscoped: bool,
) -> bool:
    return (
        _source_matches(source, root)
        and source is not None
        and (
            source.scope == CLAUDE_SCOPE_USER
            or (accept_unscoped and source.scope is None)
        )
    )


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
    already_satisfied_fragment: str,
    plugin_ref: str,
    plugin_scope: str,
    cwd: Path | None = None,
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
        choices=(MARKETPLACE_FIELD_ROOT, "claude-root", "ensure"),
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
        if args.command == MARKETPLACE_FIELD_ROOT:
            root = configured_local_marketplace_root(args.marketplace)
            print(root)
            return 0
        if args.command == "claude-root":
            root = configured_claude_directory_marketplace_root(args.marketplace)
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
                    MARKETPLACE_FIELD_ROOT: str(result.root),
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
    "CLAUDE_SCOPE_MANAGED",
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
    "CodexDistPlugin",
    "CommandRunner",
    "MarketplaceConfigRepairResult",
    "MarketplaceSource",
    "MarketplaceSourceError",
    "MARKETPLACE_FIELD_MARKETPLACE_SOURCE",
    "MARKETPLACE_FIELD_MARKETPLACES",
    "MARKETPLACE_FIELD_NAME",
    "MARKETPLACE_FIELD_PATH",
    "MARKETPLACE_FIELD_PROJECT_PATH",
    "MARKETPLACE_FIELD_ROOT",
    "MARKETPLACE_FIELD_SCOPE",
    "MARKETPLACE_FIELD_SOURCE",
    "MARKETPLACE_FIELD_SOURCE_TYPE",
    "MARKETPLACE_FIELD_URL",
    "PLUGIN_FIELD_ENABLED",
    "PLUGIN_FIELD_ID",
    "PLUGIN_MANIFEST_FIELD_VERSION",
    "available_codex_plugins",
    "configured_claude_directory_marketplace_root",
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
