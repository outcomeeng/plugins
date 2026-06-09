"""Validate that shipped plugin content carries no non-portable reference.

A plugin installs into a consumer repository that holds this marketplace's
plugins but none of its internal directories.  A reference in shipped content
under ``src/plugins/`` resolves in a consumer checkout only when it names the
consumer's own spec tree generically or the plugin's own files; a concrete
reference into this marketplace's own files dangles there.

A reference is non-portable when it is either:

* a spec-tree node or decision named by its sibling-local numeric prefix --
  ``spx/`` immediately followed by a digit (``spx/13-...``,
  ``spx/15-validation.enabler/65-gate.enabler``).  A non-numbered ``spx/`` path
  (``spx/EXCLUDE``, ``spx/CLAUDE.md``, ``spx/local/...``, ``spx/sessions/``) and
  a placeholder (``spx/{...}``, ``spx/<...>``) are portable; the numeric prefix
  is what is product-specific, and a consumer numbers its own nodes.
* a repository path segment under ``src/``, ``dist/``, or ``outcomeeng/``
  -- caught even inside an absolute checkout path.

``${CLAUDE_SKILL_DIR}`` and ``${CLAUDE_PLUGIN_ROOT}`` are the portable way to
reach the plugin's own files and are never matched.

Usage::

    uv run python -m outcomeeng.validation.reference_portability [FILE ...]

Exit codes:
    0 - No file among the arguments contains a non-portable reference
    1 - One or more files contain a non-portable reference
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# A non-portable reference into this marketplace's own files.  The leading
# lookbehind anchors each alternative at a path-segment boundary, so a substring
# inside a longer word (``redistribute``) or a dot-prefixed build directory
# (``.dist/``) does not match, while an absolute checkout path
# (``/home/dev/dist/claude/...``) does.
_NONPORTABLE_REFERENCE: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w.-])"
    r"(?:"
    r"spx/\d[\w./-]*"  # numbered spec-tree node or decision
    r"|src/[\w./-]*"  # repository source tree
    r"|dist/[\w./-]*"  # generated runtime tree
    r"|outcomeeng\w*/[\w./-]*"  # marketplace toolchain package
    r")",
)


@dataclass(frozen=True)
class Violation:
    """A single non-portable reference found on one line of a file."""

    path: Path
    line: int
    reference: str


def find_nonportable(text: str) -> list[tuple[int, str]]:
    """Return ``(line, reference)`` for each non-portable reference in ``text``."""
    return [
        (lineno, match.group(0))
        for lineno, line in enumerate(text.splitlines(), start=1)
        for match in _NONPORTABLE_REFERENCE.finditer(line)
    ]


def scan_file(path: Path) -> list[Violation]:
    """Return one violation per non-portable reference in ``path``."""
    text = path.read_text(encoding="utf-8")
    return [
        Violation(path=path, line=lineno, reference=reference)
        for lineno, reference in find_nonportable(text)
    ]


def scan_paths(paths: Iterable[str | Path]) -> list[Violation]:
    """Scan each existing file in ``paths`` for non-portable references."""
    violations: list[Violation] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue
        violations.extend(scan_file(path))
    return violations


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    violations = scan_paths(args)
    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: "
            f"non-portable reference {violation.reference!r} "
            f"does not resolve in a consumer checkout",
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
