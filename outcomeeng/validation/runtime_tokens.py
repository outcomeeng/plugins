"""Validate that authored plugin content carries no raw runtime-divergent token.

A tool or command name that a coding agent exposes under a different identifier
per runtime — Claude Code's ``AskUserQuestion`` versus Codex's
``request_user_input`` — must be authored as a registry-backed
``{{! tool('…') !}}`` token or inside the matching target's ``{!% if %!}``
branch. The build renders either form only into a target that provides the name;
a raw literal outside matching target scope ships into an incompatible runtime.

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
it holds only the instruction-block node's authored files, which name the two
instruction filenames as their subject and so cannot consume a build token; every other authored
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
from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from outcomeeng.distribution.build import (
    JINJA_NEUTRAL_BLOCK_ENDINGS,
    RUNTIME_TOKEN_REGISTRY,
    RuntimeTokenKind,
)
from outcomeeng.distribution.contracts import (
    BUILD_BLOCK_DELIMITER_END,
    BUILD_BLOCK_DELIMITER_START,
    BUILD_TARGET_VARIABLE,
    Target,
)

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
_TARGET_VALUES: Final = "|".join(re.escape(target.value) for target in Target)
_BUILD_BLOCK_PATTERN: Final = re.compile(
    re.escape(BUILD_BLOCK_DELIMITER_START)
    + r"\s*(?P<body>.*?)\s*"
    + re.escape(BUILD_BLOCK_DELIMITER_END),
    re.DOTALL,
)
_TARGET_BRANCH_PATTERN: Final = re.compile(
    rf"(?P<keyword>if|elif)\s+{re.escape(BUILD_TARGET_VARIABLE)}\s*==\s*"
    rf"(?P<quote>['\"])(?P<target>{_TARGET_VALUES})(?P=quote)\s*"
)
_JINJA_NEUTRAL_BLOCK_STARTS: Final = {
    ending: kind for kind, ending in JINJA_NEUTRAL_BLOCK_ENDINGS.items()
}
_RUNTIME_TOKEN_REMEDIATION: Final = (
    "must be a registry token or appear only in its matching per-runtime conditional"
)

# Files under src/plugins/ exempt from enforcement. Repo-relative POSIX paths.
# An entry exempts that one file without opting the rest of the tree out, and is
# either a not-yet-converted plugin or shared fragment, or an authored file of the
# instruction-block node, whose subject is the two instruction files named CLAUDE.md and
# AGENTS.md. That node names both literals as data, not as a reference a reader
# resolves to its own harness: the generator's AGENT_HARNESS_INSTRUCTION_FILENAMES must hold
# the literals when it runs from src (its tests) and dist alike, so it cannot
# consume a build token, and its skill and agent describe generating both named
# files. The canonical instruction-block template the generator renders is the same case: it is
# read per output by instruction_block.py (not the build's Jinja), so one template produces
# both instruction files and a build token could not diverge per output — it names the filenames
# as data too. The node is the source of the `file` kind's names, not a consumer.
#
# A second exempt category is a runtime-neutral citation surface. The review-changes
# reviewer prompt and verdict validator name both CLAUDE.md and AGENTS.md as rule
# citation targets and as the repo-under-review's instruction files — for any repo,
# regardless of the reviewer's own runtime, since the repo under review may carry
# either name. That deliberate both-naming is not a runtime-divergent instruction read, but
# the guard's whole-name match would false-positive on it, so review covers it (as for
# the common-word `term` kind).
RUNTIME_TOKEN_IGNORE: Final[frozenset[str]] = frozenset(
    {
        "src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py",
        "src/plugins/spec-tree/skills/update-instruction-block/SKILL.md",
        "src/plugins/spec-tree/agents/instruction-block-updater.md",
        "src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md",
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


@dataclass(frozen=True)
class _ScopeFrame:
    kind: str
    parent_targets: frozenset[str]
    active_targets: frozenset[str]
    matched_targets: frozenset[str]
    target_scoped: bool
    saw_else: bool = False


class _BlockDisposition(StrEnum):
    """How one Jinja block affects target-scope scanning."""

    HANDLED = "handled"
    INVALID = "invalid"
    SCAN = "scan"


@dataclass(frozen=True)
class _TokenScanner:
    """Token matcher with source positions and runtime ownership."""

    text: str
    pattern: re.Pattern[str]
    native_targets: dict[str, frozenset[str]]
    all_targets: frozenset[str]
    line_starts: tuple[int, ...]

    def scan_range(
        self,
        start: int,
        end: int,
        active_targets: frozenset[str],
        *,
        target_scoped: bool,
    ) -> list[tuple[int, str]]:
        matches: list[tuple[int, str]] = []
        for match in self.pattern.finditer(self.text, start, end):
            token = match.group(0)
            if target_scoped and active_targets.issubset(self.native_targets[token]):
                continue
            matches.append((bisect_right(self.line_starts, match.start()) + 1, token))
        return matches

    def flat_matches(self) -> list[tuple[int, str]]:
        """Return matches with no target-scope exemptions."""
        return self.scan_range(
            0,
            len(self.text),
            self.all_targets,
            target_scoped=False,
        )


def runtime_name_targets(
    *,
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> dict[str, frozenset[str]]:
    """Return each enforced name's native runtime targets."""
    targets: dict[str, set[str]] = {}
    for kind in registry.values():
        if not kind.lint_enforced:
            continue
        for runtime_names in kind.names.values():
            for runtime, name in runtime_names.items():
                targets.setdefault(name, set()).add(runtime)
    return {name: frozenset(runtimes) for name, runtimes in targets.items()}


def _open_if_frame(
    frames: list[_ScopeFrame],
    active_targets: frozenset[str],
    target_scoped: bool,
    target_branch: re.Match[str] | None,
) -> _BlockDisposition:
    branch_targets = (
        frozenset({target_branch.group("target")})
        if target_branch is not None
        else frozenset()
    )
    frames.append(
        _ScopeFrame(
            kind="if",
            parent_targets=active_targets,
            active_targets=(
                active_targets & branch_targets if branch_targets else active_targets
            ),
            matched_targets=branch_targets,
            target_scoped=True if branch_targets else target_scoped,
        )
    )
    return _BlockDisposition.HANDLED


def _update_elif_frame(
    frames: list[_ScopeFrame],
    target_branch: re.Match[str] | None,
) -> _BlockDisposition:
    if not frames or frames[-1].kind != "if" or frames[-1].saw_else:
        return _BlockDisposition.INVALID
    frame = frames[-1]
    if target_branch is None:
        if frame.target_scoped:
            return _BlockDisposition.INVALID
        frames[-1] = _ScopeFrame(
            kind=frame.kind,
            parent_targets=frame.parent_targets,
            active_targets=frame.parent_targets,
            matched_targets=frame.matched_targets,
            target_scoped=False,
        )
        return _BlockDisposition.HANDLED
    branch_targets = frozenset({target_branch.group("target")})
    available_targets = frame.parent_targets - frame.matched_targets
    frames[-1] = _ScopeFrame(
        kind=frame.kind,
        parent_targets=frame.parent_targets,
        active_targets=available_targets & branch_targets,
        matched_targets=frame.matched_targets | branch_targets,
        target_scoped=True,
    )
    return _BlockDisposition.HANDLED


def _update_else_frame(frames: list[_ScopeFrame]) -> _BlockDisposition:
    if not frames or frames[-1].kind not in {"for", "if"} or frames[-1].saw_else:
        return _BlockDisposition.INVALID
    frame = frames[-1]
    active_targets = frame.parent_targets
    if frame.kind == "if" and frame.target_scoped:
        active_targets -= frame.matched_targets
    frames[-1] = _ScopeFrame(
        kind=frame.kind,
        parent_targets=frame.parent_targets,
        active_targets=active_targets,
        matched_targets=frame.matched_targets,
        target_scoped=frame.target_scoped,
        saw_else=True,
    )
    return _BlockDisposition.HANDLED


def _close_scope_frame(
    frames: list[_ScopeFrame], expected_kind: str
) -> _BlockDisposition:
    if not frames or frames[-1].kind != expected_kind:
        return _BlockDisposition.INVALID
    frames.pop()
    return _BlockDisposition.HANDLED


def _open_neutral_frame(
    frames: list[_ScopeFrame],
    keyword: str,
    active_targets: frozenset[str],
    target_scoped: bool,
) -> _BlockDisposition:
    frames.append(
        _ScopeFrame(
            kind=keyword,
            parent_targets=active_targets,
            active_targets=active_targets,
            matched_targets=frozenset(),
            target_scoped=target_scoped,
        )
    )
    return _BlockDisposition.HANDLED


def _apply_scope_block(
    frames: list[_ScopeFrame],
    body: str,
    active_targets: frozenset[str],
    target_scoped: bool,
) -> _BlockDisposition:
    keyword = body.partition(" ")[0]
    target_branch = _TARGET_BRANCH_PATTERN.fullmatch(body)
    if keyword == "if":
        return _open_if_frame(frames, active_targets, target_scoped, target_branch)
    if keyword == "elif":
        return _update_elif_frame(frames, target_branch)
    if keyword == "else":
        return _update_else_frame(frames)
    if keyword == "endif":
        return _close_scope_frame(frames, "if")
    if keyword in JINJA_NEUTRAL_BLOCK_ENDINGS:
        return _open_neutral_frame(
            frames,
            keyword,
            active_targets,
            target_scoped,
        )
    expected_kind = _JINJA_NEUTRAL_BLOCK_STARTS.get(keyword)
    if expected_kind is not None:
        return _close_scope_frame(frames, expected_kind)
    return _BlockDisposition.SCAN


def find_raw_tokens(
    text: str,
    *,
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> list[tuple[int, str]]:
    """Return raw names outside their matching per-runtime conditional."""
    names = forbidden_names(registry=registry)
    scanner = _TokenScanner(
        text=text,
        pattern=(
            _RAW_RUNTIME_TOKEN
            if registry is RUNTIME_TOKEN_REGISTRY
            else compile_forbidden_pattern(names)
        ),
        native_targets=runtime_name_targets(registry=registry),
        all_targets=frozenset(target.value for target in Target),
        line_starts=tuple(
            index + 1 for index, character in enumerate(text) if character == "\n"
        ),
    )
    violations: list[tuple[int, str]] = []
    frames: list[_ScopeFrame] = []
    cursor = 0
    for block in _BUILD_BLOCK_PATTERN.finditer(text):
        active_targets = frames[-1].active_targets if frames else scanner.all_targets
        target_scoped = frames[-1].target_scoped if frames else False
        violations.extend(
            scanner.scan_range(
                cursor,
                block.start(),
                active_targets,
                target_scoped=target_scoped,
            )
        )
        body = block.group("body").strip()
        keyword = body.partition(" ")[0]
        if frames and frames[-1].kind == "raw" and keyword != "endraw":
            disposition = _BlockDisposition.SCAN
        else:
            disposition = _apply_scope_block(
                frames,
                body,
                active_targets,
                target_scoped,
            )
        if disposition is _BlockDisposition.INVALID:
            return scanner.flat_matches()
        if disposition is _BlockDisposition.SCAN:
            violations.extend(
                scanner.scan_range(
                    block.start(),
                    block.end(),
                    active_targets,
                    target_scoped=target_scoped,
                )
            )
        cursor = block.end()

    if frames:
        return scanner.flat_matches()
    violations.extend(
        scanner.scan_range(
            cursor,
            len(text),
            scanner.all_targets,
            target_scoped=False,
        )
    )
    return violations


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
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> list[Violation]:
    """Return one violation per raw runtime token in ``path``, unless ignored."""
    if is_ignored(path, ignore=ignore, repo_root=repo_root):
        return []
    text = path.read_text(encoding="utf-8")
    return [
        Violation(path=path, line=lineno, token=token)
        for lineno, token in find_raw_tokens(text, registry=registry)
    ]


def scan_paths(
    paths: Iterable[str | Path],
    *,
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    repo_root: Path = _REPO_ROOT,
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
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
        violations.extend(
            scan_file(
                path,
                ignore=ignore,
                repo_root=repo_root,
                registry=registry,
            )
        )
    return violations


def main(
    argv: list[str] | None = None,
    *,
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    repo_root: Path = _REPO_ROOT,
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> int:
    args = argv if argv is not None else sys.argv[1:]
    violations = scan_paths(
        args,
        ignore=ignore,
        repo_root=repo_root,
        registry=registry,
    )
    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: "
            f"raw runtime token {violation.token!r} "
            f"{_RUNTIME_TOKEN_REMEDIATION}",
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
