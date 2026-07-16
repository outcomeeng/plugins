"""Reviewing-changes policy module — canonical schema.

The single source of truth for the ``review-result`` shape that the
review-changes skill produces. Declares:

- ``SCHEMA_VERSION`` — the wire-format version constant.
- ``Severity``, ``Concern`` enums (``StrEnum``) — the wire vocabularies
  a review-result document may carry.
- Frozen ``Finding`` and ``ReviewResult`` dataclasses — values that cross
  the parse → validate → render boundary.
- ``ReviewResultValidationError`` — raised on every schema violation.
- ``parse_json``, ``parse_finding_json``, ``to_json_dict``,
  ``from_json_dict`` — the parser entry points. ``parse_finding_json``
  validates one streamed finding (legacy compatibility path for
  ``journal_emit.py finding-reported``); ``parse_json``
  validates a whole document. Both surface malformed input as exceptions
  before any journal append.

Stdlib-only. Mirrors the marketplace's verdict-toolchain precedent.

Tested with:

- Conforming review-result JSON with findings -> returns ``ReviewResult``.
- Conforming review-result JSON with empty findings -> returns an empty tuple.
- Missing required keys -> raises ``ReviewResultValidationError`` naming the key.
- Unknown severity and concern values -> names the value and allowed set.
- Malformed JSON -> raises ``ReviewResultValidationError``.
- Round trips through ``to_json_dict`` and ``from_json_dict`` -> preserve equality.

A review carries findings only — no summary, acknowledgement, decision, or
verdict field. The journal-rendered findings surface is the review's whole
human surface, the same shape the audit kind produces.
"""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

SCHEMA_VERSION = 4
DOCUMENT_SCHEMA_VERSION_FIELD = "schema_version"
DOCUMENT_FINDINGS_FIELD = "findings"
FINDING_ID_FIELD = "id"
FINDING_CONCERN_FIELD = "concern"
FINDING_SEVERITY_FIELD = "severity"
FINDING_FILE_FIELD = "file"
FINDING_LINE_FIELD = "line"
FINDING_RULE_FIELD = "rule"
FINDING_MESSAGE_FIELD = "message"
FINDING_ACTION_FIELD = "action"
FINDING_ID_PREFIX = "F-"
FINDING_ID_DIGITS = 3
SEVERITY_BLOCKING = "blocking"
SEVERITY_DEBT = "debt"
CONCERN_CONSISTENCY = "consistency"
CONCERN_SECURITY = "security"
CONCERN_PERFORMANCE = "performance"
CONCERN_EVIDENCE = "evidence"
CONCERN_ARCHITECTURE = "architecture"
RULE_CITATION_SPEC_ASSERTION = "spec-assertion"
RULE_CITATION_DECISION = "decision"
RULE_CITATION_PLUGIN_SKILL = "plugin-skill"
RULE_CITATION_ROOT_GUIDE = "root-guide"


class Severity(StrEnum):
    """Finding severity — one of ``blocking``, ``debt``.

    ``blocking`` marks a defect with evidence of a deterministic merge-safety
    consequence; ``debt`` marks a real defect whose evidence does not establish
    that consequence. The reviewer judges validity and severity only.
    """

    BLOCKING = SEVERITY_BLOCKING
    DEBT = SEVERITY_DEBT


class Concern(StrEnum):
    """The five categories a finding may classify under, grouped by
    three axes:

    - What the code does vs. what it is supposed to do: ``consistency``,
      ``security``, ``performance``.
    - How we know it does what it is supposed to do: ``evidence``.
    - How it is structured: ``architecture``.

    The set is closed: any finding whose ``concern`` is outside this
    enumeration is rejected by the parser with the unknown value and the
    full allowed set surfaced in the error message.
    """

    CONSISTENCY = CONCERN_CONSISTENCY
    SECURITY = CONCERN_SECURITY
    PERFORMANCE = CONCERN_PERFORMANCE
    EVIDENCE = CONCERN_EVIDENCE
    ARCHITECTURE = CONCERN_ARCHITECTURE


class RuleCitationFamily(StrEnum):
    """The closed citation families accepted by ``Finding.rule``."""

    SPEC_ASSERTION = RULE_CITATION_SPEC_ASSERTION
    DECISION = RULE_CITATION_DECISION
    PLUGIN_SKILL = RULE_CITATION_PLUGIN_SKILL
    ROOT_GUIDE = RULE_CITATION_ROOT_GUIDE


class ReviewResultValidationError(ValueError):
    """Raised when a review-result document does not conform to the schema.

    Raised by the legacy ``journal_emit.py finding-reported`` path; agents consume the error message verbatim to correlate
    the failure with the finding they just emitted and re-emit before that
    finding's journal append.
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

    Holds the (possibly empty) tuple of findings and the schema version.
    A review carries findings only — no summary or acknowledgement field —
    so the journal-rendered findings surface is the review's whole surface.
    Frozen so the parse → validate hand-off cannot mutate the value silently.
    """

    schema_version: int
    findings: tuple[Finding, ...]


# Required keys at the document level. ``findings`` is required and may be
# an empty list.
_REQUIRED_DOCUMENT_KEYS = (
    DOCUMENT_SCHEMA_VERSION_FIELD,
    DOCUMENT_FINDINGS_FIELD,
)

# Required keys per finding. ``action`` carries the Required change for
# both ``blocking`` and ``debt`` findings; the render templates label it
# uniformly.
_REQUIRED_FINDING_KEYS = (
    FINDING_ID_FIELD,
    FINDING_CONCERN_FIELD,
    FINDING_SEVERITY_FIELD,
    FINDING_FILE_FIELD,
    FINDING_LINE_FIELD,
    FINDING_RULE_FIELD,
    FINDING_MESSAGE_FIELD,
    FINDING_ACTION_FIELD,
)

# Accepted ``Finding.rule`` citation forms. A rule must cite an existing rule in
# the spec-tree or skill ecosystem; the parser verifies both the cited file and
# the cited assertion/rule slug where the citation carries one.
_SPEC_ASSERTION_RE = re.compile(
    r"(?P<path>spx/[^\s:]+\.md):"
    r"(?P<kind>ALWAYS|NEVER|MUST|SCENARIO|MAPPING|CONFORMANCE|PROPERTY|COMPLIANCE|AUDIT):"
    r"(?P<index>[1-9][0-9]*)"
)
_DECISION_RE = re.compile(r"(?P<path>spx/[^\s:]+\.(?:adr|pdr)\.md)")
_PLUGIN_SKILL_RE = re.compile(
    r"plugins/(?P<plugin>[A-Za-z0-9_-]+)/skills/(?P<skill>[A-Za-z0-9_-]+)/"
    r"SKILL\.md:(?P<slug>[A-Za-z0-9][A-Za-z0-9_-]*)"
)
_ROOT_RULE_RE = re.compile(
    r"(?P<path>(?:AGENTS|CLAUDE)\.md):(?P<slug>[A-Za-z0-9][A-Za-z0-9_-]*)"
)
_FINDING_ID_RE = re.compile(
    rf"{re.escape(FINDING_ID_PREFIX)}\d{{{FINDING_ID_DIGITS}}}",
    re.ASCII,
)
_SECTION_TITLES = {
    "SCENARIO": "Scenarios",
    "MAPPING": "Mappings",
    "CONFORMANCE": "Conformance",
    "PROPERTY": "Properties",
    "COMPLIANCE": "Compliance",
    "AUDIT": "Audit",
}


def parse_json(text: str) -> ReviewResult:
    """Parse a JSON document into a :class:`ReviewResult`.

    Pipeline:

    1. ``json.loads`` — surface a ``ReviewResultValidationError`` on
       malformed JSON (the parser error message is included).
    2. Top-level shape check — every required key is present, types
       conform.
    3. ``from_json_dict`` — convert to the frozen dataclass, parsing
       enums and findings along the way.

    Validation is enforced inside this function so a caller validating a
    whole document surfaces violations before use; the streaming review
    validates one finding at a time through ``parse_finding_json``. The
    journal channel's append and seal are the durable validity signal for the
    recorded run.
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


def parse_finding_json(text: str) -> Finding:
    """Parse and validate one finding JSON object into a :class:`Finding`.

    The streaming review appends a ``finding-reported`` event the instant it
    raises each finding, so it emits one finding JSON document at a time.
    This remains available for the legacy ``journal_emit.py finding-reported`` path before the event is appended — the same enum, required-key, and
    ``rule``-citation checks ``parse_json`` applies to a whole document,
    scoped to one finding. Every violation raises
    :class:`ReviewResultValidationError`, so a malformed finding is surfaced
    before any journal append, never appended.
    """
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReviewResultValidationError(f"invalid JSON: {exc.msg}") from exc
    return _parse_finding(raw)


def from_json_dict(data: dict[str, Any]) -> ReviewResult:
    """Parse a :class:`ReviewResult` from a JSON-compatible dict.

    Validates required keys and enum membership for ``severity`` per
    finding and ``concern`` per finding. Each violation raises
    :class:`ReviewResultValidationError` with a message that names the
    offending value and (for enum violations) the allowed set.
    """
    _require_keys(data, _REQUIRED_DOCUMENT_KEYS)
    schema_version = _require_int(data, DOCUMENT_SCHEMA_VERSION_FIELD)
    if schema_version != SCHEMA_VERSION:
        raise ReviewResultValidationError(
            f"unsupported schema_version {schema_version}; expected {SCHEMA_VERSION}"
        )

    findings_raw = data[DOCUMENT_FINDINGS_FIELD]
    if not isinstance(findings_raw, list):
        raise ReviewResultValidationError("findings must be a JSON array")
    findings = tuple(_parse_finding(entry) for entry in findings_raw)

    return ReviewResult(
        schema_version=schema_version,
        findings=findings,
    )


def to_json_dict(result: ReviewResult) -> dict[str, Any]:
    """Serialize a :class:`ReviewResult` to a JSON-compatible dict.

    Output shape matches the input shape :func:`from_json_dict` accepts;
    ``json.dumps`` on the result produces a wire payload that
    ``parse_json`` round-trips back to an equal instance.
    """
    return {
        DOCUMENT_SCHEMA_VERSION_FIELD: result.schema_version,
        DOCUMENT_FINDINGS_FIELD: [finding_to_json_dict(f) for f in result.findings],
    }


def finding_to_json_dict(finding: Finding) -> dict[str, Any]:
    """Serialize one source-contract finding to its JSON-compatible shape."""
    return {
        FINDING_ID_FIELD: finding.id,
        FINDING_CONCERN_FIELD: str(finding.concern),
        FINDING_SEVERITY_FIELD: str(finding.severity),
        FINDING_FILE_FIELD: finding.file,
        FINDING_LINE_FIELD: finding.line,
        FINDING_RULE_FIELD: finding.rule,
        FINDING_MESSAGE_FIELD: finding.message,
        FINDING_ACTION_FIELD: finding.action,
    }


def _parse_finding(data: Any) -> Finding:
    if not isinstance(data, dict):
        raise ReviewResultValidationError("finding must be a JSON object")
    _require_keys(data, _REQUIRED_FINDING_KEYS)
    concern_raw = _require_str(data, FINDING_CONCERN_FIELD)
    concern = _parse_enum(concern_raw, Concern, field=FINDING_CONCERN_FIELD)
    severity_raw = _require_str(data, FINDING_SEVERITY_FIELD)
    severity = _parse_enum(severity_raw, Severity, field=FINDING_SEVERITY_FIELD)
    line = _require_int(data, FINDING_LINE_FIELD)
    rule = _require_str(data, FINDING_RULE_FIELD)
    _validate_rule_citation(rule)
    finding_id = _require_str(data, FINDING_ID_FIELD)
    _validate_finding_id(finding_id)
    return Finding(
        id=finding_id,
        concern=concern,
        severity=severity,
        file=_require_str(data, FINDING_FILE_FIELD),
        line=line,
        rule=rule,
        message=_require_str(data, FINDING_MESSAGE_FIELD),
        action=_require_str(data, FINDING_ACTION_FIELD),
    )


def _validate_finding_id(finding_id: str) -> None:
    if not is_valid_finding_id(finding_id):
        raise ReviewResultValidationError(
            f"finding 'id' must match F-NNN; got {finding_id!r}"
        )


def is_valid_finding_id(finding_id: str) -> bool:
    """Return whether a finding identifier conforms to the wire grammar."""
    return _FINDING_ID_RE.fullmatch(finding_id) is not None


def format_finding_id(index: int) -> str:
    """Return the canonical wire identifier for a positive finding index."""
    if index < 1 or index >= 10**FINDING_ID_DIGITS:
        raise ValueError(
            f"finding index must fit {FINDING_ID_DIGITS} positive digits; got {index}"
        )
    return f"{FINDING_ID_PREFIX}{index:0{FINDING_ID_DIGITS}d}"


def is_supported_rule_citation_shape(rule: str) -> bool:
    """Return whether a citation has one of the accepted wire shapes."""
    return rule_citation_family(rule) is not None


def rule_citation_family(rule: str) -> RuleCitationFamily | None:
    """Classify one citation shape into the source-owned family vocabulary."""

    for family, pattern in (
        (RuleCitationFamily.SPEC_ASSERTION, _SPEC_ASSERTION_RE),
        (RuleCitationFamily.DECISION, _DECISION_RE),
        (RuleCitationFamily.PLUGIN_SKILL, _PLUGIN_SKILL_RE),
        (RuleCitationFamily.ROOT_GUIDE, _ROOT_RULE_RE),
    ):
        if pattern.fullmatch(rule) is not None:
            return family
    return None


def _validate_rule_citation(rule: str) -> None:
    """Reject ``rule`` values that do not cite a repository rule."""
    if not rule:
        raise ReviewResultValidationError(
            f"finding 'rule' must be a non-empty string; got {rule!r}"
        )
    family = rule_citation_family(rule)
    if family is RuleCitationFamily.SPEC_ASSERTION:
        match = _SPEC_ASSERTION_RE.fullmatch(rule)
        assert match is not None
        _validate_spec_assertion(match)
        return
    if family is RuleCitationFamily.DECISION:
        match = _DECISION_RE.fullmatch(rule)
        assert match is not None
        _validate_decision_path(match.group("path"), rule)
        _require_repo_file(match.group("path"), rule)
        return
    if family is RuleCitationFamily.PLUGIN_SKILL:
        match = _PLUGIN_SKILL_RE.fullmatch(rule)
        assert match is not None
        path = _resolve_plugin_skill_path(
            match.group("plugin"), match.group("skill"), rule
        )
        _validate_slug(path, match.group("slug"), rule)
        return
    if family is RuleCitationFamily.ROOT_GUIDE:
        match = _ROOT_RULE_RE.fullmatch(rule)
        assert match is not None
        _validate_slug(pathlib.Path(match.group("path")), match.group("slug"), rule)
        return
    raise ReviewResultValidationError(
        "finding 'rule' must be a verifiable citation such as "
        "'spx/<path>.md:ALWAYS:1', "
        "'plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>', "
        "or 'AGENTS.md:<rule-slug>'/'CLAUDE.md:<rule-slug>'; "
        f"got {rule!r}"
    )


def _validate_spec_assertion(match: re.Match[str]) -> None:
    path = pathlib.Path(match.group("path"))
    text = _require_repo_file(path, match.group(0))
    kind = match.group("kind")
    expected_index = int(match.group("index"))
    if kind in {"ALWAYS", "NEVER", "MUST"}:
        pattern = re.compile(rf"^\s*-\s*{kind}:", re.MULTILINE)
        assertion_count = len(pattern.findall(text))
    else:
        assertion_count = len(_section_assertions(text, _SECTION_TITLES[kind]))
    if assertion_count < expected_index:
        raise ReviewResultValidationError(
            f"finding 'rule' cites {kind}:{expected_index}, "
            f"but {path} does not contain that assertion"
        )


def _validate_decision_path(path: str, rule: str) -> None:
    filename = pathlib.PurePosixPath(path).name
    if filename.endswith(".adr.md"):
        stem = filename.removesuffix(".adr.md")
    elif filename.endswith(".pdr.md"):
        stem = filename.removesuffix(".pdr.md")
    else:
        raise ReviewResultValidationError(
            f"finding 'rule' cites an invalid decision file: {rule}"
        )
    index, separator, slug = stem.partition("-")
    if not separator or not index.isdigit() or int(index) <= 0 or not _is_slug(slug):
        raise ReviewResultValidationError(
            f"finding 'rule' cites an invalid decision file: {rule}"
        )


def _section_assertions(text: str, section_title: str) -> list[str]:
    assertions: list[str] = []
    in_section = False
    section_pattern = re.compile(rf"^\s*###\s+{re.escape(section_title)}\s*$")
    next_section_pattern = re.compile(r"^\s*#{1,3}\s+")
    for line in text.splitlines():
        if section_pattern.match(line):
            in_section = True
            continue
        if in_section and next_section_pattern.match(line):
            break
        if in_section and re.match(r"^\s*-\s+", line):
            assertions.append(line)
    return assertions


def _validate_slug(path: pathlib.Path, slug: str, rule: str) -> None:
    text = _require_repo_file(path, rule)
    if slug not in _declared_rule_slugs(text):
        raise ReviewResultValidationError(
            f"finding 'rule' cites slug {slug!r}, but {path} does not contain it"
        )


def _declared_rule_slugs(text: str) -> set[str]:
    slugs: set[str] = set()
    lines = text.splitlines()
    in_fence = False
    for line in lines:
        if _is_markdown_fence(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = _markdown_heading_text(line)
        if heading:
            slugs.add(_slugify(heading))
            continue
        tag = _pseudo_xml_tag(line)
        if tag:
            slugs.add(_slugify(tag))
    return {slug for slug in slugs if slug}


def _markdown_heading_text(line: str) -> str | None:
    stripped = line.lstrip()
    prefix_length = len(stripped) - len(stripped.lstrip("#"))
    if prefix_length < 1 or prefix_length > 6:
        return None
    if len(stripped) == prefix_length or stripped[prefix_length] != " ":
        return None
    return stripped[prefix_length:].strip().strip("#").strip()


def _is_markdown_fence(line: str) -> bool:
    return line.lstrip().startswith("```")


def _pseudo_xml_tag(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("<") or not stripped.endswith(">"):
        return None
    tag = stripped[1:-1]
    if tag.startswith("/") or " " in tag or not tag:
        return None
    if not (tag[0].isalpha() and all(char.isalnum() or char in "_-" for char in tag)):
        return None
    return tag


def _is_slug(text: str) -> bool:
    return bool(text) and all(char.isalnum() or char == "-" for char in text)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _resolve_plugin_skill_path(plugin: str, skill: str, rule: str) -> pathlib.Path:
    suffix = pathlib.Path(plugin) / "skills" / skill / "SKILL.md"
    candidates = (
        pathlib.Path("src") / "plugins" / suffix,
        pathlib.Path("dist") / "claude" / suffix,
        pathlib.Path("dist") / "codex" / suffix,
        *_runtime_plugin_skill_candidates(plugin, skill),
        *(ancestor / suffix for ancestor in pathlib.Path(__file__).resolve().parents),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ReviewResultValidationError(
        f"finding 'rule' cites a missing plugin skill file: {rule}"
    )


def _runtime_plugin_skill_candidates(
    plugin: str, skill: str
) -> tuple[pathlib.Path, ...]:
    return _runtime_plugin_skill_candidates_from(
        pathlib.Path(__file__).resolve(), plugin, skill
    )


def _runtime_plugin_skill_candidates_from(
    script_path: pathlib.Path, plugin: str, skill: str
) -> tuple[pathlib.Path, ...]:
    candidates: list[pathlib.Path] = []
    for ancestor in script_path.parents:
        plugin_root = ancestor / plugin
        candidates.extend(_installed_plugin_skill_candidates(plugin_root, skill))
        skills_dir = ancestor / "skills"
        if not skills_dir.is_dir():
            continue
        if ancestor.name != plugin and ancestor.parent.name != plugin:
            continue
        candidates.append(skills_dir / skill / "SKILL.md")
    return tuple(dict.fromkeys(candidates))


def _installed_plugin_skill_candidates(
    plugin_root: pathlib.Path, skill: str
) -> tuple[pathlib.Path, ...]:
    """Return direct and versioned skill paths beneath one plugin cache root."""
    if not plugin_root.is_dir():
        return ()

    skill_suffix = pathlib.Path("skills") / skill / "SKILL.md"
    candidates = [plugin_root / skill_suffix]
    version_roots = sorted(
        (entry for entry in plugin_root.iterdir() if entry.is_dir()),
        key=lambda entry: _version_sort_key(entry.name),
        reverse=True,
    )
    candidates.extend(version_root / skill_suffix for version_root in version_roots)
    return tuple(candidates)


def _version_sort_key(version: str) -> tuple[tuple[int, ...], str]:
    """Order semantic-looking cache versions without third-party packaging."""
    numeric_prefix = version.partition("-")[0]
    if all(part.isdigit() for part in numeric_prefix.split(".")):
        return tuple(int(part) for part in numeric_prefix.split(".")), version
    return (), version


def _require_repo_file(path: str | pathlib.Path, rule: str) -> str:
    repo_path = pathlib.Path(path)
    if repo_path.is_absolute():
        return _read_existing_file(repo_path, rule)
    if ".." in repo_path.parts:
        raise ReviewResultValidationError(
            f"finding 'rule' must cite a repository-relative file; got {rule!r}"
        )
    root = _repo_root()
    try:
        resolved = (root / repo_path).resolve(strict=True)
        resolved.relative_to(root)
        return _read_existing_file(resolved, rule)
    except ValueError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' must cite a repository-relative file; got {rule!r}"
        ) from exc
    except FileNotFoundError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cites a missing file: {repo_path}"
        ) from exc
    except OSError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cannot read cited file {repo_path}: {exc}"
        ) from exc


def _repo_root() -> pathlib.Path:
    cwd = pathlib.Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


def _read_existing_file(path: pathlib.Path, rule: str) -> str:
    try:
        if not path.is_file():
            raise ReviewResultValidationError(
                f"finding 'rule' cites a non-file path: {path}"
            )
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cites a missing file: {path}"
        ) from exc
    except OSError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cannot read cited file for {rule}: {exc}"
        ) from exc


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
    return cast(int, value)
