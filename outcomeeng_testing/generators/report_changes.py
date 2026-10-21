"""Generated Change stores for the `report-changes` script.

The domain is a Change store as the store holds it: issues with distinct
numbers, each carrying the issue fields and assignees the store holds and an
open or closed state, dealt across a varying number of pages in reading order,
together with a request whose Priority order lists distinct values and whose
filters are each absent or drawn from the values the store holds.

Every vocabulary item comes from the script's own registries: the Maturity and
Lifecycle values, the issue and blocker states, and the blocked-filter values.
The generator never consults the script's matching, ordering, or page-reading
code, so the rows a linked test compares against come from the test's own
statement of the spec's rule, never from the generator.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from types import ModuleType
from typing import Final

from hypothesis import strategies as st

#: The invented prefix of every generated Change URL.
URL_PREFIX: Final = "https://example.invalid/changes/"

_NAME_ALPHABET: Final = string.ascii_letters + string.digits
_MAX_NAME_LENGTH: Final = 8
_MAX_TITLE_LENGTH: Final = 40
_MAX_ISSUES: Final = 25
_MAX_POOL: Final = 3
_MAX_PRIORITIES: Final = 5
_MAX_ASSIGNEES: Final = 3
_MAX_BLOCKERS: Final = 3
_MAX_NUMBER: Final = 10_000
_SURROGATE_CATEGORY: Final = "Cs"


@dataclass(frozen=True)
class GeneratedIssue:
    """One issue as the store holds it."""

    number: int
    url: str
    title: str
    state: str
    assignees: tuple[str, ...]
    product: str | None
    maturity: str | None
    lifecycle: str | None
    priority: str | None
    parent: int | None
    blocker_numbers: tuple[int, ...]
    blocker_states: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedRequest:
    """The request values a report is asked for."""

    priority_order: tuple[str, ...]
    product: str | None
    maturity: str | None
    lifecycle: str | None
    holder: str | None
    blocked: str | None


@dataclass(frozen=True)
class GeneratedStore:
    """A store, its page boundaries in reading order, and the request."""

    issues: tuple[GeneratedIssue, ...]
    #: How many issues each page holds, in reading order.
    page_sizes: tuple[int, ...]
    request: GeneratedRequest


def _names() -> st.SearchStrategy[str]:
    return st.text(alphabet=_NAME_ALPHABET, min_size=1, max_size=_MAX_NAME_LENGTH)


def _titles() -> st.SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(blacklist_categories=(_SURROGATE_CATEGORY,)),
        max_size=_MAX_TITLE_LENGTH,
    )


def _optional(values: st.SearchStrategy[str]) -> st.SearchStrategy[str | None]:
    return st.none() | values


def _page_sizes(count: int, max_pages: int, draw: st.DrawFn) -> tuple[int, ...]:
    cuts = sorted(
        draw(
            st.lists(
                st.integers(min_value=0, max_value=count),
                max_size=max_pages - 1,
            )
        )
    )
    bounds = [0, *cuts, count]
    return tuple(after - before for before, after in zip(bounds, bounds[1:]))


def stores(script: ModuleType) -> st.SearchStrategy[GeneratedStore]:
    """Stores of any size and page count, with a request over their values."""

    @st.composite
    def build(draw: st.DrawFn) -> GeneratedStore:
        order = tuple(
            draw(st.lists(_names(), min_size=1, max_size=_MAX_PRIORITIES, unique=True))
        )
        products = draw(st.lists(_names(), min_size=1, max_size=_MAX_POOL, unique=True))
        holders = draw(st.lists(_names(), min_size=1, max_size=_MAX_POOL, unique=True))
        numbers = draw(
            st.lists(
                st.integers(min_value=1, max_value=_MAX_NUMBER),
                max_size=_MAX_ISSUES,
                unique=True,
            )
        )
        issues = []
        for number in numbers:
            blocker_numbers = tuple(
                draw(
                    st.lists(
                        st.integers(min_value=1, max_value=_MAX_NUMBER),
                        max_size=_MAX_BLOCKERS,
                        unique=True,
                    )
                )
            )
            issues.append(
                GeneratedIssue(
                    number=number,
                    url=f"{URL_PREFIX}{number}",
                    title=draw(_titles()),
                    state=draw(st.sampled_from(tuple(script.IssueState))),
                    assignees=tuple(
                        draw(
                            st.lists(
                                st.sampled_from(holders),
                                max_size=_MAX_ASSIGNEES,
                                unique=True,
                            )
                        )
                    ),
                    product=draw(_optional(st.sampled_from(products))),
                    maturity=draw(_optional(st.sampled_from(script.MATURITIES))),
                    lifecycle=draw(_optional(st.sampled_from(script.LIFECYCLES))),
                    priority=draw(_optional(st.sampled_from(order))),
                    parent=draw(
                        st.none() | st.integers(min_value=1, max_value=_MAX_NUMBER)
                    ),
                    blocker_numbers=blocker_numbers,
                    blocker_states=tuple(
                        draw(st.sampled_from(tuple(script.BlockerState)))
                        for _ in blocker_numbers
                    ),
                )
            )
        request = GeneratedRequest(
            priority_order=order,
            product=draw(_optional(st.sampled_from(products))),
            maturity=draw(_optional(st.sampled_from(script.MATURITIES))),
            lifecycle=draw(_optional(st.sampled_from(script.LIFECYCLES))),
            holder=draw(_optional(st.sampled_from(holders))),
            blocked=draw(
                st.none() | st.sampled_from(tuple(script.BlockedFilter)).map(str)
            ),
        )
        return GeneratedStore(
            issues=tuple(issues),
            page_sizes=_page_sizes(len(issues), script.MAX_PAGES, draw),
            request=request,
        )

    return build()
