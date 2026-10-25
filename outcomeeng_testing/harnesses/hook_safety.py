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

HOOK_PLUGIN_NAME = "hook-safety-plugin"

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "hook_safety"


def write_plugin_hooks(
    base: Path, runtime_root: Path, config: Mapping[str, object]
) -> Path:
    """Write ``config`` as the hook-safety plugin's hooks.json under ``base / runtime_root``."""
    path = base / runtime_root / HOOK_PLUGIN_NAME / "hooks" / "hooks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def version_pinned_cache_hooks_path() -> Path:
    """Return the path of the violating hooks config naming a version-pinned cache path."""
    return _FIXTURES / "version_pinned_cache.hooks.json"
