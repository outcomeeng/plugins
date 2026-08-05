"""Validate that shipped plugin content names no fixed temporary path.

A skill instructing Claude to write under a fixed temporary path — ``/tmp``,
``/var/tmp``, ``/private/var/tmp``, ``~/tmp`` — produces two defects at once.
Concurrent invocations collide on one name, because nothing in the path varies
per run.  And the path sits outside every directory the consumer's harness
declared for that session, so the write leaves the boundary the operator
approved.

The portable alternatives name no path at all: ``mktemp -d`` and ``mktemp -t``
in shell, ``tempfile.mkdtemp`` and ``TemporaryDirectory`` in Python.  Each
derives a unique directory from the environment's own temporary root, so
neither a fixed literal nor a ``$TMPDIR`` fallback spelling is ever needed in
shipped content.  ``${TMPDIR:-/tmp}`` is therefore a violation rather than a
portable idiom: ``mktemp`` already resolves an unset ``TMPDIR`` correctly, so
spelling the fallback only reintroduces the literal this rule removes.

Scratch-directory provenance is governed by
``spx/13-plugin-and-runtime-conventions.adr.md``; this validator is the
deterministic enforcement of that decision over shipped content.

Usage::

    uv run python -m outcomeeng.validation.scratch_paths [FILE ...]

Exit codes:
    0 - No file among the arguments names a fixed temporary path
    1 - One or more files name a fixed temporary path
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# Absolute temporary roots a consumer's harness never declares for a session.
# ``/private/var/tmp`` and ``/private/tmp`` are the macOS firmlink spellings of
# ``/var/tmp`` and ``/tmp``; a shipped path is fixed under either spelling.
ABSOLUTE_TEMPORARY_ROOTS: Final = (
    "/tmp",
    "/var/tmp",
    "/private/tmp",
    "/private/var/tmp",
)

# Home-relative temporary roots, in the two spellings shipped content uses.
HOME_TEMPORARY_ROOTS: Final = ("~/tmp", "$HOME/tmp", "${HOME}/tmp")

# The unique-per-invocation sources that replace every fixed path above.
PORTABLE_SCRATCH_SOURCES: Final = (
    "mktemp -d",
    "mktemp -t",
    "tempfile.mkdtemp",
    "tempfile.TemporaryDirectory",
    "TemporaryDirectory()",
)

# A fixed temporary path in shipped content.  The leading lookbehind anchors
# each absolute root at a path-segment boundary so a longer path that merely
# ends in the same characters (``/opt/tmp``, ``xyz/tmp``) does not match, while
# a quoted or interpolated occurrence (``"${TMPDIR:-/tmp}"``) does.  The
# trailing boundary keeps ``/tmpfs`` and ``/tmp_build`` out.
_FIXED_TEMPORARY_PATH: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.~$])"
    r"(?:"
    r"/private/var/tmp|/private/tmp|/var/tmp|/tmp"
    r"|~/tmp|\$HOME/tmp|\$\{HOME\}/tmp"
    r")"
    r"(?![\w-])"
    r"[\w./-]*"
)


@dataclass(frozen=True)
class Violation:
    """A single fixed temporary path found on one line of a file."""

    path: Path
    line: int
    reference: str


def find_fixed_temporary_paths(text: str) -> list[tuple[int, str]]:
    """Return ``(line, reference)`` for each fixed temporary path in ``text``."""
    return [
        (lineno, match.group(0))
        for lineno, line in enumerate(text.splitlines(), start=1)
        for match in _FIXED_TEMPORARY_PATH.finditer(line)
    ]


def scan_file(path: Path) -> list[Violation]:
    """Return one violation per fixed temporary path in ``path``."""
    text = path.read_text(encoding="utf-8")
    return [
        Violation(path=path, line=lineno, reference=reference)
        for lineno, reference in find_fixed_temporary_paths(text)
    ]


def scan_paths(paths: Iterable[str | Path]) -> list[Violation]:
    """Scan each existing file in ``paths`` for fixed temporary paths."""
    violations: list[Violation] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue
        violations.extend(scan_file(path))
    return violations


def format_violation(violation: Violation) -> str:
    """Return the stable diagnostic for one fixed temporary path."""
    return (
        f"{violation.path}:{violation.line}: "
        f"fixed temporary path {violation.reference!r} "
        f"collides across concurrent runs and writes outside the session boundary; "
        f"use a unique-per-invocation source such as {PORTABLE_SCRATCH_SOURCES[0]!r}"
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    violations = scan_paths(args)
    for violation in violations:
        print(format_violation(violation))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
