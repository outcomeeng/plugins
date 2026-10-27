"""Replay harness for the audit-change runner's native-blocker operations.

Backs the ``[test]`` evidence that the runner reads a Change's native blockers
one page per issue, returns each blocker's canonical identity and whether it is
open, reads at most a stated number of issues when it walks the blockers' own
blockers, and blocks naming the bound when a read fills it. The runner reaches
the store only through its injected command seam, so the harness passes the
runner a recording collaborator that answers each ``gh api graphql`` call with
the ``blockedBy`` connection of the issue the call names, under the
interaction-protocol exception of the test methodology.

Every replayed scenario is an inert fixture file under
``outcomeeng_testing/fixtures/audit_change_blockers``, written with invented
issue numbers and identities because the Change store is private and this
repository is public. A fixture holds ``issues``, the store answer for each
issue identity, and ``declared``, what the fixture's issues state for the case
under test. The page size and the issue bound the test compares against come
from the spec assertion text, read here by path.

The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng_testing.harnesses.audit_change_authority import CHANGES_SPEC
from outcomeeng_testing.harnesses.audit_change_run import REPO_ROOT, load_runner

_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "audit_change_blockers"
)
#: The invented Change identity every request names.
BLOCKERS_ISSUE: Final = "example-org/example-changes#12"
OPEN_AND_CLOSED: Final = _FIXTURES_DIR / "open-and-closed.json"
BLOCKERS_UNFINISHED: Final = _FIXTURES_DIR / "blockers-unfinished.json"
WALK_WITHIN_BOUND: Final = _FIXTURES_DIR / "walk-within-bound.json"
WALK_PAST_BOUND: Final = _FIXTURES_DIR / "walk-past-bound.json"

_PAGE_PHRASE: Final = re.compile(r"native blockers one page of (\d+) per issue")
_ISSUE_PHRASE: Final = re.compile(r"reads at most (\d+) issues when it walks")
_OWNER_PREFIX: Final = "o="
_REPOSITORY_PREFIX: Final = "r="
_NUMBER_PREFIX: Final = "n="
_AFTER_PREFIX: Final = "after="
_QUERY_PREFIX: Final = "query="

_runner = load_runner()


@dataclass(frozen=True)
class BlockersObservation:
    """What one blocker request returned and what the store was asked."""

    exit_code: int
    result: dict[str, object]
    #: The argument vector of every command the runner issued to the store.
    store_calls: tuple[tuple[str, ...], ...]
    #: The issue identity each store call named, in call order.
    issues_asked: tuple[str, ...]

    def queries(self) -> tuple[str, ...]:
        """The query text of every store call."""
        return tuple(
            arg.removeprefix(_QUERY_PREFIX)
            for call in self.store_calls
            for arg in call
            if arg.startswith(_QUERY_PREFIX)
        )

    def cursors(self) -> tuple[str, ...]:
        """Every ``after`` cursor any store call passed."""
        return tuple(
            arg.removeprefix(_AFTER_PREFIX)
            for call in self.store_calls
            for arg in call
            if arg.startswith(_AFTER_PREFIX)
        )


def _spec_text() -> str:
    return CHANGES_SPEC.read_text(encoding="utf-8")


def spec_page_size() -> int:
    """The blocker page size the spec assertion states."""
    found = _PAGE_PHRASE.search(_spec_text())
    if found is None:
        raise RuntimeError(f"no native blocker page size stated in {CHANGES_SPEC}")
    return int(found.group(1))


def spec_issue_bound() -> int:
    """The number of issues a walk may read, as the spec assertion states it."""
    found = _ISSUE_PHRASE.search(_spec_text())
    if found is None:
        raise RuntimeError(f"no blocker walk issue bound stated in {CHANGES_SPEC}")
    return int(found.group(1))


def declared_blockers(fixture: Path) -> list[dict[str, object]]:
    """The blockers a fixture's issue states, keyed by the runner's result fields."""
    return [
        {
            _runner.ResultField.IDENTITY: entry["identity"],
            _runner.ResultField.OPEN: entry["open"],
        }
        for entry in json.loads(fixture.read_text(encoding="utf-8"))["declared"]
    ]


def declared_graph(fixture: Path) -> list[dict[str, object]]:
    """The walked issues a fixture states, each with its blockers, in visit order."""
    return [
        {
            _runner.ResultField.ISSUE: entry["issue"],
            _runner.ResultField.BLOCKERS: [
                {
                    _runner.ResultField.IDENTITY: blocker["identity"],
                    _runner.ResultField.OPEN: blocker["open"],
                }
                for blocker in entry["blockers"]
            ],
        }
        for entry in json.loads(fixture.read_text(encoding="utf-8"))["declared"]
    ]


class _StoreReplay:
    """Answer each store call with the ``blockedBy`` answer of the issue it names."""

    def __init__(self, issues: dict[str, object]) -> None:
        self._issues = issues
        self.calls: list[tuple[str, ...]] = []
        self.asked: list[str] = []

    @staticmethod
    def _value(argv: Sequence[str], prefix: str) -> str:
        return next(arg.removeprefix(prefix) for arg in argv if arg.startswith(prefix))

    def __call__(
        self, argv: Sequence[str], /, *, cwd: Path, stdin: str | None
    ) -> object:
        del cwd, stdin
        identity = (
            f"{self._value(argv, _OWNER_PREFIX)}/"
            f"{self._value(argv, _REPOSITORY_PREFIX)}#"
            f"{self._value(argv, _NUMBER_PREFIX)}"
        )
        self.calls.append(tuple(argv))
        self.asked.append(identity)
        # The CLI prints an answer as one line of JSON.
        return _runner.CommandResult(0, json.dumps(self._issues[identity]), "")


def request_blockers(fixture: Path, operation: object) -> BlockersObservation:
    """Request ``operation`` for the invented Change while the store replays ``fixture``."""
    issues = json.loads(fixture.read_text(encoding="utf-8"))["issues"]
    replay = _StoreReplay(issues)
    request = json.dumps(
        {
            _runner.RequestField.OPERATION: operation,
            _runner.RequestField.ISSUE: BLOCKERS_ISSUE,
        }
    )
    code, result = _runner.execute(request, cwd=Path.cwd(), runner=replay)
    return BlockersObservation(
        exit_code=int(code),
        result=dict(result),
        store_calls=tuple(replay.calls),
        issues_asked=tuple(replay.asked),
    )
