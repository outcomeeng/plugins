"""Validate that no SKILL.md contains a loader-executable injection fence token.

The Claude Code skill loader treats a fenced block whose info string begins with
``!`` as an inline command and executes it when the skill loads.  A SKILL.md that
holds that token — even inside documentation — crashes skill registration.  This
validator scans SKILL.md files for the token and fails when one is present.

Usage::

    uv run python -m outcomeeng.validation.skill_injection_safety [SKILL.md ...]

Exit codes:
    0 - No SKILL.md among the arguments contains the token
    1 - One or more SKILL.md files contain the token
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# The skill loader executes a fenced block whose info string begins with "!".
# The token is the three-backtick fence immediately followed by "!".  Built from
# parts so this module's own source never holds the literal contiguous sequence.
INJECTION_FENCE_TOKEN: Final[str] = "`" * 3 + "!"

SKILL_FILENAME: Final[str] = "SKILL.md"


@dataclass(frozen=True)
class Violation:
    """A single line of a SKILL.md that contains the injection token."""

    path: Path
    line: int


def scan_file(path: Path) -> list[Violation]:
    """Return one violation per line of ``path`` that contains the token."""
    text = path.read_text(encoding="utf-8")
    return [
        Violation(path=path, line=lineno)
        for lineno, line in enumerate(text.splitlines(), start=1)
        if INJECTION_FENCE_TOKEN in line
    ]


def scan_paths(paths: Iterable[str | Path]) -> list[Violation]:
    """Scan each ``SKILL.md`` in ``paths``; non-``SKILL.md`` paths are skipped."""
    violations: list[Violation] = []
    for raw in paths:
        path = Path(raw)
        if path.name.lower() != SKILL_FILENAME.lower():
            continue
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
            f"SKILL.md contains a loader-executable command-injection fence token",
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
