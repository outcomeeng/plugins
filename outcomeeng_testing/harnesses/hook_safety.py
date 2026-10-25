"""Harness: lay out generated-tree hook configs for the hook-safety validator.

Writes a ``hooks/hooks.json`` under a runtime-tree root in a caller-supplied
temporary directory and returns the written path. The plugin directory name is
harness-owned: the linked tests assert only that a report names it. Also provides
the path of the inert violating whole-payload fixture for the version-pinned cache
rule. The harness asserts nothing and returns no verdicts.

Exception case: none.
"""

from __future__ import annotations

import json
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


def write_plugin_hooks(
    base: Path, runtime_root: Path, config: Mapping[str, object]
) -> Path:
    """Write ``config`` as the hook-safety plugin's hooks.json under ``base / runtime_root``."""
    path = base / runtime_root / HOOK_PLUGIN_NAME / HOOKS_DIRNAME / HOOKS_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
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


def version_pinned_cache_hooks_path() -> Path:
    """Return the path of the violating hooks config naming a version-pinned cache path."""
    return _FIXTURES / "version_pinned_cache.hooks.json"
