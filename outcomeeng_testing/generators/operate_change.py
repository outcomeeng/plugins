"""Record bodies, case domains, and spec-derived oracles for the operate-change evidence.

The record builders compose Change records in the record form. The case
domains enumerate the finite domains the node's mapping and compliance
assertions range over: the states a Transition row does not admit, the
carry-forward and review-part cases, and the maturity-ready records. The
oracles carry the orders and closed sets the spec states, spelled with the
script's own tokens, so a change to the script's constants never changes the
expectation derived from the spec.

Nothing here asserts: the linked tests read these values and decide.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from itertools import product
from typing import Any, Final

from outcomeeng_testing.harnesses.operate_change import (
    LOGIN,
    SPECIFIED,
    AuditStatus,
    HandoffKey,
    InfrastructureState,
    IssueState,
    Lifecycle,
    LowerCause,
    Maturity,
    Mover,
    ObservedKey,
    SimulatedGitHub,
    Transition,
    WriteKind,
    bound_pair,
    change_fields,
    changeset,
    close_check,
    failing_form_check,
    handoff,
    held,
    passing_form_check,
    request,
)

TARGET: Final = "spx/20-example.enabler/example.md"
NODE: Final = "spx/20-example.enabler"
RECORD: Final = "spx/20-example.enabler/15-rule.pdr.md"
CHILD: Final = "spx/20-example.enabler/child/child.md"
BASE: Final = "c" * 40
OTHER_BASE: Final = "e" * 40
UNRESOLVED_BASE: Final = "f" * 40
INFRASTRUCTURE_NODE: Final = "spx/15-infra.enabler"
REASON: Final = "a settled judgment reopened"
REOPENED: Final = "the Base moved under a settled replacement"
EDIT: Final = "\nan edit from another writer\n"
ANOTHER_ACCOUNT: Final = "another-account"


# ------------------------------------------------------------------ records


def intent() -> str:
    """A Statement of Intent that states Output, Why, and Verification."""
    return (
        "## Statement of Intent\n\n"
        "- Output: An example Output.\n"
        "- Why: An example reason.\n"
        "- Verification: An example verification.\n"
    )


def declaration(lines: list[str], heading: str = TARGET) -> str:
    """A record whose Declarations hold one subsection of the given lines."""
    return (
        intent() + f"\n## Declarations\n\n### {heading}\n\n" + "\n".join(lines) + "\n"
    )


def leaf_record(node_subsections: int = 1, infrastructure: str = "none") -> str:
    """A Leaf record holding that many Node subsections, each with an infrastructure line."""
    parts = [intent(), "\n## Declarations\n"]
    for index in range(node_subsections):
        parts.append(
            f"\n### spx/{20 + index}-example.enabler/example.md\n\n"
            "```diff\n+ - one: ALWAYS: an example\n```\n\n"
            f"Infrastructure: one {infrastructure}\n"
        )
    return "".join(parts)


def unframed_record() -> str:
    """A record whose Declarations hold nothing and give no reason."""
    return intent() + "\n## Declarations\n"


def edited(body: str) -> str:
    """The body after another writer's edit."""
    return body + EDIT


def change_store(
    maturity: str,
    lifecycle: str,
    body: str | None = None,
    base: str = BASE,
    number: int = 10,
) -> SimulatedGitHub:
    """A store holding one Change in the given state."""
    github = SimulatedGitHub()
    github.add(
        number,
        leaf_record() if body is None else body,
        change_fields(maturity, lifecycle, base),
    )
    return github


def applicable_held() -> SimulatedGitHub:
    """An Applicable, Available Change held by the session."""
    github = change_store(Maturity.APPLICABLE, Lifecycle.AVAILABLE)
    held(github, 10)
    return github


def add_child(github: SimulatedGitHub, state: str = IssueState.OPEN.value) -> None:
    """Add Change 11 as a Child of Change 10."""
    github.add(
        11,
        leaf_record(),
        change_fields(Maturity.PROPOSED, Lifecycle.AVAILABLE, parent=10),
    )
    github.issues[11].state = state


# ---------------------------------------------------------- transition rows


@dataclass(frozen=True)
class State:
    """A Change state a Transition row is judged against."""

    maturity: Maturity
    lifecycle: Lifecycle
    held: bool


@dataclass(frozen=True)
class TransitionRow:
    """One row of the spec's transitions table: a state it requires and what it changes."""

    start: State
    admits: frozenset[State]
    changes: Mapping[ObservedKey, Any]


ALL_STATES: Final = frozenset(
    State(maturity, lifecycle, holds)
    for maturity, lifecycle, holds in product(Maturity, Lifecycle, (False, True))
)
OPEN_LIFECYCLES: Final = (Lifecycle.AVAILABLE, Lifecycle.SUBMITTED)
TERMINAL_LIFECYCLES: Final = (Lifecycle.APPLIED, Lifecycle.ABANDONED)
LOWERABLE: Final = (Maturity.FRAMED, Maturity.SLICED, Maturity.APPLICABLE)


def _states(maturities: Any, lifecycles: Any, holds: Any) -> frozenset[State]:
    return frozenset(
        State(maturity, lifecycle, holder)
        for maturity, lifecycle, holder in product(maturities, lifecycles, holds)
    )


#: The transitions table of the spec, one row per Transition.
ROWS: Final[Mapping[Transition, TransitionRow]] = {
    Transition.CLAIM: TransitionRow(
        State(Maturity.SLICED, Lifecycle.AVAILABLE, False),
        _states(Maturity, (Lifecycle.AVAILABLE,), (False,)),
        {ObservedKey.ASSIGNEES: (LOGIN,)},
    ),
    Transition.RELEASE: TransitionRow(
        State(Maturity.SLICED, Lifecycle.SUBMITTED, True),
        _states(Maturity, OPEN_LIFECYCLES, (True,)),
        {ObservedKey.ASSIGNEES: (), ObservedKey.LIFECYCLE: Lifecycle.AVAILABLE.value},
    ),
    Transition.SUBMIT: TransitionRow(
        State(Maturity.PROPOSED, Lifecycle.AVAILABLE, True),
        _states(Maturity, (Lifecycle.AVAILABLE,), (True,)),
        {ObservedKey.LIFECYCLE: Lifecycle.SUBMITTED.value},
    ),
    Transition.ADVANCE: TransitionRow(
        State(Maturity.PROPOSED, Lifecycle.SUBMITTED, False),
        _states(
            [m for m in Maturity if m != Maturity.APPLICABLE],
            (Lifecycle.SUBMITTED,),
            (False, True),
        )
        | {State(Maturity.SLICED, Lifecycle.AVAILABLE, True)},
        {ObservedKey.MATURITY: Maturity.FRAMED.value},
    ),
    Transition.LOWER: TransitionRow(
        State(Maturity.SLICED, Lifecycle.AVAILABLE, False),
        _states(LOWERABLE, OPEN_LIFECYCLES, (False, True)),
        {ObservedKey.MATURITY: Maturity.FRAMED.value},
    ),
    Transition.APPLIED: TransitionRow(
        State(Maturity.APPLICABLE, Lifecycle.AVAILABLE, True),
        _states(Maturity, OPEN_LIFECYCLES, (True,)),
        {
            ObservedKey.LIFECYCLE: Lifecycle.APPLIED.value,
            ObservedKey.STATE: IssueState.CLOSED.value,
        },
    ),
    Transition.ABANDONED: TransitionRow(
        State(Maturity.FRAMED, Lifecycle.AVAILABLE, False),
        _states(Maturity, OPEN_LIFECYCLES, (False, True)),
        {
            ObservedKey.LIFECYCLE: Lifecycle.ABANDONED.value,
            ObservedKey.STATE: IssueState.CLOSED.value,
        },
    ),
}


def refused_states(transition: Transition) -> list[State]:
    """Every state the row does not admit, in a stable order."""
    return sorted(
        ALL_STATES - ROWS[transition].admits,
        key=lambda s: (
            list(Maturity).index(s.maturity),
            list(Lifecycle).index(s.lifecycle),
            s.held,
        ),
    )


def state_store(state: State) -> SimulatedGitHub:
    """A store holding Change 10 in the given state."""
    github = change_store(state.maturity, state.lifecycle)
    if state.held:
        held(github, 10)
    return github


def transition_request(
    transition: Transition, github: SimulatedGitHub
) -> dict[str, Any]:
    """The request the transition's row is exercised by, for the Change in `github`."""
    if transition == Transition.CLAIM:
        return request(transition, 10, Mover.AGENT)
    if transition == Transition.RELEASE:
        return request(transition, 10, Mover.HOLDER, handoff=handoff())
    if transition == Transition.SUBMIT:
        return request(transition, 10, Mover.HOLDER, reopened=REOPENED)
    if transition == Transition.ADVANCE:
        return request(
            transition, 10, Mover.OPERATOR, form_check=passing_form_check(github)
        )
    if transition == Transition.LOWER:
        return request(
            transition,
            10,
            Mover.OPERATOR,
            target=Maturity.FRAMED.value,
            reason=REASON,
            lower_cause=LowerCause.REOPENED.value,
        )
    if transition == Transition.APPLIED:
        return request(
            transition,
            10,
            Mover.HOLDER,
            changeset=changeset(),
            close_check=close_check(),
        )
    return request(transition, 10, Mover.OPERATOR)


# ----------------------------------------------------------- maturity-ready

#: The Maturity each row of the maturity-ready table advances a Leaf into.
ADVANCES_INTO: Final[Mapping[Maturity, Maturity]] = {
    Maturity.PROPOSED: Maturity.FRAMED,
    Maturity.FRAMED: Maturity.FRAMED,
    Maturity.SLICED: Maturity.SLICED,
    Maturity.APPLICABLE: Maturity.APPLICABLE,
}


def ready(row: Maturity, *, met: bool = True) -> tuple[SimulatedGitHub, dict[str, Any]]:
    """An advance whose record meets the row and every row above it, or misses the row alone."""
    if row in (Maturity.PROPOSED, Maturity.FRAMED):
        body = leaf_record() if met or row == Maturity.PROPOSED else unframed_record()
        github = change_store(Maturity.PROPOSED, Lifecycle.SUBMITTED, body)
        check = (
            passing_form_check(github)
            if met or row != Maturity.PROPOSED
            else failing_form_check(github)
        )
        return github, request(Transition.ADVANCE, 10, Mover.OPERATOR, form_check=check)
    if row == Maturity.SLICED:
        github = change_store(
            Maturity.FRAMED, Lifecycle.SUBMITTED, leaf_record(5 if met else 6)
        )
        return github, request(
            Transition.ADVANCE,
            10,
            Mover.OPERATOR,
            form_check=passing_form_check(github),
            review=bound_pair(github),
        )
    github = change_store(
        Maturity.SLICED,
        Lifecycle.AVAILABLE,
        leaf_record(1, f"`{INFRASTRUCTURE_NODE}`"),
    )
    held(github, 10)
    return github, request(
        Transition.ADVANCE,
        10,
        Mover.HOLDER,
        form_check=passing_form_check(github),
        audit=bound_pair(github),
        audit_status=AuditStatus.APPROVED,
        infrastructure={
            INFRASTRUCTURE_NODE: InfrastructureState.PASSING if met else SPECIFIED
        },
    )


# -------------------------------------------------------------- store-writes


class Part(StrEnum):
    """The parts the store-writes table names."""

    MATURITY = "maturity"
    LIFECYCLE = "lifecycle"
    HOLDER = "holder"
    TRANSITION = "transition"


#: Per part, the Transition whose writes reach it and the write kind of its one home.
STORE_HOMES: Final[Mapping[Part, tuple[Transition, WriteKind]]] = {
    Part.MATURITY: (Transition.ADVANCE, WriteKind.MATURITY),
    Part.LIFECYCLE: (Transition.SUBMIT, WriteKind.LIFECYCLE),
    Part.HOLDER: (Transition.CLAIM, WriteKind.ASSIGNEE),
    Part.TRANSITION: (Transition.CLAIM, WriteKind.COMMENT),
}


# ------------------------------------------------------ cases the spec names

#: Keys the log-closed line forbids in a block, and a request value no block may carry.
POSITION_KEY: Final = "position"
DELEGATE_KEY: Final = "delegate"


# ------------------------------------------------------------- every Transition


def every_transition() -> list[tuple[SimulatedGitHub, dict[str, Any]]]:
    """One Change and one request for each Transition, in the Transition's own state."""
    pairs: list[tuple[SimulatedGitHub, dict[str, Any]]] = []
    for transition in Transition:
        row = ROWS[transition]
        start = (
            replace(row.start, held=True)
            if transition == Transition.ABANDONED
            else row.start
        )
        github = state_store(start)
        payload = transition_request(transition, github)
        if transition == Transition.RELEASE:
            payload = request(
                transition,
                10,
                Mover.HOLDER,
                handoff=handoff(
                    **{
                        HandoffKey.PULL_REQUEST.value: "https://github.com/example-org/example-product/pull/7"
                    }
                ),
            )
        pairs.append((github, payload))
    return pairs


# ---------------------------------------------------------------- review carry


@dataclass(frozen=True)
class CarryCase:
    """A later publish of a reviewed record: two commits, the reviewed body, the current body."""

    name: str
    commits: tuple[Mapping[str, str], Mapping[str, str]]
    reviewed_body: str
    current_body: str
    reviewed_base_resolves: bool = True


def _commits(
    target: tuple[str, str], record: tuple[str, str] = ("decision", "decision")
) -> tuple[Mapping[str, str], Mapping[str, str]]:
    return (
        {TARGET: target[0], RECORD: record[0]},
        {TARGET: target[1], RECORD: record[1], "other.txt": "x"},
    )


def carrying_cases() -> list[CarryCase]:
    """Cases whose review carries forward: the part and its context read the same."""
    same = _commits(("same", "same"))
    leaf = leaf_record()
    reviewed_lines = ["| Case | Value |", "| ---- | ----- |", "| one | alpha |"]
    return [
        CarryCase(
            "text-outside-declarations",
            same,
            leaf,
            leaf.replace("An example reason.", "An edited reason."),
        ),
        CarryCase(
            "declarations-unchanged",
            same,
            declaration(reviewed_lines),
            declaration(list(reviewed_lines)),
        ),
    ]


def breaking_cases() -> list[CarryCase]:
    """Cases whose review carries nothing forward: a part, its file, its records, or its Base moved."""
    leaf = leaf_record()
    node_removal = declaration(["```diff", "deleted file", "```"], NODE)
    return [
        CarryCase(
            "declaration-line-edited",
            _commits(("same", "same")),
            leaf,
            leaf.replace("an example", "an edited example"),
        ),
        CarryCase("node-file-changed", _commits(("before", "after")), leaf, leaf),
        CarryCase(
            "decision-record-amended",
            _commits(("same", "same"), ("decision", "amended decision")),
            leaf,
            leaf,
        ),
        CarryCase("base-unresolved", _commits(("same", "same")), leaf, leaf, False),
        CarryCase(
            "node-branch-changed",
            (
                {TARGET: "a", CHILD: "one"},
                {TARGET: "a", CHILD: "two"},
            ),
            node_removal,
            node_removal,
        ),
    ]


# ----------------------------------------------------------------- review part


@dataclass(frozen=True)
class PartCase:
    """A later publish that changes one thing about the parts of one subsection.

    `lost` holds the lines of the current record whose review does not carry,
    and `kept` the lines whose review carries.
    """

    name: str
    reviewed_lines: tuple[str, ...]
    current_lines: tuple[str, ...]
    lost: tuple[str, ...]
    kept: tuple[str, ...]


_TABLE_HEADER: Final = "| Case | Value |"
_TABLE_RULE: Final = "| ---- | ----- |"
_ROW_ONE: Final = "| one | alpha |"
_ROW_TWO: Final = "| two | beta |"
_ITEM_ONE: Final = "- one: ALWAYS: alpha behaves"
_ITEM_TWO: Final = "- two: ALWAYS: beta behaves"


def part_cases() -> list[PartCase]:
    """Cases changing an unrelated row, then each kind of context of a part."""
    table = (_TABLE_HEADER, _TABLE_RULE, _ROW_ONE, _ROW_TWO)
    scenario = ("#### Scenario first", *table)
    items = ("Scenario: first interaction", _ITEM_ONE, _ITEM_TWO)
    return [
        PartCase(
            "unrelated-row",
            table,
            (_TABLE_HEADER, _TABLE_RULE, _ROW_ONE, "| two | gamma |"),
            ("| two | gamma |",),
            (_ROW_ONE,),
        ),
        PartCase(
            "table-header",
            table,
            ("| Case | Other |", _TABLE_RULE, _ROW_ONE, _ROW_TWO),
            (_ROW_ONE,),
            (),
        ),
        PartCase(
            "context-heading",
            scenario,
            ("#### Scenario second", *table),
            (_ROW_ONE,),
            (),
        ),
        PartCase(
            "list-opener",
            items,
            ("Scenario: second interaction", _ITEM_ONE, _ITEM_TWO),
            (_ITEM_ONE,),
            (),
        ),
        PartCase(
            "unrelated-list-item",
            items,
            ("Scenario: first interaction", _ITEM_ONE, "- two: ALWAYS: gamma behaves"),
            ("- two: ALWAYS: gamma behaves",),
            (_ITEM_ONE,),
        ),
    ]


# -------------------------------------------------------------------- binding

#: Where another writer's edit lands between the Maturity write and the comment.
RACES: Final = ("body", "base")
