"""Validate that a skill's tool grants name only paths inside its own directory.

A grant such as ``Bash(python3 "${CLAUDE_SKILL_DIR}/../other-skill/scripts/x.py":*)``
reaches a sibling skill's script by walking out of the granting skill's own
directory.  That spelling puts the provider's directory name and internal script
layout into a permission string, where no import graph, type checker, or test
can follow it.  Renaming the provider or moving its ``scripts/`` directory then
breaks the grant silently: the pattern stops matching and the call degrades to a
permission prompt rather than failing.

The portable shape owns the coupling in Python instead.  Logic two skills share
is owned by one provider skill, and each consumer keeps its own ``scripts/``
entrypoint that loads the provider's module by a path resolved relative to
``__file__``.  A moved module then raises at load, and the consumer's grant names
only its own entrypoint, so the grant stays stable while the shared surface
evolves.  It also settles the reach without depending on whether an invoked
skill's grants remain in force while it is active — a property neither agent
harness states and both are free to change.

A reference escapes when its path resolves above the skill directory, however it
is spelled: ``${VAR}/..`` and ``${VAR}/scripts/../../sibling`` both leave, while
``${VAR}/scripts/../scripts`` returns to itself and stays.  Containment is
decided by walking the segments, never by matching one spelling.

Usage::

    uv run python -m outcomeeng.validation.grant_locality [SKILL.md ...]

Exit codes:
    0 - No skill among the arguments grants a path outside its own directory
    1 - One or more skills grant a path outside their own directory
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.contracts import SKILL_FILENAME

# The frontmatter field carrying a skill's tool grants.
ALLOWED_TOOLS_FIELD: Final = "allowed-tools"

# The skill-directory variable in each agent target's spelling.  The build
# renders one authored token into both, so a rule over shipped frontmatter reads
# whichever spelling that target's tree carries.
SKILL_DIR_VARIABLES: Final = ("CLAUDE_SKILL_DIR", "SKILL_DIR")

# Any skill-directory reference and the path trailing it.  The variable's own
# name is matched with the alternation rather than a suffix match so
# ``${SKILL_DIR}`` does not also match inside ``${CLAUDE_SKILL_DIR}`` and report
# one violation twice.  Containment is decided from the trailing path, not from
# this pattern, so every spelling reaches the same walk.
#
# The path runs to the grant's own delimiter rather than stopping at a quote,
# because the shell concatenates adjacent quoted and unquoted pieces: the
# command line ``"${VAR}"/../sibling/x.py`` reaches the same file as
# ``"${VAR}/../sibling/x.py"``.  Stopping at the quote read the first spelling
# as an empty path and passed it.  Quotes are stripped before the walk, so both
# spellings reach the identical segment sequence.
# The braces are optional because the shell reads ``$VAR/x`` and ``${VAR}/x``
# identically; a rule matching only the braced spelling passes the other one.
# The leading ``$`` anchors each attempt, so one reference yields one match
# whatever order the alternation carries.
_SKILL_DIR_REFERENCE: Final[re.Pattern[str]] = re.compile(
    r"\$(?:\{(?:"
    + "|".join(SKILL_DIR_VARIABLES)
    + r")\}|(?:"
    + "|".join(SKILL_DIR_VARIABLES)
    + r")\b)(?P<path>[^\s:),]*)"
)

# The quote characters a shell concatenates across.  Removing them turns every
# spelling of one path into the same segment sequence.
_SHELL_QUOTES: Final = str.maketrans("", "", "\"'")

# The ``allowed-tools`` declaration, matched at the start of a line so a body
# mention of the field name is not read as a grant declaration.
_ALLOWED_TOOLS_LINE: Final[re.Pattern[str]] = re.compile(
    r"^" + re.escape(ALLOWED_TOOLS_FIELD) + r"\s*:(?P<value>.*)$"
)


def _escapes(path: str) -> bool:
    """Whether ``path`` resolves above the directory the variable named.

    Walks the segments rather than matching a spelling: each ordinary segment
    descends and each ``..`` ascends, so a reference escapes exactly when the
    walk ever rises above its starting directory. ``scripts/../scripts`` returns
    to itself and stays; ``scripts/../../sibling`` does not.

    Shell quotes are removed first, so a path the shell assembles from adjacent
    quoted and unquoted pieces walks as the single path it becomes.
    """
    depth = 0
    for segment in path.translate(_SHELL_QUOTES).split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            depth -= 1
            if depth < 0:
                return True
        else:
            depth += 1
    return False


def _declaration_values(text: str) -> list[tuple[int, str]]:
    """Return ``(line, value)`` for every ``allowed-tools`` declaration.

    A declaration's value is its same-line scalar plus every following indented
    line, which is what carries a YAML list form where each grant sits on its
    own ``- `` line. Continuation stops at the first line that is neither blank
    nor indented, so the next frontmatter key ends the value.
    """
    values: list[tuple[int, str]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        declaration = _ALLOWED_TOOLS_LINE.match(line)
        if declaration is None:
            continue
        collected = [declaration.group("value")]
        for continuation in lines[index + 1 :]:
            if continuation.strip() and not continuation[:1].isspace():
                break
            collected.append(continuation)
        values.append((index + 1, "\n".join(collected)))
    return values


@dataclass(frozen=True)
class Violation:
    """One grant naming a path outside the granting skill's own directory."""

    path: Path
    line: int
    reference: str


def find_escaping_grants(text: str) -> list[tuple[int, str]]:
    """Return ``(line, reference)`` for each grant that escapes the skill directory."""
    violations: list[tuple[int, str]] = []
    for lineno, value in _declaration_values(text):
        violations.extend(
            (lineno, match.group(0))
            for match in _SKILL_DIR_REFERENCE.finditer(value)
            if _escapes(match.group("path"))
        )
    return violations


def scan_file(path: Path) -> list[Violation]:
    """Return one violation per escaping grant in ``path``.

    The caller supplies the path: the gate step enumerates the shipped skill
    files, and a test supplies its own temporary file.  The read is the whole
    contract — this module opens nothing else and writes nothing.
    """
    text = path.read_text(encoding="utf-8")  # NOSONAR S8707 - read-only
    return [
        Violation(path=path, line=lineno, reference=reference)
        for lineno, reference in find_escaping_grants(text)
    ]


def scan_paths(paths: Iterable[str | Path]) -> list[Violation]:
    """Scan each existing ``SKILL.md`` among ``paths`` for escaping grants."""
    violations: list[Violation] = []
    for raw in paths:
        path = Path(raw)
        if path.name != SKILL_FILENAME or not path.is_file():
            continue
        violations.extend(scan_file(path))
    return violations


def format_violation(violation: Violation) -> str:
    """Return the stable diagnostic for one escaping grant."""
    return (
        f"{violation.path}:{violation.line}: "
        f"grant {violation.reference!r} names a path outside the skill's own "
        f"directory, encoding a sibling's name and layout in a permission; "
        f"give this skill its own scripts/ entrypoint and load the shared "
        f"module from it by a path relative to __file__"
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    violations = scan_paths(args)
    for violation in violations:
        print(format_violation(violation))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
