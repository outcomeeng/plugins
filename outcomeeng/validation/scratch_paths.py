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

Naming the environment's temporary root by variable is portable, because the
root it resolves to varies by environment.  Naming a child of that root is not:
every invocation in one environment resolves the same root, so ``$TMPDIR`` plus
a fixed segment collides exactly as ``/tmp`` plus that segment does.  Moving a
fixed name from one root to the other relocates the collision rather than
removing it, so a named child of ``$TMPDIR`` is a violation while the bare
variable passes.

One content genuinely has to spell a prohibited path: the rule prohibiting
it.  A line carrying the ``ALLOW_MARKER`` build comment is exempt, and the
build strips that comment before the content ships, so the marker never
reaches a consumer.  The exemption is per line rather than per file, so a
standard states the rule on one line while every other line in the same file
stays enforced.

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
# Each entry is a value this module forbids, never a directory it opens. The
# publicly-writable-directory rule reads them as write targets, which inverts
# the module's purpose, so each is suppressed with that reason rather than
# spelled indirectly — obfuscating a literal to satisfy a scanner would hide
# the prohibition list from the reader it exists for.
ABSOLUTE_TEMPORARY_ROOTS: Final = (
    "/tmp",  # NOSONAR S5443 - forbidden value, never a write target
    "/var/tmp",  # NOSONAR S5443 - forbidden value, never a write target
    "/private/tmp",  # NOSONAR S5443 - forbidden value, never a write target
    "/private/var/tmp",  # NOSONAR S5443 - forbidden value, never a write target
)

# Home-relative temporary roots, in the two spellings shipped content uses.
HOME_TEMPORARY_ROOTS: Final = ("~/tmp", "$HOME/tmp", "${HOME}/tmp")

# The environment's own temporary root, in the two spellings shipped content
# uses.  Naming the root is portable because it resolves per environment; a
# named child of it is not, because every invocation resolves the same child.
ENVIRONMENT_TEMPORARY_ROOTS: Final = ("$TMPDIR", "${TMPDIR}")

# The unique-per-invocation sources that replace every fixed path above.
PORTABLE_SCRATCH_SOURCES: Final = (
    "mktemp -d",
    "mktemp -t",
    "tempfile.mkdtemp",
    "tempfile.TemporaryDirectory",
    "TemporaryDirectory()",
)

# The one content that must spell a prohibited path is the rule prohibiting it:
# a standard naming the tokens an author may not write, and an audit row naming
# what to flag.  Such a line carries this build comment, which the build strips
# before the content ships, so the marker is authoring metadata a consumer never
# sees.  The exemption is per line and never per file, so a marked line states
# the rule while an unmarked line in the same file is still enforced, and every
# use is greppable for review.
ALLOW_MARKER: Final = "{!# scratch-path-allow #!}"

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

# A named child of the environment's temporary root.  The root itself varies by
# environment, so naming it is portable; naming a child of it is not, because
# every invocation in that environment resolves the same root and therefore the
# same child.  ``${TMPDIR}/agent.sock`` collides exactly as ``/tmp/agent.sock``
# does, and moving a fixed name from one root to the other relocates the
# collision rather than removing it.  The bare variable stays passing, so the
# alternation requires a following segment.
_ENVIRONMENT_ROOT_CHILD: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.~$])\$(?:TMPDIR|\{TMPDIR\})/[\w.-]+[\w./-]*"
)


@dataclass(frozen=True)
class Violation:
    """A single fixed temporary path found on one line of a file."""

    path: Path
    line: int
    reference: str


def find_fixed_temporary_paths(text: str) -> list[tuple[int, str]]:
    """Return ``(line, reference)`` for each unexempted fixed temporary path."""
    return [
        (lineno, match.group(0))
        for lineno, line in enumerate(text.splitlines(), start=1)
        if ALLOW_MARKER not in line
        for pattern in (_FIXED_TEMPORARY_PATH, _ENVIRONMENT_ROOT_CHILD)
        for match in pattern.finditer(line)
    ]


def scan_file(path: Path) -> list[Violation]:
    """Return one violation per fixed temporary path in ``path``.

    The caller supplies the path: the gate step enumerates the authored roots,
    and a test supplies its own temporary file. The read is the whole contract
    — this module opens nothing else, writes nothing, and reports only the
    lines it was asked to scan.
    """
    text = path.read_text(encoding="utf-8")  # NOSONAR S8707 - read-only
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
