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
- The sibling ``agent-tokens.json`` file absent, unreadable, malformed JSON, a non-object JSON
  value, and missing the ``CLAUDE`` or ``CODEX`` key -> each prints its ``error:`` line on
  stderr and exits 2 with no traceback when the module loads; a complete file -> the
  generated-tree citation candidates derive from its tokens.

A review carries findings only — no summary, acknowledgement, decision, or
verdict field. The journal-rendered findings surface is the review's whole
human surface, the same shape the audit kind produces.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from enum import StrEnum
from types import ModuleType
from typing import Any, cast

SCHEMA_VERSION = 4

AGENT_TOKENS_PATH = pathlib.Path(__file__).with_name("agent-tokens.json")


def _sibling_provider(skill: str, module_name: str) -> ModuleType:
    """Load a sibling provider skill's script by the installed tree's layout."""
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    skills = pathlib.Path(__file__).resolve().parents[2]
    path = skills / skill / "scripts" / f"{module_name}.py"
    if not path.is_file():
        raise ImportError(
            f"cannot load {module_name}: {path} does not exist. The {skill} "
            "skill must be installed beside review-changes under the same "
            "skills directory; reinstall the product-tree plugin so every "
            "skill is present."
        )
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"cannot load {module_name} from {path}: Python found no import "
            "loader for the file. Confirm it is a readable .py module and "
            "reinstall the product-tree plugin if it is damaged."
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        # A module that failed to execute never stays cached as if it loaded.
        del sys.modules[spec.name]
        raise
    return module


# The update-instruction-block skill owns the agent-tokens loader; this module passes it the
# data file the build renders beside this script.
_TOKENS_PROVIDER = _sibling_provider("update-instruction-block", "instruction_block")
AgentTokensLoadError = _TOKENS_PROVIDER.AgentTokensLoadError
load_agent_tokens = _TOKENS_PROVIDER.load_agent_tokens
AGENT_TOKENS_REQUIRED_KEYS = _TOKENS_PROVIDER.AGENT_TOKENS_REQUIRED_KEYS
AGENT_TOKENS_REINSTALL_ADVICE = _TOKENS_PROVIDER.AGENT_TOKENS_REINSTALL_ADVICE
AGENT_TOKENS_ERROR_PREFIX = _TOKENS_PROVIDER.AGENT_TOKENS_ERROR_PREFIX
AGENT_TOKENS_NOT_FOUND = _TOKENS_PROVIDER.AGENT_TOKENS_NOT_FOUND
AGENT_TOKENS_UNREADABLE = _TOKENS_PROVIDER.AGENT_TOKENS_UNREADABLE
AGENT_TOKENS_NOT_VALID_JSON = _TOKENS_PROVIDER.AGENT_TOKENS_NOT_VALID_JSON
AGENT_TOKENS_NOT_AN_OBJECT = _TOKENS_PROVIDER.AGENT_TOKENS_NOT_AN_OBJECT
AGENT_TOKENS_LACKS_KEYS = _TOKENS_PROVIDER.AGENT_TOKENS_LACKS_KEYS
AGENT_TOKENS_FOUND_TYPE_OPEN = _TOKENS_PROVIDER.AGENT_TOKENS_FOUND_TYPE_OPEN
AGENT_TOKENS_KEYS_FOUND_OPEN = _TOKENS_PROVIDER.AGENT_TOKENS_KEYS_FOUND_OPEN
AGENT_TOKENS_NO_KEYS = _TOKENS_PROVIDER.AGENT_TOKENS_NO_KEYS
AGENT_TOKENS_LOAD_FAILURE_EXIT_CODE = (
    _TOKENS_PROVIDER.AGENT_TOKENS_LOAD_FAILURE_EXIT_CODE
)
_AGENT_TOKENS = _TOKENS_PROVIDER.load_agent_tokens_or_exit(AGENT_TOKENS_PATH)
GENERATED_TREE_AGENT_TOKENS = tuple(
    _AGENT_TOKENS[key] for key in AGENT_TOKENS_REQUIRED_KEYS
)


class Severity(StrEnum):
    """Finding severity — one of ``blocking``, ``debt``.

    ``blocking`` marks a merge-safety defect; ``debt`` marks a real defect
    that does not jeopardize merge safety. The reviewer judges validity and
    severity; the author judges the disposition of each ``blocking`` finding,
    and a ``debt`` finding on text the changeset touches or invalidates takes
    its disposition from the ruling of a position above the changeset's author.
    """

    BLOCKING = "blocking"
    DEBT = "debt"


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

    CONSISTENCY = "consistency"
    SECURITY = "security"
    PERFORMANCE = "performance"
    EVIDENCE = "evidence"
    ARCHITECTURE = "architecture"


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
    "schema_version",
    "findings",
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

# Accepted ``Finding.rule`` citation forms. A rule must cite an existing rule in
# the product-tree or skill ecosystem; the parser verifies both the cited file and
# the cited assertion/rule slug where the citation carries one.
SPEC_ASSERTION_KINDS: tuple[str, ...] = (
    "ALWAYS",
    "NEVER",
    "MUST",
    "SCENARIO",
    "MAPPING",
    "CONFORMANCE",
    "PROPERTY",
    "AUDIT",
)
_SPEC_ASSERTION_RE = re.compile(
    r"(?P<path>spx/[^\s:]+\.md):"
    rf"(?P<kind>{'|'.join(SPEC_ASSERTION_KINDS)}):"
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
_FINDING_ID_RE = re.compile(r"F-\d{3}", re.ASCII)
# The accepted ``Finding.rule`` citation families, in the order the parser
# tries them. Each family names one path-style form; every other value is a
# rejected non-citation.
RULE_CITATION_FAMILIES: tuple[str, ...] = (
    "spec-assertion",
    "decision",
    "plugin-skill",
    "root-rule",
)
_RULE_CITATION_FAMILY_RES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("spec-assertion", _SPEC_ASSERTION_RE),
    ("decision", _DECISION_RE),
    ("plugin-skill", _PLUGIN_SKILL_RE),
    ("root-rule", _ROOT_RULE_RE),
)


def rule_citation_family(rule: str) -> str | None:
    """Return the citation family whose form ``rule`` matches, or ``None``.

    Form classification only: a value in a family may still be rejected when
    the cited file, assertion, or rule slug does not exist.
    """
    for family, pattern in _RULE_CITATION_FAMILY_RES:
        if pattern.fullmatch(rule):
            return family
    return None


_SLUG_LIST_LIMIT = 40

_SECTION_TITLES = {
    "SCENARIO": "Scenarios",
    "MAPPING": "Mappings",
    "CONFORMANCE": "Conformance",
    "PROPERTY": "Properties",
    "AUDIT": "Audit",
}
_RULE_MARKERS = ("ALWAYS", "NEVER", "MUST", "REQUIRED", "BLOCKING", "STOP")
_RULE_BEARING_PSEUDO_XML_TAGS = frozenset(
    {
        "api_surface",
        "principles",
    }
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

    Validation is enforced inside this function so a caller validating a
    whole document surfaces violations before use; the streaming review
    validates one finding at a time through ``parse_finding_json``. The
    journal channel's append and seal are the durable validity signal for the
    recorded run.
    """
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReviewResultValidationError(_invalid_json_message(exc)) from exc
    if not isinstance(raw, dict):
        raise ReviewResultValidationError(
            "review-result document must be a JSON object with keys "
            f"{list(_REQUIRED_DOCUMENT_KEYS)}, got {type(raw).__name__}. "
            "Wrap the findings in an object that also carries "
            f"'schema_version': {SCHEMA_VERSION}."
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
        raise ReviewResultValidationError(_invalid_json_message(exc)) from exc
    return _parse_finding(raw)


def _invalid_json_message(exc: json.JSONDecodeError) -> str:
    return (
        f"invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno} "
        f"(character {exc.pos}). Correct the syntax at that position and "
        "emit the document again."
    )


def _where(data: dict[str, Any]) -> str:
    """Label a finding by its id when it carries a string one."""
    finding_id = data.get("id")
    if isinstance(finding_id, str) and finding_id:
        return f"finding {finding_id}"
    return "finding"


def from_json_dict(data: dict[str, Any]) -> ReviewResult:
    """Parse a :class:`ReviewResult` from a JSON-compatible dict.

    Validates required keys and enum membership for ``severity`` per
    finding and ``concern`` per finding. Each violation raises
    :class:`ReviewResultValidationError` with a message that names the
    offending value and (for enum violations) the allowed set.
    """
    _require_keys(data, _REQUIRED_DOCUMENT_KEYS, where="review-result document")
    schema_version = _require_int(data, "schema_version", where="document")
    if schema_version != SCHEMA_VERSION:
        raise ReviewResultValidationError(
            f"unsupported schema_version {schema_version}; expected "
            f"{SCHEMA_VERSION}. Set 'schema_version' to {SCHEMA_VERSION} and "
            "emit the document in the current shape."
        )

    findings_raw = data["findings"]
    if not isinstance(findings_raw, list):
        raise ReviewResultValidationError(
            "'findings' must be a JSON array (empty when there are no "
            f"findings), got {type(findings_raw).__name__}."
        )
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
        "schema_version": result.schema_version,
        "findings": [_finding_to_dict(f) for f in result.findings],
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
        raise ReviewResultValidationError(
            "a finding must be a JSON object with keys "
            f"{list(_REQUIRED_FINDING_KEYS)}, got {type(data).__name__}."
        )
    where = _where(data)
    _require_keys(data, _REQUIRED_FINDING_KEYS, where=where)
    concern_raw = _require_str(data, "concern", where=where)
    concern = _parse_enum(concern_raw, Concern, field="concern", where=where)
    severity_raw = _require_str(data, "severity", where=where)
    severity = _parse_enum(severity_raw, Severity, field="severity", where=where)
    line = _require_int(data, "line", where=where)
    rule = _require_str(data, "rule", where=where)
    _validate_rule_citation(rule)
    finding_id = _require_str(data, "id", where=where)
    _validate_finding_id(finding_id)
    return Finding(
        id=finding_id,
        concern=concern,
        severity=severity,
        file=_require_str(data, "file", where=where),
        line=line,
        rule=rule,
        message=_require_str(data, "message", where=where),
        action=_require_str(data, "action", where=where),
    )


def _validate_finding_id(finding_id: str) -> None:
    if not _FINDING_ID_RE.fullmatch(finding_id):
        raise ReviewResultValidationError(
            f"finding 'id' must match F-NNN (F- followed by three digits, "
            f"for example F-001); got {finding_id!r}. Rename the id and emit "
            "the finding again."
        )


def _validate_rule_citation(rule: str) -> None:
    """Reject ``rule`` values that do not cite a repository rule."""
    if not rule:
        raise ReviewResultValidationError(
            "finding 'rule' must be a non-empty string citing a repository "
            "rule, for example 'spx/<path>.md:ALWAYS:1' or "
            "'plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>'; got ''."
        )
    if match := _SPEC_ASSERTION_RE.fullmatch(rule):
        _validate_spec_assertion(match)
        return
    if match := _DECISION_RE.fullmatch(rule):
        _validate_decision_path(match.group("path"), rule)
        _require_repo_file(match.group("path"), rule)
        return
    if match := _PLUGIN_SKILL_RE.fullmatch(rule):
        path = _resolve_plugin_skill_path(
            match.group("plugin"), match.group("skill"), rule
        )
        _validate_slug(path, match.group("slug"), rule)
        return
    if match := _ROOT_RULE_RE.fullmatch(rule):
        _validate_slug(pathlib.Path(match.group("path")), match.group("slug"), rule)
        return
    raise ReviewResultValidationError(
        "finding 'rule' must be a verifiable citation such as "
        "'spx/<path>.md:ALWAYS:1', "
        "'plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>', "
        "or 'AGENTS.md:<rule-slug>'/'CLAUDE.md:<rule-slug>'; "
        f"got {rule!r}. Accepted citation families: "
        f"{', '.join(RULE_CITATION_FAMILIES)}. Rewrite the rule in one of "
        "those forms."
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
            f"but {path} does not contain that assertion; it holds "
            f"{assertion_count} {kind} assertion(s). Cite an index from 1 to "
            f"{assertion_count} or the file's actual assertion kind."
        )


def _validate_decision_path(path: str, rule: str) -> None:
    filename = pathlib.PurePosixPath(path).name
    if filename.endswith(".adr.md"):
        stem = filename.removesuffix(".adr.md")
    elif filename.endswith(".pdr.md"):
        stem = filename.removesuffix(".pdr.md")
    else:
        raise ReviewResultValidationError(
            f"finding 'rule' cites an invalid decision file: {rule}; the "
            "filename must end in '.adr.md' or '.pdr.md'. Cite "
            "'spx/<path>/NN-<slug>.adr.md' or the '.pdr.md' equivalent."
        )
    index, separator, slug = stem.partition("-")
    if not separator or not index.isdigit() or int(index) <= 0 or not _is_slug(slug):
        raise ReviewResultValidationError(
            f"finding 'rule' cites an invalid decision file: {rule}; the "
            f"filename stem {stem!r} must be a positive integer index, a "
            "hyphen, then a slug of letters, digits, and hyphens (for example "
            "'21-example-decision'). Cite the decision file by its exact name."
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
    declared = sorted(_declared_rule_slugs(text))
    if slug not in declared:
        shown = declared[:_SLUG_LIST_LIMIT]
        more = len(declared) - len(shown)
        listing = ", ".join(shown) if shown else "none"
        if more > 0:
            listing += f", and {more} more"
        raise ReviewResultValidationError(
            f"finding 'rule' cites slug {slug!r}, but {path} does not contain "
            f"it; declared rule slugs: {listing}. Cite one of the declared "
            "slugs."
        )


def _declared_rule_slugs(text: str) -> set[str]:
    slugs: set[str] = set()
    lines = text.splitlines()
    in_fence = False
    for index, line in enumerate(lines):
        if _is_markdown_fence(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = _markdown_heading_text(line)
        if heading and _heading_section_has_rule_marker(lines, index):
            slugs.add(_slugify(heading))
            continue
        tag = _pseudo_xml_tag(line)
        if tag and _pseudo_xml_section_has_rule_marker(lines, index, tag):
            slugs.add(_slugify(tag))
    return {slug for slug in slugs if slug}


def _pseudo_xml_section_has_rule_marker(
    lines: list[str], tag_index: int, tag: str
) -> bool:
    if tag in _RULE_BEARING_PSEUDO_XML_TAGS:
        return True
    body: list[str] = []
    closing_tag = f"</{tag}>"
    for line in lines[tag_index + 1 :]:
        if line.strip() == closing_tag:
            break
        body.append(line)
    return any(_is_rule_marker_line(line) for line in body)


def _heading_section_has_rule_marker(lines: list[str], heading_index: int) -> bool:
    body: list[str] = []
    in_fence = False
    for line in lines[heading_index + 1 :]:
        if _is_markdown_fence(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if _markdown_heading_text(line):
            break
        body.append(line)
    return any(_is_rule_marker_line(line) for line in body)


def _is_rule_marker_line(line: str) -> bool:
    stripped = line.strip()
    bullet = stripped[2:].lstrip() if stripped.startswith(("- ", "* ")) else stripped
    while bullet and not (bullet[0].isalnum() or bullet[0] == "*"):
        bullet = bullet[1:].lstrip()
    for marker in _RULE_MARKERS:
        if bullet.startswith(f"{marker}:"):
            return True
        if bullet.startswith(f"**{marker}**"):
            rest = bullet[len(marker) + 4 :].lstrip()
            return rest.startswith(("-", ":"))
        if bullet.startswith(f"**{marker} "):
            return True
    return False


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
        *(
            pathlib.Path("dist") / token / suffix
            for token in GENERATED_TREE_AGENT_TOKENS
        ),
        *_runtime_plugin_skill_candidates(plugin, skill),
        *(ancestor / suffix for ancestor in pathlib.Path(__file__).resolve().parents),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise ReviewResultValidationError(
        f"finding 'rule' cites a missing plugin skill file: {rule}; searched "
        f"{searched}. Check the plugin and skill names in the citation "
        "against the installed skills."
    )


def _runtime_plugin_skill_candidates(
    plugin: str, skill: str
) -> tuple[pathlib.Path, ...]:
    candidates: list[pathlib.Path] = []
    for ancestor in pathlib.Path(__file__).resolve().parents:
        skills_dir = ancestor / "skills"
        if not skills_dir.is_dir():
            continue
        if ancestor.name != plugin and ancestor.parent.name != plugin:
            continue
        candidates.append(skills_dir / skill / "SKILL.md")
    return tuple(candidates)


def _require_repo_file(path: str | pathlib.Path, rule: str) -> str:
    repo_path = pathlib.Path(path)
    if repo_path.is_absolute():
        return _read_existing_file(repo_path, rule)
    if ".." in repo_path.parts:
        raise ReviewResultValidationError(
            f"finding 'rule' must cite a repository-relative file; got "
            f"{rule!r}, whose path contains '..'. Cite the path from the "
            "repository root without parent-directory segments."
        )
    root = _repo_root()
    try:
        resolved = (root / repo_path).resolve(strict=True)
        resolved.relative_to(root)
        return _read_existing_file(resolved, rule)
    except ValueError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' must cite a repository-relative file; got "
            f"{rule!r}, which resolves outside the repository root {root}. "
            "Cite a path inside the repository."
        ) from exc
    except FileNotFoundError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cites a missing file: {repo_path} (looked under "
            f"{root}). Run the review from the repository root and cite a "
            "file that exists there."
        ) from exc
    except OSError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cannot read cited file {repo_path}: "
            f"{str(exc) or type(exc).__name__}. Check the file's permissions "
            "and cite a readable file."
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
                f"finding 'rule' cites a non-file path: {path}. Cite a "
                "regular file, not a directory."
            )
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cites a missing file: {path}. Cite a file that exists."
        ) from exc
    except OSError as exc:
        raise ReviewResultValidationError(
            f"finding 'rule' cannot read cited file for {rule}: "
            f"{str(exc) or type(exc).__name__}. Check the file's permissions "
            "and cite a readable UTF-8 file."
        ) from exc


def _parse_enum(
    value: str, enum_cls: type[StrEnum], *, field: str, where: str = "finding"
) -> Any:
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = sorted(member.value for member in enum_cls)
        raise ReviewResultValidationError(
            f"unknown {field} {value!r} in {where}; allowed values: {allowed}. "
            f"Set '{field}' to one of them."
        ) from exc


def _require_keys(
    data: dict[str, Any], keys: tuple[str, ...], *, where: str = "finding"
) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise ReviewResultValidationError(
            f"missing required key(s): {missing} in {where}; keys present: "
            f"{sorted(data)}. Add the missing key(s) and emit again."
        )


def _require_str(data: dict[str, Any], key: str, *, where: str = "finding") -> str:
    value = data[key]
    if not isinstance(value, str):
        raise ReviewResultValidationError(
            f"{key!r} must be a string in {where}, got {type(value).__name__}. "
            f"Set {key!r} to a JSON string."
        )
    return value


def _require_int(data: dict[str, Any], key: str, *, where: str = "finding") -> int:
    value = data[key]
    # ``bool`` is a subclass of ``int`` in Python; reject explicitly so
    # ``True`` / ``False`` does not silently coerce to ``1`` / ``0``.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReviewResultValidationError(
            f"{key!r} must be an integer in {where}, got {type(value).__name__}. "
            f"Set {key!r} to a JSON integer, not a string or boolean."
        )
    return cast(int, value)
