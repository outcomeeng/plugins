"""Reviewing-changes policy module — canonical schema.

The single source of truth for the ``review-result`` shape that the
review-changes skill produces. Declares:

- ``SCHEMA_VERSION`` — the wire-format version constant.
- ``Severity``, ``Concern`` enums (``StrEnum``) — the wire vocabularies
  a review-result document may carry.
- Frozen ``Finding`` and ``ReviewResult`` dataclasses — values that cross
  the parse → validate → render boundary.
- ``ReviewResultValidationError`` — raised on every schema violation.
- ``parse_json``, ``to_json_dict``, ``from_json_dict`` — the parser entry
  points. ``parse_json`` validates the schema before returning, so direct
  Python callers that bypass the arbiter CLI still surface malformed
  documents as exceptions.

Stdlib-only. Mirrors the verdict-toolchain precedent in
``plugins/spec-tree/skills/audit/scripts/verdict.py``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = 3


class Severity(StrEnum):
    """Finding severity — one of ``blocking``, ``debt``.

    ``blocking`` marks a merge-safety defect; ``debt`` marks a real defect
    that does not jeopardize merge safety. The reviewer judges validity and
    severity; the author judges disposition (fix-in-PR or track-out-of-scope).
    """

    BLOCKING = "blocking"
    DEBT = "debt"


class Concern(StrEnum):
    """The six categories a finding may classify under, grouped by
    three axes:

    - What the code does vs. what it is supposed to do: ``consistency``,
      ``security``, ``performance``.
    - How we know it does what it is supposed to do: ``evidence``.
    - How it does what it is supposed to do: ``standards``,
      ``architecture``.

    The set is closed: any finding whose ``concern`` is outside this
    enumeration is rejected by the parser with the unknown value and the
    full allowed set surfaced in the error message.
    """

    CONSISTENCY = "consistency"
    SECURITY = "security"
    PERFORMANCE = "performance"
    EVIDENCE = "evidence"
    STANDARDS = "standards"
    ARCHITECTURE = "architecture"


class ReviewResultValidationError(ValueError):
    """Raised when a review-result document does not conform to the schema.

    Used by both the parser entry point and the arbiter CLI; agents
    consume the error message verbatim to correlate the failure with the
    JSON document they just emitted.
    """


@dataclass(frozen=True)
class Finding:
    """One review finding within a review result.

    Frozen so any mutation between parse and validate raises ``FrozenInstanceError``.

    Both ``blocking`` and ``debt`` findings render ``message`` as Evidence
    and ``action`` as the Required change, mirrored in the render templates.
    """

    id: str
    concern: Concern
    severity: Severity
    file: str
    line: int
    rule: str
    message: str
    action: str


@dataclass(frozen=True)
class ReviewResult:
    """A complete review result.

    Holds the (possibly empty) tuple of findings, an acknowledgement
    list, a free-form summary, and the schema version. Frozen so the
    parse → validate hand-off cannot mutate the value silently.
    """

    schema_version: int
    summary: str
    findings: tuple[Finding, ...]
    acknowledgements: tuple[str, ...]


# Required keys at the document level. ``acknowledgements`` and
# ``findings`` are required; both may be empty lists.
_REQUIRED_DOCUMENT_KEYS = (
    "schema_version",
    "summary",
    "findings",
    "acknowledgements",
)

# Required keys per finding. ``action`` carries the Required change for
# both ``blocking`` and ``debt`` findings; the render templates label it
# uniformly.
_REQUIRED_FINDING_KEYS = (
    "id",
    "concern",
    "severity",
    "file",
    "line",
    "rule",
    "message",
    "action",
)

# Accepted path-prefixes for ``Finding.rule`` citations. A rule must cite an
# existing rule in the spec-tree or skill ecosystem; the parser enforces the
# structural form here (a path beginning with one of these prefixes). The
# semantic check — that the cited rule actually exists at the referenced
# location — is the review prompt's concern and the future deterministic
# diff-reference check's concern; it is not enforced at parse time.
_RULE_CITATION_PREFIXES = (
    "spx/",
    "plugins/",
    "AGENTS.md",
    "CLAUDE.md",
    "SKILL.md",
)


def parse_json(text: str) -> ReviewResult:
    """Parse a JSON document into a :class:`ReviewResult`.

    Pipeline:

    1. ``json.loads`` — surface a ``ReviewResultValidationError`` on
       malformed JSON (the parser error message is included).
    2. Top-level shape check — every required key is present, types
       conform.
    3. ``from_json_dict`` — convert to the frozen dataclass, parsing
       enums and findings along the way.

    Validation is enforced inside this function (not only in the CLI) so
    Python callers that bypass ``validate_review_result.py`` still
    surface violations. The CLI is a thin shell over this parser.
    """
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReviewResultValidationError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ReviewResultValidationError(
            "review-result document must be a JSON object"
        )
    return from_json_dict(raw)


def from_json_dict(data: dict[str, Any]) -> ReviewResult:
    """Parse a :class:`ReviewResult` from a JSON-compatible dict.

    Validates required keys and enum membership for ``severity`` per
    finding and ``concern`` per finding. Each violation raises
    :class:`ReviewResultValidationError` with a message that names the
    offending value and (for enum violations) the allowed set.
    """
    _require_keys(data, _REQUIRED_DOCUMENT_KEYS)
    schema_version = _require_int(data, "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ReviewResultValidationError(
            f"unsupported schema_version {schema_version}; expected {SCHEMA_VERSION}"
        )

    summary = _require_str(data, "summary")

    findings_raw = data["findings"]
    if not isinstance(findings_raw, list):
        raise ReviewResultValidationError("findings must be a JSON array")
    findings = tuple(_parse_finding(entry) for entry in findings_raw)

    acks_raw = data["acknowledgements"]
    if not isinstance(acks_raw, list):
        raise ReviewResultValidationError("acknowledgements must be a JSON array")
    acknowledgements = tuple(_require_str_in_list(acks_raw, "acknowledgements"))

    return ReviewResult(
        schema_version=schema_version,
        summary=summary,
        findings=findings,
        acknowledgements=acknowledgements,
    )


def to_json_dict(result: ReviewResult) -> dict[str, Any]:
    """Serialize a :class:`ReviewResult` to a JSON-compatible dict.

    Output shape matches the input shape :func:`from_json_dict` accepts;
    ``json.dumps`` on the result produces a wire payload that
    ``parse_json`` round-trips back to an equal instance.
    """
    return {
        "schema_version": result.schema_version,
        "summary": result.summary,
        "findings": [_finding_to_dict(f) for f in result.findings],
        "acknowledgements": list(result.acknowledgements),
    }


def _finding_to_dict(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "concern": str(finding.concern),
        "severity": str(finding.severity),
        "file": finding.file,
        "line": finding.line,
        "rule": finding.rule,
        "message": finding.message,
        "action": finding.action,
    }


def _parse_finding(data: Any) -> Finding:
    if not isinstance(data, dict):
        raise ReviewResultValidationError("finding must be a JSON object")
    _require_keys(data, _REQUIRED_FINDING_KEYS)
    concern_raw = _require_str(data, "concern")
    concern = _parse_enum(concern_raw, Concern, field="concern")
    severity_raw = _require_str(data, "severity")
    severity = _parse_enum(severity_raw, Severity, field="severity")
    line = _require_int(data, "line")
    rule = _require_str(data, "rule")
    _validate_rule_citation(rule)
    return Finding(
        id=_require_str(data, "id"),
        concern=concern,
        severity=severity,
        file=_require_str(data, "file"),
        line=line,
        rule=rule,
        message=_require_str(data, "message"),
        action=_require_str(data, "action"),
    )


def _validate_rule_citation(rule: str) -> None:
    """Reject ``rule`` values that are not path-style citations.

    Accepts a string starting with one of ``_RULE_CITATION_PREFIXES``.
    Rejects empty strings, free-form prose, action text, and tracking
    locations. The semantic check (that the cited rule exists at the
    location) is not enforced here.
    """
    if not rule:
        raise ReviewResultValidationError("finding 'rule' must be a non-empty string")
    if not rule.startswith(_RULE_CITATION_PREFIXES):
        raise ReviewResultValidationError(
            f"finding 'rule' must be a path-style citation starting with one of "
            f"{list(_RULE_CITATION_PREFIXES)}; got {rule!r}"
        )


def _parse_enum(value: str, enum_cls: type[StrEnum], *, field: str) -> Any:
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = sorted(member.value for member in enum_cls)
        raise ReviewResultValidationError(
            f"unknown {field} {value!r}; allowed values: {allowed}"
        ) from exc


def _require_keys(data: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise ReviewResultValidationError(f"missing required key(s): {missing}")


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise ReviewResultValidationError(
            f"{key!r} must be a string, got {type(value).__name__}"
        )
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    value = data[key]
    # ``bool`` is a subclass of ``int`` in Python; reject explicitly so
    # ``True`` / ``False`` does not silently coerce to ``1`` / ``0``.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReviewResultValidationError(
            f"{key!r} must be an integer, got {type(value).__name__}"
        )
    return value


def _require_str_in_list(items: list[Any], field: str) -> list[str]:
    out: list[str] = []
    for index, entry in enumerate(items):
        if not isinstance(entry, str):
            raise ReviewResultValidationError(
                f"{field}[{index}] must be a string, got {type(entry).__name__}"
            )
        out.append(entry)
    return out
