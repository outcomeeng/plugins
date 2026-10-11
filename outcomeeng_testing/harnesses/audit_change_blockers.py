"""Replay harness for the audit-change runner's ``read-blockers`` operation.

Backs the ``[test]`` evidence that the operation reads a Change's native
blockers one page of a stated size per issue, returns each blocker's canonical
identity and whether it is open, reads at most a stated number of issues when it
walks the blockers' own blockers, and returns a blocked result naming the bound
when a read fills it. The runner reaches the store only through its injected
command seam, so the harness passes the runner a recording collaborator that
answers each blockers call with the page its replayed blocker graph holds for
the issue the call names.

A page entry is the inert fixture
``outcomeeng_testing/fixtures/audit_change_blockers/blocker-entry.json``, an
invented capture of the shape the store returns for a blocking issue, with the
issue number, state, and repository filled per entry. Graphs are built by
construction: a chain gives each issue one open blocker, a ring closes a chain on
its first issue, and a wide graph gives the first issue a stated number of
blockers. The expected identities follow from the construction, so no expected
value comes from the runner.

The page size and issue count the test compares against come from the spec
assertion text, read here by path, because the assertion is the rule under test.
The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng_testing.harnesses.audit_change_authority import (
    CHANGES_SPEC,
    REPLAYED_ISSUE,
)
from outcomeeng_testing.harnesses.audit_change_run import REPO_ROOT, load_runner

_ENTRY_FIXTURE: Final = (
    REPO_ROOT
    / "outcomeeng_testing"
    / "fixtures"
    / "audit_change_blockers"
    / "blocker-entry.json"
)
_PAGE_PHRASE: Final = re.compile(
    r"native blockers one page of (\d+) per issue.*?reads at most (\d+) issues"
)
_CALL_PATH: Final = re.compile(
    r"repos/[^/]+/[^/]+/issues/(\d+)/dependencies/blocked_by"
)
_PER_PAGE_PREFIX: Final = "per_page="
_REPOSITORY_URL_MARKER: Final = "/repos/"
_OPEN_STATE: Final = "open"
_CLOSED_STATE: Final = "closed"
_FIRST_ISSUE: Final = 1

#: The issue count of the ring and of the chain a read without a walk meets.
RING_LENGTH: Final = 3
UNWALKED_CHAIN_LENGTH: Final = 3

_runner = load_runner()
_OWNER_REPOSITORY, _, _ = REPLAYED_ISSUE.partition("#")

#: Each issue number mapped to the ``(blocker number, blocker is open)`` pairs the
#: store lists as blocking it.
BlockerGraph = Mapping[int, Sequence[tuple[int, bool]]]


@dataclass(frozen=True)
class BlockerBound:
    """The page size and issue count the spec assertion states."""

    page_size: int
    max_issues: int


@dataclass(frozen=True)
class BlockersCall:
    """One blockers read the runner issued to the store."""

    argv: tuple[str, ...]
    issue_number: int
    page_size: int


@dataclass(frozen=True)
class BlockersObservation:
    """What one ``read-blockers`` request returned and what the store was asked."""

    exit_code: int
    result: dict[str, object]
    calls: tuple[BlockersCall, ...]


def spec_blocker_bound() -> BlockerBound:
    """Read the page size and issue count from the blockers assertion."""
    found = _PAGE_PHRASE.search(CHANGES_SPEC.read_text(encoding="utf-8"))
    if found is None:
        raise RuntimeError(f"no blockers read bound stated in {CHANGES_SPEC}")
    return BlockerBound(page_size=int(found.group(1)), max_issues=int(found.group(2)))


def identity(number: int) -> str:
    """The canonical identity of replayed issue ``number``."""
    return f"{_OWNER_REPOSITORY}#{number}"


def chain(length: int) -> BlockerGraph:
    """Issue 1 blocked by open issue 2, and so on through ``length`` issues."""
    return {
        number: [(number + 1, True)] if number < length else []
        for number in range(_FIRST_ISSUE, length + 1)
    }


def ring(length: int) -> BlockerGraph:
    """A chain of ``length`` issues whose last issue is blocked by the first."""
    return {**chain(length), length: [(_FIRST_ISSUE, True)]}


def closed_blocker() -> BlockerGraph:
    """Issue 1 blocked by a closed issue 2, which is itself blocked by issue 3."""
    return {_FIRST_ISSUE: [(2, False)], 2: [(3, True)]}


def wide(count: int) -> BlockerGraph:
    """Issue 1 blocked by ``count`` issues, alternately open and closed."""
    return {_FIRST_ISSUE: [(number, number % 2 == 0) for number in range(2, count + 2)]}


def _entry(number: int, is_open: bool) -> dict[str, object]:
    template = json.loads(_ENTRY_FIXTURE.read_text(encoding="utf-8"))
    prefix = template["repository_url"].split(_REPOSITORY_URL_MARKER, 1)[0]
    return {
        **template,
        "number": number,
        "state": _OPEN_STATE if is_open else _CLOSED_STATE,
        "repository_url": f"{prefix}{_REPOSITORY_URL_MARKER}{_OWNER_REPOSITORY}",
    }


class _StoreReplay:
    """Answer each blockers call with the page the graph holds for its issue."""

    def __init__(self, graph: BlockerGraph) -> None:
        self._graph = graph
        self.calls: list[BlockersCall] = []

    def __call__(
        self, argv: Sequence[str], /, *, cwd: Path, stdin: str | None
    ) -> object:
        del cwd, stdin
        number = next(
            int(found.group(1))
            for arg in argv
            if (found := _CALL_PATH.fullmatch(arg)) is not None
        )
        page_size = next(
            int(arg.removeprefix(_PER_PAGE_PREFIX))
            for arg in argv
            if arg.startswith(_PER_PAGE_PREFIX)
        )
        self.calls.append(BlockersCall(tuple(argv), number, page_size))
        page = [_entry(n, is_open) for n, is_open in self._graph.get(number, [])]
        return _runner.CommandResult(0, json.dumps(page), "")


def read_blockers(graph: BlockerGraph, *, walk: bool) -> BlockersObservation:
    """Request ``read-blockers`` for issue 1 of the replayed graph."""
    replay = _StoreReplay(graph)
    request = json.dumps(
        {
            _runner.RequestField.OPERATION: _runner.Operation.READ_BLOCKERS,
            _runner.RequestField.ISSUE: identity(_FIRST_ISSUE),
            _runner.RequestField.WALK: walk,
        }
    )
    code, result = _runner.execute(request, cwd=Path.cwd(), runner=replay)
    return BlockersObservation(
        exit_code=int(code), result=dict(result), calls=tuple(replay.calls)
    )
