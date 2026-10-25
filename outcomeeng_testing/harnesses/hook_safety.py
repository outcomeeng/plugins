"""Harness: lay out generated-tree hook configs for the hook-safety validator.

Writes a ``hooks/hooks.json`` under a runtime-tree root in a caller-supplied
temporary directory and returns the written path. The plugin directory name is
harness-owned: the linked tests assert only that a report names it. Also serves
the inert whole-payload ``hooks.json`` fixtures by path: the violating ones for
each command-shape, timeout, event, and cache-path rule, and the conforming
guarded ones beside them. The harness asserts nothing and returns no verdicts.

Exception case: none.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path

from outcomeeng.validation.hook_safety import (
    COMMAND_FIELD,
    HOOKS_DIRNAME,
    HOOKS_FIELD,
    HOOKS_FILENAME,
    TIMEOUT_FIELD,
)

HOOK_PLUGIN_NAME = "hook-safety-plugin"
SAFE_COMMAND = "echo '{}'"
"""A command-shape-clean hook command: no substituted-path script and no cache path."""
HOOK_TIMEOUT_SECONDS = 5
"""The explicit timeout a well-formed sample handler declares."""
# Payload shape the validator does not judge; written so a sample reads as a real hooks.json.
_MATCHER_FIELD = "matcher"
_HANDLER_TYPE_FIELD = "type"
_COMMAND_HANDLER_TYPE = "command"

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "hook_safety"
_FIXTURE_SUFFIX = ".hooks.json"
# Fixture families by file-name prefix: ``bare_`` holds one bare substituted-path
# invocation per shape the validator must catch, ``guarded_`` the guarded form of each.
_BARE_PREFIX = "bare_"
_GUARDED_PREFIX = "guarded_"


def hooks_file_path(base: Path, runtime_root: Path) -> Path:
    """Return the hook-safety plugin's hooks.json path under ``base / runtime_root``."""
    return base / runtime_root / HOOK_PLUGIN_NAME / HOOKS_DIRNAME / HOOKS_FILENAME


def write_plugin_hooks(
    base: Path, runtime_root: Path, config: Mapping[str, object]
) -> Path:
    """Write ``config`` as the hook-safety plugin's hooks.json under ``base / runtime_root``."""
    path = hooks_file_path(base, runtime_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def copy_plugin_hooks(base: Path, runtime_root: Path, fixture: Path) -> Path:
    """Copy the whole-payload ``fixture`` in as the plugin's hooks.json under ``base / runtime_root``."""
    path = hooks_file_path(base, runtime_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fixture, path)
    return path


def hook_config(
    event: str,
    *,
    command: str = SAFE_COMMAND,
    timeout: int | None = HOOK_TIMEOUT_SECONDS,
    matcher: bool = True,
    handler_count: int = 1,
) -> dict[str, object]:
    """Build a hooks.json config registering ``handler_count`` command handlers on ``event``.

    ``timeout=None`` omits each handler's timeout and ``matcher=False`` omits the block's
    matcher, the two shapes the validator judges beside the command text. The builder
    writes payload shape only; every verdict over it belongs to the linked test.
    """
    handlers: list[dict[str, object]] = []
    for _ in range(handler_count):
        handler: dict[str, object] = {
            _HANDLER_TYPE_FIELD: _COMMAND_HANDLER_TYPE,
            COMMAND_FIELD: command,
        }
        if timeout is not None:
            handler[TIMEOUT_FIELD] = timeout
        handlers.append(handler)
    block: dict[str, object] = {}
    if matcher:
        block[_MATCHER_FIELD] = ""
    block[HOOKS_FIELD] = handlers
    return {HOOKS_FIELD: {event: [block]}}


def read_hooks_config(path: Path) -> Mapping[str, object]:
    """Parse a whole-payload hooks.json fixture into the mapping the validator judges."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, Mapping):
        raise TypeError(f"{path}: hooks fixture is not a JSON object")
    return parsed


def _fixture_family(prefix: str) -> tuple[Path, ...]:
    return tuple(sorted(_FIXTURES.glob(f"{prefix}*{_FIXTURE_SUFFIX}")))


def bare_substituted_path_hooks_paths() -> tuple[Path, ...]:
    """Return every violating fixture whose command is a bare substituted-path invocation."""
    return _fixture_family(_BARE_PREFIX)


def guarded_substituted_path_hooks_paths() -> tuple[Path, ...]:
    """Return every conforming fixture whose substituted-path invocation carries a fallback."""
    return _fixture_family(_GUARDED_PREFIX)


def guarded_plugin_root_hooks_path() -> Path:
    """Return the conforming fixture guarding a ``${CLAUDE_PLUGIN_ROOT}`` script invocation."""
    return _FIXTURES / f"{_GUARDED_PREFIX}plugin_root{_FIXTURE_SUFFIX}"


def missing_timeout_hooks_path() -> Path:
    """Return the violating fixture whose handler declares no timeout."""
    return _FIXTURES / f"missing_timeout{_FIXTURE_SUFFIX}"


def unknown_event_hooks_path() -> Path:
    """Return the violating fixture registering a hook on an event outside every known set."""
    return _FIXTURES / f"unknown_event{_FIXTURE_SUFFIX}"


def version_pinned_cache_hooks_path() -> Path:
    """Return the path of the violating hooks config naming a version-pinned cache path."""
    return _FIXTURES / f"version_pinned_cache{_FIXTURE_SUFFIX}"
