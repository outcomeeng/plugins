"""Walk spec-tree markdown for evidence links and validate their targets.

Two evidence mechanisms appear inline in spec assertions: ``[test](path)``
references a pytest collectable; ``[eval](path)`` references an
``eval.toml``. This module collects each kind and validates the targets.

Links inside fenced code blocks and inline code spans are skipped: prose
that documents the link syntax (e.g. ``the [eval](path) form``) is not a
real evidence reference. Both skips follow CommonMark: a fence is a run of
three or more backticks or tildes at the start of a line, closed by a
matching run at the start of a later line (or by the end of the file), and
an inline span opens with a backtick run of any length and closes with a
run of exactly that length — so a double-backtick span can quote a literal
triple backtick without opening a fence.

The ``outcomeeng.validation.eval_links`` module wires the validators into
the validation recipe as its ``eval-links`` step.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng_evals.definition import EVAL_TOML_FILENAME


MARKDOWN_GLOB = "**/*.md"
TEST_FILE_PREFIX = "test_"
# Co-location convention (per the eval-harness spec): a [test] link
# resolves to a file directly inside a ``tests/`` directory; an [eval]
# link resolves to ``eval.toml`` inside an ``evals/{rule}/`` directory.
TESTS_DIRNAME = "tests"
EVALS_DIRNAME = "evals"
# The reason each broken link carries; tests import these rather than
# restating the wording.
REASON_TARGET_MISSING: Final = "target does not exist"
REASON_TARGET_NOT_FILE: Final = "target is not a file"
REASON_EVAL_OUTSIDE_EVALS_DIR: Final = (
    f"target must live in an {EVALS_DIRNAME}/{{rule}}/ directory"
)
REASON_EVAL_NOT_TOML: Final = f"target must be a {EVAL_TOML_FILENAME} file"
REASON_TEST_OUTSIDE_TESTS_DIR: Final = (
    f"target must live directly in a {TESTS_DIRNAME}/ directory"
)
REASON_TEST_NOT_COLLECTABLE: Final = (
    "target must be a pytest collectable "
    f"(filename starts with {TEST_FILE_PREFIX!r} and ends in .py)"
)

_EVAL_LINK_PATTERN = re.compile(r"\[eval\]\(([^)]+)\)")
_TEST_LINK_PATTERN = re.compile(r"\[test\]\(([^)]+)\)")
# A fence opens with three or more backticks or tildes at the start of a
# line and closes with a run of the same character, at least as long as
# the opening run, at the start of a later line; an unterminated fence
# runs to the end of the file.
_FENCED_BLOCK_PATTERN = re.compile(
    r"^[ \t]{0,3}(?:"
    r"(`{3,})[^\n]*\n.*?(?:^[ \t]{0,3}\1`*[ \t]*$|\Z)"
    r"|"
    r"(~{3,})[^\n]*\n.*?(?:^[ \t]{0,3}\2~*[ \t]*$|\Z)"
    r")",
    re.DOTALL | re.MULTILINE,
)
# An inline span opens with a backtick run of any length and closes with a
# run of exactly that length, neither run adjacent to a further backtick.
_INLINE_CODE_PATTERN = re.compile(r"(?<!`)(`+)(?!`)([^\n]*?)(?<!`)\1(?!`)")


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
    """Return broken eval links.

    A link is broken when its resolved target is missing, is not a file,
    does not sit inside an ``evals/{rule}/`` directory, or is not named
    ``eval.toml``.
    """
    broken: list[BrokenEvalLink] = []
    for link in find_eval_links(root):
        if not link.target.exists():
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason=REASON_TARGET_MISSING,
                )
            )
            continue
        if not link.target.is_file():
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason=REASON_TARGET_NOT_FILE,
                )
            )
            continue
        if link.target.parent.parent.name != EVALS_DIRNAME:
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason=REASON_EVAL_OUTSIDE_EVALS_DIR,
                )
            )
            continue
        if link.target.name != EVAL_TOML_FILENAME:
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason=REASON_EVAL_NOT_TOML,
                )
            )
    return broken


def validate_test_links(root: Path) -> list[BrokenTestLink]:
    """Return broken test links.

    A link is broken when its resolved target is missing, is not a file,
    does not sit directly inside a ``tests/`` directory, or does not follow
    pytest's default naming convention (filename begins with ``test_`` and
    ends in ``.py``). This checks the convention, not actual collection —
    custom ``python_files`` settings or ``conftest`` exclusions could still
    affect whether pytest collects the file. Tightened targets (e.g.,
    language-specific test files) keep these naming checks.
    """
    broken: list[BrokenTestLink] = []
    for link in find_test_links(root):
        if not link.target.exists():
            broken.append(
                BrokenTestLink(
                    source=link.source,
                    target=link.target,
                    reason=REASON_TARGET_MISSING,
                )
            )
            continue
        if not link.target.is_file():
            broken.append(
                BrokenTestLink(
                    source=link.source,
                    target=link.target,
                    reason=REASON_TARGET_NOT_FILE,
                )
            )
            continue
        if link.target.parent.name != TESTS_DIRNAME:
            broken.append(
                BrokenTestLink(
                    source=link.source,
                    target=link.target,
                    reason=REASON_TEST_OUTSIDE_TESTS_DIR,
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
                    reason=REASON_TEST_NOT_COLLECTABLE,
                )
            )
    return broken
