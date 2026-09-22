"""Report unbounded polling waits in source, as a pure function of the paths given.

The rule the gate node declares forbids two shapes: a `while True` loop that
sleeps, and a watch invocation that blocks without bound. Both are reported
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
        for node in ast.walk(ast.parse(text, filename=str(path))):
            if isinstance(node, ast.While) and _sleeps_forever(node):
                sites.append(f"{path}::while-true-sleep:{node.lineno}")
    return tuple(sites)


def _sleeps_forever(loop: ast.While) -> bool:
    if not (isinstance(loop.test, ast.Constant) and loop.test.value is True):
        return False
    return any(
        isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Attribute)
        and inner.func.attr == SLEEP_ATTRIBUTE
        for inner in ast.walk(loop)
    )
