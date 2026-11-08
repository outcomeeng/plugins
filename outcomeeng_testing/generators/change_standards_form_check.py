"""Input domains of the change-standards form-check evidence.

The fixture cases are the finite, file-declared domain of Draft fixtures: a
fixture named ``<rule>.<case>.<verdict>.md`` under ``drafts/<group>`` declares
the rule its case exercises and whether the check passes or fails it. The key
mutations, the stored-record changes, the oversized Drafts, and the unreadable
requests derive from the shipped script's own key and field vocabulary.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from outcomeeng_testing.harnesses.change_standards_form_check import (
    DRAFT_DIR,
    DRAFT_SUFFIX,
    SPEC,
    load_form_check,
)

GROUP_MAPPING: Final = "mapping"
GROUP_COMPLIANCE: Final = "compliance"
GROUP_MAPPING_NO_TREE: Final = "mapping-no-tree"
GROUP_COMPLIANCE_NO_TREE: Final = "compliance-no-tree"
ALL_GROUPS: Final = (
    GROUP_MAPPING,
    GROUP_COMPLIANCE,
    GROUP_MAPPING_NO_TREE,
    GROUP_COMPLIANCE_NO_TREE,
)
YAML_NULL: Final = "null"
TITLE_WORD: Final = "word"
SPEC_HEADING_MARK: Final = "### "
SPEC_MAPPING_KIND: Final = "Test.Mapping"
SPEC_COMPLIANCE_KIND: Final = "Test.Compliance"
SPEC_RECORD_KEYS: Final = "record-keys"
SPEC_NULL_CLAUSE: Final = ", null"
SPEC_TABLE_PREAMBLE_ROWS: Final = 1
SPEC_RULE_PATTERN: Final = re.compile(r"^- (?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*): ")
FRONT_MATTER_FENCE: Final = "---"
TABLE_HEADING_MARK: Final = "### "
FILLER_OPEN: Final = "<!-- "
FILLER_CLOSE: Final = " -->"
FILLER_CHARACTER: Final = "x"
OUTSIDE_PREFIX: Final = "not-"
UNKNOWN_FIELD: Final = "unknown_field"
STORED_CHANGE_SUFFIX: Final = " before"
SPEC_DRAFT_ABSENT: Final = "absent from a Change Draft"
SPEC_CLAUSE_SPLIT: Final = re.compile(r", or |, | or ")
SPEC_EXPLANATION_OPENING: Final = "which "
SPEC_ENUMERATION: Final = re.compile(
    r"^[A-Z][a-z]+(?:, [A-Z][a-z]+)*,? or [A-Z][a-z]+(?:, null\b.*)?$"
)
SPEC_TITLE_LIMIT: Final = re.compile(r"\bat most (?P<limit>\d+) words\b")
# Compliance rules of the spec that no finding names: limits and interface promises.
NON_FINDING_RULES: Final = frozenset(
    {"github-limit", "check-request", "check-import", "check-reads-only"}
)


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
    """Return the metadata keys the spec's record-keys table lists for a Draft."""
    return tuple(
        row[0]
        for row in _spec_rows(SPEC_MAPPING_KIND, SPEC_RECORD_KEYS)
        if SPEC_DRAFT_ABSENT not in row[1]
    )


def operations() -> tuple[str, ...]:
    """Return every operation the script names."""
    return tuple(str(operation.value) for operation in load_form_check().Operation)


def _operation_vocabulary() -> Mapping[str, frozenset[str]]:
    """Map each phrase of the spec's "Changes through" column to operation names.

    The phrases are the spec's words; the names are the script's wire values.
    The mapping is owned here, not by the script.
    """
    op = load_form_check().Operation
    transition = frozenset(
        {
            op.CLAIM,
            op.RELEASE,
            op.SUBMIT,
            op.ADVANCE,
            op.LOWER,
            op.APPLIED,
            op.ABANDONED,
        }
    )
    phrases: dict[str, frozenset[Any]] = {
        "recording": frozenset({op.RECORD}),
        "recording a Leaf": frozenset({op.RECORD}),
        "recording a Child": frozenset({op.RECORD_CHILD}),
        "its removal when a Child makes the record a Parent": frozenset(
            {op.RECORD_CHILD}
        ),
        "a publish": frozenset({op.PUBLISH}),
        "a publish that writes its body": frozenset({op.PUBLISH}),
        "a split": frozenset({op.SPLIT}),
        "an advance": frozenset({op.ADVANCE}),
        "a lower": frozenset({op.LOWER}),
        "a claim": frozenset({op.CLAIM}),
        "a release": frozenset({op.RELEASE}),
        "a merge": frozenset({op.MERGE}),
        "the Priority decision": frozenset({op.PRIORITY_DECISION}),
        "a Transition": transition,
    }
    return {
        phrase: frozenset(str(member.value) for member in members)
        for phrase, members in phrases.items()
    }


def operations_of(key: str) -> frozenset[str]:
    """Return the operations the spec's "Changes through" cell of ``key`` names.

    A phrase of the cell that maps to no operation fails the lookup.
    """
    vocabulary = _operation_vocabulary()
    for row in _spec_rows(SPEC_MAPPING_KIND, SPEC_RECORD_KEYS):
        if row[0] != key:
            continue
        named: set[str] = set()
        for clause in SPEC_CLAUSE_SPLIT.split(row[2]):
            phrase = clause.strip()
            if phrase.startswith(SPEC_EXPLANATION_OPENING):
                continue
            if phrase not in vocabulary:
                raise AssertionError(
                    f"the spec phrase {phrase!r} of {key} maps to no operation"
                )
            named |= vocabulary[phrase]
        return frozenset(named)
    raise AssertionError(f"the spec lists no record-keys row for {key}")


def _spec_enumerated_rows() -> dict[str, str]:
    """Return the value cell of each record-keys row that lists a fixed set of members."""
    return {
        row[0]: row[1]
        for row in _spec_rows(SPEC_MAPPING_KIND, SPEC_RECORD_KEYS)
        if SPEC_ENUMERATION.match(row[1])
    }


def enumerated_values() -> tuple[tuple[str, str], ...]:
    """Return each (key, yaml value) the spec's record-keys table lists as accepted.

    A key whose row allows null contributes the yaml null beside its members.
    """
    pairs: list[tuple[str, str]] = []
    for key, cell in _spec_enumerated_rows().items():
        pairs.extend((key, member) for member in sorted(spec_key_values(key)))
        if SPEC_NULL_CLAUSE in cell:
            pairs.append((key, YAML_NULL))
    return tuple(pairs)


def foreign_values() -> tuple[tuple[str, str], ...]:
    """Return each (key, value) where the value belongs to another enumerated key's row only."""
    rows = _spec_enumerated_rows()
    pairs: list[tuple[str, str]] = []
    for key in rows:
        members = spec_key_values(key)
        for other in rows:
            if other != key:
                pairs.extend(
                    (key, value)
                    for value in sorted(spec_key_values(other))
                    if value not in members
                )
    return tuple(pairs)


def declared_values(key: str) -> frozenset[str]:
    """Return the members the script declares for an enumerated ``key``."""
    form = load_form_check()
    return frozenset(str(value) for value in form.ENUMERATED_VALUES[form.Key(key)])


def title_of_words(count: int) -> str:
    """Return a title of ``count`` words."""
    return " ".join([TITLE_WORD] * count)


def title_word_limit() -> int:
    """Return the number of words the spec's title row lets a title hold."""
    for row in _spec_rows(SPEC_MAPPING_KIND, SPEC_RECORD_KEYS):
        if row[0] == "title":
            match = SPEC_TITLE_LIMIT.search(row[1])
            assert match is not None, "the spec's title row states no word limit"
            return int(match.group("limit"))
    raise AssertionError("the spec lists no record-keys row for title")


def spec_key_values(key: str) -> frozenset[str]:
    """Return the members the spec's record-keys row lists for an enumerated ``key``."""
    for row in _spec_rows(SPEC_MAPPING_KIND, SPEC_RECORD_KEYS):
        if row[0] == key:
            listed = row[1].split(SPEC_NULL_CLAUSE)[0]
            words = listed.replace(", or ", ", ").replace(" or ", ", ")
            return frozenset(word.strip() for word in words.split(","))
    raise AssertionError(f"the spec lists no record-keys row for {key}")


def spec_row_cases(rule: str) -> tuple[str, ...]:
    """Return the case of each row of the spec's mapping table for ``rule``."""
    return tuple(row[0] for row in _spec_rows(SPEC_MAPPING_KIND, rule))


def spec_mapping_rules() -> tuple[str, ...]:
    """Return the slug of each mapping subsection whose table lists cases."""
    return tuple(
        rule
        for rule in _spec_subsections(SPEC_MAPPING_KIND)
        if rule != SPEC_RECORD_KEYS and _spec_rows(SPEC_MAPPING_KIND, rule)
    )


def spec_compliance_rules() -> tuple[str, ...]:
    """Return the slug of each compliance rule the spec lists that a finding names."""
    listed: list[str] = []
    for body in _spec_subsections(SPEC_COMPLIANCE_KIND).values():
        for line in body:
            match = SPEC_RULE_PATTERN.match(line)
            if match and match.group("slug") not in NON_FINDING_RULES:
                listed.append(match.group("slug"))
    return tuple(listed)


def covering_fixtures(rule: str, case: str) -> tuple[FixtureCase, ...]:
    """Return the fixtures of ``rule`` whose case is ``case`` or begins with it."""
    return tuple(
        fixture
        for group in ALL_GROUPS
        for fixture in fixture_cases(group)
        if fixture.rule == rule
        and (fixture.case == case or fixture.case.startswith(f"{case}-"))
    )


def fixtures_of(rule: str) -> tuple[FixtureCase, ...]:
    """Return every fixture that exercises ``rule``."""
    return tuple(
        fixture
        for group in ALL_GROUPS
        for fixture in fixture_cases(group)
        if fixture.rule == rule
    )


def _spec_subsections(kind: str) -> dict[str, list[str]]:
    subsections: dict[str, list[str]] = {}
    current: list[str] | None = None
    prefix = f"{SPEC_HEADING_MARK}{kind}: "
    for line in SPEC.read_text(encoding="utf-8").split("\n"):
        if line.startswith(SPEC_HEADING_MARK):
            current = None
            if line.startswith(prefix):
                current = subsections.setdefault(line[len(prefix) :].strip(), [])
        elif current is not None:
            current.append(line)
    return subsections


def _spec_rows(kind: str, rule: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in _spec_subsections(kind).get(rule, []):
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append(cells)
    return [
        row
        for row in rows[SPEC_TABLE_PREAMBLE_ROWS:]
        if row and not set(row[0]) <= set("-: ")
    ]


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
    """Return a yaml value that the key's domain, as the spec states it, does not hold."""
    form = load_form_check()
    member = form.Key(key)
    if key in _spec_enumerated_rows():
        return OUTSIDE_PREFIX + sorted(spec_key_values(key))[0]
    if member is form.Key.TITLE:
        return " ".join([OUTSIDE_PREFIX.strip("-")] * (title_word_limit() + 1))
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
