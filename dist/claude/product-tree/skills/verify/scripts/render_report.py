"""Check the structured results of /verify and render its report table from them.

Run as ``python3 render_report.py <results.json>``, where the file holds a JSON
array of result records. On valid records it prints the report table and exits
0; otherwise it prints one line per defect on stderr and exits 2.
"""

from __future__ import annotations

import json
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any, Final


class ResultField(StrEnum):
    SUBJECT = "subject"
    VERIFICATION_TYPE = "verification_type"
    SPECIALIST = "specialist"
    STATUS = "status"
    EVIDENCE_SHAPE = "evidence_shape"
    REASON = "reason"


class SubjectField(StrEnum):
    PATH = "path"
    LINE = "line"
    TEXT = "text"


UNSUPPORTED_TAG_SHAPE: Final = "unsupported-tag-shape"
NULL_CELL: Final = "—"
EXIT_INVALID: Final = 2
VALUES: Final[dict[ResultField, tuple[str | None, ...]]] = {
    ResultField.VERIFICATION_TYPE: ("test", "evaluate", "probe", "audit", None),
    ResultField.SPECIALIST: ("/test", "/eval", "/probe", "isolated-verifier", None),
    ResultField.STATUS: ("routed", "capability-required", "blocked"),
    ResultField.EVIDENCE_SHAPE: ("path-bearing", "pathless", "requirement", None),
}
ROUTE_FIELDS: Final = (
    ResultField.VERIFICATION_TYPE,
    ResultField.SPECIALIST,
    ResultField.EVIDENCE_SHAPE,
)
COLUMNS: Final = (*ROUTE_FIELDS, ResultField.STATUS, ResultField.REASON)
HEADER: Final = (
    "| Subject | Verification type | Specialist | Evidence shape | Status | Reason |"
)
SEPARATOR: Final = "| --- | --- | --- | --- | --- | --- |"


def defects(index: int, record: Any) -> list[str]:
    """Return one message per defect of the result record at ``index``."""
    if not isinstance(record, dict):
        return [f"result {index}: not an object"]
    found = [
        f"result {index}: lacks {name}" for name in ResultField if name not in record
    ]
    if found:
        return found
    subject = record[ResultField.SUBJECT]
    if not isinstance(subject, dict) or any(
        name not in subject for name in SubjectField
    ):
        return [f"result {index}: subject lacks path, line, or text"]
    if not isinstance(subject[SubjectField.PATH], str) or not isinstance(
        subject[SubjectField.LINE], int
    ):
        found.append(
            f"result {index}: subject path must be a string and line an integer"
        )
    found += [
        f"result {index}: {name} {record[name]!r} is not one of {allowed}"
        for name, allowed in VALUES.items()
        if record[name] not in allowed
    ]
    if not isinstance(record[ResultField.REASON], str):
        found.append(f"result {index}: reason must be a string")
    if (subject[SubjectField.TEXT] is None) != (
        record[ResultField.REASON] == UNSUPPORTED_TAG_SHAPE
    ):
        found.append(
            f"result {index}: subject text is null exactly when reason is {UNSUPPORTED_TAG_SHAPE}"
        )
    if record[ResultField.STATUS] != "blocked" and any(
        record[name] is None for name in ROUTE_FIELDS
    ):
        found.append(
            f"result {index}: a {record[ResultField.STATUS]} result names its verification type, specialist, and evidence shape"
        )
    return found


def cell(value: str | None) -> str:
    return NULL_CELL if value is None else value.replace("|", "\\|")


def render(records: list[dict[str, Any]]) -> str:
    """Render the report table, one row per result record."""
    rows = [HEADER, SEPARATOR]
    for record in records:
        subject = record[ResultField.SUBJECT]
        location = f"{subject[SubjectField.PATH]}:{subject[SubjectField.LINE]}"
        text = subject[SubjectField.TEXT]
        cells = [location if text is None else f"{location} {cell(text)}"]
        cells += [cell(record[name]) for name in COLUMNS]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def main(argv: list[str]) -> int:
    records = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    found = (
        [
            line
            for index, record in enumerate(records)
            for line in defects(index, record)
        ]
        if isinstance(records, list)
        else ["results: not a JSON array"]
    )
    if found:
        print("\n".join(found), file=sys.stderr)
        return EXIT_INVALID
    print(render(records))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
