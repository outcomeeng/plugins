#!/usr/bin/env python3
"""Derive an officer-orchestration ledger from durable source records."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Final, TextIO

SCHEMA_VERSION: Final = 1
SCHEMA_VERSION_FIELD: Final = "schemaVersion"
CHANGE_FIELD: Final = "change"
MAIL_RECORDS_FIELD: Final = "mailRecords"
JOURNAL_RUNS_FIELD: Final = "journalRuns"
STATUS_FIELD: Final = "status"
DETAIL_FIELD: Final = "detail"
LEDGER_FIELD: Final = "ledger"
BODY_FIELD: Final = "body"
ID_FIELD: Final = "id"
RUN_TOKEN_FIELD: Final = "runToken"
PASS_FIELD: Final = "pass"
HEAD_FIELD: Final = "head"
VERDICT_FIELD: Final = "verdict"
DECISION_FIELD: Final = "decision"
FAILURE_FIELD: Final = "failure"
FINDING_PROVENANCE_FIELD: Final = "findingProvenance"
READ_FIELD: Final = "read"
SPEND_FIELD: Final = "spend"
WALL_TIME_SECONDS_FIELD: Final = "wallTimeSeconds"
RUNNING_SPEND_FIELD: Final = "runningSpend"
CURRENCY_FIELD: Final = "currency"
AMOUNT_FIELD: Final = "amount"
CAUSE_FIELD: Final = "cause"
SOURCE_KIND_FIELD: Final = "kind"
SOURCE_ID_FIELD: Final = "id"
SOURCE_FIELD: Final = "source"
VALUE_FIELD: Final = "value"
SUCCEEDED_STATUS: Final = "succeeded"
INVALID_INPUT_STATUS: Final = "invalid-input"
DERIVE_OPERATION: Final = "derive"
DERIVE_ARGUMENTS: Final = (DERIVE_OPERATION,)
SUCCESS_EXIT_CODE: Final = 0
INVALID_INPUT_EXIT_CODE: Final = 2
READ_CAUSES: Final = frozenset(
    {"message", "officer-state-change", "bound-crossed", "operator-cadence"}
)
MAIL_SOURCE_KIND: Final = "mail"
JOURNAL_SOURCE_KIND: Final = "journal"
MAIL_POSITION_LABEL: Final = "mail record"
JOURNAL_POSITION_LABEL: Final = "journal run"
PASSES_FIELD: Final = "passes"
HEADS_FIELD: Final = "heads"
VERDICTS_FIELD: Final = "verdicts"
DECISIONS_FIELD: Final = "decisions"
FAILURES_FIELD: Final = "failures"
READS_FIELD: Final = "reads"
# Every scalar ledger event field with the collection it contributes to. The
# derivation folds each event through this registry, so the pairing is declared
# once rather than repeated per event kind.
SCALAR_EVENT_COLLECTIONS: Final = (
    (PASS_FIELD, PASSES_FIELD),
    (HEAD_FIELD, HEADS_FIELD),
    (VERDICT_FIELD, VERDICTS_FIELD),
    (DECISION_FIELD, DECISIONS_FIELD),
    (FAILURE_FIELD, FAILURES_FIELD),
)
COLLECTION_FIELDS: Final = (
    *(collection for _, collection in SCALAR_EVENT_COLLECTIONS),
    FINDING_PROVENANCE_FIELD,
    READS_FIELD,
)


class LedgerInputError(ValueError):
    """Report a malformed ledger source without a traceback."""


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise LedgerInputError(f"{label} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise LedgerInputError(f"{label} keys must be strings")
    return {str(key): item for key, item in value.items()}


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise LedgerInputError(f"{label} must be an array")
    return value


def _source(kind: str, source_id: int | str) -> dict[str, object]:
    return {SOURCE_KIND_FIELD: kind, SOURCE_ID_FIELD: source_id}


def _mail_source(source_id: object, where: str) -> dict[str, object]:
    if isinstance(source_id, bool) or not isinstance(source_id, int):
        raise LedgerInputError(f"{where} source identity must be an integer")
    return _source(MAIL_SOURCE_KIND, source_id)


def _journal_run_token(run_token: object, where: str) -> str:
    if not isinstance(run_token, str) or not run_token:
        raise LedgerInputError(f"{where} runToken must be a non-empty string")
    return run_token


def _journal_source(run_token: str) -> dict[str, object]:
    return _source(JOURNAL_SOURCE_KIND, run_token)


def _append_entry(
    entries: list[dict[str, object]],
    value: object,
    source: Mapping[str, object],
) -> None:
    if value is None:
        return
    entry = {VALUE_FIELD: value, SOURCE_FIELD: dict(source)}
    if entry not in entries:
        entries.append(entry)


def _append_findings(
    findings: list[dict[str, object]],
    value: object,
    source: Mapping[str, object],
    where: str,
) -> None:
    if value is None:
        return
    for finding in _sequence(value, f"{where} findingProvenance"):
        finding_data = dict(_mapping(finding, f"{where} finding provenance entry"))
        entry: dict[str, object] = {
            VALUE_FIELD: finding_data,
            SOURCE_FIELD: dict(source),
        }
        if entry not in findings:
            findings.append(entry)


def _append_reads(
    reads: list[dict[str, object]],
    value: object,
    source: Mapping[str, object],
    where: str,
) -> None:
    if value is None:
        return
    values = value if isinstance(value, list) else [value]
    for item in values:
        read = dict(_mapping(item, f"{where} read"))
        cause = read.get(CAUSE_FIELD)
        if cause not in READ_CAUSES:
            allowed = ", ".join(sorted(READ_CAUSES))
            raise LedgerInputError(f"{where} read cause must be one of: {allowed}")
        entry: dict[str, object] = {VALUE_FIELD: read, SOURCE_FIELD: dict(source)}
        if entry not in reads:
            reads.append(entry)


def _add_spend(totals: dict[str, Decimal], value: object, where: str) -> None:
    if value is None:
        return
    spend = _mapping(value, f"{where} spend")
    currency = spend.get(CURRENCY_FIELD)
    amount = spend.get(AMOUNT_FIELD)
    if not isinstance(currency, str) or not currency:
        raise LedgerInputError(f"{where} spend currency must be a non-empty string")
    if isinstance(amount, bool) or not isinstance(amount, (int, float, str)):
        raise LedgerInputError(f"{where} spend amount must be numeric")
    try:
        decimal_amount = Decimal(str(amount))
    except InvalidOperation as error:
        raise LedgerInputError(f"{where} spend amount must be numeric") from error
    if not decimal_amount.is_finite():
        raise LedgerInputError(f"{where} spend amount must be finite")
    totals[currency] = totals.get(currency, Decimal()) + decimal_amount


def _wall_time(value: object, where: str) -> Decimal:
    if value is None:
        return Decimal()
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise LedgerInputError(f"{where} wallTimeSeconds must be numeric")
    try:
        duration = Decimal(str(value))
    except InvalidOperation as error:
        raise LedgerInputError(f"{where} wallTimeSeconds must be numeric") from error
    if not duration.is_finite() or duration < 0:
        raise LedgerInputError(
            f"{where} wallTimeSeconds must be finite and non-negative"
        )
    return duration


def _json_number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    if value == integral:
        return int(integral)
    return float(value)


def _event_from_record(
    record: Mapping[str, object],
    where: str,
) -> Mapping[str, object] | None:
    body = record.get(BODY_FIELD)
    if not isinstance(body, str):
        raise LedgerInputError(f"{where} body must be a string")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping) or LEDGER_FIELD not in payload:
        return None
    return _mapping(payload[LEDGER_FIELD], f"{where} ledger event")


def _absorb(
    collected: dict[str, list[dict[str, object]]],
    spend_totals: dict[str, Decimal],
    event: Mapping[str, object],
    source: Mapping[str, object],
    where: str,
) -> Decimal:
    """Fold one event into the collected entries and report its wall time."""
    for event_field, collection in SCALAR_EVENT_COLLECTIONS:
        _append_entry(collected[collection], event.get(event_field), source)
    _append_findings(
        collected[FINDING_PROVENANCE_FIELD],
        event.get(FINDING_PROVENANCE_FIELD),
        source,
        where,
    )
    _append_reads(collected[READS_FIELD], event.get(READ_FIELD), source, where)
    _add_spend(spend_totals, event.get(SPEND_FIELD), where)
    return _wall_time(event.get(WALL_TIME_SECONDS_FIELD), where)


def derive_ledger(payload: Mapping[str, object]) -> dict[str, object]:
    """Return one deterministic ledger derived from mail and journal sources."""
    if payload.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise LedgerInputError(f"schemaVersion must be {SCHEMA_VERSION}")
    change = payload.get(CHANGE_FIELD)
    if not isinstance(change, str) or not change:
        raise LedgerInputError("change must be a non-empty string")

    collected: dict[str, list[dict[str, object]]] = {
        collection: [] for collection in COLLECTION_FIELDS
    }
    spend_totals: dict[str, Decimal] = {}
    wall_time = Decimal()

    mail_records = _sequence(payload.get(MAIL_RECORDS_FIELD), MAIL_RECORDS_FIELD)
    for index, raw_record in enumerate(mail_records):
        where = f"{MAIL_POSITION_LABEL} {index}"
        record = _mapping(raw_record, where)
        source = _mail_source(record.get(ID_FIELD), where)
        event = _event_from_record(record, where)
        if event is None:
            continue
        wall_time += _absorb(collected, spend_totals, event, source, where)

    journal_runs = _sequence(payload.get(JOURNAL_RUNS_FIELD), JOURNAL_RUNS_FIELD)
    seen_run_tokens: set[str] = set()
    for index, raw_run in enumerate(journal_runs):
        where = f"{JOURNAL_POSITION_LABEL} {index}"
        run = _mapping(raw_run, where)
        run_token = _journal_run_token(run.get(RUN_TOKEN_FIELD), where)
        if run_token in seen_run_tokens:
            continue
        seen_run_tokens.add(run_token)
        source = _journal_source(run_token)
        wall_time += _absorb(collected, spend_totals, run, source, where)

    ledger = {
        CHANGE_FIELD: change,
        **collected,
        RUNNING_SPEND_FIELD: {
            currency: _json_number(amount)
            for currency, amount in sorted(spend_totals.items())
        },
        WALL_TIME_SECONDS_FIELD: _json_number(wall_time),
    }
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: SUCCEEDED_STATUS,
        LEDGER_FIELD: ledger,
    }


def _reject(output_stream: TextIO, detail: str) -> int:
    """Write the versioned invalid-input result and report its exit code."""
    result = {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        STATUS_FIELD: INVALID_INPUT_STATUS,
        DETAIL_FIELD: detail,
    }
    json.dump(result, output_stream, sort_keys=True)
    output_stream.write("\n")
    return INVALID_INPUT_EXIT_CODE


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Run the versioned ledger derivation entry point."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    input_stream = sys.stdin if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout

    if arguments != list(DERIVE_ARGUMENTS):
        # Every rejection writes the same versioned result on stdout, so a
        # caller parsing the documented contract survives an argument mistake.
        return _reject(
            output_stream,
            f"arguments must be exactly {' '.join(DERIVE_ARGUMENTS)!r}; "
            f"received {' '.join(arguments)!r}.",
        )

    try:
        raw_payload = json.load(input_stream)
        result = derive_ledger(_mapping(raw_payload, "input"))
    except (json.JSONDecodeError, LedgerInputError) as error:
        return _reject(output_stream, str(error))

    json.dump(result, output_stream, sort_keys=True)
    output_stream.write("\n")
    return SUCCESS_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
