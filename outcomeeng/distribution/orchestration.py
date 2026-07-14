"""Build-orchestration contracts for marketplace runtime trees."""

from __future__ import annotations

import json
import shlex
from pathlib import Path, PurePosixPath
from typing import Any, Final, cast

import yaml  # type: ignore[import-untyped]

from outcomeeng.distribution.contracts import (
    BUILD_COMMAND_ARGV as _BUILD_COMMAND_ARGV,
    DIST_DIR_NAME as _DIST_DIR_NAME,
    DIST_DIFF_ARGV as _DIST_DIFF_ARGV,
    PLUGINS_DIR_NAME as _PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME as _SOURCE_ROOT_NAME,
    Target as _Target,
)

SOURCE_PLUGINS_DIR: Final = Path(_SOURCE_ROOT_NAME) / _PLUGINS_DIR_NAME

DIST_ROOT_NAME: Final = _DIST_DIR_NAME
CLAUDE_DIST_PLUGINS_DIR: Final = Path(DIST_ROOT_NAME) / _Target.CLAUDE.value
CODEX_DIST_PLUGINS_DIR: Final = Path(DIST_ROOT_NAME) / _Target.CODEX.value

BUILD_RECIPE_NAME: Final = "build-skills"
JUSTFILE_PATH: Final = Path("justfile")
LEFTHOOK_PATH: Final = Path("lefthook.yml")
CLAUDE_MARKETPLACE_PATH: Final = Path(".claude-plugin") / "marketplace.json"
CODEX_MARKETPLACE_PATH: Final = Path(".agents") / "plugins" / "marketplace.json"
CATALOG_PATHS: Final = {
    "claude": CLAUDE_MARKETPLACE_PATH,
    "codex": CODEX_MARKETPLACE_PATH,
}

CLAUDE_RUNTIME_ROOT: Final = f"./{CLAUDE_DIST_PLUGINS_DIR.as_posix()}"
CODEX_RUNTIME_ROOT: Final = f"./{CODEX_DIST_PLUGINS_DIR.as_posix()}"
LEFTHOOK_BUILD_COMMAND: Final = (
    f"just {BUILD_RECIPE_NAME} && {' '.join(_DIST_DIFF_ARGV)}"
)


def just_recipe_commands(
    text: str, recipe_name: str = BUILD_RECIPE_NAME
) -> tuple[tuple[str, ...], ...]:
    """Return shell argv lines for a just recipe body."""

    commands: list[tuple[str, ...]] = []
    in_recipe = False
    for line in text.splitlines():
        stripped = line.strip()
        if _is_recipe_header(line):
            if in_recipe:
                break
            in_recipe = _recipe_header_name(stripped) == recipe_name
            continue
        if not in_recipe or not stripped or stripped.startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            break
        commands.append(tuple(shlex.split(stripped.lstrip("@-+"))))
    return tuple(commands)


def just_recipe_names(text: str) -> tuple[str, ...]:
    """Return recipe names declared in a justfile."""

    return tuple(
        _recipe_header_name(line.strip())
        for line in text.splitlines()
        if _is_recipe_header(line)
    )


def lefthook_build_command(config: dict[str, Any]) -> str:
    """Return the pre-commit build command from a parsed lefthook config."""

    return str(config["pre-commit"]["commands"][BUILD_RECIPE_NAME]["run"])


def load_lefthook_config(path: Path = LEFTHOOK_PATH) -> dict[str, Any]:
    """Load lefthook YAML as a mapping owned by the build-orchestration contract."""

    return parse_lefthook_config(path.read_text(encoding="utf-8"))


def parse_lefthook_config(text: str) -> dict[str, Any]:
    """Parse lefthook YAML through the source-owned artifact boundary."""
    return cast("dict[str, Any]", yaml.safe_load(text))


def lefthook_config_matches_build_contract(config: dict[str, Any]) -> bool:
    """Return whether pre-commit regenerates and rejects generated-tree drift."""
    return lefthook_build_command(config) == LEFTHOOK_BUILD_COMMAND


def load_json_document(path: Path) -> dict[str, Any]:
    """Load a JSON document as a mapping owned by the build-orchestration contract."""

    return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))


def claude_marketplace_plugin_root(catalog: dict[str, Any]) -> str:
    """Return the Claude marketplace plugin root."""

    return str(catalog["metadata"]["pluginRoot"])


def claude_marketplace_plugin_sources(catalog: dict[str, Any]) -> tuple[str, ...]:
    """Return Claude plugin source paths from the marketplace catalog."""

    return tuple(str(plugin["source"]) for plugin in catalog["plugins"])


def codex_marketplace_plugin_sources(catalog: dict[str, Any]) -> tuple[str, ...]:
    """Return Codex plugin source paths from the marketplace catalog."""

    return tuple(str(plugin["source"]["path"]) for plugin in catalog["plugins"])


def path_is_under_runtime_root(path: str, runtime_root: str) -> bool:
    """Return whether a relative POSIX path is inside a runtime root."""

    path_parts = _relative_posix_parts(path)
    root_parts = _relative_posix_parts(runtime_root)
    return (
        ".." not in path_parts
        and len(path_parts) > len(root_parts)
        and path_parts[: len(root_parts)] == root_parts
    )


def check_build_orchestration(root: Path) -> list[str]:
    """Report build orchestration drift from the runtime-tree contract."""

    errors: list[str] = []

    justfile = (root / JUSTFILE_PATH).read_text(encoding="utf-8")
    recipe_names = just_recipe_names(justfile)
    if recipe_names.count(BUILD_RECIPE_NAME) != 1:
        errors.append(f"{JUSTFILE_PATH}: expected one {BUILD_RECIPE_NAME} recipe")
    if _BUILD_COMMAND_ARGV not in just_recipe_commands(justfile):
        errors.append(
            f"{JUSTFILE_PATH}: {BUILD_RECIPE_NAME} must run "
            f"{' '.join(_BUILD_COMMAND_ARGV)}"
        )

    lefthook_config = load_lefthook_config(root / LEFTHOOK_PATH)
    if not lefthook_config_matches_build_contract(lefthook_config):
        errors.append(
            f"{LEFTHOOK_PATH}: {BUILD_RECIPE_NAME} must run {LEFTHOOK_BUILD_COMMAND}"
        )

    claude_catalog = load_json_document(root / CLAUDE_MARKETPLACE_PATH)
    if claude_marketplace_plugin_root(claude_catalog) != CLAUDE_RUNTIME_ROOT:
        errors.append(
            f"{CLAUDE_MARKETPLACE_PATH}: metadata.pluginRoot must be "
            f"{CLAUDE_RUNTIME_ROOT}"
        )
    claude_sources = claude_marketplace_plugin_sources(claude_catalog)
    if not claude_sources:
        errors.append(f"{CLAUDE_MARKETPLACE_PATH}: must list plugin sources")
    for source in claude_sources:
        if not path_is_under_runtime_root(source, CLAUDE_RUNTIME_ROOT):
            errors.append(
                f"{CLAUDE_MARKETPLACE_PATH}: {source} must be under "
                f"{CLAUDE_RUNTIME_ROOT}"
            )

    codex_catalog = load_json_document(root / CODEX_MARKETPLACE_PATH)
    codex_sources = codex_marketplace_plugin_sources(codex_catalog)
    if not codex_sources:
        errors.append(f"{CODEX_MARKETPLACE_PATH}: must list plugin sources")
    for source in codex_sources:
        if not path_is_under_runtime_root(source, CODEX_RUNTIME_ROOT):
            errors.append(
                f"{CODEX_MARKETPLACE_PATH}: {source} must be under {CODEX_RUNTIME_ROOT}"
            )

    return errors


def _is_recipe_header(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and line == stripped and ":" in stripped


def _recipe_header_name(header: str) -> str:
    return header.split(":", maxsplit=1)[0].split()[0]


def _relative_posix_parts(value: str) -> tuple[str, ...]:
    normalized = value.removeprefix("./")
    return PurePosixPath(normalized).parts
