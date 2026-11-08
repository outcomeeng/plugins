"""Input domains of the change-standards form-check evidence.

The fixture cases are the finite, file-declared domain of Draft fixtures: a
fixture named ``<rule>.<case>.<verdict>.md`` under ``drafts/<group>`` declares
the rule its case exercises and whether the check passes or fails it. The key
mutations, the stored-record changes, the oversized Drafts, and the unreadable
requests derive from the shipped script's own key and field vocabulary.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from outcomeeng_testing.harnesses.change_standards_form_check import (
    DRAFT_DIR,
    DRAFT_SUFFIX,
    load_form_check,
)

GROUP_MAPPING: Final = "mapping"
GROUP_COMPLIANCE: Final = "compliance"
FRONT_MATTER_FENCE: Final = "---"
TABLE_HEADING_MARK: Final = "### "
FILLER_OPEN: Final = "<!-- "
FILLER_CLOSE: Final = " -->"
FILLER_CHARACTER: Final = "x"
OUTSIDE_PREFIX: Final = "not-"
UNKNOWN_FIELD: Final = "unknown_field"
STORED_CHANGE_SUFFIX: Final = " before"


class Verdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True)
class FixtureCase:
    """One Draft fixture and the verdict its name declares."""

    name: str
    rule: str
    case: str
    verdict: Verdict

    @property
    def identity(self) -> str:
        return f"{self.rule}.{self.case}.{self.verdict}"


def fixture_cases(group: str) -> tuple[FixtureCase, ...]:
    """Return every Draft fixture of ``group``, ordered by name."""
    cases: list[FixtureCase] = []
    for path in sorted((DRAFT_DIR / group).glob(f"*{DRAFT_SUFFIX}")):
        rule, case, verdict = path.name[: -len(DRAFT_SUFFIX)].split(".")
        cases.append(FixtureCase(f"{group}/{path.stem}", rule, case, Verdict(verdict)))
    return tuple(cases)


def draft_keys() -> tuple[str, ...]:
    """Return the metadata keys a Draft holds, in the script's order."""
    return tuple(str(key.value) for key in load_form_check().DRAFT_KEYS)


def operations() -> tuple[str, ...]:
    """Return every operation the script names."""
    return tuple(str(operation.value) for operation in load_form_check().Operation)


def operations_of(key: str) -> frozenset[str]:
    """Return the operations the script lets change ``key``."""
    form = load_form_check()
    return frozenset(str(op.value) for op in form.KEY_OPERATIONS[form.Key(key)])


def without_key(text: str, key: str) -> str:
    """Return Draft ``text`` with the line of metadata ``key`` removed."""
    kept = [line for line in text.split("\n") if not line.startswith(f"{key}:")]
    return "\n".join(kept)


def with_value(text: str, key: str, value: str) -> str:
    """Return Draft ``text`` with metadata ``key`` set to ``value``."""
    lines = [
        f"{key}: {value}" if line.startswith(f"{key}:") else line
        for line in text.split("\n")
    ]
    return "\n".join(lines)


def non_value(key: str) -> str:
    """Return a yaml value that the key's domain does not hold."""
    form = load_form_check()
    member = form.Key(key)
    if member in form.ENUMERATED_VALUES:
        return OUTSIDE_PREFIX + form.ENUMERATED_VALUES[member][0]
    if member is form.Key.TITLE:
        return " ".join([OUTSIDE_PREFIX.strip("-")] * (form.TITLE_WORD_LIMIT + 1))
    if member in {form.Key.PREDECESSORS, form.Key.BLOCKERS}:
        return OUTSIDE_PREFIX + "a-list"
    if member is form.Key.BASE:
        return OUTSIDE_PREFIX + "a-commit"
    return "[]"


def stored_record_changed_at(text: str, key: str) -> dict[str, Any]:
    """Return the record a store holds that differs from Draft ``text`` at ``key``."""
    metadata = dict(load_form_check().parse_draft(text).metadata)
    metadata[key] = json.dumps(metadata.get(key)) + STORED_CHANGE_SUFFIX
    return {
        load_form_check().RecordField.METADATA: metadata,
        load_form_check().RecordField.BODY: "",
    }


def body_length(text: str) -> int:
    """Return the number of characters in the body of Draft ``text``."""
    lines = text.split("\n")
    closing = [
        index for index, line in enumerate(lines) if line.strip() == FRONT_MATTER_FENCE
    ][1]
    return len("\n".join(lines[closing + 1 :]))


def padded_to(text: str, size: int) -> str:
    """Return Draft ``text`` with a filler line that makes its body ``size`` characters."""
    overhead = len(FILLER_OPEN) + len(FILLER_CLOSE)
    fill = size - body_length(text) - overhead
    assert fill >= 0
    return text + FILLER_OPEN + FILLER_CHARACTER * fill + FILLER_CLOSE


def table_row_name(fixture_name: str, mark: str) -> str:
    """Return ``<subsection slug>/<case>`` for the first table row a fixture marks with ``mark``."""
    heading = ""
    for line in (
        (DRAFT_DIR / f"{fixture_name}{DRAFT_SUFFIX}")
        .read_text(encoding="utf-8")
        .split("\n")
    ):
        stripped = line.lstrip("+- ")
        if stripped.startswith(TABLE_HEADING_MARK) and ":" in stripped:
            heading = stripped.split(":", 1)[1].strip()
        if line.startswith(f"{mark} |"):
            return f"{heading}/{line[1:].strip().strip('|').split('|')[0].strip()}"
    raise AssertionError(f"{fixture_name} has no table row marked {mark}")


def unreadable_requests(
    valid: Mapping[str, Any],
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield each request that breaks the request shape, with the field it names."""
    form = load_form_check()
    fields = form.RequestField
    required = (
        fields.CHECKOUT_ROOT,
        fields.OPERATION,
        fields.STORED_RECORD,
        fields.SIZE_LIMIT,
    )
    for field in required:
        request = {name: value for name, value in valid.items() if name != field}
        yield str(field.value), request
    yield (
        str(fields.DRAFT_TEXT.value),
        {name: value for name, value in valid.items() if name != fields.DRAFT_TEXT},
    )
    yield str(fields.DRAFT_PATH.value), {**valid, fields.DRAFT_PATH: "/nonexistent.md"}
    yield UNKNOWN_FIELD, {**valid, UNKNOWN_FIELD: 1}
    yield (
        str(fields.OPERATION.value),
        {**valid, fields.OPERATION: OUTSIDE_PREFIX + "an-operation"},
    )
    yield str(fields.SIZE_LIMIT.value), {**valid, fields.SIZE_LIMIT: 0}
    yield (
        str(fields.CHECKOUT_ROOT.value),
        {**valid, fields.CHECKOUT_ROOT: DRAFT_DIR.name},
    )
