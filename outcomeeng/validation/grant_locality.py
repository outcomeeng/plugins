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

Grant locality is governed by ``spx/13-plugin-and-runtime-conventions.adr.md``;
this validator is the deterministic enforcement of that decision over shipped
skill frontmatter.

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

# A skill-directory reference whose first path segment escapes that directory.
# The variable's own name is matched with the alternation rather than a suffix
# match so ``${SKILL_DIR}`` does not also match inside ``${CLAUDE_SKILL_DIR}``
# and report one violation twice.  Only a leading ``..`` escapes: a descent that
# returns to itself (``scripts/../scripts``) still resolves inside the skill and
# is left to review rather than flagged here.
_ESCAPING_GRANT: Final[re.Pattern[str]] = re.compile(
    r"\$\{(?:" + "|".join(SKILL_DIR_VARIABLES) + r")\}/\.\.(?:/[^\"'\s:)]*)?"
)

# The ``allowed-tools`` line, matched at the start of a frontmatter line so a
# body mention of the field name is not read as a grant declaration.
_ALLOWED_TOOLS_LINE: Final[re.Pattern[str]] = re.compile(
    r"^" + re.escape(ALLOWED_TOOLS_FIELD) + r"\s*:(?P<value>.*)$"
)


@dataclass(frozen=True)
class Violation:
    """One grant naming a path outside the granting skill's own directory."""

    path: Path
    line: int
    reference: str


def find_escaping_grants(text: str) -> list[tuple[int, str]]:
    """Return ``(line, reference)`` for each grant that escapes the skill directory."""
    violations: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        declaration = _ALLOWED_TOOLS_LINE.match(line)
        if declaration is None:
            continue
        violations.extend(
            (lineno, match.group(0))
            for match in _ESCAPING_GRANT.finditer(declaration.group("value"))
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
