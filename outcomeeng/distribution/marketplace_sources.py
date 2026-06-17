"""Marketplace source discovery for maintainer refresh workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

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

type CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class MarketplaceSourceError(RuntimeError):
    """Marketplace source discovery failed or reported an unsupported shape."""


@dataclass(frozen=True)
class MarketplaceSource:
    """Configured marketplace source reported by a runtime CLI."""

    name: str
    source_type: str
    path: Path | None = None
    url: str | None = None


@dataclass(frozen=True)
class CodexDistPlugin:
    """Plugin manifest discovered under ``dist/codex``."""

    name: str
    version: str
    root: Path


@dataclass(frozen=True)
class MarketplaceConfigRepairResult:
    """Result of reconciling runtime marketplace source configuration."""

    root: Path
    changed: bool
    commands: tuple[tuple[str, ...], ...]


def run_command_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True)


def parse_claude_marketplace_sources(payload: str) -> dict[str, MarketplaceSource]:
    """Parse ``claude plugin marketplace list --json`` output by marketplace name."""
    return _parse_marketplace_sources(payload, runtime="Claude Code")


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
        _repair_runtime_source(
            marketplace,
            source=claude_sources.get(marketplace),
            root=root,
            add_command=CLAUDE_MARKETPLACE_ADD_COMMAND,
            remove_command=CLAUDE_MARKETPLACE_REMOVE_COMMAND,
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


def _source_matches(source: MarketplaceSource | None, root: Path) -> bool:
    return (
        source is not None
        and source.source_type == SOURCE_TYPE_LOCAL
        and source.path is not None
        and _normalized_path(source.path) == root
    )


def _run_json_command(
    command: list[str],
    *,
    runner: CommandRunner,
) -> subprocess.CompletedProcess[str]:
    result = runner(command)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        raise MarketplaceSourceError(
            f"{' '.join(command)} exited {result.returncode}{detail}"
        )
    return result


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
    "CODEX_MARKETPLACE_ADD_COMMAND",
    "CODEX_MARKETPLACE_LIST_COMMAND",
    "CODEX_MARKETPLACE_REMOVE_COMMAND",
    "CODEX_PLUGIN_MANIFEST",
    "DEFAULT_MARKETPLACE",
    "DIST_CODEX_PLUGINS_DIR",
    "SOURCE_TYPE_GIT",
    "SOURCE_TYPE_LOCAL",
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
    "parse_codex_marketplace_sources",
    "require_matching_local_sources",
    "run_command_capture",
]


if __name__ == "__main__":
    raise SystemExit(main())
