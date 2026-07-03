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
from typing import Callable, Sequence


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
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?P<kind>const|let|var|function)\s+(?P<body>.+)",
    re.DOTALL,
)
_TYPESCRIPT_FOR_DECLARATION = re.compile(
    r"^\s*for\s+(?:await\s+)?\(\s*(?P<kind>const|let|var)\s+(?P<body>.+)",
    re.DOTALL,
)
_TYPESCRIPT_CATCH_DECLARATION = re.compile(
    r"^\s*}?\s*catch\s*\(\s*(?P<body>[^)]*)\)",
    re.DOTALL,
)
_TYPESCRIPT_WORD_CONTINUATION = re.compile(
    r"^(?:as|extends|in|instanceof|is|of|satisfies)\b"
)
_RUST_DECLARATION = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?P<kind>const|static|let|fn)\s+(?P<body>.+)",
    re.DOTALL,
)
_RUST_CONDITIONAL_LET_DECLARATION = re.compile(
    r"^\s*(?:if|while)\s+let\s+(?P<body>.+)",
    re.DOTALL,
)
_RUST_FOR_DECLARATION = re.compile(
    r"^\s*for\s+(?P<body>.+)",
    re.DOTALL,
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
        elif isinstance(node, ast.NamedExpr):
            declarations.extend(
                _python_target_declarations(node.target, path, node.lineno)
            )
        elif isinstance(node, ast.ExceptHandler):
            if node.name is not None:
                declarations.append(
                    _python_variable_declaration(node.name, path, node.lineno)
                )
        elif isinstance(node, ast.Match):
            for case in node.cases:
                declarations.extend(
                    _python_pattern_declarations(case.pattern, path, node.lineno)
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
    if isinstance(target, ast.Starred):
        return _python_target_declarations(target.value, path, line)
    return []


def _python_pattern_declarations(
    pattern: ast.pattern, path: Path, line: int
) -> list[Declaration]:
    if isinstance(pattern, ast.MatchAs):
        declarations = (
            _python_pattern_declarations(pattern.pattern, path, line)
            if pattern.pattern is not None
            else []
        )
        if pattern.name is not None:
            declarations.append(_python_variable_declaration(pattern.name, path, line))
        return declarations
    if isinstance(pattern, ast.MatchStar):
        return (
            [_python_variable_declaration(pattern.name, path, line)]
            if pattern.name is not None
            else []
        )
    if isinstance(pattern, ast.MatchMapping):
        declarations: list[Declaration] = []
        for subpattern in pattern.patterns:
            declarations.extend(_python_pattern_declarations(subpattern, path, line))
        if pattern.rest is not None:
            declarations.append(_python_variable_declaration(pattern.rest, path, line))
        return declarations
    if isinstance(pattern, (ast.MatchSequence, ast.MatchOr)):
        declarations: list[Declaration] = []
        for subpattern in pattern.patterns:
            declarations.extend(_python_pattern_declarations(subpattern, path, line))
        return declarations
    if isinstance(pattern, ast.MatchClass):
        declarations: list[Declaration] = []
        for subpattern in [*pattern.patterns, *pattern.kwd_patterns]:
            declarations.extend(_python_pattern_declarations(subpattern, path, line))
        return declarations
    return []


def _python_variable_declaration(name: str, path: Path, line: int) -> Declaration:
    return Declaration(
        path=str(path),
        line=line,
        kind=_value_kind(name),
        name=name,
        language="python",
    )


def _scan_rust(source: str, path: Path) -> list[Declaration]:
    declarations: list[Declaration] = []
    declarations.extend(_rust_match_declarations(source, path))
    for index, unit in _rust_declaration_units(source):
        stripped = unit.lstrip()
        if stripped.startswith(("//", "#")):
            continue
        item_match = _RUST_DECLARATION.match(unit)
        conditional_match = (
            _RUST_CONDITIONAL_LET_DECLARATION.match(unit)
            if item_match is None
            else None
        )
        for_match = (
            _RUST_FOR_DECLARATION.match(unit)
            if item_match is None and conditional_match is None
            else None
        )
        if item_match is None and conditional_match is None and for_match is None:
            continue
        kind = item_match.group("kind") if item_match is not None else "let"
        body = (
            item_match.group("body")
            if item_match is not None
            else conditional_match.group("body")
            if conditional_match is not None
            else for_match.group("body")
        )
        names = (
            _rust_let_binding_names(body)
            if kind == "let" and for_match is None
            else _rust_for_binding_names(body)
            if for_match is not None
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


def _rust_declaration_units(source: str) -> list[tuple[int, str]]:
    return _declaration_units(
        source,
        start_pattern=re.compile(
            r"^\s*(?:(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:const|static|let|fn)|(?:if|while)\s+let|for)\b"
        ),
        header_only_pattern=re.compile(
            r"^\s*(?:(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn|for)\b"
        ),
        conditional_header_pattern=re.compile(r"^\s*(?:if|while)\s+let\b"),
    )


def _rust_named_item_name(body: str) -> list[str]:
    names = _RUST_IDENTIFIER.findall(body)
    while names and names[0] in _RUST_PATTERN_PREFIXES:
        names = names[1:]
    return names[:1]


def _rust_let_binding_names(body: str) -> list[str]:
    pattern = _before_top_level(_before_top_level(body, "="), ":").strip()
    return _rust_pattern_names(pattern)


def _rust_for_binding_names(body: str) -> list[str]:
    pattern = _before_top_level_token(body, " in ").strip()
    return _rust_pattern_names(pattern)


def _rust_match_declarations(source: str, path: Path) -> list[Declaration]:
    declarations: list[Declaration] = []
    lexical_state = _LexicalState()
    for index, raw_line in enumerate(source.splitlines(), start=1):
        line = _strip_comments(raw_line, lexical_state)
        pattern = _rust_match_arm_pattern(line)
        if pattern is None:
            continue
        for name in _rust_pattern_names(pattern):
            declarations.append(
                Declaration(
                    path=str(path),
                    line=index,
                    kind=_value_kind(name),
                    name=name,
                    language="rust",
                )
            )
    return declarations


def _rust_match_arm_pattern(line: str) -> str | None:
    arrow_index = _top_level_token_index(line, "=>")
    if arrow_index is None:
        return None
    pattern = line[:arrow_index].strip()
    if not pattern or pattern.startswith(("//", "#")):
        return None
    return _before_top_level_token(pattern, " if ").strip()


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
    for index, unit in _typescript_declaration_units(source):
        stripped = unit.lstrip()
        if stripped.startswith(("//", "#")):
            continue
        match = _TYPESCRIPT_DECLARATION.match(unit)
        is_for_declaration = False
        is_catch_declaration = False
        if match is None:
            match = _TYPESCRIPT_FOR_DECLARATION.match(unit)
            is_for_declaration = match is not None
        if match is None:
            match = _TYPESCRIPT_CATCH_DECLARATION.match(unit)
            is_catch_declaration = match is not None
        if match is None:
            continue
        kind = match.group("kind") if not is_catch_declaration else "let"
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
        body = (
            _typescript_for_binding_body(match.group("body"))
            if is_for_declaration
            else match.group("body")
        )
        for declarator in _split_typescript_declarators(body):
            for name in _typescript_binding_names(declarator):
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


def _typescript_declaration_units(source: str) -> list[tuple[int, str]]:
    return _declaration_units(
        source,
        start_pattern=re.compile(
            r"^\s*(?:}?\s*catch\s*\(|(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:const|let|var|function)|for\s+(?:await\s+)?\()"
        ),
        header_only_pattern=re.compile(
            r"^\s*(?:}?\s*catch\s*\(|(?:export\s+)?(?:default\s+)?(?:async\s+)?function|for\s+(?:await\s+)?\()"
        ),
        conditional_header_pattern=None,
        continuation_line=_typescript_line_continues_declaration,
    )


def _split_typescript_declarators(body: str) -> list[str]:
    return _split_top_level(body, ",", track_type_angles=True)


def _typescript_for_binding_body(body: str) -> str:
    truncated = body
    for delimiter in (" of ", " in "):
        truncated = _before_top_level_token(truncated, delimiter)
    return _before_top_level(_before_top_level(truncated, ";"), "=")


def _typescript_binding_names(pattern: str) -> list[str]:
    pattern = _before_top_level(pattern.strip(), "=").strip()
    if not pattern:
        return []
    while pattern.startswith("..."):
        pattern = pattern[3:].strip()
    if pattern[0] in "[{":
        inner = _strip_enclosing_pattern(pattern)
        return _typescript_names_from_segments(
            _split_top_level_commas(inner),
            object_pattern=pattern[0] == "{",
        )
    if ":" in pattern:
        pattern = _before_top_level(pattern, ":").strip()
    name_match = _TYPESCRIPT_IDENTIFIER.fullmatch(pattern)
    return [pattern] if name_match is not None else []


def _typescript_names_from_segments(
    segments: list[str], *, object_pattern: bool = False
) -> list[str]:
    names: list[str] = []
    for segment in segments:
        binding_segment = segment
        if object_pattern:
            binding_segment = _typescript_object_binding_segment(segment)
        names.extend(_typescript_binding_names(binding_segment))
    return names


def _typescript_object_binding_segment(segment: str) -> str:
    parts = _split_top_level(segment, ":", maxsplit=1)
    if len(parts) == 1:
        return segment
    return parts[1]


def _declaration_units(
    source: str,
    *,
    start_pattern: re.Pattern[str],
    header_only_pattern: re.Pattern[str],
    conditional_header_pattern: re.Pattern[str] | None,
    continuation_line: Callable[[str], bool] | None = None,
) -> list[tuple[int, str]]:
    units: list[tuple[int, str]] = []
    current: list[str] = []
    start_line = 0
    header_only = False
    conditional_header = False
    lexical_state = _LexicalState()
    raw_lines = source.splitlines()
    for index, raw_line in enumerate(raw_lines, start=1):
        line = _strip_comments(raw_line, lexical_state)
        if not current:
            if not start_pattern.match(line):
                continue
            current = [line]
            start_line = index
            header_only = header_only_pattern.match(line) is not None
            conditional_header = (
                conditional_header_pattern.match(line) is not None
                if conditional_header_pattern is not None
                else False
            )
        else:
            current.append(line)
        unit = "\n".join(current)
        complete = (
            _declaration_header_complete(unit)
            if header_only
            else _conditional_declaration_header_complete(unit)
            if conditional_header
            else _declaration_unit_complete(unit)
        )
        if (
            complete
            and continuation_line is not None
            and not header_only
            and not conditional_header
            and _next_line_continues_declaration(
                raw_lines,
                index,
                _copy_lexical_state(lexical_state),
                continuation_line,
            )
        ):
            complete = False
        if complete:
            units.append((start_line, unit))
            current = []
            start_line = 0
            header_only = False
            conditional_header = False
    if current:
        units.append((start_line, "\n".join(current)))
    return units


def _next_line_continues_declaration(
    raw_lines: list[str],
    current_index: int,
    lexical_state: _LexicalState,
    continuation_line: Callable[[str], bool],
) -> bool:
    for next_line in raw_lines[current_index:]:
        stripped = _strip_comments(next_line, lexical_state).lstrip()
        if not stripped:
            continue
        return continuation_line(stripped)
    return False


def _typescript_line_continues_declaration(line: str) -> bool:
    return (
        line.startswith(
            (
                "=>",
                "&&",
                "||",
                "??",
                "?.",
                ".",
                ",",
                "?",
                ":",
                "+",
                "-",
                "*",
                "/",
                "%",
                "&",
                "|",
                "^",
                "~",
                "!",
                "<",
                ">",
                "=",
                "(",
                "[",
                "`",
            )
        )
        or _TYPESCRIPT_WORD_CONTINUATION.match(line) is not None
    )


def _conditional_declaration_header_complete(unit: str) -> bool:
    depth = 0
    quote: str | None = None
    escaped = False
    for char in unit:
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
        elif char in {"(", "[", "{"}:
            depth += 1
        elif char in {")", "]", "}"}:
            depth = max(0, depth - 1)
        elif depth == 0 and char == "=":
            return True
    return False


def _declaration_header_complete(unit: str) -> bool:
    depth = 0
    quote: str | None = None
    escaped = False
    for char in unit:
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
        elif char in {"(", "[", "{"}:
            if char == "{" and depth == 0:
                return True
            depth += 1
        elif char in {")", "]", "}"}:
            depth = max(0, depth - 1)
        elif depth == 0 and char == ";":
            return True
    if quote is not None:
        return False
    return depth == 0 and "\n" not in unit


def _declaration_unit_complete(unit: str) -> bool:
    depth = 0
    quote: str | None = None
    escaped = False
    last_significant = ""
    for char in unit:
        if not char.isspace():
            last_significant = char
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
        elif char in {"(", "[", "{"}:
            depth += 1
        elif char in {")", "]", "}"}:
            depth = max(0, depth - 1)
        elif depth == 0 and char == ";":
            return True
    if quote is not None:
        return False
    if depth != 0:
        return False
    if last_significant in {"", "=", ",", ".", "?", ":"}:
        return False
    stripped = unit.rstrip()
    return not _ends_with_expression_continuation(stripped)


def _ends_with_expression_continuation(text: str) -> bool:
    if text.endswith(
        (
            "=>",
            "&&",
            "||",
            "??",
            "?.",
            "+",
            "-",
            "*",
            "/",
            "%",
            "&",
            "|",
            "^",
            "~",
            "<",
            ">",
            "==",
            "===",
            "!=",
            "!==",
            "<=",
            ">=",
        )
    ):
        return True
    if re.search(
        r"\b(?:as|extends|in|instanceof|is|of|satisfies)$",
        text,
    ):
        return True
    return False


def _split_top_level_commas(body: str) -> list[str]:
    return _split_top_level(body, ",")


def _before_top_level(body: str, delimiter: str) -> str:
    return _split_top_level(body, delimiter, maxsplit=1)[0]


def _before_top_level_token(body: str, delimiter: str) -> str:
    index = _top_level_token_index(body, delimiter)
    return body[:index] if index is not None else body


def _top_level_token_index(body: str, delimiter: str) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
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
        elif char in {"(", "[", "{"}:
            depth += 1
        elif char in {")", "]", "}"}:
            depth = max(0, depth - 1)
        elif depth == 0 and body.startswith(delimiter, index):
            return index
    return None


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


@dataclass
class _LexicalState:
    in_block_comment: bool = False
    quote: str | None = None
    escaped: bool = False
    in_regex: bool = False
    regex_char_class: bool = False


def _copy_lexical_state(state: _LexicalState) -> _LexicalState:
    return _LexicalState(
        in_block_comment=state.in_block_comment,
        quote=state.quote,
        escaped=state.escaped,
        in_regex=state.in_regex,
        regex_char_class=state.regex_char_class,
    )


def _strip_comments(line: str, state: _LexicalState) -> str:
    output: list[str] = []
    index = 0
    while index < len(line):
        if state.in_block_comment:
            end = line.find("*/", index)
            if end == -1:
                return "".join(output)
            index = end + 2
            state.in_block_comment = False
            continue
        char = line[index]
        if state.quote is not None:
            output.append(char)
            if state.escaped:
                state.escaped = False
            elif char == "\\":
                state.escaped = True
            elif char == state.quote:
                state.quote = None
            index += 1
            continue
        if state.in_regex:
            output.append(char)
            if state.escaped:
                state.escaped = False
            elif char == "\\":
                state.escaped = True
            elif char == "[":
                state.regex_char_class = True
            elif char == "]":
                state.regex_char_class = False
            elif char == "/" and not state.regex_char_class:
                state.in_regex = False
            index += 1
            continue
        if char in {"'", '"', "`"}:
            state.quote = char
            output.append(char)
            index += 1
            continue
        if char == "/" and _looks_like_regex_literal_start(line, index):
            state.in_regex = True
            output.append(char)
            index += 1
            continue
        if line.startswith("//", index):
            return "".join(output)
        if line.startswith("/*", index):
            index += 2
            state.in_block_comment = True
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _looks_like_regex_literal_start(line: str, index: int) -> bool:
    if not line.startswith("/", index):
        return False
    if index + 1 >= len(line) or line[index + 1] in {"/", "*"}:
        return False
    before = line[:index].rstrip()
    if not before:
        return True
    expression_prefix_keywords = {
        "case",
        "delete",
        "return",
        "throw",
        "typeof",
        "void",
        "yield",
    }
    token = re.search(r"[A-Za-z_$][\w$]*$", before)
    if token is not None:
        return token.group(0) in expression_prefix_keywords
    if before.endswith("=>"):
        return True
    if before[-1] in "=({[:,;!?'~+-*%&|^<>":
        return True
    if before.endswith(("&&", "||", "??", "==", "===", "!=", "!==", "<=", ">=")):
        return True
    return False


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
