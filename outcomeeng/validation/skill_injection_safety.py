"""Validate that no SKILL.md carries a loader-executable injection that breaks or leaks.

The Claude Code skill loader executes two forms of command injection when a skill
loads.  A fenced block whose info string begins with ``!`` runs as a command; a
SKILL.md that holds that token — even inside documentation — crashes skill
registration.  An inline span that opens with ``!`` and a backtick runs its
command and replaces the span with the output; a command that reads another
skill's content inlines that content on every load, where build-time fan-out
supplies shared content instead.  This validator scans SKILL.md files for the
fence token and for an inline injection whose command reads sister-skill content,
and fails when either is present.

Usage::

    uv run python -m outcomeeng.validation.skill_injection_safety [SKILL.md ...]

Exit codes:
    0 - No SKILL.md among the arguments contains either injection
    1 - One or more SKILL.md files contain one
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

# The skill loader executes a fenced block whose info string begins with "!".
# The token is the three-backtick fence immediately followed by "!".  Built from
# parts so this module's own source never holds the literal contiguous sequence.
INJECTION_FENCE_TOKEN: Final[str] = "`" * 3 + "!"
# The inline form of the same injection: the command between these markers runs
# when the skill loads, and its output replaces the span.
INLINE_INJECTION_START: Final[str] = "!`"
INLINE_INJECTION_END: Final[str] = "`"
INLINE_INJECTION_PATTERN: Final = re.compile(
    rf"(?<!`){re.escape(INLINE_INJECTION_START)}"
    rf"(?P<command>[^`\r\n]*)"
    rf"{re.escape(INLINE_INJECTION_END)}"
)
# A command reads sister-skill content when it climbs out of its own skill
# directory or names a skill definition file.
PARENT_DIRECTORY_SEGMENT: Final[str] = "../"

SKILL_FILENAME: Final[str] = "SKILL.md"


class ViolationKind(StrEnum):
    """What a violating line carries; the value is the reported message."""

    INJECTION_FENCE = (
        "SKILL.md contains a loader-executable command-injection fence token"
    )
    SISTER_SKILL_INJECTION = (
        "SKILL.md contains an execution-time injection that reads sister-skill content"
    )


@dataclass(frozen=True)
class Violation:
    """A single line of a SKILL.md that carries a forbidden injection."""

    path: Path
    line: int
    kind: ViolationKind


def inline_injection_commands(text: str) -> tuple[str, ...]:
    """Return the commands the inline injection syntax embeds in ``text``."""
    return tuple(
        match.group("command") for match in INLINE_INJECTION_PATTERN.finditer(text)
    )


def reads_sister_skill_content(command: str) -> bool:
    """Return whether ``command`` reads content outside its own skill directory."""
    return PARENT_DIRECTORY_SEGMENT in command or SKILL_FILENAME in command


def _line_kinds(line: str) -> list[ViolationKind]:
    kinds: list[ViolationKind] = []
    if INJECTION_FENCE_TOKEN in line:
        kinds.append(ViolationKind.INJECTION_FENCE)
    if any(reads_sister_skill_content(c) for c in inline_injection_commands(line)):
        kinds.append(ViolationKind.SISTER_SKILL_INJECTION)
    return kinds


def scan_file(path: Path) -> list[Violation]:
    """Return one violation per forbidden injection kind on each line of ``path``."""
    text = path.read_text(encoding="utf-8")
    return [
        Violation(path=path, line=lineno, kind=kind)
        for lineno, line in enumerate(text.splitlines(), start=1)
        for kind in _line_kinds(line)
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
        print(f"{violation.path}:{violation.line}: {violation.kind.value}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
