"""Case schema and JSONL loader for eval evidence."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Case:
    """One eval case: input payload plus expected verdict structure.

    ``must_contain`` and ``must_not_contain`` carry JSON sub-structures
    that the grader checks against the verdict document via recursive
    structural-subset matching (see ``outcomeeng_evals.grader.is_subset``).
    """

    id: str
    input: dict[str, Any]
    must_contain: tuple[dict[str, Any], ...]
    must_not_contain: tuple[dict[str, Any], ...]


def load_cases(path: Path) -> list[Case]:
    """Read a JSONL case file and parse each record into a Case."""
    cases: list[Case] = []
    for line_no, record in _iter_records(path):
        try:
            cases.append(_record_to_case(record))
        except KeyError as exc:
            msg = f"{path}:{line_no} missing required field {exc.args[0]!r}"
            raise ValueError(msg) from exc
    return cases


def _iter_records(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            yield line_no, json.loads(stripped)


def _record_to_case(record: dict[str, Any]) -> Case:
    expected = record.get("expected_verdict", {})
    must_contain = tuple(expected.get("must_contain", []))
    must_not_contain = tuple(expected.get("must_not_contain", []))
    return Case(
        id=record["id"],
        input=record["input"],
        must_contain=must_contain,
        must_not_contain=must_not_contain,
    )
