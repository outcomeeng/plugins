#!/usr/bin/env python3
"""Derive an officer-orchestration ledger from durable source records."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any, TextIO

SCHEMA_VERSION = 1
DERIVE_OPERATION = "derive"
READ_CAUSES = frozenset(
    {"message", "officer-state-change", "bound-crossed", "operator-cadence"}
)
LEDGER_KEYS = (
    "change",
    "passes",
    "heads",
    "verdicts",
    "findingProvenance",
    "reads",
    "runningSpend",
    "wallTimeSeconds",
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
    return {"kind": kind, "id": source_id}


def _append_entry(
    entries: list[dict[str, object]],
    value: object,
    source: Mapping[str, str],
) -> None:
    if value is None:
        return
    entry = {"value": value, "source": dict(source)}
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
        entry = {"value": finding_data, "source": dict(source)}
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
        cause = read.get("cause")
        if cause not in READ_CAUSES:
            allowed = ", ".join(sorted(READ_CAUSES))
            raise LedgerInputError(f"read cause must be one of: {allowed}")
        entry = {"value": read, "source": dict(source)}
        if entry not in reads:
            reads.append(entry)


def _add_spend(totals: dict[str, Decimal], value: object) -> None:
    if value is None:
        return
    spend = _mapping(value, "spend")
    currency = spend.get("currency")
    amount = spend.get("amount")
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
    body = record.get("body")
    if not isinstance(body, str):
        raise LedgerInputError("mail record body must be a string")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping) or "ledger" not in payload:
        return None
    return _mapping(payload["ledger"], "mail ledger event")


def derive_ledger(payload: Mapping[str, Any]) -> dict[str, object]:
    """Return one deterministic ledger derived from mail and journal sources."""
    if payload.get("schemaVersion") != SCHEMA_VERSION:
        raise LedgerInputError(f"schemaVersion must be {SCHEMA_VERSION}")
    change = payload.get("change")
    if not isinstance(change, str) or not change:
        raise LedgerInputError("change must be a non-empty string")

    passes: list[dict[str, object]] = []
    heads: list[dict[str, object]] = []
    verdicts: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    reads: list[dict[str, object]] = []
    spend_totals: dict[str, Decimal] = {}
    wall_time = Decimal()

    mail_records = _sequence(payload.get("mailRecords"), "mailRecords")
    for raw_record in mail_records:
        record = _mapping(raw_record, "mail record")
        source = _source("mail", record.get("id"))
        event = _event_from_record(record)
        if event is None:
            continue
        _append_entry(passes, event.get("pass"), source)
        _append_entry(heads, event.get("head"), source)
        _append_entry(verdicts, event.get("verdict"), source)
        _append_findings(findings, event.get("findingProvenance"), source)
        _append_reads(reads, event.get("read"), source)
        _add_spend(spend_totals, event.get("spend"))
        wall_time += _wall_time(event.get("wallTimeSeconds"))

    journal_runs = _sequence(payload.get("journalRuns"), "journalRuns")
    for raw_run in journal_runs:
        run = _mapping(raw_run, "journal run")
        source = _source("journal", run.get("runId"))
        _append_entry(passes, run.get("pass"), source)
        _append_entry(heads, run.get("head"), source)
        _append_entry(verdicts, run.get("verdict"), source)
        _append_findings(findings, run.get("findingProvenance"), source)
        _append_reads(reads, run.get("read"), source)
        _add_spend(spend_totals, run.get("spend"))
        wall_time += _wall_time(run.get("wallTimeSeconds"))

    ledger = {
        "change": change,
        "passes": passes,
        "heads": heads,
        "verdicts": verdicts,
        "findingProvenance": findings,
        "reads": reads,
        "runningSpend": {
            currency: _json_number(amount)
            for currency, amount in sorted(spend_totals.items())
        },
        "wallTimeSeconds": _json_number(wall_time),
    }
    return {"schemaVersion": SCHEMA_VERSION, "status": "succeeded", "ledger": ledger}


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

    if arguments != [DERIVE_OPERATION]:
        print(f"usage: derive_ledger.py {DERIVE_OPERATION}", file=error_stream)
        return 2

    try:
        raw_payload = json.load(input_stream)
        result = derive_ledger(_mapping(raw_payload, "input"))
    except (json.JSONDecodeError, LedgerInputError) as error:
        result = {
            "schemaVersion": SCHEMA_VERSION,
            "status": "invalid-input",
            "detail": str(error),
        }
        json.dump(result, output_stream, sort_keys=True)
        output_stream.write("\n")
        return 2

    json.dump(result, output_stream, sort_keys=True)
    output_stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
