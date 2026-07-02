#!/usr/bin/env python3
"""Report declarations inside executed test files for the audit-tests screen."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Sequence


class DeclarationKind(StrEnum):
    VARIABLE = "variable"
    CONSTANT = "constant"
    FUNCTION = "function"


@dataclass(frozen=True)
class Declaration:
    path: str
    line: int
    kind: DeclarationKind
    name: str
    language: str


_TYPESCRIPT_DECLARATION = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?P<kind>const|let|var|function)\s+(?P<name>[A-Za-z_$][\w$]*)"
)
_RUST_DECLARATION = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?P<kind>const|static|let|fn)\s+(?P<name>[A-Za-z_]\w*)"
)


class PathValidationError(ValueError):
    """Raised when a scanner input path is outside the current repository tree."""


def scan_paths(paths: Sequence[Path]) -> list[Declaration]:
    declarations: list[Declaration] = []
    for path in paths:
        safe_path = _validated_input_path(path)
        declarations.extend(scan_text(safe_path.read_text(encoding="utf-8"), safe_path))
    return declarations


def _validated_input_path(path: Path) -> Path:
    root = Path.cwd().resolve(strict=True)
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise PathValidationError(f"input path is not readable: {path}") from error
    if not resolved.is_relative_to(root):
        raise PathValidationError(
            f"input path escapes current working directory: {path}"
        )
    if not resolved.is_file():
        raise PathValidationError(f"input path is not a regular file: {path}")
    return resolved


def scan_text(source: str, path: Path) -> list[Declaration]:
    language = _language_for(path)
    if language == "python":
        return _scan_python(source, path)
    if language == "typescript":
        return _scan_line_language(source, path, language, _TYPESCRIPT_DECLARATION)
    if language == "rust":
        return _scan_line_language(source, path, language, _RUST_DECLARATION)
    return []


def _language_for(path: Path) -> str:
    name = path.name
    if name.endswith(".py"):
        return "python"
    if name.endswith((".ts", ".tsx", ".js", ".jsx")):
        return "typescript"
    if name.endswith(".rs"):
        return "rust"
    return "unknown"


def _scan_python(source: str, path: Path) -> list[Declaration]:
    tree = ast.parse(source, filename=str(path))
    declarations: list[Declaration] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            declarations.append(
                Declaration(
                    path=str(path),
                    line=node.lineno,
                    kind=DeclarationKind.FUNCTION,
                    name=node.name,
                    language="python",
                )
            )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                declarations.extend(
                    _python_target_declarations(target, path, node.lineno)
                )
        elif isinstance(node, ast.AnnAssign):
            declarations.extend(
                _python_target_declarations(node.target, path, node.lineno)
            )
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            declarations.extend(
                _python_target_declarations(node.target, path, node.lineno)
            )
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    declarations.extend(
                        _python_target_declarations(
                            item.optional_vars, path, node.lineno
                        )
                    )
    return declarations


def _python_target_declarations(
    target: ast.expr, path: Path, line: int
) -> list[Declaration]:
    if isinstance(target, ast.Name):
        return [
            Declaration(
                path=str(path),
                line=line,
                kind=_value_kind(target.id),
                name=target.id,
                language="python",
            )
        ]
    if isinstance(target, (ast.Tuple, ast.List)):
        declarations: list[Declaration] = []
        for element in target.elts:
            declarations.extend(_python_target_declarations(element, path, line))
        return declarations
    return []


def _scan_line_language(
    source: str,
    path: Path,
    language: str,
    declaration_pattern: re.Pattern[str],
) -> list[Declaration]:
    declarations: list[Declaration] = []
    for index, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith(("//", "#")):
            continue
        match = declaration_pattern.match(line)
        if match is None:
            continue
        name = match.group("name")
        declarations.append(
            Declaration(
                path=str(path),
                line=index,
                kind=DeclarationKind.FUNCTION
                if match.group("kind") in {"function", "fn"}
                else _value_kind(name),
                name=name,
                language=language,
            )
        )
    return declarations


def _value_kind(name: str) -> DeclarationKind:
    return DeclarationKind.CONSTANT if name.isupper() else DeclarationKind.VARIABLE


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report declarations in executed test files."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        declarations = scan_paths(args.paths)
    except PathValidationError as error:
        sys.stderr.write(f"declaration_scan.py: {error}\n")
        return 2
    json.dump(
        [asdict(declaration) for declaration in declarations], sys.stdout, indent=2
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
