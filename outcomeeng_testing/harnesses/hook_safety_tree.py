"""Test infrastructure: the temporary hook tree the hook-safety validator scans.

The harness owns the whole lifecycle of a throwaway generated-tree fixture: the
temporary root, the runtime directory, the plugin directory, the
``hooks/hooks.json`` location, and the JSON write with its encoding. Every layout
name and the encoding come from the validator's source owner
(``outcomeeng.validation.hook_contract``), so a fixture lands exactly where the
validator looks. It hands the test a tree handle; it accepts no expected result,
calls no assertion API, and returns no verdict.

Exception case: none.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.validation.hook_contract import (
    HOOKS_CONFIG_ENCODING,
    HOOKS_CONFIG_FILE,
    HOOKS_DIRECTORY,
)


@dataclass(frozen=True)
class HookTree:
    """A temporary directory tree holding plugin hook configs per runtime tree."""

    root: Path

    def runtime_root(self, runtime: str) -> Path:
        """Return the directory of one generated runtime tree."""
        return self.root / runtime

    def hooks_path(self, runtime: str, plugin: str) -> Path:
        """Return where one plugin's hook config lives in one runtime tree."""
        return self.runtime_root(runtime) / plugin / HOOKS_DIRECTORY / HOOKS_CONFIG_FILE

    def write_hooks(
        self, runtime: str, plugin: str, config: Mapping[str, object]
    ) -> Path:
        """Write one plugin's hook config into one runtime tree; return its path."""
        path = self.hooks_path(runtime, plugin)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config), encoding=HOOKS_CONFIG_ENCODING)
        return path

    def subtree(self, name: str) -> HookTree:
        """Return an isolated tree rooted in a named directory beneath this one."""
        return HookTree(self.root / name)


@contextmanager
def hook_tree() -> Iterator[HookTree]:
    """Yield an empty temporary hook tree and release it on exit."""
    with TemporaryDirectory() as directory:
        yield HookTree(Path(directory))


__all__ = ["HookTree", "hook_tree"]
