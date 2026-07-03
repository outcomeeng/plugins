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
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?P<kind>const|let|var|function)\s+(?P<body>.+)"
)
_RUST_DECLARATION = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?P<kind>const|static|let|fn)\s+(?P<body>.+)"
)
_TYPESCRIPT_IDENTIFIER = re.compile(r"(?P<name>[A-Za-z_$][\w$]*)")
_RUST_IDENTIFIER = re.compile(r"[A-Za-z_]\w*")
_RUST_PATTERN_PREFIXES: frozenset[str] = frozenset(("mut", "ref"))


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
        return _scan_typescript(source, path)
    if language == "rust":
        return _scan_rust(source, path)
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


def _scan_rust(source: str, path: Path) -> list[Declaration]:
    declarations: list[Declaration] = []
    in_block_comment = False
    for index, line in enumerate(source.splitlines(), start=1):
        line, in_block_comment = _strip_block_comments(line, in_block_comment)
        stripped = line.lstrip()
        if stripped.startswith(("//", "#")):
            continue
        match = _RUST_DECLARATION.match(line)
        if match is None:
            continue
        kind = match.group("kind")
        body = match.group("body")
        names = (
            _rust_let_binding_names(body)
            if kind == "let"
            else _rust_named_item_name(body)
        )
        for name in names:
            declarations.append(
                Declaration(
                    path=str(path),
                    line=index,
                    kind=DeclarationKind.FUNCTION
                    if kind == "fn"
                    else _value_kind(name),
                    name=name,
                    language="rust",
                )
            )
    return declarations


def _rust_named_item_name(body: str) -> list[str]:
    names = _RUST_IDENTIFIER.findall(body)
    while names and names[0] in _RUST_PATTERN_PREFIXES:
        names = names[1:]
    return names[:1]


def _rust_let_binding_names(body: str) -> list[str]:
    pattern = _before_top_level(_before_top_level(body, "="), ":").strip()
    return _rust_pattern_names(pattern)


def _rust_pattern_names(pattern: str) -> list[str]:
    pattern = pattern.strip()
    while pattern.startswith("&"):
        pattern = pattern[1:].strip()
    for prefix in _RUST_PATTERN_PREFIXES:
        if pattern.startswith(f"{prefix} "):
            return _rust_pattern_names(pattern[len(prefix) :])
    if not pattern or pattern in {"_", ".."}:
        return []
    alias_parts = _split_top_level(pattern, "@", maxsplit=1)
    if len(alias_parts) > 1:
        return _rust_names_from_segments(alias_parts)
    if pattern[0] in "([{":
        inner = _strip_enclosing_pattern(pattern)
        return _rust_names_from_segments(_split_top_level_commas(inner))
    if "{" in pattern:
        inner = pattern[pattern.find("{") + 1 : pattern.rfind("}")]
        return _rust_struct_field_names(inner)
    if "(" in pattern and pattern.endswith(")"):
        inner = pattern[pattern.find("(") + 1 : -1]
        return _rust_names_from_segments(_split_top_level_commas(inner))
    match = _RUST_IDENTIFIER.fullmatch(pattern)
    return [pattern] if match is not None else []


def _rust_struct_field_names(inner: str) -> list[str]:
    names: list[str] = []
    for segment in _split_top_level_commas(inner):
        field = segment.strip()
        if not field or field == "..":
            continue
        if ":" in field:
            names.extend(_rust_pattern_names(field.split(":", 1)[1]))
            continue
        names.extend(_rust_pattern_names(field))
    return names


def _rust_names_from_segments(segments: list[str]) -> list[str]:
    names: list[str] = []
    for segment in segments:
        names.extend(_rust_pattern_names(segment))
    return names


def _strip_enclosing_pattern(pattern: str) -> str:
    pairs = {"(": ")", "[": "]", "{": "}"}
    closing = pairs.get(pattern[0])
    if closing is not None and pattern.endswith(closing):
        return pattern[1:-1]
    return pattern


def _scan_typescript(source: str, path: Path) -> list[Declaration]:
    declarations: list[Declaration] = []
    in_block_comment = False
    for index, line in enumerate(source.splitlines(), start=1):
        line, in_block_comment = _strip_block_comments(line, in_block_comment)
        stripped = line.lstrip()
        if stripped.startswith(("//", "#")):
            continue
        match = _TYPESCRIPT_DECLARATION.match(line)
        if match is None:
            continue
        kind = match.group("kind")
        if kind == "function":
            name_match = _TYPESCRIPT_IDENTIFIER.match(match.group("body"))
            if name_match is not None:
                declarations.append(
                    Declaration(
                        path=str(path),
                        line=index,
                        kind=DeclarationKind.FUNCTION,
                        name=name_match.group("name"),
                        language="typescript",
                    )
                )
            continue
        for declarator in _split_typescript_declarators(match.group("body")):
            name_match = _TYPESCRIPT_IDENTIFIER.search(declarator.strip())
            if name_match is not None:
                name = name_match.group("name")
                declarations.append(
                    Declaration(
                        path=str(path),
                        line=index,
                        kind=_value_kind(name),
                        name=name,
                        language="typescript",
                    )
                )
    return declarations


def _split_typescript_declarators(body: str) -> list[str]:
    return _split_top_level(body, ",", track_type_angles=True)


def _split_top_level_commas(body: str) -> list[str]:
    return _split_top_level(body, ",")


def _before_top_level(body: str, delimiter: str) -> str:
    return _split_top_level(body, delimiter, maxsplit=1)[0]


def _split_top_level(
    body: str,
    delimiter: str,
    *,
    maxsplit: int | None = None,
    track_type_angles: bool = False,
) -> list[str]:
    declarators: list[str] = []
    start = 0
    depth = 0
    angle_depth = 0
    quote: str | None = None
    escaped = False
    splits = 0
    for index, char in enumerate(body):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif track_type_angles and depth == 0 and char == "<":
            angle_depth += 1
        elif track_type_angles and depth == 0 and char == ">":
            angle_depth = max(0, angle_depth - 1)
        elif char in {"(", "[", "{"}:
            depth += 1
        elif char in {
            ")",
            "]",
            "}",
        }:
            depth = max(0, depth - 1)
        elif char == delimiter and depth == 0 and angle_depth == 0:
            declarators.append(body[start:index])
            start = index + 1
            splits += 1
            if maxsplit is not None and splits >= maxsplit:
                break
    declarators.append(body[start:])
    return declarators


def _strip_block_comments(line: str, in_block_comment: bool) -> tuple[str, bool]:
    output: list[str] = []
    index = 0
    quote: str | None = None
    escaped = False
    while index < len(line):
        if in_block_comment:
            end = line.find("*/", index)
            if end == -1:
                return "".join(output), True
            index = end + 2
            in_block_comment = False
            continue
        char = line[index]
        if quote is not None:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            output.append(char)
            index += 1
            continue
        if line.startswith("//", index):
            return "".join(output), False
        if line.startswith("/*", index):
            index += 2
            in_block_comment = True
            continue
        output.append(char)
        index += 1
    return "".join(output), in_block_comment


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
