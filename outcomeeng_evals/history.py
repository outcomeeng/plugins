"""Append-only history.jsonl writer.

Each suite run appends one summary row capturing the suite verdict and
aggregate metrics. The file is the durable trend record; the full
transcripts live under the sibling ``runs/`` directory and are gitignored.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


HISTORY_FILENAME = "history.jsonl"


class HistoryRow(TypedDict):
    """One summary row appended to ``history.jsonl`` per suite run.

    This field set is the integration contract between the runner and any
    trend-reading tooling. It is a ``TypedDict`` so mypy flags field-name
    drift at the construction site (``_history_row`` in the ``run``
    command) — the previous runtime field-set guard caught drift only when
    a row was actually written, after the typo had already shipped.
    """

    timestamp: str
    schema_version: str
    git_sha: str
    model: str
    max_budget_usd: float
    timeout_seconds: int
    passed: bool
    pass_rate: float
    cases_total: int
    cases_passed: int
    total_cost_usd: float | None
    total_duration_ms: float | None
    total_input_tokens: int | None
    total_output_tokens: int | None
    total_cache_read_input_tokens: int | None
    total_cache_creation_input_tokens: int | None
    transcript: str


# Field list with ``HistoryRow`` as the single source of truth — consumed
# by tests that introspect which keys a row must carry.
HISTORY_ROW_FIELDS: tuple[str, ...] = tuple(HistoryRow.__annotations__)


def append_history_row(history_path: Path, row: HistoryRow) -> None:
    """Append one JSONL row to ``history_path``.

    Creates the file (and parent directories) if missing. Existing content
    is preserved; the writer opens in append mode and emits a single line.
    """
    history_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(row, separators=(",", ":"), sort_keys=False)
    with history_path.open("a", encoding="utf-8") as fh:
        fh.write(serialized)
        fh.write("\n")
