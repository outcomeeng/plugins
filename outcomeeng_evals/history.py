"""Append-only history.jsonl writer.

Each suite run appends one summary row capturing the suite verdict and
aggregate metrics. The file is the durable trend record; the full
transcripts live under the sibling ``runs/`` directory and are gitignored.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HISTORY_ROW_FIELDS: tuple[str, ...] = (
    "timestamp",
    "schema_version",
    "git_sha",
    "passed",
    "pass_rate",
    "cases_total",
    "cases_passed",
    "total_cost_usd",
    "total_duration_ms",
    "transcript",
)


def append_history_row(history_path: Path, row: dict[str, Any]) -> None:
    """Append a JSONL row to ``history_path``.

    Creates the file (and parent directories) if missing. Existing content
    is preserved; the writer opens in append mode and emits one line.
    """
    history_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(row, separators=(",", ":"), sort_keys=False)
    with history_path.open("a", encoding="utf-8") as fh:
        fh.write(serialized)
        fh.write("\n")
