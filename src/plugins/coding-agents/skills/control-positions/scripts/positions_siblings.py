#!/usr/bin/env python3
"""Access to the sibling scripts of this plugin that the position controller reuses.

The controller imports the consumption-control accounting, its file publishing and its
bounded command runner, and the Prowl adapter, each by a path relative to this file.
It restates none of their operations.
"""

from __future__ import annotations

import contextlib
import importlib
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any, Final

SKILLS_ROOT: Final = Path(__file__).resolve().parents[2]
PROWL_ADAPTER: Final = ("operate-prowl", "prowl_environment")
TOKEN_ACCOUNTING: Final = ("control-token-spend", "usage_accounting")
FILE_PUBLISHING: Final = ("control-token-spend", "usage_reports")
COMMAND_RUNNER: Final = ("control-token-spend", "usage_schedule")

_SCOPE_DEPTH = 0


def _is_sibling_script(module: object) -> bool:
    origin = getattr(module, "__file__", None)
    return origin is not None and SKILLS_ROOT in Path(origin).parents


@contextlib.contextmanager
def sibling_scope() -> Iterator[None]:
    """Leave `sys.modules` as the operation found it, sharing sibling loads inside.

    Within the scope a sibling imported once stays registered, so every load of one
    pass sees the same module state. When the outermost scope ends, the names the
    scope added for sibling scripts are removed and each registration it replaced
    is put back.
    """
    global _SCOPE_DEPTH
    before = dict(sys.modules) if _SCOPE_DEPTH == 0 else None
    _SCOPE_DEPTH += 1
    try:
        yield
    finally:
        _SCOPE_DEPTH -= 1
        if before is not None:
            for name in set(sys.modules) - set(before):
                if _is_sibling_script(sys.modules[name]):
                    del sys.modules[name]
            for name, previous in before.items():
                if sys.modules.get(name) is not previous:
                    sys.modules[name] = previous


def load_sibling(skill: str, module_name: str) -> ModuleType:
    """Import a script of a sibling skill of this plugin by a `__file__`-relative path."""
    directory = SKILLS_ROOT / skill / "scripts"
    path = directory / f"{module_name}.py"
    cached = sys.modules.get(module_name)
    if cached is not None and Path(getattr(cached, "__file__", "")) == path:
        return cached
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing; install the sibling skill {skill} in the same plugin"
        )
    sys.modules.pop(module_name, None)
    sys.path.insert(0, str(directory))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.remove(str(directory))


def publish(path: Path, content: str | bytes) -> None:
    """Publish `content` at `path` as the consumption-control scripts publish a file.

    The sibling writes a unique temporary file beside `path`, flushes and fsyncs it,
    and renames it over `path`.
    """
    with sibling_scope():
        load_sibling(*FILE_PUBLISHING).atomic_write(path, content)


def run_bounded(argv: Sequence[str], timeout_seconds: float) -> Any:
    """Run `argv` through the sibling's bounded runner and return its command result.

    The sibling kills the command at its deadline and bounds the bytes it captures;
    it raises `TimeoutError`, `RuntimeError`, or `OSError` when it cannot answer.
    """
    with sibling_scope():
        runner = load_sibling(*COMMAND_RUNNER).SubprocessRunner()
        return runner.run(tuple(argv), timeout_seconds)
