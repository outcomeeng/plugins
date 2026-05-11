"""Scenario tests for the history.jsonl append-only writer.

Each suite run appends one row capturing the suite verdict and aggregate
metrics. The file is the durable trend record; runs/ holds the full
transcripts and is gitignored.
"""

from __future__ import annotations

import json
from pathlib import Path

from outcomeeng_evals.history import HISTORY_ROW_FIELDS, append_history_row


SCHEMA_VERSION = "1"
GIT_SHA = "9999af8"
TIMESTAMP = "2026-05-11T15:48:00Z"
TRANSCRIPT_REL = "runs/2026-05-11T15-48-00Z.json"


def _passing_row() -> dict[str, object]:
    return {
        "timestamp": TIMESTAMP,
        "schema_version": SCHEMA_VERSION,
        "git_sha": GIT_SHA,
        "passed": True,
        "pass_rate": 1.0,
        "cases_total": 4,
        "cases_passed": 4,
        "total_cost_usd": 1.04,
        "total_duration_ms": 18960.0,
        "transcript": TRANSCRIPT_REL,
    }


def _failing_row() -> dict[str, object]:
    row = _passing_row()
    row["passed"] = False
    row["pass_rate"] = 0.75
    row["cases_passed"] = 3
    row["timestamp"] = "2026-05-12T09:00:00Z"
    row["transcript"] = "runs/2026-05-12T09-00-00Z.json"
    return row


def _read_history(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def test_creates_history_file_when_missing(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    assert not history_path.exists()

    append_history_row(history_path, _passing_row())

    assert history_path.exists()


def test_appends_row_to_existing_history(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _passing_row())
    append_history_row(history_path, _failing_row())

    rows = _read_history(history_path)
    assert len(rows) == 2
    assert rows[0]["passed"] is True
    assert rows[1]["passed"] is False


def test_preserves_pre_existing_rows(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    pre_existing = '{"manual":"row"}\n'
    history_path.write_text(pre_existing, encoding="utf-8")

    append_history_row(history_path, _passing_row())

    text = history_path.read_text(encoding="utf-8")
    assert text.startswith(pre_existing)


def test_row_carries_required_schema_fields(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _passing_row())

    row = _read_history(history_path)[0]
    assert set(HISTORY_ROW_FIELDS).issubset(row.keys())


def test_row_is_valid_json_per_line(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _passing_row())
    append_history_row(history_path, _failing_row())

    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert all(json.loads(line) for line in lines if line)


def test_each_row_lands_on_its_own_line(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _passing_row())
    append_history_row(history_path, _failing_row())

    content = history_path.read_text(encoding="utf-8")
    assert content.count("\n") >= 2
