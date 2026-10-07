"""Replay harness for the audit-change runner's ``read-authority`` operation.

Backs the ``[test]`` evidence that the operation reads a Change's field-change
events and comments within a page bound and blocks when a read fills it. The
runner reaches the store only through its injected command seam, so the harness
passes the runner a recording collaborator that answers each ``gh api graphql``
call with a page the store returned when that page was recorded. Every
recorded page is an inert fixture file under
``outcomeeng_testing/fixtures/audit_change_authority``: a final page ends its
connection, and a "more" page reports a further page, which is what the store
returns once a connection holds more entries than one page.

The collaborator exposes the calls it received and the harness exposes what the
recorded pages hold; every predicate belongs to the linked test. The page bound
the test compares against comes from the spec assertion text, read here by
path, because the assertion is the rule under test.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from outcomeeng_testing.harnesses.audit_change_run import REPO_ROOT, load_runner

_CHANGES_NODE: Final = (
    REPO_ROOT / "spx" / "31-outcomeeng.enabler" / "32-changes.enabler"
)
CHANGES_SPEC: Final = _CHANGES_NODE / "changes.md"
_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "audit_change_authority"
)

#: The Change the recorded pages were read from.
RECORDED_ISSUE: Final = "outcomeeng/changes#333"

_BOUND_PHRASE: Final = re.compile(
    r"`read-authority` operation reads .*? at (\d+) per page and at most (\d+) pages"
)
_QUERY_ARGUMENT_PREFIX: Final = "query="
_AFTER_ARGUMENT_PREFIX: Final = "after="

_runner = load_runner()
AuthorityRead = _runner.AuthorityRead
_CONNECTION_ROUTES: Final = (
    ("timelineItems", AuthorityRead.EVENTS),
    ("comments(", AuthorityRead.COMMENTS),
)


@dataclass(frozen=True)
class PageBound:
    """The page size and page count the spec assertion states."""

    page_size: int
    max_pages: int


@dataclass(frozen=True)
class StoreCall:
    """One command the runner issued to the store."""

    argv: tuple[str, ...]
    kind: StrEnum
    query: str
    after: str | None


@dataclass(frozen=True)
class RecordedPage:
    """What one recorded store page holds."""

    node_count: int
    end_cursor: str
    has_next_page: bool


@dataclass(frozen=True)
class AuthorityObservation:
    """What one ``read-authority`` request returned and what the store was asked."""

    exit_code: int
    result: dict[str, object]
    calls: tuple[StoreCall, ...]
    pages: dict[StrEnum, RecordedPage]

    def calls_for(self, kind: StrEnum) -> tuple[StoreCall, ...]:
        return tuple(call for call in self.calls if call.kind == kind)


def spec_page_bound() -> PageBound:
    """Read the page size and page count from the ``read-authority`` assertion."""
    found = _BOUND_PHRASE.search(CHANGES_SPEC.read_text(encoding="utf-8"))
    if found is None:
        raise RuntimeError(f"no read-authority page bound stated in {CHANGES_SPEC}")
    return PageBound(page_size=int(found.group(1)), max_pages=int(found.group(2)))


def _recorded_path(kind: StrEnum, *, more: bool) -> Path:
    return _FIXTURES_DIR / f"{kind}-{'more' if more else 'final'}.json"


def _recorded_page(kind: StrEnum, *, more: bool) -> tuple[str, RecordedPage]:
    recorded = json.loads(_recorded_path(kind, more=more).read_text(encoding="utf-8"))
    connection = next(iter(recorded["data"]["repository"]["issue"].values()))
    info = connection["pageInfo"]
    # The CLI prints an answer as one line of JSON; the fixture file is indented
    # by the repository formatter, so the replay serves it as one line again.
    return json.dumps(recorded), RecordedPage(
        node_count=len(connection["nodes"]),
        end_cursor=info["endCursor"],
        has_next_page=info["hasNextPage"],
    )


class _StoreReplay:
    """Answer each store call with the recorded page for its connection."""

    def __init__(self, answers: dict[StrEnum, str]) -> None:
        self._answers = answers
        self.calls: list[StoreCall] = []

    def __call__(
        self, argv: Sequence[str], /, *, cwd: Path, stdin: str | None
    ) -> object:
        del cwd, stdin
        query = next(
            arg.removeprefix(_QUERY_ARGUMENT_PREFIX)
            for arg in argv
            if arg.startswith(_QUERY_ARGUMENT_PREFIX)
        )
        after = next(
            (
                arg.removeprefix(_AFTER_ARGUMENT_PREFIX)
                for arg in argv
                if arg.startswith(_AFTER_ARGUMENT_PREFIX)
            ),
            None,
        )
        kind = next(route for marker, route in _CONNECTION_ROUTES if marker in query)
        self.calls.append(StoreCall(tuple(argv), kind, query, after))
        return _runner.CommandResult(0, self._answers[kind], "")


def read_authority(*, filled: StrEnum | None) -> AuthorityObservation:
    """Request ``read-authority`` for the recorded Change.

    The store answers every call for the ``filled`` kind with a page that
    reports a further page; every other call receives a final page. ``None``
    gives every connection a final page.
    """
    answers: dict[StrEnum, str] = {}
    pages: dict[StrEnum, RecordedPage] = {}
    for kind in AuthorityRead:
        answers[kind], pages[kind] = _recorded_page(kind, more=kind == filled)
    replay = _StoreReplay(answers)
    request = json.dumps(
        {
            _runner.RequestField.OPERATION: _runner.Operation.READ_AUTHORITY,
            _runner.RequestField.ISSUE: RECORDED_ISSUE,
        }
    )
    code, result = _runner.execute(request, cwd=Path.cwd(), runner=replay)
    return AuthorityObservation(
        exit_code=int(code),
        result=dict(result),
        calls=tuple(replay.calls),
        pages=pages,
    )
