"""Conformance tests for the history.jsonl append-only writer.

Each suite run appends one row capturing the suite verdict and aggregate
metrics. The file is the durable trend record; runs/ holds the full
transcripts and is gitignored.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from outcomeeng_evals.case import Case
from outcomeeng_evals.cli.commands.run import _git_sha, _history_row
from outcomeeng_evals.grader import GradeResult
from outcomeeng_evals.history import HISTORY_ROW_FIELDS, HistoryRow, append_history_row
from outcomeeng_evals.runner import RunMetadata
from outcomeeng_evals.suite import CaseOutcome, SuiteResult, TrialResult
from outcomeeng_evals.testing.factories import make_bimodal_cache_suite_result


SCHEMA_VERSION = "1"
GIT_SHA = "9999af81234567890abcdef1234567890abcdef1"
TIMESTAMP = "2026-05-11T15:48:00Z"
TRANSCRIPT_REL = "runs/2026-05-11T15-48-00Z.json"
FAILING_TIMESTAMP = "2026-05-12T09:00:00Z"
FAILING_TRANSCRIPT_REL = "runs/2026-05-12T09-00-00Z.json"


def _passing_row() -> HistoryRow:
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
        "total_input_tokens": 40,
        "total_output_tokens": 24,
        "total_cache_read_input_tokens": 198560,
        "total_cache_creation_input_tokens": 0,
        "transcript": TRANSCRIPT_REL,
    }


def _failing_row() -> HistoryRow:
    # Built from scratch (not a mutated copy of _passing_row) so the two
    # rows are obviously distinct values.
    return {
        "timestamp": FAILING_TIMESTAMP,
        "schema_version": SCHEMA_VERSION,
        "git_sha": GIT_SHA,
        "passed": False,
        "pass_rate": 0.75,
        "cases_total": 4,
        "cases_passed": 3,
        "total_cost_usd": 1.04,
        "total_duration_ms": 18960.0,
        "total_input_tokens": 39,
        "total_output_tokens": 31,
        "total_cache_read_input_tokens": 52160,
        "total_cache_creation_input_tokens": 33830,
        "transcript": FAILING_TRANSCRIPT_REL,
    }


def _read_history(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


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


def test_row_carries_token_aggregates_for_cache_hit_rate(tmp_path: Path) -> None:
    # The durable row carries the input/output/cache token totals so a
    # reader can derive the prompt-cache hit rate over time without the
    # gitignored transcript.
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _passing_row())

    row = _read_history(history_path)[0]
    for field in (
        "total_input_tokens",
        "total_output_tokens",
        "total_cache_read_input_tokens",
        "total_cache_creation_input_tokens",
    ):
        assert field in HISTORY_ROW_FIELDS
        assert field in row
    assert row["total_cache_read_input_tokens"] == 198560


def test_history_row_aggregates_token_counts_across_trials() -> None:
    # Exercises the run-command aggregation (_history_row -> _sum_int), not
    # just persistence: the row's token totals must be the per-trial sums.
    # Deleting the _sum_int cache-token calls in run.py fails this.
    row = _history_row(
        timestamp=TIMESTAMP,
        result=make_bimodal_cache_suite_result(),
        transcript_relative=TRANSCRIPT_REL,
    )
    assert row["total_input_tokens"] == 22
    assert row["total_output_tokens"] == 12
    assert row["total_cache_read_input_tokens"] == 49600
    assert row["total_cache_creation_input_tokens"] == 34000


def test_git_sha_uses_full_head_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "tracked.txt").write_text("content\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-m", "initial")
    expected = _git(tmp_path, "rev-parse", "HEAD")

    monkeypatch.chdir(tmp_path)

    assert _git_sha() == expected


def test_history_row_token_aggregates_are_none_without_metadata() -> None:
    # A run whose trials carry no metadata reports null aggregates, never a
    # fabricated zero — so "no data" stays distinguishable from "billed zero".
    case = Case(id="c-1", input={}, must_contain=(), must_not_contain=())
    bare = TrialResult(
        case_id="c-1",
        trial_index=0,
        prompt="p",
        response="r",
        verdict=None,
        grade=GradeResult(passed=True, reasons=()),
        metadata=RunMetadata(),
    )
    result = SuiteResult(
        outcomes=(CaseOutcome(case=case, trials=(bare,), passed=True),),
        pass_rate=1.0,
        threshold=0.85,
        passed=True,
    )
    row = _history_row(
        timestamp=TIMESTAMP, result=result, transcript_relative=TRANSCRIPT_REL
    )
    assert row["total_input_tokens"] is None
    assert row["total_output_tokens"] is None
    assert row["total_cache_read_input_tokens"] is None
    assert row["total_cache_creation_input_tokens"] is None


def test_row_is_valid_json_per_line(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _passing_row())
    append_history_row(history_path, _failing_row())

    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert all(isinstance(json.loads(line), dict) for line in lines if line)


def test_each_row_lands_on_its_own_line(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _passing_row())
    append_history_row(history_path, _failing_row())

    content = history_path.read_text(encoding="utf-8")
    assert content.count("\n") >= 2
