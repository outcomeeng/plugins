"""Walk spec-tree markdown for evidence links and validate their targets.

Two evidence mechanisms appear inline in spec assertions: ``[test](path)``
references a pytest collectable; ``[eval](path)`` references an
``eval.toml``. This module collects each kind and validates the targets.

Links inside fenced code blocks and inline code spans are skipped: prose
that documents the link syntax (e.g. ``the [eval](path) form``) is not a
real evidence reference. The fenced-block pattern matches backtick fences
only — tilde fences (CommonMark also allows ``~~~``) are a deliberate
simplification because no spec markdown in the marketplace uses them.

The ``outcomeeng/scripts/validate_eval_links.py`` script wires the
validators into ``just check``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


EVAL_TOML_FILENAME = "eval.toml"
MARKDOWN_GLOB = "**/*.md"
TEST_FILE_PREFIX = "test_"

_EVAL_LINK_PATTERN = re.compile(r"\[eval\]\(([^)]+)\)")
_TEST_LINK_PATTERN = re.compile(r"\[test\]\(([^)]+)\)")
_FENCED_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_PATTERN = re.compile(r"`[^`\n]*`")


@dataclass(frozen=True)
class EvalLink:
    """An ``[eval](path)`` reference found in a markdown file."""

    source: Path
    target: Path


@dataclass(frozen=True)
class TestLink:
    """A ``[test](path)`` reference found in a markdown file."""

    # The class name happens to start with "Test", which pytest's default
    # collection rule treats as a test class. Suppress collection.
    __test__ = False

    source: Path
    target: Path


@dataclass(frozen=True)
class BrokenEvalLink:
    """An eval link whose target failed validation."""

    source: Path
    target: Path
    reason: str


@dataclass(frozen=True)
class BrokenTestLink:
    """A test link whose target failed validation."""

    source: Path
    target: Path
    reason: str


def find_eval_links(root: Path) -> list[EvalLink]:
    """Walk ROOT for markdown files and collect every ``[eval](path)`` reference.

    Skips matches inside fenced code blocks and inline code spans so prose
    that documents the link syntax does not produce false-positive
    references to nonexistent files.
    """
    links: list[EvalLink] = []
    for md_path in sorted(root.glob(MARKDOWN_GLOB)):
        if not md_path.is_file():
            continue
        text = _strip_code_regions(md_path.read_text(encoding="utf-8"))
        for match in _EVAL_LINK_PATTERN.finditer(text):
            target_rel = match.group(1).strip()
            target = (md_path.parent / target_rel).resolve()
            links.append(EvalLink(source=md_path, target=target))
    return links


def find_test_links(root: Path) -> list[TestLink]:
    """Walk ROOT for markdown files and collect every ``[test](path)`` reference.

    Same code-region skipping rules as ``find_eval_links``.
    """
    links: list[TestLink] = []
    for md_path in sorted(root.glob(MARKDOWN_GLOB)):
        if not md_path.is_file():
            continue
        text = _strip_code_regions(md_path.read_text(encoding="utf-8"))
        for match in _TEST_LINK_PATTERN.finditer(text):
            target_rel = match.group(1).strip()
            target = (md_path.parent / target_rel).resolve()
            links.append(TestLink(source=md_path, target=target))
    return links


def _strip_code_regions(text: str) -> str:
    """Replace fenced code blocks and inline code spans with whitespace.

    Whitespace replacement preserves absolute character offsets — the link
    regex skips the blanked regions because the bracket and parenthesis
    tokens are gone. Newlines inside fenced regions become spaces, so
    per-line positions across multi-line fences shift; offset preservation
    is sufficient for the current caller (no positions are reported).
    """
    text = _FENCED_BLOCK_PATTERN.sub(lambda m: " " * len(m.group(0)), text)
    return _INLINE_CODE_PATTERN.sub(lambda m: " " * len(m.group(0)), text)


def validate_eval_links(root: Path) -> list[BrokenEvalLink]:
    """Return broken eval links: target missing, not a file, or not an eval.toml."""
    broken: list[BrokenEvalLink] = []
    for link in find_eval_links(root):
        if not link.target.exists():
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason="target does not exist",
                )
            )
            continue
        if not link.target.is_file():
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason="target is not a file",
                )
            )
            continue
        if link.target.name != EVAL_TOML_FILENAME:
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason=f"target must be a {EVAL_TOML_FILENAME} file",
                )
            )
    return broken


def validate_test_links(root: Path) -> list[BrokenTestLink]:
    """Return broken test links: target missing, not a file, or not a pytest collectable.

    A pytest collectable lives under a ``tests/`` directory, has a
    ``.py`` suffix, and its filename begins with ``test_``. Tightened
    targets (e.g., language-specific test files) keep these
    naming-convention checks.
    """
    broken: list[BrokenTestLink] = []
    for link in find_test_links(root):
        if not link.target.exists():
            broken.append(
                BrokenTestLink(
                    source=link.source,
                    target=link.target,
                    reason="target does not exist",
                )
            )
            continue
        if not link.target.is_file():
            broken.append(
                BrokenTestLink(
                    source=link.source,
                    target=link.target,
                    reason="target is not a file",
                )
            )
            continue
        if link.target.suffix != ".py" or not link.target.name.startswith(
            TEST_FILE_PREFIX
        ):
            broken.append(
                BrokenTestLink(
                    source=link.source,
                    target=link.target,
                    reason=(
                        "target must be a pytest collectable "
                        f"(filename starts with {TEST_FILE_PREFIX!r} and ends in .py)"
                    ),
                )
            )
    return broken
