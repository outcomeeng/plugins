"""Build-orchestration contracts for marketplace runtime trees."""

from __future__ import annotations

import json
import shlex
from pathlib import Path, PurePosixPath
from typing import Any, Final, cast

import yaml  # type: ignore[import-untyped]

from outcomeeng.distribution.contracts import (
    BUILD_COMMAND_ARGV as _BUILD_COMMAND_ARGV,
    CLAUDE_DIST_RELATIVE as _CLAUDE_DIST_RELATIVE,
    DIST_DIR_NAME as _DIST_DIR_NAME,
    DIST_DIFF_ARGV as _DIST_DIFF_ARGV,
    DIST_DIFF_MODULE_NAME as _DIST_DIFF_MODULE_NAME,
    MINIMUM_VERSION_PREFIX as _MINIMUM_VERSION_PREFIX,
    PLUGINS_DIR_NAME as _PLUGINS_DIR_NAME,
    RECURSIVE_GLOB as _RECURSIVE_GLOB,
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
RAW_GIT_DIFF_COMMAND: Final = "git diff --exit-code"
RAW_DIFF_SUBCOMMAND: Final = "diff"

DISTRIBUTION_RUNTIME_PATH: Final = (
    f"{_CLAUDE_DIST_RELATIVE.as_posix()}/{_RECURSIVE_GLOB}"
)
DISTRIBUTION_SOURCE_PATH: Final = (
    f"{_SOURCE_ROOT_NAME}/{_PLUGINS_DIR_NAME}/{_RECURSIVE_GLOB}"
)
RETIRED_DISTRIBUTION_SOURCE_PREFIX: Final = f"{_PLUGINS_DIR_NAME}/"
CODEX_DISTRIBUTION_PATH: Final = (
    f"{_DIST_DIR_NAME}/{_Target.CODEX.value}/{_RECURSIVE_GLOB}"
)

type Workflow = dict[str, Any]


class ConfigPathError(ValueError):
    """A requested orchestration config path escapes its declared root."""


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


def lefthook_build_command(config: Workflow) -> str:
    """Return the pre-commit build command from a parsed lefthook config."""

    return str(config["pre-commit"]["commands"][BUILD_RECIPE_NAME]["run"])


def load_lefthook_config(
    path: Path = LEFTHOOK_PATH,
    *,
    root: Path | None = None,
) -> Workflow:
    """Load lefthook YAML as a mapping owned by the build-orchestration contract."""
    resolved_path = _resolve_config_path(path, root=root)
    return parse_lefthook_config(resolved_path.read_text(encoding="utf-8"))


def parse_lefthook_config(text: str) -> Workflow:
    """Parse lefthook YAML through the source-owned artifact boundary."""
    return cast(Workflow, yaml.safe_load(text))


def lefthook_config_matches_build_contract(config: Workflow) -> bool:
    """Return whether pre-commit regenerates and rejects generated-tree drift."""
    return lefthook_build_command(config) == LEFTHOOK_BUILD_COMMAND


def dist_diff_surfaces_match_contract(
    dist_diff_argvs: set[tuple[str, ...]],
    lefthook_command: str,
) -> bool:
    """Return whether gate and hook use the actionable dist-drift reporter."""
    return (
        dist_diff_argvs == {_DIST_DIFF_ARGV}
        and _DIST_DIFF_MODULE_NAME in _DIST_DIFF_ARGV
        and RAW_DIFF_SUBCOMMAND not in _DIST_DIFF_ARGV
        and _DIST_DIFF_MODULE_NAME in lefthook_command
        and RAW_GIT_DIFF_COMMAND not in lefthook_command
    )


def justfile_matches_build_contract(text: str) -> bool:
    """Return whether the justfile owns one complete build recipe."""
    return just_recipe_names(text).count(
        BUILD_RECIPE_NAME
    ) == 1 and _BUILD_COMMAND_ARGV in just_recipe_commands(text)


def distribution_workflow_paths_match_contract(paths: set[str]) -> bool:
    """Return whether distribution watches canonical source and runtime paths."""
    return (
        DISTRIBUTION_RUNTIME_PATH in paths
        and DISTRIBUTION_SOURCE_PATH in paths
        and all(
            not path.startswith(RETIRED_DISTRIBUTION_SOURCE_PREFIX) for path in paths
        )
        and CODEX_DISTRIBUTION_PATH not in paths
    )


def distribution_python_version_matches_project(
    workflow_version: str,
    requires_python: str,
) -> bool:
    """Return whether distribution uses the project's minimum Python version."""
    return workflow_version == requires_python.removeprefix(_MINIMUM_VERSION_PREFIX)


def load_json_document(
    path: Path,
    *,
    root: Path | None = None,
) -> Workflow:
    """Load a JSON document as a mapping owned by the build-orchestration contract."""
    resolved_path = _resolve_config_path(path, root=root)
    return cast(Workflow, json.loads(resolved_path.read_text(encoding="utf-8")))


def claude_marketplace_plugin_root(catalog: Workflow) -> str:
    """Return the Claude marketplace plugin root."""

    return str(catalog["metadata"]["pluginRoot"])


def claude_marketplace_plugin_sources(catalog: Workflow) -> tuple[str, ...]:
    """Return Claude plugin source paths from the marketplace catalog."""

    return tuple(str(plugin["source"]) for plugin in catalog["plugins"])


def codex_marketplace_plugin_sources(catalog: Workflow) -> tuple[str, ...]:
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
    if not justfile_matches_build_contract(justfile):
        errors.append(
            f"{JUSTFILE_PATH}: expected one {BUILD_RECIPE_NAME} recipe running "
            f"{' '.join(_BUILD_COMMAND_ARGV)}"
        )

    lefthook_config = load_lefthook_config(root / LEFTHOOK_PATH, root=root)
    if not lefthook_config_matches_build_contract(lefthook_config):
        errors.append(
            f"{LEFTHOOK_PATH}: {BUILD_RECIPE_NAME} must run {LEFTHOOK_BUILD_COMMAND}"
        )

    claude_catalog = load_json_document(root / CLAUDE_MARKETPLACE_PATH, root=root)
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

    codex_catalog = load_json_document(root / CODEX_MARKETPLACE_PATH, root=root)
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


def _resolve_config_path(path: Path, *, root: Path | None) -> Path:
    allowed_root = (root or Path.cwd()).resolve()
    resolved_path = (path if path.is_absolute() else allowed_root / path).resolve()
    if not resolved_path.is_relative_to(allowed_root):
        raise ConfigPathError(f"config path escapes declared root: {path}")
    return resolved_path


def _recipe_header_name(header: str) -> str:
    return header.split(":", maxsplit=1)[0].split()[0]


def _relative_posix_parts(value: str) -> tuple[str, ...]:
    normalized = value.removeprefix("./")
    return PurePosixPath(normalized).parts
