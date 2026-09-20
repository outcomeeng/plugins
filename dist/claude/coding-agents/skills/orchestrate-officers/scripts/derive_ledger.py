#!/usr/bin/env python3
"""Derive an officer-orchestration ledger from durable source records."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any, Final, TextIO

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
RUN_ID_FIELD: Final = "runId"
PASS_FIELD: Final = "pass"
HEAD_FIELD: Final = "head"
VERDICT_FIELD: Final = "verdict"
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
EMPTY_SOURCE_SAMPLE_CHANGE: Final = "owner/changes#123"
ENTRYPOINT_PARAMETER_NAMES: Final = ("argv", "stdin", "stdout", "stderr")
RESULT_FIELDS: Final = (SCHEMA_VERSION_FIELD, STATUS_FIELD, LEDGER_FIELD)
READ_CAUSES: Final = frozenset(
    {"message", "officer-state-change", "bound-crossed", "operator-cadence"}
)
PASSES_FIELD: Final = "passes"
HEADS_FIELD: Final = "heads"
VERDICTS_FIELD: Final = "verdicts"
READS_FIELD: Final = "reads"
LEDGER_FIELDS: Final = (
    CHANGE_FIELD,
    PASSES_FIELD,
    HEADS_FIELD,
    VERDICTS_FIELD,
    FINDING_PROVENANCE_FIELD,
    READS_FIELD,
    RUNNING_SPEND_FIELD,
    WALL_TIME_SECONDS_FIELD,
)
EMPTY_LEDGER_SEQUENCE_FIELDS: Final = (
    PASSES_FIELD,
    HEADS_FIELD,
    VERDICTS_FIELD,
    FINDING_PROVENANCE_FIELD,
    READS_FIELD,
)


class LedgerInputError(ValueError):
    """Report a malformed ledger source without a traceback."""


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LedgerInputError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise LedgerInputError(f"{label} must be an array")
    return value


def _source(kind: str, source_id: object) -> dict[str, str]:
    if not isinstance(source_id, str) or not source_id:
        raise LedgerInputError(f"{kind} source identity must be a non-empty string")
    return {SOURCE_KIND_FIELD: kind, SOURCE_ID_FIELD: source_id}


def _append_entry(
    entries: list[dict[str, object]],
    value: object,
    source: Mapping[str, str],
) -> None:
    if value is None:
        return
    entry = {VALUE_FIELD: value, SOURCE_FIELD: dict(source)}
    if entry not in entries:
        entries.append(entry)


def _append_findings(
    findings: list[dict[str, object]],
    value: object,
    source: Mapping[str, str],
) -> None:
    if value is None:
        return
    for finding in _sequence(value, "findingProvenance"):
        finding_data = dict(_mapping(finding, "finding provenance entry"))
        entry: dict[str, object] = {
            VALUE_FIELD: finding_data,
            SOURCE_FIELD: dict(source),
        }
        if entry not in findings:
            findings.append(entry)


def _append_reads(
    reads: list[dict[str, object]],
    value: object,
    source: Mapping[str, str],
) -> None:
    if value is None:
        return
    values = value if isinstance(value, list) else [value]
    for item in values:
        read = dict(_mapping(item, "read"))
        cause = read.get(CAUSE_FIELD)
        if cause not in READ_CAUSES:
            allowed = ", ".join(sorted(READ_CAUSES))
            raise LedgerInputError(f"read cause must be one of: {allowed}")
        entry: dict[str, object] = {VALUE_FIELD: read, SOURCE_FIELD: dict(source)}
        if entry not in reads:
            reads.append(entry)


def _add_spend(totals: dict[str, Decimal], value: object) -> None:
    if value is None:
        return
    spend = _mapping(value, "spend")
    currency = spend.get(CURRENCY_FIELD)
    amount = spend.get(AMOUNT_FIELD)
    if not isinstance(currency, str) or not currency:
        raise LedgerInputError("spend currency must be a non-empty string")
    if isinstance(amount, bool) or not isinstance(amount, (int, float, str)):
        raise LedgerInputError("spend amount must be numeric")
    try:
        decimal_amount = Decimal(str(amount))
    except InvalidOperation as error:
        raise LedgerInputError("spend amount must be numeric") from error
    if not decimal_amount.is_finite():
        raise LedgerInputError("spend amount must be finite")
    totals[currency] = totals.get(currency, Decimal()) + decimal_amount


def _wall_time(value: object) -> Decimal:
    if value is None:
        return Decimal()
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise LedgerInputError("wallTimeSeconds must be numeric")
    try:
        duration = Decimal(str(value))
    except InvalidOperation as error:
        raise LedgerInputError("wallTimeSeconds must be numeric") from error
    if not duration.is_finite() or duration < 0:
        raise LedgerInputError("wallTimeSeconds must be finite and non-negative")
    return duration


def _json_number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    if value == integral:
        return int(integral)
    return float(value)


def _event_from_record(record: Mapping[str, Any]) -> Mapping[str, Any] | None:
    body = record.get(BODY_FIELD)
    if not isinstance(body, str):
        raise LedgerInputError("mail record body must be a string")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping) or LEDGER_FIELD not in payload:
        return None
    return _mapping(payload[LEDGER_FIELD], "mail ledger event")


def empty_source_request() -> dict[str, object]:
    """Return the documented empty-source request for one named Change."""
    return {
        SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
        CHANGE_FIELD: EMPTY_SOURCE_SAMPLE_CHANGE,
        MAIL_RECORDS_FIELD: [],
        JOURNAL_RUNS_FIELD: [],
    }


def derive_ledger(payload: Mapping[str, Any]) -> dict[str, object]:
    """Return one deterministic ledger derived from mail and journal sources."""
    if payload.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        raise LedgerInputError(f"schemaVersion must be {SCHEMA_VERSION}")
    change = payload.get(CHANGE_FIELD)
    if not isinstance(change, str) or not change:
        raise LedgerInputError("change must be a non-empty string")

    passes: list[dict[str, object]] = []
    heads: list[dict[str, object]] = []
    verdicts: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    reads: list[dict[str, object]] = []
    spend_totals: dict[str, Decimal] = {}
    wall_time = Decimal()

    mail_records = _sequence(payload.get(MAIL_RECORDS_FIELD), MAIL_RECORDS_FIELD)
    for raw_record in mail_records:
        record = _mapping(raw_record, "mail record")
        source = _source("mail", record.get(ID_FIELD))
        event = _event_from_record(record)
        if event is None:
            continue
        _append_entry(passes, event.get(PASS_FIELD), source)
        _append_entry(heads, event.get(HEAD_FIELD), source)
        _append_entry(verdicts, event.get(VERDICT_FIELD), source)
        _append_findings(findings, event.get(FINDING_PROVENANCE_FIELD), source)
        _append_reads(reads, event.get(READ_FIELD), source)
        _add_spend(spend_totals, event.get(SPEND_FIELD))
        wall_time += _wall_time(event.get(WALL_TIME_SECONDS_FIELD))

    journal_runs = _sequence(payload.get(JOURNAL_RUNS_FIELD), JOURNAL_RUNS_FIELD)
    for raw_run in journal_runs:
        run = _mapping(raw_run, "journal run")
        source = _source("journal", run.get(RUN_ID_FIELD))
        _append_entry(passes, run.get(PASS_FIELD), source)
        _append_entry(heads, run.get(HEAD_FIELD), source)
        _append_entry(verdicts, run.get(VERDICT_FIELD), source)
        _append_findings(findings, run.get(FINDING_PROVENANCE_FIELD), source)
        _append_reads(reads, run.get(READ_FIELD), source)
        _add_spend(spend_totals, run.get(SPEND_FIELD))
        wall_time += _wall_time(run.get(WALL_TIME_SECONDS_FIELD))

    ledger = {
        CHANGE_FIELD: change,
        PASSES_FIELD: passes,
        HEADS_FIELD: heads,
        VERDICTS_FIELD: verdicts,
        FINDING_PROVENANCE_FIELD: findings,
        READS_FIELD: reads,
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


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the versioned ledger derivation entry point."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    input_stream = sys.stdin if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr

    if arguments != list(DERIVE_ARGUMENTS):
        print(f"usage: derive_ledger.py {DERIVE_OPERATION}", file=error_stream)
        return INVALID_INPUT_EXIT_CODE

    try:
        raw_payload = json.load(input_stream)
        result = derive_ledger(_mapping(raw_payload, "input"))
    except (json.JSONDecodeError, LedgerInputError) as error:
        result = {
            SCHEMA_VERSION_FIELD: SCHEMA_VERSION,
            STATUS_FIELD: INVALID_INPUT_STATUS,
            DETAIL_FIELD: str(error),
        }
        json.dump(result, output_stream, sort_keys=True)
        output_stream.write("\n")
        return INVALID_INPUT_EXIT_CODE

    json.dump(result, output_stream, sort_keys=True)
    output_stream.write("\n")
    return SUCCESS_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
