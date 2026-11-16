"""Compliance evidence for the append-only history.jsonl writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from outcomeeng_evals.history import (
    HISTORY_FILENAME,
    HISTORY_ROW_FIELDS,
    HISTORY_TOKEN_FIELDS,
    HISTORY_TRANSCRIPT_FIELD,
    append_history_row,
)
from outcomeeng_testing.evals.factories import (
    make_bimodal_cache_suite_result,
    make_suite_result,
)
from outcomeeng_testing.harnesses.eval_history import (
    append_rows,
    commit_in_new_repository,
    fixture_rows,
    history_row_for,
    observe_git_sha,
    read_history,
    read_history_lines,
)
from outcomeeng_testing.harnesses.eval_run_exit import (
    configured_ceiling_run,
    configured_threshold_run,
)


def test_history_file_is_created_when_missing(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    assert not history_path.exists()

    append_history_row(history_path, fixture_rows()[0])

    assert history_path.exists()


def test_append_keeps_every_earlier_row_in_order(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    rows = fixture_rows()
    append_rows(history_path, (rows[0], rows[1]))

    observed = read_history(history_path)

    assert observed == [rows[0], rows[1]]
    assert observed[0]["passed"] is True
    assert observed[1]["passed"] is False


def test_identical_rows_each_remain_in_the_file(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    row = fixture_rows()[0]
    append_rows(history_path, (row, row))

    assert read_history(history_path) == [row, row]


def test_row_carries_exactly_the_schema_fields(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    fixture_row = fixture_rows()[0]
    append_history_row(history_path, fixture_row)

    row = read_history(history_path)[0]

    assert set(fixture_row) == set(HISTORY_ROW_FIELDS)
    assert set(row) == set(HISTORY_ROW_FIELDS)
    assert row["model"] == fixture_row["model"]


def test_row_carries_token_aggregates_for_cache_hit_rate(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    fixture_row = fixture_rows()[0]
    append_history_row(history_path, fixture_row)

    row = read_history(history_path)[0]

    for field in HISTORY_TOKEN_FIELDS:
        assert field in fixture_row
        assert field in row
    assert (
        row["total_cache_read_input_tokens"]
        == fixture_row["total_cache_read_input_tokens"]
    )


def test_run_row_token_totals_are_the_per_trial_sums() -> None:
    fixture_row = fixture_rows()[0]
    result = make_bimodal_cache_suite_result()

    row = history_row_for(result, fixture_row)

    metadata = [
        trial.metadata for outcome in result.outcomes for trial in outcome.trials
    ]
    assert set(row) == set(fixture_row)
    assert row["model"] == fixture_row["model"]
    assert row["max_budget_usd"] == pytest.approx(fixture_row["max_budget_usd"])
    assert row["timeout_seconds"] == fixture_row["timeout_seconds"]
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


def test_run_row_token_totals_are_null_without_trial_metadata() -> None:
    row = history_row_for(make_suite_result(), fixture_rows()[0])

    assert row["total_input_tokens"] is None
    assert row["total_output_tokens"] is None
    assert row["total_cache_read_input_tokens"] is None
    assert row["total_cache_creation_input_tokens"] is None


def test_git_sha_is_the_full_head_identity(tmp_path: Path) -> None:
    expected = commit_in_new_repository(tmp_path)

    assert observe_git_sha(tmp_path) == expected


def test_every_row_is_one_json_object_line(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    append_rows(history_path, fixture_rows()[:2])

    lines = read_history_lines(history_path)

    assert all(isinstance(json.loads(line), dict) for line in lines if line)


def test_each_row_lands_on_its_own_line(tmp_path: Path) -> None:
    history_path = tmp_path / HISTORY_FILENAME
    rows = fixture_rows()
    append_rows(history_path, rows[:2])

    assert read_history(history_path) == list(rows[:2])
    assert len(read_history_lines(history_path)) == 2


def test_run_command_appends_one_row_beside_its_transcript() -> None:
    with configured_threshold_run() as eval_dir:
        rows = read_history(eval_dir / HISTORY_FILENAME)

        assert len(rows) == 1
        transcript = rows[0][HISTORY_TRANSCRIPT_FIELD]
        assert isinstance(transcript, str)
        assert (eval_dir / transcript).is_file()


def test_run_command_row_records_the_configured_ceilings() -> None:
    with configured_ceiling_run() as run:
        rows = read_history(run.eval_dir / HISTORY_FILENAME)

        assert len(rows) == 1
        assert rows[0]["max_budget_usd"] == pytest.approx(run.max_budget_usd)
        assert rows[0]["timeout_seconds"] == run.timeout_seconds
