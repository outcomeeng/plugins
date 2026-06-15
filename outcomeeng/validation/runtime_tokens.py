"""Validate that authored plugin content carries no raw runtime-divergent token.

A tool or command name that a coding agent exposes under a different identifier
per runtime — Claude Code's ``AskUserQuestion`` versus Codex's
``request_user_input`` — must be authored as a registry-backed
``{!% %!}``/``{{! tool('…') !}}`` token, never a hardcoded literal.  The build
renders the token into each target's native name; a raw literal in source ships
into a target whose runtime does not provide it.

The forbidden-name set is derived from the build's runtime-token registry
(``outcomeeng.distribution.build.RUNTIME_TOKEN_REGISTRY``) — the single source of
truth for which names diverge per runtime — so this validator never restates a
copied literal list.  A correctly-authored reference carries the capability key
(``tool('ask_user')``), not the name, so it never matches; naming a specific
runtime's tool uses the runtime-explicit token (``tool('ask_user', 'claude')``),
which also renders rather than embeds the literal.

Every file under ``src/plugins/`` is enforced by default.  ``RUNTIME_TOKEN_IGNORE``
names the not-yet-converted files exempt from enforcement; the set shrinks to
empty as each plugin's content is converted to tokens.  A newly added plugin is
enforced without being opted in.

Usage::

    uv run python -m outcomeeng.validation.runtime_tokens [FILE ...]

Exit codes:
    0 - No enforced file among the arguments contains a raw runtime token
    1 - One or more enforced files contain a raw runtime token
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.build import RUNTIME_TOKEN_REGISTRY

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]

# Every runtime-divergent name the build's registry owns, longest first so the
# alternation prefers the most specific match. Word boundaries keep a name from
# matching inside a longer identifier.
_FORBIDDEN_NAMES: Final = tuple(
    sorted(
        {name for entry in RUNTIME_TOKEN_REGISTRY.values() for name in entry.values()},
        key=len,
        reverse=True,
    )
)
_RAW_RUNTIME_TOKEN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w-])(?:"
    + "|".join(re.escape(name) for name in _FORBIDDEN_NAMES)
    + r")(?![\w-])"
)

# Files under src/plugins/ exempt from enforcement until their content is
# converted to runtime-token tokens. Repo-relative POSIX paths. Shrinks to empty
# as each plugin converts; a converted plugin's entries are removed here.
RUNTIME_TOKEN_IGNORE: Final[frozenset[str]] = frozenset(
    {
        "src/plugins/spec-tree/commands/clarify.md",
        "src/plugins/spec-tree/skills/applying/SKILL.md",
        "src/plugins/spec-tree/skills/authoring/SKILL.md",
        "src/plugins/spec-tree/skills/bootstrapping/SKILL.md",
        "src/plugins/spec-tree/skills/github-actions/SKILL.md",
        "src/plugins/spec-tree/skills/github-pr/SKILL.md",
        "src/plugins/spec-tree/skills/handoff/SKILL.md",
        "src/plugins/spec-tree/skills/handoff/workflows/01-anchor-to-nodes.md",
        "src/plugins/spec-tree/skills/handoff/workflows/02-reflect.md",
        "src/plugins/spec-tree/skills/handoff/workflows/03-propose.md",
        "src/plugins/spec-tree/skills/handoff/workflows/04-execute.md",
        "src/plugins/spec-tree/skills/init-worktrees/SKILL.md",
        "src/plugins/spec-tree/skills/interviewing/SKILL.md",
        "src/plugins/spec-tree/skills/interviewing/workflows/direct-interview.md",
        "src/plugins/spec-tree/skills/merge/SKILL.md",
        "src/plugins/spec-tree/skills/pickup/SKILL.md",
        "src/plugins/spec-tree/skills/pickup/workflows/pickup.md",
        "src/plugins/spec-tree/skills/standardizing-merging/SKILL.md",
        "src/plugins/spec-tree/skills/testing/SKILL.md",
        "src/plugins/spec-tree/skills/tracking-tasks/SKILL.md",
        "src/plugins/spec-tree/skills/understanding/references/imperfection-protocol.md",
        "src/plugins/spec-tree/skills/update-spx/SKILL.md",
        "src/plugins/work/skills/sanitizing-powerpoint/SKILL.md",
    }
)


@dataclass(frozen=True)
class Violation:
    """A single raw runtime token found on one line of a file."""

    path: Path
    line: int
    token: str


def find_raw_tokens(text: str) -> list[tuple[int, str]]:
    """Return ``(line, token)`` for each raw runtime token in ``text``."""
    return [
        (lineno, match.group(0))
        for lineno, line in enumerate(text.splitlines(), start=1)
        for match in _RAW_RUNTIME_TOKEN.finditer(line)
    ]


def is_ignored(path: Path) -> bool:
    """Return whether ``path`` is on the not-yet-converted ignore-list."""
    try:
        relative = path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return False
    return relative in RUNTIME_TOKEN_IGNORE


def scan_file(path: Path) -> list[Violation]:
    """Return one violation per raw runtime token in ``path``, unless ignored."""
    if is_ignored(path):
        return []
    text = path.read_text(encoding="utf-8")
    return [
        Violation(path=path, line=lineno, token=token)
        for lineno, token in find_raw_tokens(text)
    ]


def scan_paths(paths: Iterable[str | Path]) -> list[Violation]:
    """Scan each existing file in ``paths`` for raw runtime tokens."""
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
            f"raw runtime token {violation.token!r} "
            f"must be a tool(...) token, not a hardcoded literal",
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
