"""Compliance evidence: the publish of the author-change script.

Each rule is a spec assertion about what the script's publish does and never
does. The violating case of a rule is the input that would tempt a script to
break it: a form check that fails, a record that another writer edited between
the script's read and its write, a Draft that leaves parts unchanged, a field
write the store drops, a Transition that is refused. The conforming case beside
it shows the publish completes when nothing violates the rule.

The controlled Change store, the stand-ins for the two sibling skills, and the
Draft and body files come from the ``author_change`` harness and fixtures under
the failure-simulation, interaction-protocol, and time-and-concurrency
exceptions of the test methodology. The expected writes derive from the
Draft files and the stored body, never from the script.
"""

from __future__ import annotations

from collections.abc import Mapping

import re
from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.author_change import (
    BLOCKER_NUMBER,
    CHECK_FAILS,
    CHECK_PASSES,
    FIXTURES,
    STORED_BASE,
    SUBJECT_NUMBER,
    TRANSITION_DONE,
    TRANSITION_REFUSED,
    WRITE_KINDS,
    EventKind,
    Interference,
    Moment,
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
Operation = script.Operation

EDITED_BODY_DRAFT = FIXTURES / "draft-leaf-edited-body.md"
METADATA_ONLY_DRAFT = FIXTURES / "draft-leaf-metadata-only.md"
STORED_BODY = (FIXTURES / "stored-leaf-body.md").read_text()
FOREIGN_BODY = (FIXTURES / "foreign-body.md").read_text()
DRAFT_BASE = re.search(
    r"^base: (\S+)$", EDITED_BODY_DRAFT.read_text(), re.MULTILINE
).group(1)  # type: ignore[union-attr]
ALL_MATURITIES = [member.value for member in Maturity]


def publish(
    store: Store,
    draft: Path,
    *,
    form_check_result: Mapping[str, object] | None = None,
    transition_result: Mapping[str, object] | None = None,
) -> Observation:
    return run_script(
        request_for(
            Operation.PUBLISH,
            {Request.NUMBER: SUBJECT_NUMBER, Request.DRAFT_PATH: str(draft)},
        ),
        store,
        form_check_result=form_check_result,
        transition_result=transition_result,
    )


def writes(observation: Observation) -> list[EventKind]:
    return [
        event.kind for event in observation.store.events if event.kind in WRITE_KINDS
    ]


def body_edits(observation: Observation) -> list[str]:
    return [
        event.detail["body"]
        for event in observation.store.events
        if event.kind == EventKind.EDIT and "body" in event.detail
    ]


def field_writes(observation: Observation, name: str) -> list[object]:
    return [
        event.detail["value"]
        for event in observation.store.events
        if event.kind == EventKind.FIELD and event.detail["name"] == name
    ]


@pytest.mark.parametrize("maturity", ALL_MATURITIES)
def test_form_check_runs_before_every_write_and_a_failing_check_publishes_nothing(
    maturity: str,
) -> None:
    refused_store = Store()
    seed_leaf(refused_store, maturity)
    refused = publish(refused_store, EDITED_BODY_DRAFT, form_check_result=CHECK_FAILS)

    assert refused.exit_code != 0
    assert refused.result[Result.STATUS] == Status.FAILED
    assert len(refused.bridge.check_requests) == 1
    assert writes(refused) == []
    assert refused.store.issues[SUBJECT_NUMBER].body == STORED_BODY

    published_store = Store()
    seed_leaf(published_store, maturity)
    published = publish(
        published_store, EDITED_BODY_DRAFT, form_check_result=CHECK_PASSES
    )

    assert published.result[Result.STATUS] == Status.OK
    assert published.bridge.check_writes_before == [0]
    assert body_edits(published) == [
        EDITED_BODY_DRAFT.read_text().split("---\n", 2)[2].lstrip("\n")
    ]


@pytest.mark.parametrize("maturity", ALL_MATURITIES)
def test_base_moves_only_on_a_publish_that_writes_the_body(maturity: str) -> None:
    body_store = Store()
    seed_leaf(body_store, maturity)
    with_body = publish(body_store, EDITED_BODY_DRAFT)

    assert with_body.result[Result.STATUS] == Status.OK
    assert field_writes(with_body, "Base") == [DRAFT_BASE]
    assert body_store.issues[SUBJECT_NUMBER].fields["Base"] == DRAFT_BASE

    metadata_store = Store()
    seed_leaf(metadata_store, maturity)
    seed_leaf(metadata_store, Maturity.PROPOSED.value, number=BLOCKER_NUMBER)
    without_body = publish(metadata_store, METADATA_ONLY_DRAFT)

    assert without_body.result[Result.STATUS] == Status.OK
    assert body_edits(without_body) == []
    assert field_writes(without_body, "Base") == []
    assert metadata_store.issues[SUBJECT_NUMBER].fields["Base"] == STORED_BASE


def test_a_record_edited_after_the_publish_read_fails_the_publish_before_any_write() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)
    store.interference = Interference(Moment.BEFORE_SECOND_READ, FOREIGN_BODY)

    observed = publish(store, EDITED_BODY_DRAFT)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert writes(observed) == []
    (request,) = observed.bridge.check_requests
    assert request["stored_record"]["body"] == STORED_BODY
    first_read = next(e for e in store.events if e.kind == EventKind.READ)
    check = next(e for e in store.events if e.kind == EventKind.FORM_CHECK)
    assert first_read.sequence < check.sequence
    assert store.issues[SUBJECT_NUMBER].body == FOREIGN_BODY


def test_a_revision_landed_between_the_read_and_the_write_is_restored_and_fails_the_publish() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)
    store.interference = Interference(Moment.BEFORE_WRITE, FOREIGN_BODY)

    observed = publish(store, EDITED_BODY_DRAFT)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert observed.result[Result.RESTORED] is True
    assert store.issues[SUBJECT_NUMBER].body == FOREIGN_BODY


def test_a_revision_landed_after_the_write_stands_and_fails_the_publish() -> None:
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)
    store.interference = Interference(Moment.AFTER_WRITE, FOREIGN_BODY)

    observed = publish(store, EDITED_BODY_DRAFT)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert Result.RESTORED not in observed.result
    assert len(body_edits(observed)) == 1
    assert store.issues[SUBJECT_NUMBER].body == FOREIGN_BODY


def test_a_publish_with_no_foreign_revision_completes() -> None:
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)

    observed = publish(store, EDITED_BODY_DRAFT)

    assert observed.result[Result.STATUS] == Status.OK


@pytest.mark.parametrize("moment", list(Moment))
def test_github_race_fails_the_publish_at_each_moment_and_keeps_the_foreign_revision(
    moment: Moment,
) -> None:
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)
    store.interference = Interference(moment, FOREIGN_BODY)

    observed = publish(store, EDITED_BODY_DRAFT)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert observed.exit_code != 0
    assert store.issues[SUBJECT_NUMBER].body == FOREIGN_BODY
    if moment == Moment.BEFORE_SECOND_READ:
        assert body_edits(observed) == []
    else:
        assert len(body_edits(observed)) >= 1


def test_a_form_check_that_fails_on_the_new_base_of_a_sliced_record_publishes_nothing() -> (
    None
):
    refused_store = Store()
    seed_leaf(refused_store, Maturity.SLICED.value)
    refused = publish(refused_store, EDITED_BODY_DRAFT, form_check_result=CHECK_FAILS)

    assert refused.result[Result.STATUS] == Status.FAILED
    (request,) = refused.bridge.check_requests
    assert request["stored_record"]["metadata"]["base"] == STORED_BASE
    assert f"base: {DRAFT_BASE}" in request["draft_text"]
    assert writes(refused) == []
    assert refused_store.issues[SUBJECT_NUMBER].fields["Base"] == STORED_BASE

    passed_store = Store()
    seed_leaf(passed_store, Maturity.SLICED.value)
    passed = publish(passed_store, EDITED_BODY_DRAFT, form_check_result=CHECK_PASSES)

    assert passed.result[Result.STATUS] == Status.OK
    assert passed_store.issues[SUBJECT_NUMBER].fields["Base"] == DRAFT_BASE


def test_a_publish_writes_the_changed_parts_and_no_part_the_draft_leaves_unchanged() -> (
    None
):
    body_store = Store()
    seed_leaf(body_store, Maturity.PROPOSED.value)
    body_publish = publish(body_store, EDITED_BODY_DRAFT)

    assert body_publish.result[Result.STATUS] == Status.OK
    assert writes(body_publish) == [EventKind.EDIT, EventKind.FIELD]
    assert all("title" not in e.detail for e in body_store.events)

    metadata_store = Store()
    seed_leaf(metadata_store, Maturity.PROPOSED.value)
    seed_leaf(metadata_store, Maturity.PROPOSED.value, number=BLOCKER_NUMBER)
    metadata_publish = publish(metadata_store, METADATA_ONLY_DRAFT)

    assert metadata_publish.result[Result.STATUS] == Status.OK
    assert writes(metadata_publish) == [EventKind.EDIT, EventKind.BLOCKER_ADD]
    assert body_edits(metadata_publish) == []
    assert metadata_store.issues[SUBJECT_NUMBER].blockers == [BLOCKER_NUMBER]


def test_a_publish_stops_after_a_readback_that_differs_and_reports_what_it_wrote() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)
    store.dropped_fields = frozenset({"Base"})

    observed = publish(store, EDITED_BODY_DRAFT)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert script.Metadata.BASE.value in observed.result[Result.MISMATCH]
    assert len(observed.result[Result.WRITES]) == len(writes(observed))
    last_write = max(e.sequence for e in store.events if e.kind in WRITE_KINDS)
    last_read = max(e.sequence for e in store.events if e.kind == EventKind.READ)
    assert last_read > last_write


def test_a_body_publish_of_an_applicable_record_lowers_to_sliced_before_it_writes_the_body() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.APPLICABLE.value)

    observed = publish(store, EDITED_BODY_DRAFT, transition_result=TRANSITION_DONE)

    assert observed.result[Result.STATUS] == Status.OK
    (lower,) = observed.bridge.transitions
    assert lower["transition"] == script.Move.LOWER.value
    assert lower["target"] == Maturity.SLICED.value
    assert lower["lower_cause"] == script.LowerCause.APPLICABLE_PUBLISH.value
    order = [
        e.kind
        for e in store.events
        if e.kind in (EventKind.FORM_CHECK, EventKind.TRANSITION, EventKind.EDIT)
    ]
    assert order == [EventKind.FORM_CHECK, EventKind.TRANSITION, EventKind.EDIT]
    assert store.issues[SUBJECT_NUMBER].fields["Maturity"] == Maturity.SLICED.value
    assert EventKind.ASSIGNEE not in writes(observed)


def test_a_refused_lower_leaves_the_body_unwritten() -> None:
    store = Store()
    seed_leaf(store, Maturity.APPLICABLE.value)

    observed = publish(store, EDITED_BODY_DRAFT, transition_result=TRANSITION_REFUSED)

    assert observed.result[Result.STATUS] == Status.FAILED
    assert body_edits(observed) == []
    assert store.issues[SUBJECT_NUMBER].body == STORED_BODY


def test_a_metadata_publish_of_an_applicable_record_writes_no_body_and_keeps_its_maturity() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.APPLICABLE.value)
    seed_leaf(store, Maturity.PROPOSED.value, number=BLOCKER_NUMBER)

    observed = publish(store, METADATA_ONLY_DRAFT)

    assert observed.result[Result.STATUS] == Status.OK
    assert observed.bridge.transitions == []
    assert body_edits(observed) == []
    issue = store.issues[SUBJECT_NUMBER]
    assert issue.body == STORED_BODY
    assert issue.fields["Maturity"] == Maturity.APPLICABLE.value
    assert issue.fields["Base"] == STORED_BASE
