"""Compliance evidence: record, split, and draft of the author-change script.

Each rule is a spec assertion about what the script's record, split, and draft
operations do and never do. The violating case of a rule is the input that
would tempt a script to break it: a Draft that fails the form check, a split of
an Applicable record or of a Parent, a holder that would leak into a Draft. The
conforming case beside it shows the operation completes when nothing violates
the rule.

The controlled Change store, the stand-ins for the two sibling skills, and the
Draft files come from the ``author_change`` harness and fixtures. The expected
fields come from the record decision's rows, never from the script.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest

from outcomeeng_testing.harnesses.author_change import (
    CHECK_FAILS,
    CHECK_PASSES,
    FIXTURES,
    SUBJECT_NUMBER,
    WRITE_KINDS,
    EventKind,
    Observation,
    Store,
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
Metadata = script.Metadata

NEW_LEAF_DRAFT = FIXTURES / "draft-leaf-new.md"
INTENT_ONLY_DRAFT = FIXTURES / "draft-leaf-intent-only.md"
CHILD_DRAFTS = [FIXTURES / "draft-child-one.md", FIXTURES / "draft-child-two.md"]
CROSS_PRODUCT_CHILD_DRAFTS = [
    FIXTURES / "draft-child-one.md",
    FIXTURES / "draft-child-other-product.md",
]
STORED_BODY = (FIXTURES / "stored-leaf-body.md").read_text()
BELOW_APPLICABLE = [
    member.value for member in Maturity if member != Maturity.APPLICABLE
]


def record(
    store: Store,
    draft_name: object,
    *,
    form_check_result: Mapping[str, object] | None = None,
) -> Observation:
    return run_script(
        request_for(Operation.RECORD, {Request.DRAFT_PATH: str(draft_name)}),
        store,
        form_check_result=form_check_result,
    )


def split(store: Store, children: Sequence[object] = CHILD_DRAFTS) -> Observation:
    return run_script(
        request_for(
            Operation.SPLIT,
            {
                Request.NUMBER: SUBJECT_NUMBER,
                Request.CHILDREN: [str(path) for path in children],
            },
        ),
        store,
    )


def writes(observation: Observation) -> list[EventKind]:
    return [
        event.kind for event in observation.store.events if event.kind in WRITE_KINDS
    ]


@pytest.mark.parametrize(
    "draft", [NEW_LEAF_DRAFT, INTENT_ONLY_DRAFT], ids=lambda p: p.stem
)
def test_record_writes_a_proposed_submitted_leaf_held_by_the_recorder_with_the_default_branch_head_as_base(
    draft: object,
) -> None:
    store = Store()

    observed = record(store, draft, form_check_result=CHECK_PASSES)

    assert observed.result[Result.STATUS] == Status.OK
    created = store.issues[observed.result[Result.NUMBER]]
    assert created.fields["Maturity"] == Maturity.PROPOSED.value
    assert created.fields["Lifecycle"] == Lifecycle.SUBMITTED.value
    assert created.fields["Base"] == store.default_branch_head
    assert created.assignees == [script.RECORDER]
    assert observed.bridge.transitions == []
    assert created.comments == []
    assert observed.bridge.check_writes_before == [0]


def test_record_creates_nothing_when_the_draft_fails_the_form_check() -> None:
    store = Store()

    observed = record(store, NEW_LEAF_DRAFT, form_check_result=CHECK_FAILS)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert writes(observed) == []
    assert store.issues == {}


@pytest.mark.parametrize("maturity", BELOW_APPLICABLE)
def test_split_records_each_child_under_the_split_record_and_leaves_it_only_its_intent(
    maturity: str,
) -> None:
    store = Store()
    seed_leaf(store, maturity)

    observed = split(store)

    assert observed.result[Result.STATUS] == Status.OK
    children = observed.result[Result.NUMBERS]
    assert len(children) == len(CHILD_DRAFTS)
    for number in children:
        child = store.issues[number]
        assert child.fields["Parent"] == float(SUBJECT_NUMBER)
        assert child.fields["Lifecycle"] == Lifecycle.AVAILABLE.value
        assert child.fields["Maturity"] == Maturity.PROPOSED.value
    parent = store.issues[SUBJECT_NUMBER]
    assert "## Statement of Intent" in parent.body
    assert "## Declarations" not in parent.body
    assert STORED_BODY.startswith(parent.body.rstrip("\n"))
    assert parent.fields.get("Base") is None
    assert parent.fields["Product"] == "example"


def test_split_refuses_children_that_span_two_products_and_writes_nothing() -> None:
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)

    observed = split(store, CROSS_PRODUCT_CHILD_DRAFTS)

    assert observed.result[Result.STATUS] == Status.BLOCKED
    assert "Product" in str(observed.result)
    assert writes(observed) == []
    assert set(store.issues) == {SUBJECT_NUMBER}


def test_split_refuses_an_applicable_record_and_writes_nothing() -> None:
    store = Store()
    seed_leaf(store, Maturity.APPLICABLE.value)

    observed = split(store)

    assert observed.result[Result.STATUS] == Status.INVALID_REQUEST
    assert writes(observed) == []
    assert set(store.issues) == {SUBJECT_NUMBER}


def test_split_refuses_a_parent_and_writes_nothing() -> None:
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value, base=None)

    observed = split(store)

    assert observed.result[Result.STATUS] == Status.INVALID_REQUEST
    assert writes(observed) == []
    assert set(store.issues) == {SUBJECT_NUMBER}


def test_draft_writes_the_stored_metadata_except_the_holder_then_the_stored_body() -> (
    None
):
    holder = "example-holder"
    store = Store()
    seed_leaf(store, Maturity.SLICED.value, assignees=[holder])

    observed = run_script(
        request_for(
            Operation.DRAFT,
            {
                Request.NUMBER: SUBJECT_NUMBER,
                Request.DRAFT_PATH: lambda checkout: str(checkout / "draft.md"),
            },
        ),
        store,
    )

    assert observed.result[Result.STATUS] == Status.OK
    assert writes(observed) == []
    text = observed.checkout_files["draft.md"]
    front_matter, _, body = text.removeprefix("---\n").partition("\n---\n")
    keys = [line.partition(":")[0] for line in front_matter.splitlines()]
    assert keys == [key.value for key in Metadata if key != Metadata.HOLDER]
    assert holder not in text
    assert body.strip() == STORED_BODY.strip()
