"""Case schema and JSONL loader for eval evidence."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Upper bound on the length of any list inside a case expectation.
# ``grader.is_subset`` matches an expected list against an actual list in
# O(len(expected) x len(actual)) time, so an oversized expectation
# silently degrades grading at eval runtime. The loader rejects it instead
# — a clear error beats a slow run. Real expectations are a handful of
# fields; 50 is far past anything legitimate.
MAX_EXPECTED_LIST_LENGTH = 50
CASE_ID_FIELD = "id"
CASE_INPUT_FIELD = "input"
EXPECTED_VERDICT_FIELD = "expected_verdict"
MUST_CONTAIN_FIELD = "must_contain"
MUST_NOT_CONTAIN_FIELD = "must_not_contain"


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
    """Read a JSONL case file and parse each record into a Case.

    Blank lines and lines starting with ``#`` are skipped silently — eval
    authors can annotate ``cases.jsonl`` with shell-style comments
    without breaking the parser.
    """
    cases: list[Case] = []
    for line_no, record in _iter_records(path):
        try:
            cases.append(_record_to_case(record))
        except KeyError as exc:
            msg = f"{path}:{line_no} missing required field {exc.args[0]!r}"
            raise ValueError(msg) from exc
        except ValueError as exc:
            msg = f"{path}:{line_no} {exc}"
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
    expected = record.get(EXPECTED_VERDICT_FIELD, {})
    must_contain = tuple(expected.get(MUST_CONTAIN_FIELD, []))
    must_not_contain = tuple(expected.get(MUST_NOT_CONTAIN_FIELD, []))
    case_id = record[CASE_ID_FIELD]
    if not isinstance(case_id, str) or not case_id:
        msg = f"case 'id' must be a non-empty string, got {case_id!r}"
        raise ValueError(msg)
    for entry in must_contain:
        _reject_oversized_lists(entry, field="must_contain", case_id=case_id)
    for entry in must_not_contain:
        _reject_oversized_lists(entry, field="must_not_contain", case_id=case_id)
    return Case(
        id=case_id,
        input=record[CASE_INPUT_FIELD],
        must_contain=must_contain,
        must_not_contain=must_not_contain,
    )


def _reject_oversized_lists(value: Any, *, field: str, case_id: str) -> None:
    """Raise ``ValueError`` if any list inside ``value`` exceeds the cap."""
    if isinstance(value, list):
        if len(value) > MAX_EXPECTED_LIST_LENGTH:
            msg = (
                f"case {case_id!r}: {field} contains a list of {len(value)} elements; "
                f"is_subset matches expected lists in O(expected x actual) time — "
                f"keep expectation lists under {MAX_EXPECTED_LIST_LENGTH}"
            )
            raise ValueError(msg)
        for item in value:
            _reject_oversized_lists(item, field=field, case_id=case_id)
    elif isinstance(value, dict):
        for sub_value in value.values():
            _reject_oversized_lists(sub_value, field=field, case_id=case_id)
