"""Audit verdict toolchain — canonical schema and rollup logic.

This module is the single source of truth for what an audit
verdict looks like. Every audit skill emits a JSON document that conforms
to the schema declared here. Companion CLI scripts validate, aggregate,
and journal-render that JSON; skills never hand-format markdown verdicts.

Status value space:

- Root-level overall (orchestrator decision): ``APPROVED`` | ``REJECTED`` |
  ``UNKNOWN``.
- Skill-level overall and per-row status (individual contribution): ``PASS``
  | ``FAIL`` | ``UNKNOWN``.
- Finding severity (per finding): ``REJECT`` | ``WARNING`` | ``INFO``. Only
  ``REJECT`` findings flip a row to ``FAIL``.

Rollup rule (``roll_up``): any ``FAIL`` or ``REJECTED`` child → ``REJECTED``.
Otherwise, if any child is ``UNKNOWN`` → ``UNKNOWN``. Otherwise → ``APPROVED``.

Portability: stdlib only — no third-party packages, no ``uv``, no
``outcomeeng_*`` imports. This script ships into consumer plugin trees where
only the standard library is available.

Tested inputs and error cases: ``test_verdict.compliance.l1.py`` exercises
valid wrapper and leaf verdict dicts, optional ``children``/``metadata``,
resolved and reopened finding arrays, JSON round trips, rollup combinations,
and row-status derivation. The same suite covers malformed JSON, non-object
documents, missing required keys, schema-version mismatches, unknown overall
values, unknown row statuses, unknown finding severities, and null metadata
values before this script is bundled.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = 1

ROOT_STATUSES: frozenset[str] = frozenset({"APPROVED", "REJECTED", "UNKNOWN"})
SKILL_STATUSES: frozenset[str] = frozenset({"PASS", "FAIL", "UNKNOWN"})
SEVERITIES: frozenset[str] = frozenset({"REJECT", "WARNING", "INFO"})


class Status(StrEnum):
    """All status values a verdict or row may carry.

    The same enum covers root-level and skill-level statuses; the producing
    skill decides which subset applies. ``roll_up`` derives a root-level
    status from a sequence of child statuses regardless of whether each
    child is root-level or skill-level — both vocabularies coexist in the
    rollup logic.
    """

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Severity(StrEnum):
    """Finding severity. Only ``REJECT`` findings cause a row to ``FAIL``.

    Member names and wire values are both uppercase, matching the
    :class:`Status` convention so that ``finding.severity == "REJECT"``
    and ``status == "PASS"`` are consistent equality checks across the
    schema.
    """

    REJECT = "REJECT"
    WARNING = "WARNING"
    INFO = "INFO"


class VerdictValidationError(ValueError):
    """Raised when a verdict dict does not conform to the schema."""


@dataclass(frozen=True)
class Finding:
    """One audit finding within a row.

    ``line`` is ``None`` when the finding is whole-file rather than
    pinned to a specific line. ``id`` is unique within its containing
    verdict and stable across re-runs when the underlying finding
    persists (see the orchestrator's regression-detection helpers).
    """

    id: str
    file: str
    line: int | None
    rule: str
    severity: Severity
    message: str


@dataclass(frozen=True)
class Row:
    """One concern's outcome within a verdict.

    ``name`` is a free-form string chosen by the producing skill (e.g.,
    ``scope``, ``evidence``, ``coupling``). Row names are not drawn from a
    marketplace-wide enum — orchestrator and dispatched skills name their
    rows independently. ``status`` is in ``SKILL_STATUSES``.
    """

    name: str
    status: Status
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class Verdict:
    """A complete audit verdict.

    Leaf verdicts (produced by dispatched audit skills) populate ``rows``
    and leave ``children`` empty; ``overall`` is in ``SKILL_STATUSES``.

    Wrapper verdicts (produced by the orchestrator) populate ``children``
    and may leave ``rows`` empty; ``overall`` is in ``ROOT_STATUSES`` and
    is the result of ``roll_up`` over child overalls.

    Mixed wrappers (with both rows and children) are permitted; the
    orchestrator-level rollup still applies.

    ``resolved`` and ``reopened`` are verdict-level finding lists used by
    callers that diff a current audit against a prior verdict (e.g., a
    PR-thread review-orchestrator). Both default to empty so a stateless
    audit run leaves them out of the rendered output. Their absence on the
    wire is tolerated by ``from_json_dict`` so verdicts emitted before
    these fields existed continue to parse.

    Not hashable. ``frozen=True`` prevents reassignment of fields, but the
    ``metadata`` dict field is mutable in place. The auto-generated
    ``__hash__`` would also fail on the dict at hash time. Explicit
    ``__hash__ = None`` marks the class unhashable up front so attempts
    to put a Verdict in a set or use it as a dict key fail with a clear
    TypeError("unhashable type: 'Verdict'") instead of a deeper failure.
    """

    schema_version: int
    skill: str
    target: str
    overall: Status
    rows: tuple[Row, ...] = ()
    children: tuple["Verdict", ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    resolved: tuple[Finding, ...] = ()
    reopened: tuple[Finding, ...] = ()

    __hash__ = None  # type: ignore[assignment]


def roll_up(child_overalls: list[Status]) -> Status:
    """Compute the orchestrator's overall from a sequence of child overalls.

    Operates over the union of ``ROOT_STATUSES`` and ``SKILL_STATUSES`` so
    that a wrapper can aggregate other wrappers and leaf verdicts in one
    pass. Returns a value in ``ROOT_STATUSES``.

    Rules:

    - Any child is ``FAIL`` or ``REJECTED`` → ``REJECTED``.
    - Else any child is ``UNKNOWN`` → ``UNKNOWN``.
    - Else (every child is ``PASS`` or ``APPROVED``) → ``APPROVED``.

    An empty list returns ``UNKNOWN`` because aggregating zero verdicts
    yields no signal.
    """
    if not child_overalls:
        return Status.UNKNOWN
    if any(c in (Status.FAIL, Status.REJECTED) for c in child_overalls):
        return Status.REJECTED
    if any(c == Status.UNKNOWN for c in child_overalls):
        return Status.UNKNOWN
    return Status.APPROVED


def row_status_from_findings(findings: tuple[Finding, ...]) -> Status:
    """Derive a row's status from its findings.

    ``FAIL`` if any finding has severity ``REJECT``; ``PASS`` otherwise.
    Warning and info findings do not cause ``FAIL``. ``UNKNOWN`` is never
    derived from findings — a row reaches ``UNKNOWN`` only when the
    producing skill cannot evaluate the concern.
    """
    if any(f.severity == Severity.REJECT for f in findings):
        return Status.FAIL
    return Status.PASS


def to_json_dict(verdict: Verdict) -> dict[str, Any]:
    """Serialize a ``Verdict`` to a JSON-compatible dict.

    The output is suitable for ``json.dumps``; nested ``Row`` and
    ``Finding`` instances are converted to dicts. ``children`` are
    serialized recursively. The shape is the canonical wire format
    every audit skill emits.
    """
    return {
        "schema_version": verdict.schema_version,
        "skill": verdict.skill,
        "target": verdict.target,
        "overall": str(verdict.overall),
        "rows": [
            {
                "name": row.name,
                "status": str(row.status),
                "findings": [finding_to_json_dict(finding) for finding in row.findings],
            }
            for row in verdict.rows
        ],
        "children": [to_json_dict(child) for child in verdict.children],
        "metadata": dict(verdict.metadata),
        "resolved": [finding_to_json_dict(finding) for finding in verdict.resolved],
        "reopened": [finding_to_json_dict(finding) for finding in verdict.reopened],
    }


def finding_to_json_dict(finding: Finding) -> dict[str, Any]:
    """Serialize one Finding to a JSON-compatible dict.

    Public so callers (tests, future helpers) build Finding-shaped wire
    dicts from the source-owned dataclass instead of duplicating the
    field set as inline literals. Used by ``to_json_dict`` for both
    row-level findings and the verdict-level ``resolved``/``reopened``
    lists so the wire shape is emitted from one source.
    """
    return {
        "id": finding.id,
        "file": finding.file,
        "line": finding.line,
        "rule": finding.rule,
        "severity": str(finding.severity),
        "message": finding.message,
    }


def from_json_dict(data: dict[str, Any]) -> Verdict:
    """Parse a ``Verdict`` from a JSON-compatible dict and validate the schema.

    Raises ``VerdictValidationError`` on:

    - Missing required keys (``schema_version``, ``skill``, ``target``,
      ``overall``).
    - Unknown ``overall`` value.
    - Row with unknown ``status`` value.
    - Finding with unknown ``severity`` value.
    - ``schema_version`` mismatch.

    Tolerates absent ``rows``, ``children``, and ``metadata`` (defaulted
    to empty).

    Does not validate the convention that leaf verdicts (with ``rows``
    and no ``children``) use ``SKILL_STATUSES`` while wrapper verdicts
    (with ``children``) use ``ROOT_STATUSES`` — a dispatched skill that
    accidentally emits ``APPROVED`` instead of ``PASS`` passes parsing
    and only surfaces in the rollup arithmetic (which handles both
    vocabularies gracefully). The convention is documented on
    ``Verdict``; enforcement is left to producer-side review.

    Consumer-side consequence: a caller writing
    ``verdict.overall in ROOT_STATUSES`` to discriminate "is this a
    wrapper?" returns ``False`` for a correctly-emitted leaf with
    ``overall == "PASS"``. Discriminate by structure (``verdict.children
    != ()``) rather than by the ``overall`` vocabulary.

    Coerces non-string scalar metadata values to ``str`` rather than
    raising: ``{"line_count": 42}`` parses as
    ``{"line_count": "42"}``, ``{"ratio": 0.5}`` parses as
    ``{"ratio": "0.5"}``. The ``Verdict.metadata`` field is typed
    ``dict[str, str]``, so the coercion preserves that contract for
    downstream readers.

    Rejects ``None`` metadata values outright. Coercing ``None`` to the
    string ``"None"`` would silently turn ``{"flag": None}`` into
    ``{"flag": "None"}`` — a value indistinguishable from an intentional
    string. Downstream code testing ``metadata.get("flag") is None``
    would then incorrectly find a value. Callers that mean "no value"
    must omit the metadata key rather than emit a JSON ``null``.
    """
    _require_keys(data, ("schema_version", "skill", "target", "overall"))
    schema_version = _require_int(data, "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise VerdictValidationError(
            f"unsupported schema_version {schema_version}; expected {SCHEMA_VERSION}"
        )
    overall_raw = _require_str(data, "overall")
    if overall_raw not in ROOT_STATUSES and overall_raw not in SKILL_STATUSES:
        raise VerdictValidationError(
            f"invalid overall {overall_raw!r}; expected one of "
            f"{sorted(ROOT_STATUSES | SKILL_STATUSES)}"
        )
    rows_raw = data.get("rows", [])
    if not isinstance(rows_raw, list):
        raise VerdictValidationError("rows must be an array")
    rows = tuple(_parse_row(r) for r in rows_raw)
    children_raw = data.get("children", [])
    if not isinstance(children_raw, list):
        raise VerdictValidationError("children must be an array")
    children = tuple(from_json_dict(c) for c in children_raw)
    metadata_raw = data.get("metadata", {})
    if not isinstance(metadata_raw, dict):
        raise VerdictValidationError("metadata must be an object")
    metadata: dict[str, str] = {}
    for raw_key, raw_value in metadata_raw.items():
        if raw_value is None:
            raise VerdictValidationError(
                f"metadata value for {raw_key!r} is null; omit the key "
                "instead of emitting None"
            )
        metadata[str(raw_key)] = str(raw_value)
    resolved_raw = data.get("resolved", [])
    if not isinstance(resolved_raw, list):
        raise VerdictValidationError("resolved must be an array")
    resolved = tuple(_parse_finding(f) for f in resolved_raw)
    reopened_raw = data.get("reopened", [])
    if not isinstance(reopened_raw, list):
        raise VerdictValidationError("reopened must be an array")
    reopened = tuple(_parse_finding(f) for f in reopened_raw)
    return Verdict(
        schema_version=schema_version,
        skill=_require_str(data, "skill"),
        target=_require_str(data, "target"),
        overall=Status(overall_raw),
        rows=rows,
        children=children,
        metadata=metadata,
        resolved=resolved,
        reopened=reopened,
    )


def parse_json(text: str) -> Verdict:
    """Parse a JSON document into a ``Verdict``.

    Convenience wrapper around ``json.loads`` + ``from_json_dict``.
    Raises ``VerdictValidationError`` for both JSON syntax errors and
    schema violations.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VerdictValidationError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise VerdictValidationError("verdict document must be a JSON object")
    return from_json_dict(data)


def dump_json(verdict: Verdict, *, indent: int | None = 2) -> str:
    """Serialize a ``Verdict`` to a JSON string with stable key order.

    ``sort_keys=False`` preserves the natural schema key order from
    ``to_json_dict`` (schema_version → skill → target → overall → rows →
    children → metadata → resolved → reopened) rather than reordering
    alphabetically; downstream readers expecting that order — including the
    canonical example JSON in skill prose — stay aligned.
    """
    return json.dumps(to_json_dict(verdict), indent=indent, sort_keys=False)


def _parse_row(data: Any) -> Row:
    if not isinstance(data, dict):
        raise VerdictValidationError("row must be a JSON object")
    _require_keys(data, ("name", "status"))
    status_raw = _require_str(data, "status")
    if status_raw not in SKILL_STATUSES:
        raise VerdictValidationError(
            f"invalid row status {status_raw!r}; expected one of {sorted(SKILL_STATUSES)}"
        )
    findings_raw = data.get("findings", [])
    if not isinstance(findings_raw, list):
        raise VerdictValidationError("findings must be an array")
    findings = tuple(_parse_finding(f) for f in findings_raw)
    return Row(
        name=_require_str(data, "name"),
        status=Status(status_raw),
        findings=findings,
    )


def _parse_finding(data: Any) -> Finding:
    if not isinstance(data, dict):
        raise VerdictValidationError("finding must be a JSON object")
    _require_keys(data, ("id", "file", "rule", "severity", "message"))
    severity_raw = _require_str(data, "severity")
    if severity_raw not in SEVERITIES:
        raise VerdictValidationError(
            f"invalid severity {severity_raw!r}; expected one of {sorted(SEVERITIES)}"
        )
    line_raw = data.get("line")
    if line_raw is not None and (
        isinstance(line_raw, bool) or not isinstance(line_raw, int)
    ):
        raise VerdictValidationError("finding.line must be an integer or null")
    return Finding(
        id=_require_str(data, "id"),
        file=_require_str(data, "file"),
        line=line_raw,
        rule=_require_str(data, "rule"),
        severity=Severity(severity_raw),
        message=_require_str(data, "message"),
    )


def _require_keys(data: dict[str, Any], keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise VerdictValidationError(f"missing required keys: {missing}")


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise VerdictValidationError(
            f"{key!r} must be a string, got {type(value).__name__}"
        )
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    value = data[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise VerdictValidationError(
            f"{key!r} must be an integer, got {type(value).__name__}"
        )
    return value
