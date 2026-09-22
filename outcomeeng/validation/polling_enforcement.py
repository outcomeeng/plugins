"""Report unbounded polling waits in source, as a pure function of the paths given.

The rule the gate node declares forbids two shapes: a `while True` loop that
sleeps — through an attribute or through a name the file imports from `time` —
and a watch invocation that blocks without bound. Both are reported
here rather than asserted at a call site, so the detection itself is exercised
against violating source and cannot pass by recognising nothing.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import Final

SLEEP_ATTRIBUTE: Final = "sleep"
"""The call whose presence inside an unbounded loop makes it a polling wait."""
SLEEP_MODULE: Final = "time"
"""The module whose sleep an import can bind to a bare name in the scanned file."""
WATCH_INVOCATION: Final = "gh run watch"
"""The blocking watch invocation no gate module may carry."""
DECLARING_MODULE: Final = Path(__file__).resolve()
"""This module, the one file exempt because it publishes the forbidden invocation."""


def unbounded_polling_sites(paths: Iterable[Path]) -> tuple[str, ...]:
    """Return every unbounded polling site among `paths`, named by file and kind.

    This module is exempt by declaration rather than by any subject's shape: it
    publishes the watch invocation as `WATCH_INVOCATION`, so a subject that
    included it would report the rule's own declaration as a violation.
    """
    sites: list[str] = []
    for path in sorted(paths):
        if path.resolve() == DECLARING_MODULE:
            continue
        text = path.read_text(encoding="utf-8")
        if WATCH_INVOCATION in text:
            sites.append(f"{path}::{WATCH_INVOCATION}")
        module = ast.parse(text, filename=str(path))
        sleep_names = _sleep_names(module)
        for node in ast.walk(module):
            if isinstance(node, ast.While) and _sleeps_forever(node, sleep_names):
                sites.append(f"{path}::while-true-sleep:{node.lineno}")
    return tuple(sites)


def _sleep_names(module: ast.Module) -> frozenset[str]:
    """Return every bare name an import in this module binds to `time.sleep`.

    A loop reaches the sleep through a name rather than an attribute when the
    file imports it directly, so the names that form can use are read from the
    file's own imports. A name bound to something else of the same spelling — a
    function the module defines itself — is not among them.
    """
    names: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and node.module == SLEEP_MODULE:
            names.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name == SLEEP_ATTRIBUTE
            )
    return frozenset(names)


def _reaches_sleep(func: ast.expr, sleep_names: frozenset[str]) -> bool:
    if isinstance(func, ast.Attribute):
        return func.attr == SLEEP_ATTRIBUTE
    return isinstance(func, ast.Name) and func.id in sleep_names


def _sleeps_forever(loop: ast.While, sleep_names: frozenset[str]) -> bool:
    if not (isinstance(loop.test, ast.Constant) and loop.test.value is True):
        return False
    return any(
        isinstance(inner, ast.Call) and _reaches_sleep(inner.func, sleep_names)
        for inner in ast.walk(loop)
    )
