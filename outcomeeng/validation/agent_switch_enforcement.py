"""Enforce that only the declaring module names a switch and every row projects it.

Two structural rules over repository source, each a pure function of the paths
and the source-owned names it receives, so both are verifiable against
violating fixtures without touching the real tree.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Final

from outcomeeng.validation import agent_disable
from outcomeeng.validation.agent_disable import AGENT_SWITCHES

DECLARING_MODULE: Final = Path(agent_disable.__file__).resolve()
"""The one module permitted to name a switch, resolved from the module itself."""

PYTHON_SUFFIX: Final = ".py"
"""The suffix of the source files these rules read."""

DECLARING_MODULE_NAME: Final = agent_disable.__name__
"""The dotted name a reader would import the predicate from."""

ACQUIRED_EXECUTABLE_LEVELS: Final = ("l2", "l3")
"""The execution-level cells whose rows reach an acquired agent executable."""


def modules_naming_a_switch(roots: Iterable[Path]) -> tuple[Path, ...]:
    """Return every Python file under `roots`, bar the declaring module, naming a switch.

    A module that imports the declared constants carries their identifiers, not
    their values, so only a second spelling of a switch's own text is reported.
    """
    offenders: list[Path] = []
    for root in roots:
        for path in python_modules(root):
            if path.resolve() == DECLARING_MODULE:
                continue
            text = path.read_text(encoding="utf-8")
            if any(switch in text for switch in AGENT_SWITCHES):
                offenders.append(path)
    return tuple(offenders)


class NotAPythonSource(ValueError):
    """A scanned path is neither a directory nor a Python module."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"neither a directory nor a Python module: {path}")
        self.path = path


def python_modules(root: Path) -> tuple[Path, ...]:
    """Return the Python modules `root` names, whether it is a directory or one file.

    A path that is neither is refused rather than scanned as empty, because a
    rule handed such a path would otherwise report no violation and read as a
    pass.
    """
    if root.is_dir():
        return tuple(sorted(root.rglob(f"*{PYTHON_SUFFIX}")))
    if root.is_file() and root.suffix == PYTHON_SUFFIX:
        return (root,)
    raise NotAPythonSource(root)


def rows_without_their_projection(
    test_files: Iterable[Path],
    *,
    projections: Mapping[str, Sequence[str]],
) -> tuple[str, ...]:
    """Return every row that reaches a real-process entry point without its projection.

    A row is a test function; it projects an agent's switch by carrying that
    agent's projection as a decorator. `projections` binds each entry point that
    starts a real agent process to the projections of the agents it starts, so a
    row reaching that entry point carries every one of them. A row that starts
    one agent's process while projecting only another agent's switch is
    therefore reported: a projection of an agent the row never starts declares
    nothing about the process it does start.
    """
    entry_points = frozenset(projections)
    offenders: list[str] = []
    for path in sorted(test_files):
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in _rows(module):
            reached = _reached(node, entry_points)
            if not reached:
                continue
            required = frozenset(
                projection
                for entry_point in reached
                for projection in projections[entry_point]
            )
            if required <= _decorator_names(node):
                continue
            offenders.append(f"{path}::{node.name}")
    return tuple(offenders)


type _Row = ast.FunctionDef | ast.AsyncFunctionDef


def _rows(module: ast.Module) -> tuple[_Row, ...]:
    """Return every row in the module, at any nesting depth, sync or async."""
    return tuple(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    )


def _reached(node: _Row, entry_points: frozenset[str]) -> frozenset[str]:
    """Return every entry point the row names, bare or through a module."""
    reached: set[str] = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Name) and inner.id in entry_points:
            reached.add(inner.id)
        elif isinstance(inner, ast.Attribute) and inner.attr in entry_points:
            reached.add(inner.attr)
    return frozenset(reached)


def _decorator_names(node: _Row) -> frozenset[str]:
    names: set[str] = set()
    for decorator in node.decorator_list:
        for inner in ast.walk(decorator):
            if isinstance(inner, ast.Name):
                names.add(inner.id)
            elif isinstance(inner, ast.Attribute):
                names.add(inner.attr)
    return frozenset(names)


def modules_reading_the_switch_predicate(paths: Iterable[Path]) -> tuple[Path, ...]:
    """Return every file among `paths` that imports from the declaring module.

    A module that never names a switch can still read one by importing the
    predicate, so the naming rule alone does not establish that a module
    reads no switch.
    """
    readers: list[Path] = []
    for root in sorted(paths):
        for path in python_modules(root):
            module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if any(_imports_the_declaration(node) for node in ast.walk(module)):
                readers.append(path)
    return tuple(readers)


def _imports_the_declaration(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        return node.module == DECLARING_MODULE_NAME
    if isinstance(node, ast.Import):
        return any(alias.name == DECLARING_MODULE_NAME for alias in node.names)
    return False
