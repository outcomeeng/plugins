"""Compliance evidence for the history.jsonl append-only writer.

Each suite run appends one row capturing the suite verdict and aggregate
metrics. The file is the durable trend record; runs/ holds the full
transcripts and is gitignored.
"""

from __future__ import annotations

import json
import subprocess
from contextlib import chdir
from pathlib import Path

from outcomeeng_evals.cli.commands.run import _git_sha, _history_row
from outcomeeng_evals.history import HistoryRow, append_history_row
from outcomeeng_evals.suite import SuiteResult
from outcomeeng_testing.evals.factories import load_history_rows_fixture

_FIXTURE_PATH = Path(__file__).parents[1] / "fixtures/evals/history_rows.json"


def fixture_rows() -> tuple[HistoryRow, ...]:
    """The captured history rows the compliance evidence replays."""

    return load_history_rows_fixture(_FIXTURE_PATH)


def append_rows(history_path: Path, rows: tuple[HistoryRow, ...]) -> None:
    """Append each row through the real writer, in order."""

    for row in rows:
        append_history_row(history_path, row)


def read_history(path: Path) -> list[dict[str, object]]:
    """Parse every non-blank line of a history file as JSON."""

    with path.open(encoding="utf-8") as history_file:
        return [json.loads(line) for line in history_file if line.strip()]


def read_history_lines(path: Path) -> list[str]:
    """Return the raw lines of a history file."""

    return path.read_text(encoding="utf-8").splitlines()


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def commit_in_new_repository(repo: Path) -> str:
    """Create a real repository with one commit and return its full HEAD sha."""

    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "tracked.txt").write_text("content\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "initial")
    return _git(repo, "rev-parse", "HEAD")


def observe_git_sha(repo: Path) -> str:
    """Return the sha the run command records when invoked inside the repository."""

    with chdir(repo):
        return _git_sha()


def history_row_for(result: SuiteResult, fixture_row: HistoryRow) -> HistoryRow:
    """Build the row the run command appends for a suite result."""

    return _history_row(
        timestamp=fixture_row["timestamp"],
        result=result,
        model=fixture_row["model"],
        max_budget_usd=fixture_row["max_budget_usd"],
        timeout_seconds=fixture_row["timeout_seconds"],
        transcript_relative=fixture_row["transcript"],
    )
