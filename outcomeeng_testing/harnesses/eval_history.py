"""Compliance evidence for the history.jsonl append-only writer.

Each suite run appends one row capturing the suite verdict and aggregate
metrics. The file is the durable trend record; runs/ holds the full
transcripts and is gitignored.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from contextlib import chdir
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from outcomeeng_evals.cli.commands.run import _git_sha, _history_row
from outcomeeng_evals.history import (
    HISTORY_FILENAME,
    HISTORY_ROW_FIELDS,
    HISTORY_TRANSCRIPT_FIELD,
    HISTORY_TOKEN_FIELDS,
    HistoryRow,
    append_history_row,
)
from outcomeeng_evals.testing.factories import (
    load_history_rows_fixture,
    make_bimodal_cache_suite_result,
    make_suite_result,
)
from outcomeeng_testing.harnesses.eval_run_exit import configured_threshold_run

_FIXTURE_PATH = Path(__file__).parents[1] / "fixtures/evals/history_rows.json"


def _rows() -> tuple[HistoryRow, ...]:
    return load_history_rows_fixture(_FIXTURE_PATH)


def _read_history(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as history_file:
        return [json.loads(line) for line in history_file if line.strip()]


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _assert_creates_history_file_when_missing(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    assert not history_path.exists()

    append_history_row(history_path, _rows()[0])

    assert history_path.exists()


def _assert_appends_row_to_existing_history(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _rows()[0])
    append_history_row(history_path, _rows()[1])

    rows = _read_history(history_path)
    assert len(rows) == 2
    assert rows[0]["passed"] is True
    assert rows[1]["passed"] is False


def _assert_preserves_pre_existing_rows(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _rows()[0])
    append_history_row(history_path, _rows()[0])

    assert _read_history(history_path) == [_rows()[0], _rows()[0]]


def _assert_row_carries_required_schema_fields(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    fixture_row = _rows()[0]
    append_history_row(history_path, fixture_row)

    row = _read_history(history_path)[0]
    assert set(fixture_row) == set(HISTORY_ROW_FIELDS)
    assert set(row) == set(HISTORY_ROW_FIELDS)
    assert row["model"] == fixture_row["model"]


def _assert_row_carries_token_aggregates_for_cache_hit_rate(tmp_path: Path) -> None:
    # The durable row carries the input/output/cache token totals so a
    # reader can derive the prompt-cache hit rate over time without the
    # gitignored transcript.
    history_path = tmp_path / "history.jsonl"
    fixture_row = _rows()[0]
    append_history_row(history_path, fixture_row)

    row = _read_history(history_path)[0]
    for field in HISTORY_TOKEN_FIELDS:
        assert field in fixture_row
        assert field in row
    assert (
        row["total_cache_read_input_tokens"]
        == fixture_row["total_cache_read_input_tokens"]
    )


def _assert_history_row_aggregates_token_counts_across_trials() -> None:
    # Exercises the run-command aggregation (_history_row -> _sum_int), not
    # just persistence: the row's token totals must be the per-trial sums.
    # Deleting the _sum_int cache-token calls in run.py fails this.
    fixture_row = _rows()[0]
    result = make_bimodal_cache_suite_result()
    row = _history_row(
        timestamp=fixture_row["timestamp"],
        result=result,
        model=fixture_row["model"],
        max_budget_usd=fixture_row["max_budget_usd"],
        timeout_seconds=fixture_row["timeout_seconds"],
        transcript_relative=fixture_row["transcript"],
    )
    assert set(row) == set(fixture_row)
    assert row["model"] == fixture_row["model"]
    assert row["max_budget_usd"] == pytest.approx(fixture_row["max_budget_usd"])
    assert row["timeout_seconds"] == fixture_row["timeout_seconds"]
    metadata = [
        trial.metadata for outcome in result.outcomes for trial in outcome.trials
    ]
    assert row["total_input_tokens"] == sum(item.input_tokens or 0 for item in metadata)
    assert row["total_output_tokens"] == sum(
        item.output_tokens or 0 for item in metadata
    )
    assert row["total_cache_read_input_tokens"] == sum(
        item.cache_read_input_tokens or 0 for item in metadata
    )
    assert row["total_cache_creation_input_tokens"] == sum(
        item.cache_creation_input_tokens or 0 for item in metadata
    )


def _assert_git_sha_uses_full_head_identity(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "tracked.txt").write_text("content\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-m", "initial")
    expected = _git(tmp_path, "rev-parse", "HEAD")

    with chdir(tmp_path):
        assert _git_sha() == expected


def _assert_history_row_token_aggregates_are_none_without_metadata() -> None:
    # A run whose trials carry no metadata reports null aggregates, never a
    # fabricated zero — so "no data" stays distinguishable from "billed zero".
    fixture_row = _rows()[0]
    row = _history_row(
        timestamp=fixture_row["timestamp"],
        result=make_suite_result(),
        model=fixture_row["model"],
        max_budget_usd=fixture_row["max_budget_usd"],
        timeout_seconds=fixture_row["timeout_seconds"],
        transcript_relative=fixture_row["transcript"],
    )
    assert row["total_input_tokens"] is None
    assert row["total_output_tokens"] is None
    assert row["total_cache_read_input_tokens"] is None
    assert row["total_cache_creation_input_tokens"] is None


def _assert_row_is_valid_json_per_line(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _rows()[0])
    append_history_row(history_path, _rows()[1])

    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert all(isinstance(json.loads(line), dict) for line in lines if line)


def _assert_each_row_lands_on_its_own_line(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history_row(history_path, _rows()[0])
    append_history_row(history_path, _rows()[1])

    assert _read_history(history_path) == list(_rows())


def assert_history_compliance() -> None:
    """Run the complete append-only history evidence in one managed workspace."""

    for assertion in (
        _assert_creates_history_file_when_missing,
        _assert_appends_row_to_existing_history,
        _assert_preserves_pre_existing_rows,
        _assert_row_carries_required_schema_fields,
        _assert_row_carries_token_aggregates_for_cache_hit_rate,
        _assert_git_sha_uses_full_head_identity,
        _assert_row_is_valid_json_per_line,
        _assert_each_row_lands_on_its_own_line,
    ):
        _run_in_temporary_directory(assertion)

    _assert_history_row_aggregates_token_counts_across_trials()
    _assert_history_row_token_aggregates_are_none_without_metadata()
    _assert_run_command_appends_eval_local_history()


def _assert_run_command_appends_eval_local_history() -> None:
    with configured_threshold_run() as eval_dir:
        rows = _read_history(eval_dir / HISTORY_FILENAME)
        assert len(rows) == 1
        transcript = rows[0][HISTORY_TRANSCRIPT_FIELD]
        assert isinstance(transcript, str)
        assert (eval_dir / transcript).is_file()


def _run_in_temporary_directory(assertion: Callable[[Path], None]) -> None:
    with TemporaryDirectory() as tmp:
        assertion(Path(tmp))
