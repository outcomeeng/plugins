"""Judge a Change Draft against the Change record: the form check.

Reads one JSON request on stdin and writes one JSON result on stdout. The
request carries the Draft's text or its path, the Product's checkout root, the
operation, the record the Change Store holds or null, the record of each
Change the Draft names as a blocker, and the Change Store's size limit. The
result holds `pass` or `fail` and every finding with the slug of the rule it
breaks, the subsection or line it names, and its detail. A request the script
cannot read yields `invalid-request` and no finding.

The module exposes `check`, which returns for a request the result `main`
writes for it, so a sibling Change skill's script reaches the check through a
`__file__`-relative import.

The check reads the Draft and runs only reading git commands at the Draft's
base commit in the checkout root. It writes no file and no Change Store.

Portability: stdlib only; supports Python 3.13 and later.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, Protocol, TextIO

EXIT_PASS: Final = 0
EXIT_FAIL: Final = 1
EXIT_INVALID_REQUEST: Final = 2

TITLE_WORD_LIMIT: Final = 15
STATEMENT_WORD_LIMIT: Final = 120
GITHUB_SIZE_LIMIT: Final = 65_536
GITHUB_STORE: Final = "github"


class Status(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INVALID_REQUEST = "invalid-request"


class RequestField(StrEnum):
    DRAFT_TEXT = "draft_text"
    DRAFT_PATH = "draft_path"
    CHECKOUT_ROOT = "checkout_root"
    OPERATION = "operation"
    STORED_RECORD = "stored_record"
    BLOCKER_RECORDS = "blocker_records"
    SIZE_LIMIT = "size_limit"


class RecordField(StrEnum):
    METADATA = "metadata"
    BODY = "body"


class ResultField(StrEnum):
    STATUS = "status"
    FINDINGS = "findings"
    DETAIL = "detail"


class FindingField(StrEnum):
    RULE = "rule"
    WHERE = "where"
    DETAIL = "detail"


class Rule(StrEnum):
    """The slug of each rule a finding names."""

    RECORD_KEYS = "record-keys"
    RECORD_BODY = "record-body"
    STATEMENT_OF_INTENT = "statement-of-intent"
    SUBSECTION_HEADINGS = "subsection-headings"
    PAYLOADS = "payloads"
    HEADERS = "headers"
    DIFF_LINES = "diff-lines"
    BODY_LINES_ONLY = "body-lines-only"
    NO_TAG = "no-tag"
    PLAIN_SLUG = "plain-slug"
    TABLE_CASE = "table-case"
    FRONT_MATTER_BLOCK = "front-matter-block"
    NO_INDEX = "no-index"
    MOVE_READS = "move-reads"
    ONE_PAYLOAD = "one-payload"
    FENCE = "fence"
    NO_MODE = "no-mode"
    OPERATION_KINDS = "operation-kinds"
    SPEC_DELETION = "spec-deletion"
    ONE_SUBSECTION_PER_FILE = "one-subsection-per-file"
    SLUG_RENAME = "slug-rename"
    PATH_NAMING = "path-naming"
    INFRASTRUCTURE_LINE = "infrastructure-line"
    REPLACED_ASSERTION = "replaced-assertion"
    INFRASTRUCTURE_FORM = "infrastructure-form"
    INFRASTRUCTURE_EXISTS = "infrastructure-exists"
    SPEC_NODE_NONE = "spec-node-none"
    NONE_LEAF = "none-leaf"
    SIZE_LIMIT = "size-limit"
    ONE_HOME = "one-home"


class Operation(StrEnum):
    """What a publish or a Transition does to the record."""

    RECORD = "record"
    PUBLISH = "publish"
    SPLIT = "split"
    RECORD_CHILD = "record-child"
    MERGE = "merge"
    PRIORITY_DECISION = "priority-decision"
    CLAIM = "claim"
    RELEASE = "release"
    SUBMIT = "submit"
    ADVANCE = "advance"
    LOWER = "lower"
    APPLIED = "applied"
    ABANDONED = "abandoned"


TRANSITIONS: Final = frozenset(
    {
        Operation.CLAIM,
        Operation.RELEASE,
        Operation.SUBMIT,
        Operation.ADVANCE,
        Operation.LOWER,
        Operation.APPLIED,
        Operation.ABANDONED,
    }
)


class Key(StrEnum):
    """The metadata keys of a record."""

    TITLE = "title"
    PRODUCT = "product"
    MATURITY = "maturity"
    LIFECYCLE = "lifecycle"
    HOLDER = "holder"
    PARENT = "parent"
    PREDECESSORS = "predecessors"
    BLOCKERS = "blockers"
    BASE = "base"
    PRIORITY = "priority"
    PRIMARY_VALUE = "primary_value"
    INVESTMENT = "investment"


DRAFT_KEYS: Final = tuple(key for key in Key if key is not Key.HOLDER)

KEY_OPERATIONS: Final[Mapping[Key, frozenset[Operation]]] = {
    Key.TITLE: frozenset({Operation.RECORD, Operation.PUBLISH}),
    Key.PRODUCT: frozenset(
        {Operation.RECORD, Operation.PUBLISH, Operation.SPLIT, Operation.RECORD_CHILD}
    ),
    Key.MATURITY: frozenset({Operation.RECORD, Operation.ADVANCE, Operation.LOWER}),
    Key.LIFECYCLE: frozenset({Operation.RECORD}) | TRANSITIONS,
    Key.HOLDER: frozenset({Operation.RECORD, Operation.CLAIM, Operation.RELEASE}),
    Key.PARENT: frozenset({Operation.RECORD, Operation.SPLIT}),
    Key.PREDECESSORS: frozenset({Operation.MERGE}),
    Key.BLOCKERS: frozenset({Operation.PUBLISH}),
    Key.BASE: frozenset({Operation.RECORD, Operation.PUBLISH, Operation.RECORD_CHILD}),
    Key.PRIORITY: frozenset({Operation.PRIORITY_DECISION}),
    Key.PRIMARY_VALUE: frozenset({Operation.PRIORITY_DECISION}),
    Key.INVESTMENT: frozenset({Operation.PRIORITY_DECISION}),
}

MATURITIES: Final = ("Proposed", "Framed", "Sliced", "Applicable")
LIFECYCLES: Final = ("Available", "Submitted", "Applied", "Abandoned")
PRIMARY_VALUES: Final = ("Offering", "Quality", "Capability", "Safety")
INVESTMENTS: Final = ("Harvest", "Shield", "Frontier", "Seed")
PROPOSED: Final = MATURITIES[0]

ENUMERATED_VALUES: Final[Mapping[Key, tuple[str, ...]]] = {
    Key.MATURITY: MATURITIES,
    Key.LIFECYCLE: LIFECYCLES,
    Key.PRIMARY_VALUE: PRIMARY_VALUES,
    Key.INVESTMENT: INVESTMENTS,
}

REFERENCE_LIST_KEYS: Final = (Key.PREDECESSORS, Key.BLOCKERS)
NULLABLE_KEYS: Final = (Key.PRIORITY, Key.PRIMARY_VALUE, Key.INVESTMENT)

SECTION_STATEMENT: Final = "Statement of Intent"
SECTION_DECLARATIONS: Final = "Declarations"
STATEMENT_PARTS: Final = ("Output", "Why", "Verification")

NEW_KINDS: Final = (
    "adr",
    "pdr",
    "enabler",
    "outcome",
    "substrate",
    "capability",
    "domain",
    "interface",
    "surface",
    "variant",
    "product",
)
DECISION_KINDS: Final = ("adr", "pdr")
MALLEABILITY_LEVELS: Final = ("spec", "verification", "implementation")
DEFAULT_MALLEABILITY: Final = "implementation"

INFRASTRUCTURE_LABEL: Final = "Infrastructure:"
INFRASTRUCTURE_NONE: Final = "none"
TREE_ROOT: Final = "spx"
KNOWLEDGE_DIR: Final = "knowledge"
CONTRACTS_DIR: Final = "contracts"

GIT_HEADER_DELETE: Final = "deleted file"
GIT_HEADER_CREATE: Final = "new file"
GIT_HEADER_RENAME_FROM: Final = "rename from "
GIT_HEADER_RENAME_TO: Final = "rename to "

READING_GIT_COMMANDS: Final = frozenset({"cat-file", "ls-tree", "grep", "rev-parse"})

SHA_PATTERN: Final = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SLUG_PATTERN: Final = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CASE_PATTERN: Final = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
INDEX_PREFIX_PATTERN: Final = re.compile(r"^\d{2}(?:\.\d+)?-")
NODE_DIR_PATTERN: Final = re.compile(
    r"^\d{2}(?:\.\d+)?-(?P<slug>[a-z0-9][a-z0-9-]*)\.(?P<kind>[a-z]+)$"
)
DECISION_FILE_PATTERN: Final = re.compile(
    r"^\d{2}(?:\.\d+)?-(?P<slug>[a-z0-9][a-z0-9-]*)\.(?P<kind>adr|pdr)\.md$"
)
PATH_PATTERN: Final = re.compile(r"^[A-Za-z0-9_.@+/-]+$")
NEW_HEADING_PATTERN: Final = re.compile(
    r"^new (?P<kind>[a-z]+) `(?P<slug>[^`]+)`, between `(?P<before>[^`]+)` and `(?P<after>[^`]+)`$"
)
FENCE_OPEN_PATTERN: Final = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
HEADING_PATTERN: Final = re.compile(r"^(?P<marks>#{1,6}) (?P<text>.+?)\s*$")
GROUP_PATTERN: Final = re.compile(
    r"^#{3,4} (?:Test\.)?(?:Mapping|Eval|Evaluate): (?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\s*$"
)
ROW_PATTERN: Final = re.compile(r"^- (?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*): ")
INFRASTRUCTURE_PATTERN: Final = re.compile(
    r"^Infrastructure: (?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*) (?P<rest>.+)$"
)
PATH_LIST_PATTERN: Final = re.compile(r"^`[^`]+`(?:, `[^`]+`)*$")
SEPARATOR_ROW_PATTERN: Final = re.compile(r"^\|[\s:|-]+\|?$")
HEADER_CASE: Final = "Case"
TAG_PATTERN: Final = re.compile(r"\[(?:test|eval|probe)\]\(|\[audit(?::[a-z0-9-]+)?\]")
LINK_PATTERN: Final = re.compile(
    r"\[[^\]]*\]\((?P<target>(?:tests|evals|probes)/[^)\s]+)\)"
)
LABEL_PATTERN: Final = re.compile(r"^- (?P<label>[A-Za-z]+):")
METADATA_LINE_PATTERN: Final = re.compile(r"^(?P<key>[a-z_]+):(?: (?P<value>.*))?$")
BLOCK_METADATA_PATTERN: Final = re.compile(
    "^(?:" + "|".join(key.value for key in Key) + r"):(?: |$)"
)
FRONT_MATTER_FIELD_PATTERN: Final = re.compile(r"^[+-] ?(?P<key>id|malleability|kind):")
SCAFFOLDING_PREFIXES: Final = (
    "@@",
    "diff --git",
    "index ",
    "--- a/",
    "+++ b/",
    "--- /dev/null",
    "+++ /dev/null",
)
GIT_HEADER_PREFIXES: Final = (
    "deleted file",
    "new file",
    "rename from",
    "rename to",
    "old mode",
    "new mode",
    "similarity index",
    "dissimilarity index",
    "copy from",
    "copy to",
    "index ",
    "diff --git",
)
LANGUAGES: Final = {
    ".md": "markdown",
    ".toml": "toml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".py": "python",
}
DIFF_LANGUAGE: Final = "diff"
TEXT_LANGUAGE: Final = "text"
YAML_LANGUAGE: Final = "yaml"
REGULAR_MODES: Final = frozenset({"100644", "100755"})
TREE_MODE: Final = "040000"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: bytes


class CommandRunner(Protocol):
    def __call__(self, args: Sequence[str], cwd: str) -> CommandResult: ...


def run_command(args: Sequence[str], cwd: str) -> CommandResult:
    try:
        completed = subprocess.run(  # noqa: S603
            list(args), cwd=cwd, capture_output=True, check=False
        )
    except OSError:
        return CommandResult(returncode=127, stdout=b"")
    return CommandResult(completed.returncode, completed.stdout)


@dataclass(frozen=True)
class Finding:
    rule: Rule
    where: str
    detail: str

    def as_json(self) -> dict[str, str]:
        return {
            FindingField.RULE: self.rule,
            FindingField.WHERE: self.where,
            FindingField.DETAIL: self.detail,
        }


class Findings:
    def __init__(self) -> None:
        self.items: list[Finding] = []

    def add(self, rule: Rule, where: str, detail: str) -> None:
        self.items.append(Finding(rule, where, detail))


class InvalidRequest(Exception):
    """The request names a field the check cannot read."""


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    kind: str


class Base:
    """Reading git commands at one commit of the checkout root."""

    def __init__(self, root: str, commit: str, run: CommandRunner) -> None:
        self.root = root
        self.commit = commit
        self.run = run
        self._entries: dict[str, TreeEntry | None] = {}

    def _git(self, *args: str) -> CommandResult:
        return self.run(("git", *args), self.root)

    def resolves(self) -> bool:
        if not SHA_PATTERN.match(self.commit):
            return False
        return (
            self._git(
                "rev-parse", "--verify", "--quiet", f"{self.commit}^{{commit}}"
            ).returncode
            == 0
        )

    def entry(self, path: str) -> TreeEntry | None:
        if path not in self._entries:
            self._entries[path] = self._read_entry(path)
        return self._entries[path]

    def _read_entry(self, path: str) -> TreeEntry | None:
        result = self._git("ls-tree", self.commit, "--", path.rstrip("/"))
        if result.returncode != 0 or not result.stdout:
            return None
        meta, _, name = result.stdout.decode("utf-8", "replace").partition("\t")
        fields = meta.split()
        if len(fields) < 2 or name.strip() != path.rstrip("/"):
            return None
        return TreeEntry(mode=fields[0], kind=fields[1])

    def is_dir(self, path: str) -> bool:
        entry = self.entry(path)
        return entry is not None and entry.kind == "tree"

    def exists(self, path: str) -> bool:
        return self.entry(path) is not None

    def regular_text(self, path: str) -> str | None:
        entry = self.entry(path)
        if entry is None or entry.mode not in REGULAR_MODES:
            return None
        result = self._git("cat-file", "blob", f"{self.commit}:{path}")
        if result.returncode != 0 or b"\0" in result.stdout:
            return None
        try:
            return result.stdout.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def children(self, path: str) -> list[str]:
        prefix = path.rstrip("/") + "/" if path else ""
        result = self._git("ls-tree", "--name-only", self.commit, "--", prefix or ".")
        if result.returncode != 0:
            return []
        return [
            line.rsplit("/", 1)[-1]
            for line in result.stdout.decode("utf-8", "replace").splitlines()
            if line
        ]

    def has_tree(self) -> bool:
        return self.is_dir(TREE_ROOT)

    def mentions(self, needle: str) -> list[str]:
        result = self._git("grep", "-I", "-l", "-F", "-e", needle, self.commit, "--")
        if result.returncode != 0:
            return []
        prefix = f"{self.commit}:"
        return sorted(
            line.removeprefix(prefix)
            for line in result.stdout.decode("utf-8", "replace").splitlines()
            if line
        )


# ---------------------------------------------------------------- parsing


@dataclass(frozen=True)
class Block:
    info: str
    fence: str
    lines: tuple[str, ...]
    line: int


@dataclass
class Subsection:
    heading: str
    line: int
    blocks: list[Block] = field(default_factory=list)
    loose: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class Section:
    title: str
    line: int
    text: list[tuple[int, str]] = field(default_factory=list)
    subsections: list[Subsection] = field(default_factory=list)


@dataclass
class Draft:
    metadata: dict[str, Any]
    duplicate_keys: list[str]
    bad_lines: list[tuple[int, str]]
    body_lines: list[tuple[int, str]]
    preamble: list[tuple[int, str]]
    sections: list[Section]
    body_text: str
    has_front_matter: bool


def parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if text in {"", "null", "~"}:
        return None
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [parse_scalar(part) for part in split_flow(inner)] if inner else []
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def split_flow(inner: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote = ""
    for char in inner:
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
            current.append(char)
        elif char == ",":
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts]


def parse_metadata(
    lines: Sequence[tuple[int, str]],
) -> tuple[dict[str, Any], list[str], list[tuple[int, str]]]:
    metadata: dict[str, Any] = {}
    duplicates: list[str] = []
    bad: list[tuple[int, str]] = []
    current: str | None = None
    for number, text in lines:
        if not text.strip() or text.lstrip().startswith("#"):
            continue
        if text.startswith((" ", "\t")) and current is not None:
            stripped = text.strip()
            if stripped.startswith("- "):
                if not isinstance(metadata[current], list):
                    metadata[current] = []
                metadata[current].append(parse_scalar(stripped[2:]))
                continue
        match = METADATA_LINE_PATTERN.match(text)
        if match is None:
            bad.append((number, text))
            continue
        key = match.group("key")
        if key in metadata:
            duplicates.append(key)
        metadata[key] = parse_scalar(match.group("value") or "")
        current = key
    return metadata, duplicates, bad


def scan_elements(lines: Sequence[tuple[int, str]]) -> list[Any]:
    """Split numbered lines into headings, fenced blocks, and loose lines."""

    elements: list[Any] = []
    index = 0
    while index < len(lines):
        number, text = lines[index]
        opening = FENCE_OPEN_PATTERN.match(text)
        if opening is not None and "`" not in opening.group("info"):
            fence = opening.group("fence")
            body: list[str] = []
            index += 1
            while index < len(lines):
                inner = lines[index][1]
                closing = inner.strip()
                if closing.startswith(fence[0] * len(fence)) and closing == fence[
                    0
                ] * len(closing):
                    break
                body.append(inner)
                index += 1
            elements.append(
                Block(opening.group("info").strip(), fence, tuple(body), number)
            )
        else:
            heading = HEADING_PATTERN.match(text)
            if heading is not None:
                elements.append(
                    (
                        "heading",
                        len(heading.group("marks")),
                        heading.group("text"),
                        number,
                    )
                )
            else:
                elements.append(("line", number, text))
        index += 1
    return elements


def parse_draft(text: str) -> Draft:
    lines = text.split("\n")
    numbered = list(enumerate(lines, start=1))
    metadata: dict[str, Any] = {}
    duplicates: list[str] = []
    bad: list[tuple[int, str]] = []
    has_front_matter = bool(lines) and lines[0].strip() == "---"
    body_start = 0
    if has_front_matter:
        for offset in range(1, len(lines)):
            if lines[offset].strip() == "---":
                metadata, duplicates, bad = parse_metadata(numbered[1:offset])
                body_start = offset + 1
                break
        else:
            has_front_matter = False
    body = numbered[body_start:]
    sections: list[Section] = []
    preamble: list[tuple[int, str]] = []
    for element in scan_elements(body):
        if isinstance(element, tuple) and element[0] == "heading" and element[1] == 2:
            sections.append(Section(title=element[2], line=element[3]))
        elif (
            isinstance(element, tuple)
            and element[0] == "heading"
            and element[1] == 3
            and sections
            and sections[-1].title == SECTION_DECLARATIONS
        ):
            sections[-1].subsections.append(
                Subsection(heading=element[2], line=element[3])
            )
        else:
            place_element(element, sections, preamble)
    return Draft(
        metadata=metadata,
        duplicate_keys=duplicates,
        bad_lines=bad,
        body_lines=body,
        preamble=preamble,
        sections=sections,
        body_text="\n".join(line for _, line in body),
        has_front_matter=has_front_matter,
    )


def place_element(
    element: Any, sections: list[Section], preamble: list[tuple[int, str]]
) -> None:
    if not sections:
        if isinstance(element, tuple) and element[0] == "line" and element[2].strip():
            preamble.append((element[1], element[2]))
        elif isinstance(element, tuple) and element[0] == "heading":
            preamble.append((element[3], f"{'#' * element[1]} {element[2]}"))
        elif isinstance(element, Block):
            preamble.append((element.line, "".join(element.fence)))
        return
    section = sections[-1]
    target = section.subsections[-1] if section.subsections else None
    if isinstance(element, Block):
        if target is not None:
            target.blocks.append(element)
        else:
            section.text.append((element.line, element.fence + element.info))
            section.text.extend((element.line, line) for line in element.lines)
    elif element[0] == "heading":
        text = f"{'#' * element[1]} {element[2]}"
        (target.loose if target is not None else section.text).append(
            (element[3], text)
        )
    elif element[2].strip():
        (target.loose if target is not None else section.text).append(
            (element[1], element[2])
        )


# ------------------------------------------------------------ rule checks


def word_count(text: str) -> int:
    return sum(1 for token in text.split() if any(char.isalnum() for char in token))


def is_reference(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value > 0
    return isinstance(value, str) and bool(value.strip())


def check_value(key: Key, draft: Draft, findings: Findings) -> None:
    value = draft.metadata[key]
    problem = value_problem(key, value, draft.metadata)
    if problem:
        findings.add(Rule.RECORD_KEYS, key, problem)


def value_problem(key: Key, value: Any, metadata: Mapping[str, Any]) -> str:
    if key is Key.TITLE:
        if not isinstance(value, str) or not value.strip():
            return "the title is a non-empty string"
        count = word_count(value)
        return (
            f"the title holds {count} words; the limit is {TITLE_WORD_LIMIT}"
            if count > TITLE_WORD_LIMIT
            else ""
        )
    if key is Key.PRODUCT:
        if isinstance(value, list):
            ok = value and all(isinstance(item, str) and item.strip() for item in value)
            return "" if ok else "a Parent's product is a non-empty list of Products"
        return (
            ""
            if isinstance(value, str) and value.strip()
            else "a Leaf's product is one Product"
        )
    if key in ENUMERATED_VALUES:
        allowed = ENUMERATED_VALUES[key]
        if value is None and key in NULLABLE_KEYS:
            return ""
        return "" if value in allowed else f"the value is one of {', '.join(allowed)}"
    if key is Key.PRIORITY:
        return (
            ""
            if value is None or (isinstance(value, str) and value.strip())
            else "the priority is null or one Priority"
        )
    if key is Key.PARENT:
        return (
            ""
            if value is None or is_reference(value)
            else "the parent is a Change reference or null"
        )
    if key in REFERENCE_LIST_KEYS:
        if not isinstance(value, list) or not all(is_reference(item) for item in value):
            return f"{key} is a list of Change references, [] when it holds none"
        return (
            ""
            if len({str(item) for item in value}) == len(value)
            else f"{key} names a Change twice"
        )
    if key is Key.BASE:
        if isinstance(metadata.get(Key.PRODUCT), list):
            return "a Parent holds no base key"
        return (
            ""
            if isinstance(value, str) and SHA_PATTERN.match(value)
            else "the base is the full commit id of the default branch's head"
        )
    return ""


def comparable(value: Any) -> Any:
    return json.dumps(value, sort_keys=True)


def check_metadata(
    draft: Draft,
    stored: Mapping[str, Any] | None,
    operation: Operation,
    findings: Findings,
) -> None:
    if not draft.has_front_matter:
        findings.add(
            Rule.RECORD_KEYS,
            "front matter",
            "the Draft opens with a yaml front-matter block",
        )
    for number, text in draft.bad_lines:
        findings.add(
            Rule.RECORD_KEYS,
            f"line {number}",
            f"the front-matter line `{text}` is no key and value",
        )
    for key in draft.duplicate_keys:
        findings.add(Rule.RECORD_KEYS, key, "the key stands once")
    known = {key.value for key in Key}
    for name in draft.metadata:
        if name not in known:
            findings.add(Rule.RECORD_KEYS, name, "the key is no key of a record")
    if Key.HOLDER in draft.metadata:
        findings.add(
            Rule.RECORD_KEYS, Key.HOLDER, "the holder is absent from a Change Draft"
        )
    parent = isinstance(draft.metadata.get(Key.PRODUCT), list)
    for key in DRAFT_KEYS:
        if key not in draft.metadata:
            if key is Key.BASE and parent:
                continue
            findings.add(
                Rule.RECORD_KEYS,
                key,
                "the key is missing; a key with no value holds null",
            )
            continue
        check_value(key, draft, findings)
    if stored is not None:
        check_operation(draft.metadata, stored, operation, findings)


def check_operation(
    draft: Mapping[str, Any],
    stored: Mapping[str, Any],
    operation: Operation,
    findings: Findings,
) -> None:
    for key in DRAFT_KEYS:
        before = stored.get(key.value)
        after = draft.get(key.value)
        if (
            comparable(before) != comparable(after)
            and operation not in KEY_OPERATIONS[key]
        ):
            findings.add(
                Rule.RECORD_KEYS,
                key,
                f"the operation {operation} changes no {key}; only {', '.join(sorted(KEY_OPERATIONS[key]))} do",
            )


def check_body(draft: Draft, findings: Findings) -> bool:
    for number, text in draft.preamble:
        findings.add(
            Rule.RECORD_BODY,
            f"line {number}",
            f"the body holds `{text}` before its first section",
        )
    titles = [section.title for section in draft.sections]
    parent = isinstance(draft.metadata.get(Key.PRODUCT), list)
    proposed = draft.metadata.get(Key.MATURITY) == PROPOSED
    if parent or proposed:
        allowed = (
            [[SECTION_STATEMENT]]
            if parent
            else [[SECTION_STATEMENT], [SECTION_STATEMENT, SECTION_DECLARATIONS]]
        )
    else:
        allowed = [[SECTION_STATEMENT, SECTION_DECLARATIONS]]
    if titles not in allowed:
        expected = " or ".join(", then ".join(option) for option in allowed)
        findings.add(
            Rule.RECORD_BODY,
            "body",
            f"the body holds {', then '.join(titles) or 'no section'}; it holds {expected}",
        )
    return SECTION_DECLARATIONS in titles


def check_statement(section: Section, findings: Findings) -> None:
    labels: list[str] = []
    for number, text in section.text:
        match = LABEL_PATTERN.match(text)
        if match is not None:
            labels.append(match.group("label"))
        elif text.startswith("- "):
            findings.add(
                Rule.STATEMENT_OF_INTENT,
                f"line {number}",
                "the Statement of Intent holds only its three labeled parts",
            )
    if labels != list(STATEMENT_PARTS):
        findings.add(
            Rule.STATEMENT_OF_INTENT,
            SECTION_STATEMENT,
            f"the parts read {', '.join(labels) or 'none'}; they are {', '.join(STATEMENT_PARTS)}, in this order",
        )
    count = word_count(
        " ".join(LABEL_PATTERN.sub("", text) for _, text in section.text)
    )
    if count > STATEMENT_WORD_LIMIT:
        findings.add(
            Rule.STATEMENT_OF_INTENT,
            SECTION_STATEMENT,
            f"the Statement of Intent holds {count} words; the limit is {STATEMENT_WORD_LIMIT}",
        )


def check_homes(draft: Draft, findings: Findings) -> None:
    lines = list(draft.preamble)
    for section in draft.sections:
        lines.extend(section.text)
        for sub in section.subsections:
            lines.extend(sub.loose)
    for number, text in lines:
        if BLOCK_METADATA_PATTERN.match(text):
            findings.add(
                Rule.ONE_HOME,
                f"line {number}",
                "the body holds a metadata field; the metadata holds it",
            )
        elif text.strip() == "---":
            findings.add(
                Rule.ONE_HOME,
                f"line {number}",
                "the body holds a second front-matter block",
            )


def resolve_size_limit(raw: Any) -> int:
    if raw == GITHUB_STORE:
        return GITHUB_SIZE_LIMIT
    if isinstance(raw, int) and not isinstance(raw, bool) and raw > 0:
        return raw
    raise InvalidRequest(
        f"{RequestField.SIZE_LIMIT} is a positive integer or {GITHUB_STORE}"
    )


def check_size(draft: Draft, limit: int, findings: Findings) -> None:
    if len(draft.body_text) > limit:
        findings.add(
            Rule.SIZE_LIMIT,
            "body",
            f"the body holds {len(draft.body_text)} characters; the Change Store's limit is {limit}",
        )


# ------------------------------------------------------- Declarations


class Op(StrEnum):
    EDIT = "edit"
    REPLACE = "replace"
    DELETE = "delete"
    CREATE = "create"
    MOVE = "move"


class PathKind(StrEnum):
    NODE = "node"
    DECISION = "decision"
    SPEC = "spec"
    CONTRACT = "contract"
    OUTCOME = "outcome"
    PRODUCT_SPEC = "product-spec"
    NO_TREE_FILE = "no-tree-file"
    OTHER = "other"


READ_KINDS: Final = frozenset(PathKind) - {PathKind.OTHER}
CREATE_KINDS: Final = frozenset(
    {PathKind.CONTRACT, PathKind.OUTCOME, PathKind.PRODUCT_SPEC, PathKind.NO_TREE_FILE}
)


def path_kind(path: str, has_tree: bool) -> PathKind:
    if not has_tree:
        return PathKind.NO_TREE_FILE
    parts = path.split("/")
    name = parts[-1]
    if NODE_DIR_PATTERN.match(name):
        return PathKind.NODE
    if DECISION_FILE_PATTERN.match(name):
        return PathKind.DECISION
    if name.endswith(".outcome.md"):
        return PathKind.OUTCOME
    if (
        len(parts) == 2
        and parts[0] == TREE_ROOT
        and name.endswith((".spec.md", ".product.md"))
    ):
        return PathKind.PRODUCT_SPEC
    if CONTRACTS_DIR in parts[:-1]:
        return PathKind.CONTRACT
    if name.endswith(".md") and len(parts) >= 3:
        stem = (
            name.removesuffix(".spec.md")
            if name.endswith(".spec.md")
            else name.removesuffix(".md")
        )
        parent = NODE_DIR_PATTERN.match(parts[-2])
        if parent is not None and parent.group("slug") == stem:
            return PathKind.SPEC
    return PathKind.OTHER


def node_spec_path(base: Base, node_dir: str) -> str | None:
    match = NODE_DIR_PATTERN.match(node_dir.rsplit("/", 1)[-1])
    if match is None:
        return None
    for candidate in (f"{match.group('slug')}.spec.md", f"{match.group('slug')}.md"):
        if base.exists(f"{node_dir}/{candidate}"):
            return f"{node_dir}/{candidate}"
    return None


@dataclass
class Analysis:
    sub: Subsection
    heading: str
    new: re.Match[str] | None = None
    path: str = ""
    read_path: str = ""
    op: Op = Op.EDIT
    kind: PathKind = PathKind.OTHER
    diff: Block | None = None
    yaml: Block | None = None
    replacement: Block | None = None
    headers: list[str] = field(default_factory=list)
    edit_lines: list[tuple[int, str]] = field(default_factory=list)
    rename_to: str = ""
    is_node: bool = False
    in_moved: bool = False
    valid: bool = True


def normalized_heading(text: str) -> str:
    stripped = text.strip()
    if (
        len(stripped) > 2
        and stripped.startswith("`")
        and stripped.endswith("`")
        and stripped.count("`") == 2
    ):
        return stripped[1:-1]
    return stripped


def split_diff(block: Block) -> tuple[list[str], list[tuple[int, str]]]:
    headers: list[str] = []
    rest: list[tuple[int, str]] = []
    in_headers = True
    for offset, text in enumerate(block.lines):
        if in_headers and text.startswith(GIT_HEADER_PREFIXES):
            headers.append(text)
            continue
        in_headers = False
        rest.append((block.line + 1 + offset, text))
    return headers, rest


def classify_operation(headers: Sequence[str]) -> Op:
    if GIT_HEADER_DELETE in headers:
        return Op.DELETE
    if GIT_HEADER_CREATE in headers:
        return Op.CREATE
    if any(header.startswith(GIT_HEADER_RENAME_FROM) for header in headers):
        return Op.MOVE
    return Op.EDIT


def language_for(path: str, is_node: bool) -> str | None:
    if is_node:
        return "markdown"
    suffix = Path(path).suffix
    return LANGUAGES.get(suffix)


# ------------------------------------------------------------ assertions


@dataclass(frozen=True)
class Unit:
    group: str
    slug: str


def parse_units(lines: Sequence[str]) -> dict[Unit, str]:
    units: dict[Unit, list[str]] = {}
    group = ""
    current: Unit | None = None
    for text in lines:
        heading = HEADING_PATTERN.match(text)
        if heading is not None and len(heading.group("marks")) >= 3:
            mapping = GROUP_PATTERN.match(text)
            if mapping is not None:
                group = text
                current = Unit(text, mapping.group("slug"))
                units[current] = [text]
            else:
                group = text
                current = None
            continue
        row = ROW_PATTERN.match(text)
        if row is not None:
            current = Unit(group, row.group("slug"))
            units[current] = [text]
        elif current is not None and (text.startswith(" ") or text.strip()):
            if not text.startswith("## "):
                units[current].append(text)
    return {unit: "\n".join(body).strip() for unit, body in units.items()}


def apply_line_edits(
    base_lines: Sequence[str], edits: Sequence[tuple[int, str]]
) -> list[str]:
    """Apply the - and + lines and the context lines of an edit to the Base lines."""

    result: list[str] = []
    cursor = 0
    for _, raw in edits:
        marker = raw[:1]
        content = marker_content(raw)
        if marker == "+":
            result.append(content)
            continue
        found = next(
            (
                i
                for i in range(cursor, len(base_lines))
                if base_lines[i].rstrip() == content.rstrip()
            ),
            None,
        )
        if found is None:
            continue
        result.extend(base_lines[cursor:found])
        if marker != "-":
            result.append(base_lines[found])
        cursor = found + 1
    result.extend(base_lines[cursor:])
    return result


def marker_content(raw: str) -> str:
    if raw[:1] in {"+", "-"}:
        rest = raw[1:]
    else:
        rest = raw
    return rest[1:] if rest.startswith(" ") else rest


def front_matter_value(lines: Sequence[str], key: str) -> str | None:
    if not lines or lines[0].strip() != "---":
        return None
    for text in lines[1:]:
        if text.strip() == "---":
            return None
        match = METADATA_LINE_PATTERN.match(text)
        if match is not None and match.group("key") == key:
            return (match.group("value") or "").strip().strip("\"'")
    return None


def malleability_of(lines: Sequence[str]) -> str:
    return front_matter_value(lines, "malleability") or DEFAULT_MALLEABILITY


# --------------------------------------------------------------- checker


class DeclarationChecker:
    def __init__(
        self,
        base: Base,
        draft: Draft,
        blockers: Sequence[str],
        blocker_records: Mapping[str, Mapping[str, Any]],
        findings: Findings,
    ) -> None:
        self.base = base
        self.draft = draft
        self.blockers = blockers
        self.blocker_records = blocker_records
        self.findings = findings
        self.has_tree = base.has_tree()
        self.moves: list[tuple[str, str]] = []
        self.analyses: list[Analysis] = []
        self.written: dict[str, str] = {}

    def run(self, section: Section) -> None:
        if not section.subsections:
            self.check_none_leaf(section)
            return
        if not self.base.resolves():
            self.findings.add(
                Rule.RECORD_KEYS,
                Key.BASE,
                "the base commit does not resolve at the checkout root",
            )
        for sub in section.subsections:
            self.analyses.append(self.check_subsection(sub))
        self.check_files()
        self.check_path_naming()

    def check_none_leaf(self, section: Section) -> None:
        text = " ".join(line for _, line in section.text).strip()
        match = re.match(r"^none\b[\s:.,;—–-]*(?P<reason>.*)$", text, re.IGNORECASE)
        if match is None or not match.group("reason").strip():
            self.findings.add(
                Rule.NONE_LEAF,
                SECTION_DECLARATIONS,
                "a Leaf that declares nothing holds none and its reason",
            )

    # ---- one subsection

    def check_subsection(self, sub: Subsection) -> Analysis:
        analysis = Analysis(sub=sub, heading=normalized_heading(sub.heading))
        self.sort_blocks(analysis)
        new = (
            NEW_HEADING_PATTERN.match(analysis.heading)
            if analysis.heading.startswith("new ")
            else None
        )
        if analysis.heading.startswith("new ") and new is None:
            self.findings.add(
                Rule.SUBSECTION_HEADINGS,
                sub.heading,
                "a new Node or Decision Record heading names its kind, its slug, and the two existing siblings between which it stands",
            )
            analysis.valid = False
        elif new is not None:
            analysis.new = new
            self.check_new_heading(analysis, new)
        else:
            self.check_path_heading(analysis)
        self.check_payloads(analysis)
        if analysis.valid:
            self.check_operation_and_lines(analysis)
        self.check_infrastructure(analysis)
        return analysis

    def sort_blocks(self, analysis: Analysis) -> None:
        for block in analysis.sub.blocks:
            if block.info == DIFF_LANGUAGE and analysis.diff is None:
                analysis.diff = block
            elif (
                block.info == YAML_LANGUAGE
                and analysis.diff is None
                and analysis.yaml is None
                and analysis.replacement is None
            ):
                analysis.yaml = block
            elif analysis.replacement is None and block.info != DIFF_LANGUAGE:
                analysis.replacement = block

    def check_new_heading(self, analysis: Analysis, new: re.Match[str]) -> None:
        where = analysis.sub.heading
        kind, slug = new.group("kind"), new.group("slug")
        if kind not in NEW_KINDS:
            self.findings.add(
                Rule.SUBSECTION_HEADINGS,
                where,
                f"the kind {kind} is no kind of a Node or Decision Record",
            )
        if INDEX_PREFIX_PATTERN.match(slug):
            self.findings.add(
                Rule.NO_INDEX,
                where,
                "a record names no Index for a new Node or Decision Record",
            )
        if not self.siblings_exist(new.group("before"), new.group("after")):
            self.findings.add(
                Rule.SUBSECTION_HEADINGS,
                where,
                "the two siblings stand together at the Base",
            )
        analysis.is_node = kind not in DECISION_KINDS
        analysis.op = Op.CREATE
        analysis.path = ""

    def siblings_exist(self, before: str, after: str) -> bool:
        if not self.has_tree:
            return False
        stack = [TREE_ROOT]
        while stack:
            directory = stack.pop()
            names = self.base.children(directory)
            if before in names and after in names:
                return True
            stack.extend(
                f"{directory}/{name}"
                for name in names
                if self.base.is_dir(f"{directory}/{name}")
            )
        return False

    def check_path_heading(self, analysis: Analysis) -> None:
        heading = analysis.heading
        where = analysis.sub.heading
        if (
            not PATH_PATTERN.match(heading)
            or heading.startswith("/")
            or ".." in heading.split("/")
            or heading.endswith("/")
        ):
            self.findings.add(
                Rule.SUBSECTION_HEADINGS,
                where,
                "a heading names a path with no space, no leading slash, and no parent step",
            )
            analysis.valid = False
            return
        if (
            self.has_tree
            and not heading.startswith(f"{TREE_ROOT}/")
            and not self.in_moved_prefix(heading)
        ):
            self.findings.add(
                Rule.SUBSECTION_HEADINGS, where, "a heading names its path from spx/"
            )
            analysis.valid = False
            return
        analysis.path = heading
        analysis.read_path = heading
        moved = self.in_moved_prefix(heading)
        if moved is not None:
            analysis.in_moved = True
            analysis.read_path = moved
        analysis.kind = path_kind(heading, self.has_tree)
        analysis.is_node = analysis.kind is PathKind.NODE

    def in_moved_prefix(self, path: str) -> str | None:
        for old, new in self.moves:
            if path.startswith(f"{new}/"):
                return f"{old}{path[len(new) :]}"
        return None

    # ---- payloads

    def check_payloads(self, analysis: Analysis) -> None:
        sub = analysis.sub
        where = sub.heading
        for block in sub.blocks:
            if not block.info:
                self.findings.add(
                    Rule.FENCE,
                    where,
                    f"the block at line {block.line} names no language",
                )
        diff, replacement, yaml = analysis.diff, analysis.replacement, analysis.yaml
        headers: list[str] = []
        rest: list[tuple[int, str]] = []
        if diff is not None:
            headers, rest = split_diff(diff)
            analysis.headers = headers
            analysis.edit_lines = rest
            analysis.op = classify_operation(headers)
        move_rewrite = (
            diff is not None
            and replacement is not None
            and not rest
            and sum(header.startswith(GIT_HEADER_RENAME_FROM) for header in headers)
            >= 1
        )
        if diff is not None and replacement is not None and not move_rewrite:
            self.findings.add(
                Rule.ONE_PAYLOAD,
                where,
                "a subsection holds one payload, a diff block or a replacement, except a move that rewrites its file",
            )
        elif diff is None and replacement is None:
            self.findings.add(
                Rule.PAYLOADS, where, "a subsection holds a diff block or a replacement"
            )
        elif replacement is not None and yaml is not None:
            self.findings.add(
                Rule.PAYLOADS,
                where,
                "a replacement holds the whole front matter and takes no yaml block",
            )
        extra = len(sub.blocks) - sum(
            item is not None for item in (diff, replacement, yaml)
        )
        if extra > 0:
            self.findings.add(
                Rule.PAYLOADS, where, "a subsection holds no block besides its payload"
            )
        if replacement is not None and diff is None:
            analysis.op = Op.REPLACE
        if replacement is not None:
            self.check_replacement(analysis, replacement)

    def check_replacement(self, analysis: Analysis, block: Block) -> None:
        where = analysis.sub.heading
        expected = language_for(analysis.path or analysis.heading, analysis.is_node)
        if (
            expected is not None
            and block.info
            and block.info not in {expected, TEXT_LANGUAGE}
        ):
            self.findings.add(
                Rule.PAYLOADS,
                where,
                f"a replacement is fenced with the file's own language, {expected}",
            )
        longest = 0
        for text in block.lines:
            inner = FENCE_OPEN_PATTERN.match(text)
            if inner is not None:
                longest = max(longest, len(inner.group("fence")))
        if longest >= len(block.fence):
            self.findings.add(
                Rule.FENCE,
                where,
                "a replacement's outer fence is longer than every fence inside the file",
            )

    # ---- operations and lines

    def check_operation_and_lines(self, analysis: Analysis) -> None:
        self.check_headers(analysis)
        self.check_kinds(analysis)
        if analysis.op is Op.MOVE:
            self.register_move(analysis)
        self.check_front_matter(analysis)
        self.check_lines(analysis)

    def check_headers(self, analysis: Analysis) -> None:
        where = analysis.sub.heading
        headers = analysis.headers
        for header in headers:
            exact = header in {GIT_HEADER_DELETE, GIT_HEADER_CREATE}
            rename = header.startswith((GIT_HEADER_RENAME_FROM, GIT_HEADER_RENAME_TO))
            if not exact and not rename:
                self.findings.add(
                    Rule.NO_MODE,
                    where,
                    f"the header `{header}` is no header of a record; it carries a file mode or is another git header",
                )
        if not headers:
            return
        rest = [text for _, text in analysis.edit_lines]
        if analysis.op is Op.DELETE:
            if len(headers) != 1 or any(line.strip() for line in rest):
                self.findings.add(
                    Rule.HEADERS, where, "nothing follows the deleted file header"
                )
        elif analysis.op is Op.CREATE:
            if len(headers) != 1 or any(
                line.strip() and not line.startswith("+") for line in rest
            ):
                self.findings.add(
                    Rule.HEADERS,
                    where,
                    "every line after the new file header is a + line",
                )
        else:
            self.check_rename_headers(analysis)

    def check_rename_headers(self, analysis: Analysis) -> None:
        where = analysis.sub.heading
        renames = [
            h
            for h in analysis.headers
            if h.startswith((GIT_HEADER_RENAME_FROM, GIT_HEADER_RENAME_TO))
        ]
        pairs_ok = (
            len(renames) >= 2
            and len(renames) % 2 == 0
            and all(
                renames[i].startswith(GIT_HEADER_RENAME_FROM)
                and renames[i + 1].startswith(GIT_HEADER_RENAME_TO)
                for i in range(0, len(renames), 2)
            )
        )
        if (
            not pairs_ok
            or GIT_HEADER_DELETE in analysis.headers
            or GIT_HEADER_CREATE in analysis.headers
        ):
            self.findings.add(
                Rule.HEADERS,
                where,
                "a move opens with rename from the heading's path, then rename to the new path",
            )
            return
        source = renames[0].removeprefix(GIT_HEADER_RENAME_FROM).strip()
        if source != analysis.path:
            self.findings.add(
                Rule.HEADERS, where, "rename from names the heading's path"
            )
        analysis.rename_to = renames[1].removeprefix(GIT_HEADER_RENAME_TO).strip()

    def register_move(self, analysis: Analysis) -> None:
        if not analysis.rename_to:
            return
        self.moves.append((analysis.path, analysis.rename_to))
        if analysis.is_node:
            self.check_slug_rename(analysis)

    def check_slug_rename(self, analysis: Analysis) -> None:
        old = NODE_DIR_PATTERN.match(analysis.path.rsplit("/", 1)[-1])
        new = NODE_DIR_PATTERN.match(analysis.rename_to.rsplit("/", 1)[-1])
        if old is None or new is None or old.group("slug") == new.group("slug"):
            return
        renames = {
            analysis.headers[i]
            .removeprefix(GIT_HEADER_RENAME_FROM)
            .strip(): analysis.headers[i + 1].removeprefix(GIT_HEADER_RENAME_TO).strip()
            for i in range(len(analysis.headers) - 1)
            if analysis.headers[i].startswith(GIT_HEADER_RENAME_FROM)
        }
        for suffixes in ((".spec.md", ".md"), (".outcome.md",)):
            for suffix in suffixes:
                source = f"{analysis.path}/{old.group('slug')}{suffix}"
                if self.base.exists(source):
                    target = f"{analysis.rename_to}/{new.group('slug')}{suffix}"
                    if renames.get(source) != target:
                        self.findings.add(
                            Rule.SLUG_RENAME,
                            analysis.sub.heading,
                            f"a move that changes a Node's slug renames {source} to {target}",
                        )
                    break

    def check_kinds(self, analysis: Analysis) -> None:
        where = analysis.sub.heading
        if analysis.new is not None or not analysis.path:
            return
        if analysis.in_moved:
            return
        kind = analysis.kind
        base_entry = self.base.entry(analysis.path)
        if analysis.op is Op.CREATE:
            if kind not in CREATE_KINDS:
                self.findings.add(
                    Rule.OPERATION_KINDS,
                    where,
                    "new file creates only a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree",
                )
            if base_entry is not None:
                self.findings.add(
                    Rule.OPERATION_KINDS,
                    where,
                    "the path of a new file does not exist at the Base",
                )
            return
        if kind not in READ_KINDS:
            self.findings.add(
                Rule.OPERATION_KINDS,
                where,
                "an operation acts on a Node, a Decision Record, a spec, a contract file, an Outcome record, the Product spec, or a file of a Product with no Product Tree",
            )
        if base_entry is None:
            self.findings.add(
                Rule.SUBSECTION_HEADINGS,
                where,
                "the path of an existing file stands at the Base",
            )
            return
        if kind is not PathKind.NODE and self.base.regular_text(analysis.path) is None:
            self.findings.add(
                Rule.OPERATION_KINDS,
                where,
                "the file is a regular text file at the Base",
            )
        if kind is PathKind.NODE and not self.base.is_dir(analysis.path):
            self.findings.add(
                Rule.OPERATION_KINDS,
                where,
                "a Node heading names a directory at the Base",
            )
        if analysis.op is Op.DELETE and kind in {PathKind.SPEC, PathKind.PRODUCT_SPEC}:
            self.findings.add(
                Rule.SPEC_DELETION,
                where,
                "a Change deletes a spec only with its Node and never deletes the Product spec",
            )

    def check_front_matter(self, analysis: Analysis) -> None:
        where = analysis.sub.heading
        spec_target = analysis.is_node or analysis.kind is PathKind.SPEC
        if analysis.yaml is not None:
            metadata, _, bad = parse_metadata(
                [
                    (analysis.yaml.line + 1 + i, t)
                    for i, t in enumerate(analysis.yaml.lines)
                ]
            )
            for number, text in bad:
                self.findings.add(
                    Rule.FRONT_MATTER_BLOCK,
                    f"line {number}",
                    f"`{text}` is no front-matter field",
                )
            allowed = {"id", "malleability", "kind"}
            for name in metadata:
                if name not in allowed:
                    self.findings.add(
                        Rule.FRONT_MATTER_BLOCK,
                        where,
                        f"{name} is no front-matter field of a Node",
                    )
            if (
                "malleability" in metadata
                and metadata["malleability"] not in MALLEABILITY_LEVELS
            ):
                self.findings.add(
                    Rule.FRONT_MATTER_BLOCK,
                    where,
                    f"malleability is one of {', '.join(MALLEABILITY_LEVELS)}",
                )
            self.check_id(analysis, metadata.get("id"))
        for number, text in analysis.edit_lines:
            match = FRONT_MATTER_FIELD_PATTERN.match(text)
            if match is not None and spec_target:
                self.findings.add(
                    Rule.FRONT_MATTER_BLOCK,
                    f"line {number}",
                    "a diff block sets a front-matter field only through the yaml block before it",
                )
        if (
            analysis.replacement is not None
            and spec_target
            and analysis.op in {Op.REPLACE, Op.MOVE, Op.EDIT}
        ):
            lines = list(analysis.replacement.lines)
            if (
                not lines
                or lines[0].strip() != "---"
                or front_matter_value(lines, "id") is None
                and "---" not in [t.strip() for t in lines[1:]]
            ):
                self.findings.add(
                    Rule.FRONT_MATTER_BLOCK,
                    where,
                    "a replaced spec holds its whole front matter",
                )
            else:
                self.check_id(analysis, front_matter_value(lines, "id"))

    def check_id(self, analysis: Analysis, declared: Any) -> None:
        if declared is None or not analysis.read_path:
            return
        spec = (
            node_spec_path(self.base, analysis.read_path)
            if analysis.is_node
            else analysis.read_path
        )
        if not spec:
            return
        text = self.base.regular_text(spec)
        if text is None:
            return
        current = front_matter_value(text.split("\n"), "id")
        if current is not None and str(declared) != current:
            self.findings.add(
                Rule.FRONT_MATTER_BLOCK,
                analysis.sub.heading,
                "a replaced or moved spec keeps its Node's id",
            )

    # ---- diff lines

    def base_lines(self, analysis: Analysis) -> list[str] | None:
        path = analysis.read_path
        if not path:
            return None
        if analysis.is_node and self.base.is_dir(path):
            path = node_spec_path(self.base, path) or ""
        text = self.base.regular_text(path) if path else None
        return None if text is None else text.split("\n")

    def check_lines(self, analysis: Analysis) -> None:
        if not analysis.edit_lines and analysis.diff is None:
            return
        reads = self.base_lines(analysis)
        known = {line.rstrip() for line in reads} if reads is not None else set()
        move_like = analysis.op is Op.MOVE or analysis.in_moved
        read_rule = Rule.MOVE_READS if move_like else Rule.DIFF_LINES
        group = ""
        carried = removed_tags(analysis.edit_lines)
        for number, raw in analysis.edit_lines:
            where = f"{analysis.sub.heading} line {number}"
            if raw.startswith(SCAFFOLDING_PREFIXES):
                self.findings.add(
                    Rule.BODY_LINES_ONLY,
                    where,
                    "a diff block holds only lines of the file's body",
                )
                continue
            marker = raw[:1] if raw[:1] in {"+", "-"} else " "
            content = marker_content(raw)
            heading = GROUP_PATTERN.match(content)
            if heading is not None:
                group = heading.group("slug")
            case = row_case(content)
            label = f"{group}/{case}" if group and case else where
            if marker == "+":
                self.check_added(analysis, label, content, case, carried)
            elif (
                content.strip() and reads is not None and content.rstrip() not in known
            ):
                self.findings.add(
                    read_rule,
                    label,
                    f"the {'-' if marker == '-' else 'context'} line `{content.strip()[:60]}` stands in the file at the Base",
                )
            elif content.strip() and reads is None:
                self.findings.add(
                    read_rule,
                    label,
                    "the file the line reads does not stand at the Base",
                )

    def check_added(
        self,
        analysis: Analysis,
        label: str,
        content: str,
        case: str,
        carried: Mapping[str, set[str]],
    ) -> None:
        row = ROW_PATTERN.match(content)
        kept = carried.get(row.group("slug"), set()) if row is not None else set()
        if set(TAG_PATTERN.findall(content)) - kept:
            self.findings.add(Rule.NO_TAG, label, "a Declarations line adds no tag")
        for link in LINK_PATTERN.finditer(content):
            if not TAG_PATTERN.search(link.group(0)) and not self.evidence_exists(
                analysis, link.group("target")
            ):
                self.findings.add(
                    Rule.PLAIN_SLUG,
                    label,
                    f"the evidence {link.group('target')} is absent at the Base, so its slug stands plain",
                )
        if case and not CASE_PATTERN.match(case):
            self.findings.add(
                Rule.TABLE_CASE,
                label,
                "a table row's case reads as its subsection's slug, a slash, and the case slug",
            )

    def evidence_exists(self, analysis: Analysis, target: str) -> bool:
        directory = analysis.read_path or analysis.path
        if (
            analysis.kind in {PathKind.SPEC, PathKind.DECISION, PathKind.OUTCOME}
            and "/" in directory
        ):
            directory = directory.rsplit("/", 1)[0]
        return bool(directory) and self.base.exists(f"{directory}/{target}")

    # ---- files

    def write_keys(self, analysis: Analysis) -> list[str]:
        if analysis.new is not None or not analysis.path:
            return []
        keys = [self.file_key(analysis)]
        if analysis.op is Op.MOVE and analysis.rename_to:
            keys.append(analysis.rename_to)
        if analysis.op is Op.DELETE and analysis.is_node:
            keys.append(analysis.path)
        return keys

    def file_key(self, analysis: Analysis) -> str:
        if analysis.kind is PathKind.NODE:
            spec = node_spec_path(self.base, analysis.path)
            return spec or f"{analysis.path}#spec"
        return analysis.path

    def check_files(self) -> None:
        owners: dict[str, str] = {}
        for analysis in self.analyses:
            if not analysis.valid:
                continue
            for key in self.write_keys(analysis):
                if key in owners:
                    self.findings.add(
                        Rule.ONE_SUBSECTION_PER_FILE,
                        analysis.sub.heading,
                        f"{key.removesuffix('#spec')} is written by {owners[key]} as well",
                    )
                else:
                    owners[key] = analysis.sub.heading
        self.check_inside_removed(owners)

    def check_inside_removed(self, owners: Mapping[str, str]) -> None:
        removed = [
            a.path
            for a in self.analyses
            if a.valid and a.is_node and a.op in {Op.DELETE, Op.MOVE} and a.path
        ]
        for analysis in self.analyses:
            if not analysis.valid or analysis.in_moved or not analysis.path:
                continue
            for directory in removed:
                if analysis.path.startswith(f"{directory}/"):
                    self.findings.add(
                        Rule.ONE_SUBSECTION_PER_FILE,
                        analysis.sub.heading,
                        f"{directory} is deleted or moved by another subsection",
                    )

    def check_path_naming(self) -> None:
        keyed = {
            key.removesuffix("#spec")
            for a in self.analyses
            for key in self.write_keys(a)
        }
        for analysis in self.analyses:
            if (
                not analysis.valid
                or analysis.op not in {Op.DELETE, Op.MOVE}
                or not analysis.path
            ):
                continue
            needle = analysis.path
            for path in self.base.mentions(needle):
                if path.startswith(f"{needle}/") or path == needle:
                    continue
                if KNOWLEDGE_DIR in path.split("/"):
                    continue
                if self.covered(path, keyed):
                    continue
                if path_kind(path, self.has_tree) not in READ_KINDS:
                    continue
                self.findings.add(
                    Rule.PATH_NAMING,
                    analysis.sub.heading,
                    f"{path} names {needle}; it takes its own subsection",
                )

    def covered(self, path: str, keyed: set[str]) -> bool:
        if path in keyed:
            return True
        parts = path.split("/")
        return any("/".join(parts[:i]) in keyed for i in range(1, len(parts)))

    # ---- infrastructure

    def check_infrastructure(self, analysis: Analysis) -> None:
        lines = [
            (n, t) for n, t in analysis.sub.loose if t.startswith(INFRASTRUCTURE_LABEL)
        ]
        node_subsection = (
            (analysis.is_node or analysis.kind is PathKind.SPEC)
            and analysis.valid
            and not analysis.in_moved
        )
        where = analysis.sub.heading
        if not node_subsection:
            if lines:
                self.findings.add(
                    Rule.INFRASTRUCTURE_LINE,
                    where,
                    "only a Node subsection holds infrastructure lines",
                )
            return
        self.check_line_positions(analysis, lines)
        entries = self.parse_infrastructure(analysis, lines)
        before, after, before_units, after_units = self.assertion_state(analysis)
        if after == "spec":
            if lines:
                self.findings.add(
                    Rule.SPEC_NODE_NONE,
                    where,
                    "an Assertion of a spec-malleable Node carries no infrastructure line",
                )
            return
        required, replaced = self.required_slugs(
            before, after, before_units, after_units
        )
        for slug in sorted(required):
            rule = (
                Rule.REPLACED_ASSERTION
                if slug in replaced
                else Rule.INFRASTRUCTURE_LINE
            )
            count = sum(1 for entry_slug, _ in entries if entry_slug == slug)
            if count == 0:
                self.findings.add(
                    rule,
                    f"{where} {slug}",
                    f"the subsection ends with one infrastructure line for {slug}",
                )
            elif count > 1:
                self.findings.add(
                    Rule.INFRASTRUCTURE_LINE,
                    f"{where} {slug}",
                    f"the subsection holds {count} infrastructure lines for {slug}; it holds one",
                )
        for slug in sorted({s for s, _ in entries} - required):
            self.findings.add(
                Rule.INFRASTRUCTURE_LINE,
                f"{where} {slug}",
                f"{slug} is no Assertion the subsection adds or replaces",
            )
        for slug, paths in entries:
            for path in paths:
                if not self.node_available(path):
                    self.findings.add(
                        Rule.INFRASTRUCTURE_EXISTS,
                        f"{where} {slug}",
                        f"{path} stands at the Base or a blocking Change builds it",
                    )

    def check_line_positions(
        self, analysis: Analysis, lines: list[tuple[int, str]]
    ) -> None:
        if not lines:
            return
        last_block = max(
            (block.line + len(block.lines) + 1 for block in analysis.sub.blocks),
            default=0,
        )
        for number, text in lines:
            if number < last_block:
                self.findings.add(
                    Rule.INFRASTRUCTURE_LINE,
                    f"line {number}",
                    "the subsection ends with its infrastructure lines",
                )
        others = [
            (n, t)
            for n, t in analysis.sub.loose
            if not t.startswith(INFRASTRUCTURE_LABEL) and n > last_block
        ]
        if others and lines and others[-1][0] > lines[0][0]:
            self.findings.add(
                Rule.INFRASTRUCTURE_LINE,
                f"line {others[-1][0]}",
                "the subsection ends with its infrastructure lines",
            )

    def parse_infrastructure(
        self, analysis: Analysis, lines: list[tuple[int, str]]
    ) -> list[tuple[str, list[str]]]:
        entries: list[tuple[str, list[str]]] = []
        for number, text in lines:
            match = INFRASTRUCTURE_PATTERN.match(text)
            if match is None:
                self.findings.add(
                    Rule.INFRASTRUCTURE_FORM,
                    f"line {number}",
                    "an infrastructure line reads `Infrastructure:`, the Assertion's slug, and either the path of each Node or `none`",
                )
                continue
            rest = match.group("rest").strip()
            if rest == INFRASTRUCTURE_NONE:
                entries.append((match.group("slug"), []))
            elif PATH_LIST_PATTERN.match(rest):
                entries.append((match.group("slug"), re.findall(r"`([^`]+)`", rest)))
            else:
                self.findings.add(
                    Rule.INFRASTRUCTURE_FORM,
                    f"line {number}",
                    "each path stands in a code span with a comma between two paths, or `none` stands in their place",
                )
        return entries

    def assertion_state(
        self, analysis: Analysis
    ) -> tuple[str | None, str, dict[Unit, str], dict[Unit, str]]:
        base_lines = self.base_lines(analysis) if analysis.new is None else None
        before = malleability_of(base_lines) if base_lines is not None else None
        before_units = parse_units(base_lines) if base_lines is not None else {}
        if analysis.replacement is not None and analysis.diff is None:
            lines = list(analysis.replacement.lines)
        elif analysis.replacement is not None:
            lines = list(analysis.replacement.lines)
        else:
            edits = analysis.edit_lines
            lines = (
                apply_line_edits(base_lines or [], edits)
                if base_lines is not None
                else [marker_content(t) for _, t in edits if t[:1] == "+"]
            )
        after = malleability_of(lines)
        if analysis.yaml is not None:
            declared = front_matter_value(
                ["---", *analysis.yaml.lines, "---"], "malleability"
            )
            after = declared or (before if before is not None else DEFAULT_MALLEABILITY)
        elif analysis.replacement is None and before is not None:
            after = before
        return before, after, before_units, parse_units(lines)

    def required_slugs(
        self,
        before: str | None,
        after: str,
        before_units: Mapping[Unit, str],
        after_units: Mapping[Unit, str],
    ) -> tuple[set[str], set[str]]:
        required: set[str] = set()
        replaced: set[str] = set()
        for unit, text in after_units.items():
            if unit not in before_units:
                required.add(unit.slug)
            elif before_units[unit] != text:
                required.add(unit.slug)
                replaced.add(unit.slug)
        hardens = before is not None and MALLEABILITY_LEVELS.index(
            after
        ) > MALLEABILITY_LEVELS.index(before)
        if hardens:
            required |= {unit.slug for unit in after_units}
        return required, replaced

    def node_available(self, path: str) -> bool:
        if self.base.is_dir(path):
            return True
        match = NODE_DIR_PATTERN.match(path.rstrip("/").rsplit("/", 1)[-1])
        if match is None:
            return False
        target = (match.group("slug"), match.group("kind"))
        for reference in self.blockers:
            record = self.blocker_records.get(reference)
            if record is not None and target in created_nodes(
                str(record.get(RecordField.BODY, ""))
            ):
                return True
        return False


def removed_tags(edits: Sequence[tuple[int, str]]) -> dict[str, set[str]]:
    """Map the slug of each removed row to the tags that row carried."""

    carried: dict[str, set[str]] = {}
    for _, raw in edits:
        if raw[:1] != "-":
            continue
        row = ROW_PATTERN.match(marker_content(raw))
        if row is not None:
            carried[row.group("slug")] = set(TAG_PATTERN.findall(raw))
    return carried


def row_case(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("|") or SEPARATOR_ROW_PATTERN.match(stripped):
        return ""
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    case = cells[0] if cells else ""
    return "" if case == HEADER_CASE else case


def created_nodes(body: str) -> set[tuple[str, str]]:
    created: set[tuple[str, str]] = set()
    draft = parse_draft("---\n---\n" + body)
    for section in draft.sections:
        for sub in section.subsections:
            match = NEW_HEADING_PATTERN.match(normalized_heading(sub.heading))
            if match is not None and match.group("kind") not in DECISION_KINDS:
                created.add((match.group("slug"), match.group("kind")))
    return created


# ---------------------------------------------------------------- request


def read_request(request: object) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise InvalidRequest("the request is one JSON object")
    known = {field.value for field in RequestField}
    for name in request:
        if name not in known:
            raise InvalidRequest(f"{name} is no field of the request")
    return request


def required(request: Mapping[str, Any], name: RequestField) -> Any:
    if name not in request:
        raise InvalidRequest(f"{name} is missing")
    return request[name]


def read_draft_text(request: Mapping[str, Any]) -> str:
    text = request.get(RequestField.DRAFT_TEXT)
    path = request.get(RequestField.DRAFT_PATH)
    if (text is None) == (path is None):
        raise InvalidRequest(
            f"the request names exactly one of {RequestField.DRAFT_TEXT} and {RequestField.DRAFT_PATH}"
        )
    if text is not None:
        if not isinstance(text, str):
            raise InvalidRequest(f"{RequestField.DRAFT_TEXT} is a string")
        return text
    if not isinstance(path, str):
        raise InvalidRequest(f"{RequestField.DRAFT_PATH} is a string")
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raise InvalidRequest(
            f"{RequestField.DRAFT_PATH} names no readable text file"
        ) from None


def read_record(raw: Any, name: str) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or not isinstance(
        raw.get(RecordField.METADATA, {}), dict
    ):
        raise InvalidRequest(f"{name} is null or an object with metadata and body")
    return raw


def read_root(raw: Any) -> str:
    if (
        not isinstance(raw, str)
        or not Path(raw).is_absolute()
        or not Path(raw).is_dir()
    ):
        raise InvalidRequest(
            f"{RequestField.CHECKOUT_ROOT} is the absolute path of a directory"
        )
    return raw


def read_operation(raw: Any) -> Operation:
    try:
        return Operation(raw)
    except ValueError:
        raise InvalidRequest(
            f"{RequestField.OPERATION} is one of {', '.join(Operation)}"
        ) from None


def read_blockers(request: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw = request.get(RequestField.BLOCKER_RECORDS, {})
    if not isinstance(raw, dict) or not all(
        isinstance(value, dict) for value in raw.values()
    ):
        raise InvalidRequest(
            f"{RequestField.BLOCKER_RECORDS} maps each blocker reference to its record"
        )
    return {str(key): value for key, value in raw.items()}


def check(request: object, run: CommandRunner = run_command) -> dict[str, Any]:
    """Return for a request the result the script writes for it."""

    try:
        fields = read_request(request)
        text = read_draft_text(fields)
        root = read_root(required(fields, RequestField.CHECKOUT_ROOT))
        operation = read_operation(required(fields, RequestField.OPERATION))
        stored = read_record(
            required(fields, RequestField.STORED_RECORD), RequestField.STORED_RECORD
        )
        blockers = read_blockers(fields)
        limit = resolve_size_limit(required(fields, RequestField.SIZE_LIMIT))
    except InvalidRequest as error:
        return {
            ResultField.STATUS: Status.INVALID_REQUEST,
            ResultField.FINDINGS: [],
            ResultField.DETAIL: str(error),
        }
    findings = judge(text, root, operation, stored, blockers, limit, run)
    status = Status.FAIL if findings else Status.PASS
    return {
        ResultField.STATUS: status,
        ResultField.FINDINGS: [item.as_json() for item in findings],
    }


def judge(
    text: str,
    root: str,
    operation: Operation,
    stored: Mapping[str, Any] | None,
    blocker_records: Mapping[str, Mapping[str, Any]],
    limit: int,
    run: CommandRunner,
) -> list[Finding]:
    draft = parse_draft(text)
    findings = Findings()
    stored_metadata = None if stored is None else stored.get(RecordField.METADATA, {})
    check_metadata(draft, stored_metadata, operation, findings)
    has_declarations = check_body(draft, findings)
    check_homes(draft, findings)
    check_size(draft, limit, findings)
    for section in draft.sections:
        if section.title == SECTION_STATEMENT:
            check_statement(section, findings)
    leaf = not isinstance(draft.metadata.get(Key.PRODUCT), list)
    declarations = next(
        (s for s in draft.sections if s.title == SECTION_DECLARATIONS), None
    )
    commit = draft.metadata.get(Key.BASE)
    if leaf and declarations is not None and has_declarations:
        base = Base(root, commit if isinstance(commit, str) else "", run)
        blockers = [
            str(item)
            for item in draft.metadata.get(Key.BLOCKERS, [])
            if isinstance(item, (str, int))
        ]
        DeclarationChecker(base, draft, blockers, blocker_records, findings).run(
            declarations
        )
    return findings.items


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    run: CommandRunner = run_command,
) -> int:
    source = stdin if stdin is not None else sys.stdin
    sink = stdout if stdout is not None else sys.stdout
    try:
        request: object = json.loads(source.read())
    except json.JSONDecodeError:
        result: dict[str, Any] = {
            ResultField.STATUS: Status.INVALID_REQUEST,
            ResultField.FINDINGS: [],
            ResultField.DETAIL: "the request is one JSON document",
        }
    else:
        result = check(request, run)
    sink.write(json.dumps(result, sort_keys=True) + "\n")
    status = result[ResultField.STATUS]
    if status == Status.PASS:
        return EXIT_PASS
    return EXIT_FAIL if status == Status.FAIL else EXIT_INVALID_REQUEST


Callback = Callable[..., Any]

if __name__ == "__main__":
    sys.exit(main())
