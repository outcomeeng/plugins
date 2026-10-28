"""Find harness launches of a script that leave the interpreter's bytecode writing on.

A harness starts a shipped script as ``[sys.executable, <script>, ...]``.  The
launch carries the interpreter's no-bytecode option directly after the
interpreter, so the run leaves no bytecode cache beside the script.  A launch of
an inline program (``-c``) or a module (``-m``) runs no script file and needs no option.
"""

from __future__ import annotations

import ast
from typing import Final

from outcomeeng.distribution.shipped_scripts import NO_BYTECODE_OPTION

INTERPRETER_ATTRIBUTE: Final = "executable"
INTERPRETER_MODULE: Final = "sys"
INLINE_PROGRAM_OPTION: Final = "-c"
MODULE_OPTION: Final = "-m"
_OPTION_NAME: Final = "NO_BYTECODE_OPTION"


def unguarded_script_launches(source: str) -> tuple[int, ...]:
    """Return the line of every script launch whose argv lacks the no-bytecode option."""
    lines: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.List, ast.Tuple)) and _is_unguarded_launch(node.elts):
            lines.append(node.lineno)
    return tuple(sorted(lines))


def _is_unguarded_launch(elements: list[ast.expr]) -> bool:
    if not elements or not _is_interpreter(elements[0]):
        return False
    options: list[str] = []
    for element in elements[1:]:
        if isinstance(element, ast.Name) and element.id == _OPTION_NAME:
            options.append(NO_BYTECODE_OPTION)
            continue
        if isinstance(element, ast.Constant) and isinstance(element.value, str):
            if element.value.startswith("-"):
                options.append(element.value)
                continue
        break
    else:
        return False
    if INLINE_PROGRAM_OPTION in options or MODULE_OPTION in options:
        return False
    return NO_BYTECODE_OPTION not in options


def _is_interpreter(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == INTERPRETER_ATTRIBUTE
        and isinstance(node.value, ast.Name)
        and node.value.id == INTERPRETER_MODULE
    )


__all__ = ["unguarded_script_launches"]
