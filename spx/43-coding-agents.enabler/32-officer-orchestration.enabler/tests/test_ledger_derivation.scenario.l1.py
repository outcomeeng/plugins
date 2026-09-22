"""Reachability and populated-derivation evidence for the officer ledger."""

from typing import cast

from outcomeeng_testing.harnesses.officer_orchestration import (
    derive,
    event_record,
    load_ledger_module,
    run_ledger,
)


def test_entrypoint_returns_the_minimum_versioned_ledger() -> None:
    """The shipped entry point is executable and pins its minimum result shape."""
    source = load_ledger_module()
    observation = run_ledger(
        [source.DERIVE_OPERATION],
        {
            source.SCHEMA_VERSION_FIELD: source.SCHEMA_VERSION,
            source.CHANGE_FIELD: "owner/changes#123",
            source.MAIL_RECORDS_FIELD: [],
            source.JOURNAL_RUNS_FIELD: [],
        },
    )
    result = observation.result
    ledger = cast(dict[str, object], result[source.LEDGER_FIELD])

    assert observation.exit_code == source.SUCCESS_EXIT_CODE
    assert observation.stderr == ""
    assert set(result) == {
        source.LEDGER_FIELD,
        source.SCHEMA_VERSION_FIELD,
        source.STATUS_FIELD,
    }
    assert result[source.SCHEMA_VERSION_FIELD] == source.SCHEMA_VERSION
    assert result[source.STATUS_FIELD] == source.SUCCEEDED_STATUS
    assert set(ledger) == {
        source.CHANGE_FIELD,
        source.DECISIONS_FIELD,
        source.FAILURES_FIELD,
        source.FINDING_PROVENANCE_FIELD,
        source.HEADS_FIELD,
        source.PASSES_FIELD,
        source.READS_FIELD,
        source.RUNNING_SPEND_FIELD,
        source.VERDICTS_FIELD,
        source.WALL_TIME_SECONDS_FIELD,
    }
    assert ledger[source.CHANGE_FIELD] == "owner/changes#123"
    assert ledger[source.PASSES_FIELD] == []
    assert ledger[source.HEADS_FIELD] == []
    assert ledger[source.VERDICTS_FIELD] == []
    assert ledger[source.DECISIONS_FIELD] == []
    assert ledger[source.FAILURES_FIELD] == []
    assert ledger[source.FINDING_PROVENANCE_FIELD] == []
    assert ledger[source.READS_FIELD] == []
    assert ledger[source.RUNNING_SPEND_FIELD] == {}
    assert ledger[source.WALL_TIME_SECONDS_FIELD] == 0


def test_one_ledger_body_populates_every_collection_with_its_provenance() -> None:
    """One record carrying every declared event field lands in the ledger.

    The read's cause comes from the entry point's declared cause set rather than
    a literal; this scenario exercises recording, while the complete cause
    domain is the mapping evidence's subject.
    """
    source = load_ledger_module()
    read = {source.CAUSE_FIELD: min(source.READ_CAUSES), "messageId": 41}
    finding = {"rule": "source-ownership", "disposition": "filed"}
    decision = {
        "class": "two-round-ceiling",
        "choice": "track",
        "reasoning": "the branch carries the findings and the next Activity resumes",
    }
    event = {
        source.PASS_FIELD: "round-2",
        source.HEAD_FIELD: "ecf41380c089203f6248a29ad8284bf8df4cd74a",
        source.VERDICT_FIELD: "REJECT",
        source.DECISION_FIELD: decision,
        source.FAILURE_FIELD: "an operator instruction named the officer session",
        source.FINDING_PROVENANCE_FIELD: [finding],
        source.READ_FIELD: read,
        source.SPEND_FIELD: {
            source.CURRENCY_FIELD: "USD",
            source.AMOUNT_FIELD: "12.50",
        },
        source.WALL_TIME_SECONDS_FIELD: "93.5",
    }
    observation = derive(
        source,
        "owner/changes#123",
        mail_records=[event_record(source, 41, event)],
    )
    ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])
    provenance = {
        source.SOURCE_KIND_FIELD: source.MAIL_SOURCE_KIND,
        source.SOURCE_ID_FIELD: 41,
    }

    assert observation.exit_code == source.SUCCESS_EXIT_CODE
    assert observation.stderr == ""
    assert ledger[source.PASSES_FIELD] == [
        {source.VALUE_FIELD: event[source.PASS_FIELD], source.SOURCE_FIELD: provenance}
    ]
    assert ledger[source.HEADS_FIELD] == [
        {source.VALUE_FIELD: event[source.HEAD_FIELD], source.SOURCE_FIELD: provenance}
    ]
    assert ledger[source.VERDICTS_FIELD] == [
        {
            source.VALUE_FIELD: event[source.VERDICT_FIELD],
            source.SOURCE_FIELD: provenance,
        }
    ]
    assert ledger[source.DECISIONS_FIELD] == [
        {source.VALUE_FIELD: decision, source.SOURCE_FIELD: provenance}
    ]
    assert ledger[source.FAILURES_FIELD] == [
        {
            source.VALUE_FIELD: event[source.FAILURE_FIELD],
            source.SOURCE_FIELD: provenance,
        }
    ]
    assert ledger[source.FINDING_PROVENANCE_FIELD] == [
        {source.VALUE_FIELD: finding, source.SOURCE_FIELD: provenance}
    ]
    assert ledger[source.READS_FIELD] == [
        {source.VALUE_FIELD: read, source.SOURCE_FIELD: provenance}
    ]
    assert ledger[source.RUNNING_SPEND_FIELD] == {"USD": 12.5}
    assert ledger[source.WALL_TIME_SECONDS_FIELD] == 93.5


def test_entrypoint_rejects_schema_version_two() -> None:
    """The shipped entry point rejects the declared unsupported schema case."""
    source = load_ledger_module()
    observation = run_ledger(
        [source.DERIVE_OPERATION],
        {
            source.SCHEMA_VERSION_FIELD: 2,
            source.CHANGE_FIELD: "owner/changes#123",
            source.MAIL_RECORDS_FIELD: [],
            source.JOURNAL_RUNS_FIELD: [],
        },
    )
    detail = cast(str, observation.result[source.DETAIL_FIELD])

    assert observation.exit_code == source.INVALID_INPUT_EXIT_CODE
    assert observation.stderr == ""
    assert set(observation.result) == {
        source.DETAIL_FIELD,
        source.SCHEMA_VERSION_FIELD,
        source.STATUS_FIELD,
    }
    assert observation.result[source.SCHEMA_VERSION_FIELD] == source.SCHEMA_VERSION
    assert observation.result[source.STATUS_FIELD] == source.INVALID_INPUT_STATUS
    assert source.SCHEMA_VERSION_FIELD in detail
    assert str(source.SCHEMA_VERSION) in detail


def test_entrypoint_rejects_malformed_json() -> None:
    """The shipped entry point converts malformed stdin into a stable result."""
    source = load_ledger_module()
    observation = run_ledger([source.DERIVE_OPERATION], "{")

    assert observation.exit_code == source.INVALID_INPUT_EXIT_CODE
    assert observation.stderr == ""
    assert set(observation.result) == {
        source.DETAIL_FIELD,
        source.SCHEMA_VERSION_FIELD,
        source.STATUS_FIELD,
    }
    assert observation.result[source.SCHEMA_VERSION_FIELD] == source.SCHEMA_VERSION
    assert observation.result[source.STATUS_FIELD] == source.INVALID_INPUT_STATUS
    assert cast(str, observation.result[source.DETAIL_FIELD])
