"""Enforce that only the declaring module names a switch and every row projects it.

Two structural rules over repository source, each a pure function of the paths
and the source-owned names it receives, so both are verifiable against
violating fixtures without touching the real tree.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Final

from outcomeeng.validation import agent_disable
from outcomeeng.validation.agent_disable import AGENT_SWITCHES

DECLARING_MODULE: Final = Path(agent_disable.__file__).resolve()
"""The one module permitted to name a switch, resolved from the module itself."""

PYTHON_SUFFIX: Final = ".py"
"""The suffix of the source files these rules read."""


def modules_naming_a_switch(roots: Iterable[Path]) -> tuple[Path, ...]:
    """Return every Python file under `roots`, bar the declaring module, naming a switch.

    A module that imports the declared constants carries their identifiers, not
    their values, so only a second spelling of a switch's own text is reported.
    """
    offenders: list[Path] = []
    for root in roots:
        for path in sorted(root.rglob(f"*{PYTHON_SUFFIX}")):
            resolved = path.resolve()
            if resolved == DECLARING_MODULE:
                continue
            text = path.read_text(encoding="utf-8")
            if any(switch in text for switch in AGENT_SWITCHES):
                offenders.append(path)
    return tuple(offenders)


def rows_without_their_projection(
    test_files: Iterable[Path],
    *,
    entry_points: Sequence[str],
    projections: Sequence[str],
) -> tuple[str, ...]:
    """Return every row that reaches a real-process entry point without a projection.

    A row is a test function; it projects its agent's switch by carrying one of
    `projections` as a decorator. `entry_points` names the harness entry points
    that start a real agent process.
    """
    entry_point_set = frozenset(entry_points)
    projection_set = frozenset(projections)
    offenders: list[str] = []
    for path in sorted(test_files):
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in module.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith("test_"):
                continue
            if not _reaches(node, entry_point_set):
                continue
            if _decorator_names(node) & projection_set:
                continue
            offenders.append(f"{path}::{node.name}")
    return tuple(offenders)


def _reaches(node: ast.FunctionDef, entry_points: frozenset[str]) -> bool:
    return any(
        isinstance(inner, ast.Name) and inner.id in entry_points
        for inner in ast.walk(node)
    )


def _decorator_names(node: ast.FunctionDef) -> frozenset[str]:
    names: set[str] = set()
    for decorator in node.decorator_list:
        for inner in ast.walk(decorator):
            if isinstance(inner, ast.Name):
                names.add(inner.id)
            elif isinstance(inner, ast.Attribute):
                names.add(inner.attr)
    return frozenset(names)
