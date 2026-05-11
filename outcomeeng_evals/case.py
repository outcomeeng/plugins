"""Case schema and JSONL loader for eval evidence."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExpectedElement:
    """A structural expectation against the audit verdict XML."""

    element: str
    attributes: dict[str, str]


@dataclass(frozen=True)
class Case:
    """One eval case: input payload plus expected verdict fields."""

    id: str
    input: dict[str, Any]
    must_contain: tuple[ExpectedElement, ...]
    must_not_contain: tuple[ExpectedElement, ...]


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
    must_contain = tuple(_to_element(e) for e in expected.get("must_contain", []))
    must_not_contain = tuple(
        _to_element(e) for e in expected.get("must_not_contain", [])
    )
    return Case(
        id=record["id"],
        input=record["input"],
        must_contain=must_contain,
        must_not_contain=must_not_contain,
    )


def _to_element(record: dict[str, Any]) -> ExpectedElement:
    return ExpectedElement(
        element=record["element"],
        attributes=dict(record.get("attributes", {})),
    )
