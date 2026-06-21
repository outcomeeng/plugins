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

Every authored-source file the build renders or inlines — plugin content under
``src/plugins/`` and the shared fragments under ``src/_shared/`` that plugin files
include — is enforced by default.  ``RUNTIME_TOKEN_IGNORE`` is the exemption surface:
it is empty (every authored file is converted, so the marketplace is fully enforced),
and remains the explicit, tracked hatch for any future not-yet-converted file.  A newly
added plugin or shared fragment is enforced without being opted in.

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
# converted to runtime-token tokens. Repo-relative POSIX paths. Empty: every
# authored file is converted, so the marketplace is fully enforced with no
# exemptions. The mechanism remains as the explicit, tracked exemption surface
# for any future not-yet-converted plugin or shared fragment — an entry added
# here exempts that one file without opting the rest of the tree out.
RUNTIME_TOKEN_IGNORE: Final[frozenset[str]] = frozenset()


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


def is_ignored(
    path: Path,
    *,
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    repo_root: Path = _REPO_ROOT,
) -> bool:
    """Return whether ``path`` is on the exemption ignore-list.

    ``ignore`` and ``repo_root`` default to the module-level exemption set and
    repository root; both are injectable so the exemption mechanism is testable
    with a controlled ignore-list and root independent of the live (empty) set.
    """
    try:
        relative = path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return relative in ignore


def scan_file(
    path: Path,
    *,
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    repo_root: Path = _REPO_ROOT,
) -> list[Violation]:
    """Return one violation per raw runtime token in ``path``, unless ignored."""
    if is_ignored(path, ignore=ignore, repo_root=repo_root):
        return []
    text = path.read_text(encoding="utf-8")
    return [
        Violation(path=path, line=lineno, token=token)
        for lineno, token in find_raw_tokens(text)
    ]


def scan_paths(
    paths: Iterable[str | Path],
    *,
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    repo_root: Path = _REPO_ROOT,
) -> list[Violation]:
    """Scan each existing file in ``paths`` for raw runtime tokens.

    ``ignore`` and ``repo_root`` forward to ``scan_file`` so the exemption the
    gate's ``main`` -> ``scan_paths`` -> ``scan_file`` path applies is testable
    with a controlled ignore-list and root, defaulting to the module globals.
    """
    violations: list[Violation] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue
        violations.extend(scan_file(path, ignore=ignore, repo_root=repo_root))
    return violations


def main(
    argv: list[str] | None = None,
    *,
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    repo_root: Path = _REPO_ROOT,
) -> int:
    args = argv if argv is not None else sys.argv[1:]
    violations = scan_paths(args, ignore=ignore, repo_root=repo_root)
    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: "
            f"raw runtime token {violation.token!r} "
            f"must be a tool(...) token, not a hardcoded literal",
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
