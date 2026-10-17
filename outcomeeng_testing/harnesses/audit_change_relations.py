"""Replay harness for the audit-change runner's ``read-relations`` operation.

Backs the ``[test]`` evidence that the operation decodes a Change's Parent,
returns its absorbers, reads the store's issue pages until the store reports no
further page, and blocks when a read fills a bound. The runner reaches the store
only through its injected command seam, so the harness passes the runner a
recording collaborator that answers each ``gh api graphql`` call with a page in
the shape of the store's answer, under the interaction-protocol exception of the
test methodology.

Every replayed scenario is an inert fixture file under
``outcomeeng_testing/fixtures/audit_change_relations``, written with invented
issue numbers and identities because the Change store is private and this
repository is public. A fixture holds ``pages``, the store answers in reading
order, and ``declared``, what the fixture's issues state for the case under
test. The collaborator answers the first call with the first page and each later
call with the page that follows the page whose ``endCursor`` the call passes as
``after``; once the pages run out it answers with the final page again, which is
what a store that never ends its connection does. The page bound the test
compares against comes from the spec assertion text, read here by path.

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
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "audit_change_relations"
)
#: The invented Change identity every request names; its number is 12.
RELATIONS_ISSUE: Final = "example-org/example-changes#12"
#: The replayed Parent-form scenarios, one fixture per form.
PARENT_FIXTURES: Final = _FIXTURES_DIR / "parent"
CHILDREN_ON_LATER_PAGE: Final = _FIXTURES_DIR / "children-on-later-page.json"
ABSORBERS: Final = _FIXTURES_DIR / "absorbers.json"
UNENDING_ISSUES: Final = _FIXTURES_DIR / "unending-issues.json"
FIELD_VALUES_UNFINISHED: Final = _FIXTURES_DIR / "field-values-unfinished.json"

_PAGE_BOUND_PHRASE: Final = re.compile(
    r"blocked result naming `(\d+ issues per page, \d+ pages)`"
)
_FIELD_BOUND_PHRASE: Final = re.compile(
    r"blocked result naming `(\d+ issue field values per issue)`"
)
_AFTER_ARGUMENT_PREFIX: Final = "after="

_runner = load_runner()


@dataclass(frozen=True)
class RelationsObservation:
    """What one ``read-relations`` request returned and what the store was asked."""

    exit_code: int
    result: dict[str, object]
    #: The argument vector of every command the runner issued to the store.
    store_calls: tuple[tuple[str, ...], ...]
    #: The ``after`` cursor each store call passed, ``None`` for the first page.
    cursors: tuple[str | None, ...]


def parent_fixtures() -> tuple[Path, ...]:
    """Every replayed scenario that states one Parent form."""
    return tuple(sorted(PARENT_FIXTURES.glob("*.json")))


def declared(fixture: Path) -> object:
    """What a fixture's issues state for the case under test."""
    return json.loads(fixture.read_text(encoding="utf-8"))["declared"]


def spec_issue_page_bound() -> str:
    """The issue-page bound the spec assertion says a blocked read names."""
    found = _PAGE_BOUND_PHRASE.search(CHANGES_SPEC.read_text(encoding="utf-8"))
    if found is None:
        raise RuntimeError(
            f"no read-relations issue page bound stated in {CHANGES_SPEC}"
        )
    return found.group(1)


def spec_field_value_bound() -> str:
    """The field-value bound the spec assertion says a blocked read names."""
    found = _FIELD_BOUND_PHRASE.search(CHANGES_SPEC.read_text(encoding="utf-8"))
    if found is None:
        raise RuntimeError(
            f"no read-relations field value bound stated in {CHANGES_SPEC}"
        )
    return found.group(1)


class _StoreReplay:
    """Answer each store call with the page its ``after`` cursor selects."""

    def __init__(self, pages: Sequence[dict[str, object]]) -> None:
        self._pages = pages
        self.calls: list[tuple[str, ...]] = []
        self.cursors: list[str | None] = []

    def _end_cursor(self, page: dict[str, object]) -> str:
        return page["data"]["repository"]["issues"]["pageInfo"]["endCursor"]  # type: ignore[index,return-value]

    def __call__(
        self, argv: Sequence[str], /, *, cwd: Path, stdin: str | None
    ) -> object:
        del cwd, stdin
        after = next(
            (
                arg.removeprefix(_AFTER_ARGUMENT_PREFIX)
                for arg in argv
                if arg.startswith(_AFTER_ARGUMENT_PREFIX)
            ),
            None,
        )
        self.calls.append(tuple(argv))
        self.cursors.append(after)
        position = 0
        if after is not None:
            ends = [self._end_cursor(page) for page in self._pages]
            position = ends.index(after) + 1 if after in ends else len(self._pages)
        page = self._pages[min(position, len(self._pages) - 1)]
        # The CLI prints an answer as one line of JSON.
        return _runner.CommandResult(0, json.dumps(page), "")


def read_relations(fixture: Path) -> RelationsObservation:
    """Request ``read-relations`` for the invented Change while the store replays ``fixture``."""
    pages = json.loads(fixture.read_text(encoding="utf-8"))["pages"]
    replay = _StoreReplay(pages)
    request = json.dumps(
        {
            _runner.RequestField.OPERATION: _runner.Operation.READ_RELATIONS,
            _runner.RequestField.ISSUE: RELATIONS_ISSUE,
        }
    )
    code, result = _runner.execute(request, cwd=Path.cwd(), runner=replay)
    return RelationsObservation(
        exit_code=int(code),
        result=dict(result),
        store_calls=tuple(replay.calls),
        cursors=tuple(replay.cursors),
    )
