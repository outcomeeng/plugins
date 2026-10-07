"""Convert the citations in a spec tree to tree-absolute Markdown links.

Usage: convert_links.py ROOT [PATH ...]

ROOT is the product root, the directory that holds ``spx/``. Each PATH is a
file or directory beneath ``ROOT/spx``; the default is ``spx``. The script
rewrites the Markdown files it reaches in place and prints one JSON document on
stdout:

    {"schemaVersion": 1, "rewritten": [...], "unconvertible": [...]}

``rewritten`` lists each changed file as a path from ROOT. ``unconvertible``
lists each citation the script cannot convert as ``file``, ``line``, ``form``
and ``target``; the run continues past it.

The exit status is 0 when no citation remains unconvertible, 3 after the
complete report when any does, and 1 when ROOT holds no ``spx/`` directory, a
PATH is missing or lies outside ``ROOT/spx``, or another error stops the run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

SCHEMA_VERSION = 1
DESCRIPTION = "Convert spec-tree citations to tree-absolute Markdown links."
SPEC_TREE_DIRECTORY = "spx"
MARKDOWN_SUFFIX = ".md"
DECISION_SUFFIXES = (".adr.md", ".pdr.md")
FORM_BARE_PROSE = "text-decision"
FORM_UNRESOLVABLE = "broken"
FORM_OUTSIDE_TREE = "outside-tree"
FORM_EVIDENCE_LINK = "evidence-link"
EVIDENCE_LINK_TEXTS = frozenset({"test", "eval", "probe"})
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_UNCONVERTIBLE = 3
NODE_KINDS = (
    "enabler",
    "outcome",
    "product",
    "substrate",
    "capability",
    "domain",
    "interface",
    "surface",
    "variant",
)
PLACEHOLDER_INDEX_PREFIX = "NN-"

NODE_DIRECTORY = re.compile(
    rf"^\d+(?:\.\d+)*-[a-z0-9]+(?:-[a-z0-9]+)*\.(?:{'|'.join(NODE_KINDS)})$"
)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
REFERENCE_DEFINITION = re.compile(
    r"^(?P<lead>\s*\[(?P<label>[^\]]+)\]:\s*)(?P<href>\S+)(?P<rest>.*)$"
)
EVIDENCE_REFERENCE_USE = re.compile(
    rf"\[(?:{'|'.join(sorted(EVIDENCE_LINK_TEXTS))})\]\[(?P<label>[^\]]+)\]"
)
INLINE = re.compile(
    r"(?P<link>(?P<bang>!?)\[(?P<text>(?:[^\[\]`]|`[^`]*`|\[[^\]]*\])*)\]"
    r"\((?P<href>[^)\s]+)(?P<title>\s+\"[^\"]*\")?\))"
    r"|(?P<code>(?P<ticks>`+)(?P<body>.+?)(?P=ticks))"
)
CODE_SPAN_DECISION = re.compile(r"[A-Za-z0-9_./-]+\.(?:adr|pdr)\.md")
CODE_SPAN_HELD_DECISION = re.compile(r"[A-Za-z0-9_./-]*[A-Za-z0-9]\.(?:adr|pdr)\.md")
PROSE_DECISION = re.compile(r"[A-Za-z0-9_./{}-]*\.(?:adr|pdr)\.md")


class ResultField(StrEnum):
    SCHEMA_VERSION = "schemaVersion"
    REWRITTEN = "rewritten"
    UNCONVERTIBLE = "unconvertible"
    FILE = "file"
    LINE = "line"
    FORM = "form"
    TARGET = "target"


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    form: str
    target: str


@dataclass(frozen=True)
class ConversionResult:
    rewritten: tuple[str, ...]
    unconvertible: tuple[Finding, ...]


class ConversionError(Exception):
    """A Markdown file could not be read, decoded, or written."""

    def __init__(self, file: str, cause: Exception, rewritten: tuple[str, ...]) -> None:
        super().__init__(f"{file}: {cause}")
        self.file = file
        self.cause = cause
        self.rewritten = rewritten


@dataclass(frozen=True)
class FileContext:
    root: Path
    file: Path
    node_directory: Path


def has_placeholder(path: str) -> bool:
    return any(
        "{" in segment or "}" in segment or segment.startswith(PLACEHOLDER_INDEX_PREFIX)
        for segment in path.split("/")
    )


def is_decision(path: str) -> bool:
    return path.endswith(DECISION_SUFFIXES)


def locate_node_directory(root: Path, file: Path) -> Path:
    spec_tree = root / SPEC_TREE_DIRECTORY
    directory = file.parent
    while directory != spec_tree and directory != root:
        if NODE_DIRECTORY.match(directory.name):
            return directory
        directory = directory.parent
    return spec_tree


def resolve_target(context: FileContext, path: str) -> Path | None:
    """Return the existing target a path names, or None when it names none."""
    if path.startswith("/"):
        candidate = context.root / path.lstrip("/")
    elif path == SPEC_TREE_DIRECTORY or path.startswith(f"{SPEC_TREE_DIRECTORY}/"):
        candidate = context.root / path
    else:
        candidate = context.file.parent / path
    target = Path(os.path.normpath(candidate))
    if not target.is_relative_to(context.root) or not target.exists():
        return None
    return target


def is_in_spec_tree(context: FileContext, target: Path) -> bool:
    return target.is_relative_to(context.root / SPEC_TREE_DIRECTORY)


def reaches_into_descendant(context: FileContext, target: Path) -> bool:
    if not target.is_relative_to(context.node_directory):
        return False
    parts = target.relative_to(context.node_directory).parts
    directories = parts if target.is_dir() else parts[:-1]
    return any(NODE_DIRECTORY.match(part) for part in directories)


def needs_conversion(context: FileContext, path: str, target: Path) -> bool:
    return (
        is_decision(path)
        or path.startswith("/")
        or ".." in path.split("/")
        or reaches_into_descendant(context, target)
    )


def tree_absolute(context: FileContext, path: str, target: Path) -> str:
    converted = target.relative_to(context.root).as_posix()
    return converted + "/" if path.endswith("/") else converted


class LineConverter:
    """Convert one Markdown line and collect the citations it cannot convert."""

    def __init__(
        self,
        context: FileContext,
        line_number: int,
        evidence_labels: frozenset[str] = frozenset(),
    ) -> None:
        self._context = context
        self._line_number = line_number
        self._evidence_labels = evidence_labels
        self.findings: list[Finding] = []

    def _report(self, form: str, target: str) -> None:
        file = self._context.file.relative_to(self._context.root).as_posix()
        self.findings.append(Finding(file, self._line_number, form, target))

    def _convert_href(self, href: str, *, evidence: bool = False) -> str | None:
        """Return the converted href, or None when the href stays as written."""
        path, separator, fragment = href.partition("#")
        if SCHEME.match(href) or not path or has_placeholder(path):
            return None
        target = resolve_target(self._context, path)
        if target is None:
            self._report(FORM_UNRESOLVABLE, href)
            return None
        if not needs_conversion(self._context, path, target):
            return None
        if not is_in_spec_tree(self._context, target):
            self._report(FORM_OUTSIDE_TREE, href)
            return None
        if evidence:
            self._report(FORM_EVIDENCE_LINK, href)
            return None
        return tree_absolute(self._context, path, target) + separator + fragment

    def _link(self, match: re.Match[str]) -> str:
        href = match["href"]
        converted = self._convert_href(
            href, evidence=match["text"] in EVIDENCE_LINK_TEXTS
        )
        if converted is None:
            return match[0]
        old_path = href.partition("#")[0]
        new_path = converted.partition("#")[0]
        text = match["text"]
        if text in (old_path, f"`{old_path}`"):
            text = text.replace(old_path, new_path)
        return f"{match['bang']}[{text}]({converted}{match['title'] or ''})"

    def _code_span(self, match: re.Match[str]) -> str:
        body = match["body"]
        if not CODE_SPAN_DECISION.fullmatch(body):
            for path in PROSE_DECISION.finditer(body):
                if has_placeholder(path[0]):
                    continue
                for held in CODE_SPAN_HELD_DECISION.finditer(path[0]):
                    self._report(FORM_BARE_PROSE, held[0])
            return match[0]
        if has_placeholder(body):
            return match[0]
        target = resolve_target(self._context, body)
        if target is None:
            self._report(FORM_UNRESOLVABLE, body)
            return match[0]
        if not is_in_spec_tree(self._context, target):
            self._report(FORM_OUTSIDE_TREE, body)
            return match[0]
        converted = tree_absolute(self._context, body, target)
        return f"[`{converted}`]({converted})"

    def _prose(self, segment: str) -> str:
        for match in PROSE_DECISION.finditer(segment):
            if not has_placeholder(match[0]):
                self._report(FORM_BARE_PROSE, match[0])
        return segment

    def convert(self, line: str) -> str:
        definition = REFERENCE_DEFINITION.match(line)
        if definition is not None:
            label = definition["label"]
            converted = self._convert_href(
                definition["href"],
                evidence=label in EVIDENCE_LINK_TEXTS
                or label.casefold() in self._evidence_labels,
            )
            if converted is None:
                return line
            return f"{definition['lead']}{converted}{definition['rest']}"
        pieces: list[str] = []
        position = 0
        for match in INLINE.finditer(line):
            pieces.append(self._prose(line[position : match.start()]))
            convert_match: Callable[[re.Match[str]], str] = (
                self._link if match["link"] else self._code_span
            )
            pieces.append(convert_match(match))
            position = match.end()
        pieces.append(self._prose(line[position:]))
        return "".join(pieces)


def closes_fence(line: str, fence: str) -> bool:
    stripped = line.strip()
    return len(stripped) >= len(fence) and set(stripped) == {fence[0]}


def fenced_lines(lines: Sequence[str]) -> list[bool]:
    """Return, for each line, whether a fence line or fenced content holds it."""
    fenced: list[bool] = []
    fence: str | None = None
    for line in lines:
        if fence is not None:
            fenced.append(True)
            if closes_fence(line, fence):
                fence = None
            continue
        opening = FENCE_OPEN.match(line)
        if opening is not None:
            fence = opening[1]
        fenced.append(opening is not None)
    return fenced


def convert_text(context: FileContext, text: str) -> tuple[str, list[Finding]]:
    converted: list[str] = []
    findings: list[Finding] = []
    lines = text.split("\n")
    fenced = fenced_lines(lines)
    evidence_labels = frozenset(
        use["label"].casefold()
        for line, inside_fence in zip(lines, fenced, strict=True)
        if not inside_fence
        for use in EVIDENCE_REFERENCE_USE.finditer(line)
    )
    for number, (line, inside_fence) in enumerate(
        zip(lines, fenced, strict=True), start=1
    ):
        if inside_fence:
            converted.append(line)
            continue
        converter = LineConverter(context, number, evidence_labels)
        converted.append(converter.convert(line))
        findings.extend(converter.findings)
    return "\n".join(converted), findings


def markdown_files(root: Path, paths: Sequence[str]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        base = root / path
        if base.is_file():
            files.add(base)
            continue
        for directory, _, names in os.walk(base):
            files.update(
                Path(directory) / name
                for name in names
                if name.endswith(MARKDOWN_SUFFIX)
            )
    return sorted(files, key=lambda file: file.relative_to(root).as_posix())


def convert_tree(
    root: Path, paths: Sequence[str] = (SPEC_TREE_DIRECTORY,)
) -> ConversionResult:
    rewritten: list[str] = []
    findings: list[Finding] = []
    for file in markdown_files(root, paths):
        name = file.relative_to(root).as_posix()
        context = FileContext(root, file, locate_node_directory(root, file))
        try:
            original = file.read_bytes().decode("utf-8")
            converted, file_findings = convert_text(context, original)
            findings.extend(file_findings)
            if converted != original:
                file.write_bytes(converted.encode("utf-8"))
                rewritten.append(name)
        except (OSError, UnicodeError) as cause:
            raise ConversionError(name, cause, tuple(rewritten)) from cause
    return ConversionResult(tuple(rewritten), tuple(findings))


def render_result(result: ConversionResult) -> str:
    document = {
        ResultField.SCHEMA_VERSION: SCHEMA_VERSION,
        ResultField.REWRITTEN: list(result.rewritten),
        ResultField.UNCONVERTIBLE: [
            {
                ResultField.FILE: finding.file,
                ResultField.LINE: finding.line,
                ResultField.FORM: finding.form,
                ResultField.TARGET: finding.target,
            }
            for finding in result.unconvertible
        ],
    }
    return json.dumps(document, indent=2, sort_keys=True)


def path_error(root: Path, path: str) -> str | None:
    spec_tree = (root / SPEC_TREE_DIRECTORY).resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(spec_tree):
        return f"error: {path} lies outside {spec_tree}"
    if not target.exists():
        return f"error: {path} does not exist beneath {spec_tree}"
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("root", type=Path, help="product root that holds spx/")
    parser.add_argument(
        "paths",
        nargs="*",
        default=[SPEC_TREE_DIRECTORY],
        help="files or directories beneath ROOT/spx to convert",
    )
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as request:
        return EXIT_OK if request.code in (0, None) else EXIT_ERROR
    root = arguments.root.resolve()
    if not (root / SPEC_TREE_DIRECTORY).is_dir():
        print(
            f"error: {root} holds no {SPEC_TREE_DIRECTORY}/ directory", file=sys.stderr
        )
        return EXIT_ERROR
    for path in arguments.paths:
        message = path_error(root, path)
        if message is not None:
            print(message, file=sys.stderr)
            return EXIT_ERROR
    try:
        result = convert_tree(root, arguments.paths)
    except ConversionError as failure:
        print(
            f"error: cannot convert {failure.file}: {failure.cause}; make the file "
            f"readable UTF-8 Markdown, then run the conversion again. "
            f"Files already rewritten stay converted: "
            f"{', '.join(failure.rewritten) or 'none'}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    print(render_result(result))
    return EXIT_UNCONVERTIBLE if result.unconvertible else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
