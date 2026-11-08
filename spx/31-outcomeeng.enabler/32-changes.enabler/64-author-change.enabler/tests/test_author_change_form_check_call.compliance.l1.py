"""Compliance evidence: the script's call of the form check.

Each rule is a spec assertion about how the author-change script calls the form
check of the change-standards skill. The violating case of a rule is the input
that would tempt a script to break it: a form check that fails, a sibling skill
that is absent. The conforming case beside it shows the call completes when
nothing violates the rule.

The controlled Change store and the stand-in for the form check come from the
``author_change`` harness. The stand-in records each request it receives with
the number of store writes and the entries of the checkout root at that moment,
so the tests judge the request and the order of the script's writes.
"""

from __future__ import annotations

from collections.abc import Mapping

from outcomeeng_testing.harnesses.author_change import (
    ALTERNATE_SIZE_LIMIT,
    BLOCKER_NUMBER,
    CHECK_FAILS,
    CHECK_PASSES,
    FIXTURES,
    STORE_IDENTITY,
    SUBJECT_NUMBER,
    WRITE_KINDS,
    EventKind,
    Observation,
    Store,
    Stub,
    load_script,
    request_for,
    run_script,
    seed_leaf,
)

script = load_script()
Request = script.RequestField
CheckRequest = script.CheckRequestField
Result = script.ResultField
Status = script.Status
Maturity = script.Maturity
Operation = script.Operation
Metadata = script.Metadata
Record = script.RecordField

EDITED_BODY_DRAFT = FIXTURES / "draft-leaf-edited-body.md"
METADATA_ONLY_DRAFT = FIXTURES / "draft-leaf-metadata-only.md"
NEW_LEAF_DRAFT = FIXTURES / "draft-leaf-new.md"
STORED_BODY = (FIXTURES / "stored-leaf-body.md").read_text()


def publish(
    store: Store,
    draft: object,
    *,
    size_limit: int | None = None,
    form_check_result: Mapping[str, object] | None = None,
    with_form_check: bool = True,
) -> Observation:
    fields: dict[object, object] = {
        Request.NUMBER: SUBJECT_NUMBER,
        Request.DRAFT_PATH: str(draft),
    }
    if size_limit is not None:
        fields[Request.SIZE_LIMIT] = size_limit
    return run_script(
        request_for(Operation.PUBLISH, fields),  # type: ignore[arg-type]
        store,
        form_check_result=form_check_result,
        with_form_check=with_form_check,
    )


def record(
    store: Store,
    *,
    form_check_result: Mapping[str, object] | None = None,
) -> Observation:
    return run_script(
        request_for(Operation.RECORD, {Request.DRAFT_PATH: str(NEW_LEAF_DRAFT)}),
        store,
        form_check_result=form_check_result,
    )


def writes(observation: Observation) -> list[EventKind]:
    return [
        event.kind for event in observation.store.events if event.kind in WRITE_KINDS
    ]


def test_one_check_request_names_the_draft_the_root_the_operation_both_records_and_the_limit() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.SLICED.value)
    blocker = seed_leaf(
        store,
        Maturity.PROPOSED.value,
        number=BLOCKER_NUMBER,
        title="Blocking change",
    )

    observed = publish(store, METADATA_ONLY_DRAFT, size_limit=ALTERNATE_SIZE_LIMIT)

    assert observed.result[Result.STATUS] == Status.OK
    (request,) = observed.bridge.check_requests
    assert set(request) == {member.value for member in CheckRequest}
    assert request[CheckRequest.DRAFT_TEXT] == METADATA_ONLY_DRAFT.read_text()
    assert request[CheckRequest.CHECKOUT_ROOT] == str(observed.bridge.checkout_root)
    assert request[CheckRequest.OPERATION] == script.FormCheckOperation.PUBLISH.value
    stored = request[CheckRequest.STORED_RECORD]
    assert stored[Record.BODY] == STORED_BODY
    assert stored[Record.METADATA][Metadata.MATURITY.value] == Maturity.SLICED.value
    blockers = request[CheckRequest.BLOCKER_RECORDS]
    assert list(blockers) == [f"{STORE_IDENTITY}#{BLOCKER_NUMBER}"]
    (blocker_record,) = blockers.values()
    assert blocker_record[Record.BODY] == blocker.body
    assert request[CheckRequest.SIZE_LIMIT] == ALTERNATE_SIZE_LIMIT


def test_the_check_request_of_a_record_holds_no_stored_record() -> None:
    store = Store()

    observed = record(store)

    (request,) = observed.bridge.check_requests
    assert request[CheckRequest.OPERATION] == script.FormCheckOperation.RECORD.value
    assert request[CheckRequest.STORED_RECORD] is None
    assert request[CheckRequest.BLOCKER_RECORDS] == {}


def test_the_script_publishes_only_on_a_pass_and_reads_one_result_per_request() -> None:
    passing_store = Store()
    seed_leaf(passing_store, Maturity.PROPOSED.value)
    passed = publish(passing_store, EDITED_BODY_DRAFT, form_check_result=CHECK_PASSES)

    assert passed.result[Result.STATUS] == Status.OK
    assert len(passed.bridge.check_requests) == 1
    assert EventKind.EDIT in writes(passed)

    failing_store = Store()
    seed_leaf(failing_store, Maturity.PROPOSED.value)
    failed = publish(failing_store, EDITED_BODY_DRAFT, form_check_result=CHECK_FAILS)

    assert failed.result[Result.STATUS] == Status.FAILED
    assert failed.result[Result.FINDINGS] == CHECK_FAILS["findings"]
    assert writes(failed) == []

    recording_store = Store()
    recorded = record(recording_store, form_check_result=CHECK_FAILS)

    assert recorded.result[Result.STATUS] == Status.FAILED
    assert writes(recorded) == []


def test_the_script_reaches_the_check_function_of_the_sibling_skill_by_import_alone() -> (
    None
):
    store = Store()
    seed_leaf(store, Maturity.PROPOSED.value)

    observed = publish(store, EDITED_BODY_DRAFT)

    assert len(observed.bridge.check_requests) == 1
    assert all(
        call[0] in (script_program for script_program in ("gh", "git"))
        for call in observed.calls
    )

    absent_store = Store()
    seed_leaf(absent_store, Maturity.PROPOSED.value)
    absent = publish(absent_store, EDITED_BODY_DRAFT, with_form_check=False)

    assert absent.result[Result.STATUS] == Status.BLOCKED
    assert Stub.FORM_CHECK_SKILL in absent.result[Result.DETAIL]
    assert writes(absent) == []


def test_the_call_of_the_check_writes_no_file_and_no_store_and_every_write_follows_it() -> (
    None
):
    publish_store = Store()
    seed_leaf(publish_store, Maturity.PROPOSED.value)

    published = publish(publish_store, EDITED_BODY_DRAFT)

    record_store = Store()
    recorded = record(record_store)

    for observed in (published, recorded):
        assert observed.result[Result.STATUS] == Status.OK
        assert observed.bridge.check_writes_before == [0]
        assert observed.bridge.check_roots_before == [()]
        assert observed.checkout_entries_after == ()

    refused_store = Store()
    seed_leaf(refused_store, Maturity.PROPOSED.value)
    refused = publish(refused_store, EDITED_BODY_DRAFT, form_check_result=CHECK_FAILS)

    assert writes(refused) == []
    assert refused.checkout_entries_after == ()
