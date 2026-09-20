"""Reachability evidence for the officer-ledger derivation entry point."""

import json
from typing import cast

from outcomeeng_testing.harnesses.officer_orchestration import (
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

    assert observation.parameters == ("argv", "stdin", "stdout", "stderr")
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


def test_entrypoint_preserves_decision_reasoning_and_operator_contact_failures() -> None:
    """Durable mail facts rebuild both required orchestration ledger classes."""
    source = load_ledger_module()
    decision = {
        "class": "two-round-ceiling",
        "choice": "stop",
        "reasoning": "No bounded repair remains.",
    }
    failure = {
        "kind": "operator-interaction",
        "detail": "The officer reported a direct operator answer.",
    }
    message_id = 1062
    observation = run_ledger(
        [source.DERIVE_OPERATION],
        {
            source.SCHEMA_VERSION_FIELD: source.SCHEMA_VERSION,
            source.CHANGE_FIELD: "owner/changes#123",
            source.MAIL_RECORDS_FIELD: [
                {
                    "id": message_id,
                    "body": json.dumps(
                        {
                            source.LEDGER_FIELD: {
                                source.DECISION_FIELD: decision,
                                source.FAILURE_FIELD: failure,
                            }
                        }
                    ),
                }
            ],
            source.JOURNAL_RUNS_FIELD: [],
        },
    )
    ledger = cast(dict[str, object], observation.result[source.LEDGER_FIELD])
    provenance = {"kind": "mail", "id": message_id}

    assert observation.exit_code == source.SUCCESS_EXIT_CODE
    assert ledger[source.DECISIONS_FIELD] == [
        {"value": decision, "source": provenance}
    ]
    assert ledger[source.FAILURES_FIELD] == [
        {"value": failure, "source": provenance}
    ]


def test_entrypoint_rejects_schema_version_two() -> None:
    """The shipped entry point rejects the declared unsupported schema case."""
    source = load_ledger_module()
    observation = run_ledger(
        [source.DERIVE_OPERATION],
        {
            source.SCHEMA_VERSION_FIELD: source.SCHEMA_VERSION + 1,
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
