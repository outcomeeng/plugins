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
it holds only the guide-generation node's authored files, which name the two guide
filenames as their subject and so cannot consume a build token; every other authored
file is converted and enforced, and the hatch remains for any future not-yet-converted
file.  A newly added plugin or shared fragment is enforced without being opted in.

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

from outcomeeng.distribution.build import RUNTIME_TOKEN_REGISTRY, RuntimeTokenKind

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]


def forbidden_names(
    *,
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> tuple[str, ...]:
    """Return the guard-enforced runtime-divergent names, longest first.

    Derived only from the registry's lint-enforced kinds (``tool``, ``field``,
    ``file``); the review-only ``term`` kind is excluded because its common-word
    concept terms would match throughout prose. Longest-first ordering lets the
    scanner's alternation prefer the most specific match. The keyword-only
    ``registry`` seam defaults to the build registry and is injectable so the
    kind-aware derivation is exercised with a controlled registry independent of
    the live names — the same seam shape ``is_ignored``/``scan_file`` use.
    """
    return tuple(
        sorted(
            {
                name
                for kind in registry.values()
                if kind.lint_enforced
                for entry in kind.names.values()
                for name in entry.values()
            },
            key=len,
            reverse=True,
        )
    )


def compile_forbidden_pattern(names: tuple[str, ...]) -> re.Pattern[str]:
    """Compile the scanner pattern matching any guard-enforced ``names`` as a token.

    The ``(?<![\\w-]) … (?![\\w-])`` boundaries keep a name from matching inside a
    longer identifier. With no enforced names — possible now that a kind can be
    enforced yet carry no entries — the pattern matches nothing rather than the
    empty string, which an empty alternation would otherwise match at every
    position.
    """
    if not names:
        return re.compile(r"(?!)")  # never matches
    return re.compile(
        r"(?<![\w-])(?:" + "|".join(re.escape(name) for name in names) + r")(?![\w-])"
    )


# Every guard-enforced runtime-divergent name the build's registry owns.
_FORBIDDEN_NAMES: Final = forbidden_names()
_RAW_RUNTIME_TOKEN: Final[re.Pattern[str]] = compile_forbidden_pattern(_FORBIDDEN_NAMES)

# Files under src/plugins/ exempt from enforcement. Repo-relative POSIX paths.
# An entry exempts that one file without opting the rest of the tree out, and is
# either a not-yet-converted plugin or shared fragment, or an authored file of the
# guide-generation node, whose subject is the two guide files named CLAUDE.md and
# AGENTS.md. That node names both literals as data, not as a reference a reader
# resolves to its own harness: the generator's AGENT_HARNESS_GUIDE_FILENAMES must hold
# the literals when it runs from src (its tests) and dist alike, so it cannot
# consume a build token, and its skill and agent describe generating both named
# files. The canonical guide template the generator renders is the same case: it is
# read per output by update_spx.py (not the build's Jinja), so one template produces
# both guides and a build token could not diverge per output — it names the filenames
# as data too. The node is the source of the `file` kind's names, not a consumer.
#
# A second exempt category is a runtime-neutral citation surface. The review-changes
# reviewer prompt and verdict validator name both CLAUDE.md and AGENTS.md as rule
# citation targets and as the repo-under-review's instruction files — for any repo,
# regardless of the reviewer's own runtime, since the repo under review may carry
# either name. That deliberate both-naming is not a runtime-divergent guide read, but
# the guard's whole-name match would false-positive on it, so review covers it (as for
# the common-word `term` kind).
RUNTIME_TOKEN_IGNORE: Final[frozenset[str]] = frozenset(
    {
        "src/plugins/spec-tree/skills/update-spx/scripts/update_spx.py",
        "src/plugins/spec-tree/skills/update-spx/SKILL.md",
        "src/plugins/spec-tree/agents/spx-updater.md",
        "src/plugins/spec-tree/skills/understand/templates/spx-claude.md",
        "src/plugins/spec-tree/skills/review-changes/references/review-prompt.md",
        "src/plugins/spec-tree/skills/review-changes/scripts/review_result.py",
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


def is_ignored(
    path: Path,
    *,
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    repo_root: Path = _REPO_ROOT,
) -> bool:
    """Return whether ``path`` is on the exemption ignore-list.

    ``ignore`` and ``repo_root`` default to the module-level exemption set and
    repository root; both are injectable so the exemption mechanism is testable
    with a controlled ignore-list and root independent of the live set.
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
