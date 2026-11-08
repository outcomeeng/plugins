"""Compliance evidence: reframe, merge, and the transition import of author-change.

Each rule is a spec assertion about what the script's reframe and merge do and
never do. The violating case of a rule is the input that would tempt a script
to break it: a Transition function that is absent or refuses, a record at each
Maturity a reframe starts from. The conforming case beside it shows the
operation completes when nothing violates the rule.

The controlled Change store and the stand-ins for the two sibling skills come
from the ``author_change`` harness. The stand-in for the transition function
records each request it receives, so the tests judge which Transitions the
script asked for and which writes it made itself.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from outcomeeng_testing.harnesses.author_change import (
    ABSORBED_NUMBER,
    EARLIER_PREDECESSOR_NUMBER,
    FIXTURES,
    HANDOFF,
    SUBJECT_NUMBER,
    TRANSITION_REFUSED,
    WRITE_KINDS,
    EventKind,
    Observation,
    Store,
    Stub,
    canonical_identity,
    load_script,
    request_for,
    run_script,
    seed_leaf,
)

script = load_script()
Request = script.RequestField
Result = script.ResultField
Status = script.Status
Maturity = script.Maturity
Lifecycle = script.Lifecycle
Operation = script.Operation
Move = script.Move

EDITED_BODY_DRAFT = FIXTURES / "draft-leaf-edited-body.md"
ALL_MATURITIES = [member.value for member in Maturity]
MATURITIES_ABOVE_PROPOSED = [
    member.value for member in Maturity if member != Maturity.PROPOSED
]
PREDECESSOR_SEPARATOR = ", "


def reframe(
    store: Store,
    *,
    handoff: dict[str, str] | None = None,
    with_transition: bool = True,
) -> Observation:
    fields: dict[object, object] = {
        Request.NUMBER: SUBJECT_NUMBER,
        Request.DRAFT_PATH: str(EDITED_BODY_DRAFT),
    }
    if handoff is not None:
        fields[Request.HANDOFF] = handoff
    return run_script(
        request_for(Operation.REFRAME, fields),  # type: ignore[arg-type]
        store,
        with_transition=with_transition,
    )


def merge(
    store: Store,
    *,
    transition_result: Mapping[str, object] | None = None,
    with_transition: bool = True,
) -> Observation:
    return run_script(
        request_for(
            Operation.MERGE,
            {Request.NUMBER: SUBJECT_NUMBER, Request.ABSORBED: ABSORBED_NUMBER},
        ),
        store,
        transition_result=transition_result,
        with_transition=with_transition,
    )


def publish_body(store: Store, *, with_transition: bool = True) -> Observation:
    return run_script(
        request_for(
            Operation.PUBLISH,
            {
                Request.NUMBER: SUBJECT_NUMBER,
                Request.DRAFT_PATH: str(EDITED_BODY_DRAFT),
            },
        ),
        store,
        with_transition=with_transition,
    )


def writes(observation: Observation) -> list[EventKind]:
    return [
        event.kind for event in observation.store.events if event.kind in WRITE_KINDS
    ]


def field_writes(observation: Observation, *names: str) -> list[str]:
    return [
        event.detail["name"]
        for event in observation.store.events
        if event.kind == EventKind.FIELD and event.detail["name"] in names
    ]


def posted_comment(observation: Observation) -> bool:
    return any("comment" in call for call in observation.calls)


@pytest.mark.parametrize("maturity", ALL_MATURITIES)
def test_reframe_edits_the_change_in_place_and_leaves_it_at_proposed(
    maturity: str,
) -> None:
    store = Store()
    seed_leaf(store, maturity)

    observed = reframe(store)

    assert observed.result[Result.STATUS] == Status.OK
    assert set(store.issues) == {SUBJECT_NUMBER}
    assert EventKind.CREATE not in writes(observed)
    issue = store.issues[SUBJECT_NUMBER]
    assert issue.fields["Maturity"] == Maturity.PROPOSED.value
    assert issue.body.startswith("## Statement of Intent")
    assert issue.body != (FIXTURES / "stored-leaf-body.md").read_text()
    lowers = observed.bridge.transitions
    if maturity == Maturity.PROPOSED.value:
        assert lowers == []
    else:
        (lower,) = lowers
        assert lower["transition"] == Move.LOWER.value
        assert lower["target"] == Maturity.PROPOSED.value
        assert lower["lower_cause"] == script.LowerCause.REFRAME.value


def test_reframe_of_a_held_change_hands_the_lower_the_handoff() -> None:
    store = Store()
    seed_leaf(store, Maturity.SLICED.value, assignees=["example-holder"])

    observed = reframe(store, handoff=HANDOFF)

    assert observed.result[Result.STATUS] == Status.OK
    (lower,) = observed.bridge.transitions
    assert lower["handoff"] == HANDOFF


def test_merge_closes_the_absorbed_change_abandoned_and_appends_it_to_the_predecessors() -> (
    None
):
    store = Store()
    seed_leaf(
        store,
        Maturity.SLICED.value,
        extra_fields={"Predecessors": canonical_identity(EARLIER_PREDECESSOR_NUMBER)},
    )
    seed_leaf(store, Maturity.SLICED.value, number=ABSORBED_NUMBER)

    observed = merge(store)

    assert observed.result[Result.STATUS] == Status.OK
    survivor = store.issues[SUBJECT_NUMBER]
    assert survivor.fields["Predecessors"].split(PREDECESSOR_SEPARATOR) == [
        canonical_identity(EARLIER_PREDECESSOR_NUMBER),
        canonical_identity(ABSORBED_NUMBER),
    ]
    absorbed = store.issues[ABSORBED_NUMBER]
    assert absorbed.fields["Lifecycle"] == Lifecycle.ABANDONED.value
    (abandon,) = observed.bridge.transitions
    assert abandon["transition"] == Move.ABANDONED.value
    assert abandon["number"] == ABSORBED_NUMBER
    assert abandon["merged_into"] == SUBJECT_NUMBER


def test_merge_reports_a_refused_abandonment_as_failed() -> None:
    store = Store()
    seed_leaf(store, Maturity.SLICED.value)
    seed_leaf(store, Maturity.SLICED.value, number=ABSORBED_NUMBER)

    observed = merge(store, transition_result=TRANSITION_REFUSED)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert (
        store.issues[ABSORBED_NUMBER].fields["Lifecycle"] != Lifecycle.ABANDONED.value
    )


@pytest.mark.parametrize("maturity", MATURITIES_ABOVE_PROPOSED)
def test_the_lower_of_a_reframe_goes_through_the_transition_function_alone(
    maturity: str,
) -> None:
    store = Store()
    seed_leaf(store, maturity)

    observed = reframe(store)

    assert len(observed.bridge.transitions) == 1
    assert field_writes(observed, "Maturity", "Lifecycle") == []
    assert not posted_comment(observed)

    unavailable_store = Store()
    seed_leaf(unavailable_store, maturity)
    unavailable = reframe(unavailable_store, with_transition=False)

    assert unavailable.result[Result.STATUS] == Status.BLOCKED
    assert Stub.TRANSITION_SKILL in unavailable.result[Result.DETAIL]
    assert writes(unavailable) == []


def test_the_lower_of_a_body_publish_goes_through_the_transition_function_alone() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.APPLICABLE.value)

    observed = publish_body(store)

    assert len(observed.bridge.transitions) == 1
    assert field_writes(observed, "Maturity", "Lifecycle") == []
    assert not posted_comment(observed)

    unavailable_store = Store()
    seed_leaf(unavailable_store, Maturity.APPLICABLE.value)
    unavailable = publish_body(unavailable_store, with_transition=False)

    assert unavailable.result[Result.STATUS] == Status.BLOCKED
    assert Stub.TRANSITION_SKILL in unavailable.result[Result.DETAIL]
    assert writes(unavailable) == []
    assert (
        unavailable_store.issues[SUBJECT_NUMBER].body
        == (FIXTURES / "stored-leaf-body.md").read_text()
    )


def test_the_abandoned_transition_of_a_merge_goes_through_the_transition_function_alone() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.SLICED.value)
    seed_leaf(store, Maturity.SLICED.value, number=ABSORBED_NUMBER)

    observed = merge(store)

    assert len(observed.bridge.transitions) == 1
    assert field_writes(observed, "Maturity", "Lifecycle") == []
    assert not posted_comment(observed)

    unavailable_store = Store()
    seed_leaf(unavailable_store, Maturity.SLICED.value)
    seed_leaf(unavailable_store, Maturity.SLICED.value, number=ABSORBED_NUMBER)
    unavailable = merge(unavailable_store, with_transition=False)

    assert unavailable.result[Result.STATUS] == Status.BLOCKED
    assert Stub.TRANSITION_SKILL in unavailable.result[Result.DETAIL]
    assert writes(unavailable) == []
