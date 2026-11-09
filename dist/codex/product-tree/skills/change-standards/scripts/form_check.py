#!/usr/bin/env python3
"""Check the form of a Change Draft before a publish.

The check reads one Draft file and the checkout it names paths in, runs only
reading ``git`` and ``gh`` commands, writes nothing, and prints one JSON result:
``status`` (``pass`` or ``fail``), ``findings`` (one ``{rule, location, detail}``
entry per breach, named by the slug of the rule it breaks), and ``informational``
(each file at the Base that names a deleted or moved path and takes a mechanical
repair rather than a subsection). It exits 0 on ``pass``, 1 on ``fail``, and 2
when the invocation is unusable.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Final, Protocol

TEXT_ENCODING: Final = "utf-8"
GITHUB_BODY_LIMIT: Final = 65_536
TITLE_WORD_LIMIT: Final = 15
INTENT_WORD_LIMIT: Final = 120
NODE_BOUND: Final = 5


class ExitCode(IntEnum):
    """Exit status of one check."""

    PASS = 0
    FAIL = 1
    UNUSABLE = 2


class Rule(StrEnum):
    """Slugs of the rules the check judges."""

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
    DEPENDS_ON_FORM = "depends-on-form"
    PRECEDES_FORM = "precedes-form"
    NEW_PATH_REFERENCE = "new-path-reference"
    MOVE_READS = "move-reads"
    ONE_PAYLOAD = "one-payload"
    FENCE = "fence"
    NO_MODE = "no-mode"
    OPERATION_KINDS = "operation-kinds"
    SPEC_DELETION = "spec-deletion"
    ONE_SUBSECTION_PER_FILE = "one-subsection-per-file"
    NEW_SIBLING_NAMES = "new-sibling-names"
    SLUG_RENAME = "slug-rename"
    PATH_NAMING = "path-naming"
    INFRASTRUCTURE_LINE = "infrastructure-line"
    REPLACED_ASSERTION = "replaced-assertion"
    INFRASTRUCTURE_FORM = "infrastructure-form"
    INFRASTRUCTURE_EXISTS = "infrastructure-exists"
    SPEC_NODE_NONE = "spec-node-none"
    NONE_LEAF = "none-leaf"
    ONE_PRODUCT = "one-product"
    DRAFT_LIFECYCLE = "draft-lifecycle"
    DRAFT_BASE = "draft-base"
    SIZE_LIMIT = "size-limit"
    STALE_REVISION = "stale-revision"
    OPERATOR_BOUND_BASE = "operator-bound-base"
    ONE_HOME = "one-home"


DRAFT_KEYS: Final = (
    "title",
    "product",
    "maturity",
    "lifecycle",
    "parent",
    "predecessors",
    "blockers",
    "base",
    "priority",
    "primary_value",
    "investment",
)
RECORD_KEYS: Final = frozenset({*DRAFT_KEYS, "holder"})
MATURITIES: Final = ("Proposed", "Framed", "Sliced", "Applicable")
LIFECYCLES: Final = ("Available", "Submitted", "Applied", "Abandoned")
PRIMARY_VALUES: Final = ("Offering", "Quality", "Capability", "Safety")
INVESTMENTS: Final = ("Harvest", "Shield", "Frontier", "Seed")
MALLEABILITY_ORDER: Final = ("spec", "verification", "implementation")
NODE_KINDS: Final = (
    "product",
    "substrate",
    "capability",
    "domain",
    "interface",
    "surface",
    "variant",
    "enabler",
    "outcome",
)
OPENING_KEYWORDS: Final = (
    "PROVIDES",
    "SUPPLIES",
    "OWNS",
    "ADAPTS",
    "EXPOSES",
    "SO THAT",
    "CAN",
    "FOR",
    "TO",
    "GOVERNS",
    "CONSTRAINS",
    "DEFINES",
)
GIT_HEADERS: Final = (
    "diff --git",
    "index ",
    "--- ",
    "+++ ",
    "similarity index",
    "dissimilarity index",
    "old mode",
    "new mode",
    "copy from",
    "copy to",
)
SECTION_INTENT: Final = "Statement of Intent"
SECTION_DECLARATIONS: Final = "Declarations"
INTENT_PARTS: Final = ("Output", "Why", "Verification")

REF_RE: Final = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*$")
SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")
SLUG_RE: Final = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CASE_RE: Final = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
NODE_SEGMENT_RE: Final = re.compile(
    r"^(?P<index>NN|\d{2}(?:\.\d{2})*)-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.(?P<kind>[a-z]+)$"
)
DECISION_SEGMENT_RE: Final = re.compile(
    r"^(?P<index>NN|\d{2}(?:\.\d{2})*)-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.(?P<kind>adr|pdr)\.md$"
)
FENCE_RE: Final = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<info>[^`]*)$")
DEPENDS_RE: Final = re.compile(r"^Depends on: (?:none|`[^`\s]+`(?:, `[^`\s]+`)*)$")
PRECEDES_RE: Final = re.compile(r"^Precedes: (?:none|`[^`\s]+`(?:, `[^`\s]+`)*)$")
INFRA_RE: Final = re.compile(
    r"^Infrastructure: (?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)?) "
    r"(?P<paths>none|`[^`\s]+`(?:, `[^`\s]+`)*)$"
)
ROW_SLUG_RE: Final = re.compile(r"^- (?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*): ")
LINKED_SLUG_RE: Final = re.compile(r"^- \[(?P<slug>[a-z0-9-]+)\]\((?P<path>[^)]+)\): ")
TAG_RE: Final = re.compile(
    r"\((?:\[(?:test|eval|probe)\]\([^)]*\)|\[audit(?::[a-z0-9-]+)?\])\)"
)
GROUP_HEADING_RE: Final = re.compile(
    r"^#{3,} (?P<type>[A-Za-z.]+)(?:: (?P<subject>.+))?$"
)
CODE_PATH_RE: Final = re.compile(r"`([^`\s]+)`")
METADATA_LINE_RE: Final = re.compile(
    r"^(?:" + "|".join(sorted(RECORD_KEYS)) + r"):(?:\s|$)"
)


@dataclass(frozen=True)
class CommandResult:
    """What one external command produced."""

    exit_code: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    """Execute one reading command through an injectable process boundary."""

    def __call__(
        self, argv: Sequence[str], /, *, cwd: pathlib.Path
    ) -> CommandResult: ...


def run_subprocess(argv: Sequence[str], /, *, cwd: pathlib.Path) -> CommandResult:
    """Run ``argv`` without a shell and capture its output."""
    completed = subprocess.run(  # noqa: S603
        list(argv), cwd=cwd, capture_output=True, check=False, stdin=subprocess.DEVNULL
    )
    return CommandResult(
        completed.returncode,
        completed.stdout.decode(TEXT_ENCODING, "backslashreplace"),
        completed.stderr.decode(TEXT_ENCODING, "backslashreplace"),
    )


class Unusable(Exception):
    """The invocation cannot be judged; the detail names the argument or read."""


@dataclass(frozen=True)
class Finding:
    """One breach of one rule."""

    rule: Rule
    location: str
    detail: str


@dataclass
class Block:
    """One fenced block of a subsection."""

    fence: str
    info: str
    lines: list[str]


@dataclass
class Subsection:
    """One Declarations subsection."""

    heading: str
    preamble: list[str] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)
    trailing: list[str] = field(default_factory=list)
    stray: list[str] = field(default_factory=list)


@dataclass
class Draft:
    """A parsed Change Draft."""

    keys: list[str]
    values: dict[str, str]
    body: str


@dataclass
class Context:
    """The checkout, the runner, and the findings of one check."""

    root: pathlib.Path
    runner: CommandRunner
    findings: list[Finding] = field(default_factory=list)
    informational: list[dict[str, str]] = field(default_factory=list)

    def add(self, rule: Rule, location: str, detail: str) -> None:
        self.findings.append(Finding(rule, location, detail))

    def git(self, *argv: str) -> CommandResult:
        return self.runner(["git", *argv], cwd=self.root)


def count_words(text: str) -> int:
    """Count words as a reader does: tokens holding a letter or a digit."""
    return sum(1 for token in text.split() if re.search(r"[A-Za-z0-9]", token))


def parse_draft(text: str) -> Draft:
    """Split a Draft into its front-matter keys, raw values, and body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise Unusable("the Draft opens with no `---` front-matter line")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise Unusable("the Draft's front matter has no closing `---` line") from exc
    keys: list[str] = []
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator or line[0].isspace():
            raise Unusable(f"front-matter line is no `key: value` line: {line!r}")
        keys.append(key.strip())
        values[key.strip()] = value.strip()
    return Draft(keys, values, "\n".join(lines[end + 1 :]).lstrip("\n"))


def scalar(raw: str) -> str | None:
    """Return a front-matter scalar, ``None`` for ``null``."""
    if raw in ("null", "~", ""):
        return None
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    return raw


def flow_list(raw: str) -> list[str] | None:
    """Return the entries of a YAML flow list, or ``None`` when ``raw`` is none."""
    if not (raw.startswith("[") and raw.endswith("]")):
        return None
    inner = raw[1:-1].strip()
    return [entry.strip() for entry in inner.split(",")] if inner else []


def check_keys(context: Context, draft: Draft, recorded: bool) -> bool:
    """Judge the metadata; return whether the Draft is a Leaf."""
    has_base = "base" in draft.values
    expected = [key for key in DRAFT_KEYS if has_base or key != "base"]
    if draft.keys != expected:
        context.add(
            Rule.RECORD_KEYS,
            "front matter",
            f"keys are {draft.keys}; a Draft holds exactly {expected} in this order, holder left out",
        )
    values = draft.values
    title = scalar(values.get("title", "")) or ""
    if not title or count_words(title) > TITLE_WORD_LIMIT:
        context.add(
            Rule.RECORD_KEYS,
            "title",
            f"the title holds {count_words(title)} words; it states the Output in 1 to {TITLE_WORD_LIMIT} words",
        )
    product = values.get("product", "")
    if not scalar(product) or product.startswith("["):
        context.add(
            Rule.ONE_PRODUCT,
            "product",
            f"product is {product!r}; a Change names one Product",
        )
    for key, allowed in (
        ("maturity", MATURITIES),
        ("lifecycle", LIFECYCLES),
    ):
        if scalar(values.get(key, "")) not in allowed:
            context.add(
                Rule.RECORD_KEYS,
                key,
                f"{key} is {values.get(key)!r}; it holds one of {allowed}",
            )
    for key, allowed in (
        ("primary_value", PRIMARY_VALUES),
        ("investment", INVESTMENTS),
    ):
        value = scalar(values.get(key, ""))
        if value is not None and value not in allowed:
            context.add(
                Rule.RECORD_KEYS,
                key,
                f"{key} is {value!r}; it holds null or one of {allowed}",
            )
    parent = scalar(values.get("parent", ""))
    if parent is not None and not REF_RE.match(parent):
        context.add(
            Rule.RECORD_KEYS,
            "parent",
            f"parent is {parent!r}; it holds null or one owner/repo#N reference",
        )
    for key in ("predecessors", "blockers"):
        entries = flow_list(values.get(key, ""))
        if entries is None or any(not REF_RE.match(entry) for entry in entries):
            context.add(
                Rule.RECORD_KEYS,
                key,
                f"{key} is {values.get(key)!r}; it holds [] or a list of owner/repo#N references",
            )
    if not recorded:
        lifecycle = scalar(values.get("lifecycle", ""))
        expected_lifecycle = "Available" if parent else "Submitted"
        if lifecycle != expected_lifecycle:
            context.add(
                Rule.DRAFT_LIFECYCLE,
                "lifecycle",
                f"lifecycle is {lifecycle!r}; recording gives a Change {'with' if parent else 'with no'} Parent {expected_lifecycle}",
            )
    return has_base


def check_base(context: Context, base: str | None) -> str | None:
    """Judge the Base; return it when it resolves."""
    if base is None or not SHA_RE.match(base):
        context.add(
            Rule.DRAFT_BASE,
            "base",
            f"base is {base!r}; a Leaf's base is the full 40-hex head commit of the default branch",
        )
        return None
    if context.git("cat-file", "-e", f"{base}^{{commit}}").exit_code != 0:
        context.add(
            Rule.DRAFT_BASE,
            "base",
            f"base {base} names no commit in the checkout; fetch the default branch and confirm the commit",
        )
        return None
    head = context.git("rev-parse", "--abbrev-ref", "origin/HEAD")
    default = (
        head.stdout.strip()
        if head.exit_code == 0 and head.stdout.strip()
        else "origin/main"
    )
    if context.git("merge-base", "--is-ancestor", base, default).exit_code != 0:
        context.add(
            Rule.DRAFT_BASE,
            "base",
            f"base {base} is no commit of {default}; the base names a head of the default branch",
        )
    return base


def split_sections(body: str) -> list[tuple[str, list[str]]]:
    """Split a body at its level-two headings, outside fenced blocks."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    fence: str | None = None
    for line in body.splitlines():
        match = FENCE_RE.match(line)
        if match and (
            fence is None
            or match.group("fence").startswith(fence)
            and not match.group("info").strip()
        ):
            fence = match.group("fence") if fence is None else None
        if fence is None and line.startswith("## ") and not match:
            sections.append((line[3:].strip(), []))
            continue
        sections[-1][1].append(line)
    return sections


def check_body(context: Context, draft: Draft, leaf: bool) -> list[str] | None:
    """Judge the body sections; return the Declarations lines of a Leaf."""
    sections = split_sections(draft.body)
    preamble, *named = sections
    if any(line.strip() for line in preamble[1]):
        context.add(
            Rule.RECORD_BODY,
            "body",
            "text stands before the first section; the body opens with `## Statement of Intent`",
        )
    names = [name for name, _ in named]
    maturity = scalar(draft.values.get("maturity", ""))
    if leaf:
        allowed = ([SECTION_INTENT], [SECTION_INTENT, SECTION_DECLARATIONS])
        if names not in allowed or (maturity != "Proposed" and names != allowed[1]):
            context.add(
                Rule.RECORD_BODY,
                "body",
                f"sections are {names}; a Leaf holds Statement of Intent then Declarations, a Proposed Leaf may hold the Statement of Intent alone",
            )
    elif names != [SECTION_INTENT]:
        context.add(
            Rule.RECORD_BODY,
            "body",
            f"sections are {names}; a Parent holds only its Statement of Intent",
        )
    for name, lines in named:
        for line in lines:
            if METADATA_LINE_RE.match(line):
                context.add(
                    Rule.ONE_HOME,
                    f"## {name}",
                    f"the body holds the metadata line {line!r}; each field has its one home",
                )
    intent = next((lines for name, lines in named if name == SECTION_INTENT), None)
    if intent is not None:
        check_intent(context, intent)
    return next((lines for name, lines in named if name == SECTION_DECLARATIONS), None)


def check_intent(context: Context, lines: list[str]) -> None:
    """Judge the three parts of the Statement of Intent."""
    items = [line for line in lines if line.strip()]
    labels = [item.partition(":")[0].removeprefix("- ") for item in items]
    if (
        len(items) != len(INTENT_PARTS)
        or labels != list(INTENT_PARTS)
        or not all(item.startswith("- ") for item in items)
    ):
        context.add(
            Rule.STATEMENT_OF_INTENT,
            "## Statement of Intent",
            "the section holds three list items, `- Output:`, `- Why:`, and `- Verification:`, in this order, and nothing else",
        )
    words = count_words(" ".join(items))
    if words > INTENT_WORD_LIMIT:
        context.add(
            Rule.STATEMENT_OF_INTENT,
            "## Statement of Intent",
            f"the Statement of Intent holds {words} words; the limit is {INTENT_WORD_LIMIT}",
        )


def split_subsections(context: Context, lines: list[str]) -> list[Subsection] | None:
    """Split the Declarations at their level-three headings; ``None`` for a none Leaf."""
    subsections: list[Subsection] = []
    lead: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = FENCE_RE.match(line)
        if match:
            fence, info = match.group("fence"), match.group("info").strip()
            body: list[str] = []
            index += 1
            while index < len(lines) and not (
                lines[index].startswith(fence)
                and not lines[index][len(fence) :].strip()
                and set(lines[index].strip()) == set(fence[0])
            ):
                body.append(lines[index])
                index += 1
            if index >= len(lines):
                context.add(
                    Rule.FENCE,
                    subsections[-1].heading if subsections else "## Declarations",
                    f"a block opened with {fence} never closes",
                )
            target = subsections[-1] if subsections else None
            if target is None:
                lead.append(line)
            else:
                if target.trailing:
                    target.stray.extend(target.trailing)
                    target.trailing = []
                target.blocks.append(Block(fence, info, body))
            index += 1
            continue
        if line.startswith("### "):
            subsections.append(Subsection(line[4:].strip()))
        elif not subsections:
            if line.strip():
                lead.append(line)
        elif line.strip():
            target = subsections[-1]
            (target.trailing if target.blocks else target.preamble).append(line)
        index += 1
    if not subsections:
        if not lead or not lead[0].startswith("none"):
            context.add(
                Rule.NONE_LEAF,
                "## Declarations",
                "a Leaf that declares nothing holds `none` and its reason",
            )
        return None
    if lead:
        context.add(
            Rule.PAYLOADS,
            "## Declarations",
            f"text stands before the first subsection: {lead[0]!r}",
        )
    return subsections


def path_segments(path: str) -> list[str]:
    return [segment for segment in path.split("/") if segment]


def is_new(path: str) -> bool:
    return any(segment.startswith("NN-") for segment in path_segments(path))


def new_prefix(path: str) -> str | None:
    """Return the path up to and including its last ``NN`` segment."""
    segments = path_segments(path)
    last = max(
        (i for i, segment in enumerate(segments) if segment.startswith("NN-")),
        default=None,
    )
    return None if last is None else "/".join(segments[: last + 1])


def node_kind(segment: str) -> str | None:
    match = NODE_SEGMENT_RE.match(segment)
    return match.group("kind") if match and match.group("kind") in NODE_KINDS else None


def is_node(path: str) -> bool:
    segments = path_segments(path)
    return bool(segments) and node_kind(segments[-1]) is not None


def is_decision(path: str) -> bool:
    segments = path_segments(path)
    return bool(segments) and DECISION_SEGMENT_RE.match(segments[-1]) is not None


def node_slug(segment: str) -> str:
    match = NODE_SEGMENT_RE.match(segment)
    return match.group("slug") if match else segment


def spec_candidates(node: str) -> list[str]:
    slug = node_slug(path_segments(node)[-1])
    return [f"{node}/{slug}.spec.md", f"{node}/{slug}.md"]


def is_spec(path: str) -> bool:
    segments = path_segments(path)
    if len(segments) < 2 or node_kind(segments[-2]) is None:
        return False
    slug = node_slug(segments[-2])
    return segments[-1] in (f"{slug}.spec.md", f"{slug}.md")


def is_product_spec(path: str) -> bool:
    segments = path_segments(path)
    return (
        len(segments) == 2
        and segments[0] == "spx"
        and (segments[1].endswith(".spec.md") or segments[1].endswith(".product.md"))
    )


def is_contract(path: str) -> bool:
    return "/contracts/" in path


def is_outcome(path: str) -> bool:
    return path.endswith(".outcome.md")


def at_base(context: Context, base: str | None, path: str) -> str | None:
    """Return the file at the Base, or ``None`` when absent or unreadable."""
    if base is None:
        return None
    result = context.git("show", f"{base}:{path}")
    return result.stdout if result.exit_code == 0 else None


def exists_at_base(context: Context, base: str | None, path: str) -> bool:
    return (
        base is not None
        and context.git("cat-file", "-e", f"{base}:{path}").exit_code == 0
    )


def tree_mode(context: Context, base: str | None, path: str) -> str | None:
    if base is None:
        return None
    result = context.git("ls-tree", base, "--", path)
    return (
        result.stdout.split(" ", 1)[0]
        if result.exit_code == 0 and result.stdout
        else None
    )


@dataclass
class Operation:
    """The operation one subsection's payload declares."""

    kind: str  # edit, replace, delete, create, move
    rename_to: str | None = None
    diff: Block | None = None
    replacement: Block | None = None
    front_matter: Block | None = None


def check_payload(context: Context, sub: Subsection) -> Operation | None:
    """Judge one subsection's payload and return its operation."""
    if sub.stray:
        context.add(
            Rule.PAYLOADS,
            sub.heading,
            f"text stands between the subsection's blocks: {sub.stray[0]!r}",
        )
    blocks = sub.blocks
    for block in blocks:
        if not block.info:
            context.add(Rule.FENCE, sub.heading, "a block carries no language")
    if not blocks:
        context.add(Rule.PAYLOADS, sub.heading, "the subsection holds no payload")
        return None
    infos = [block.info for block in blocks]
    if infos == ["diff"] or infos == ["yaml", "diff"]:
        diff = blocks[-1]
        operation = header_operation(context, sub, diff)
        operation.front_matter = blocks[0] if len(blocks) == 2 else None
        return operation
    if len(blocks) == 1:
        return Operation("replace", replacement=blocks[0])
    if len(blocks) == 2 and infos[0] == "diff":
        operation = header_operation(context, sub, blocks[0])
        if operation.kind != "move" or any(
            not line.startswith("rename ") for line in blocks[0].lines if line.strip()
        ):
            context.add(
                Rule.ONE_PAYLOAD,
                sub.heading,
                "a subsection holds both payloads only for a move whose diff holds the two rename headers alone",
            )
        operation.replacement = blocks[1]
        operation.diff = None
        return operation
    context.add(
        Rule.PAYLOADS,
        sub.heading,
        f"blocks are {infos}; a subsection holds line edits, a replacement, or a move with its replacement",
    )
    return None


def header_operation(context: Context, sub: Subsection, block: Block) -> Operation:
    lines = block.lines
    for line in lines:
        if line.startswith(GIT_HEADERS) or re.match(
            r"^(?:deleted|new) file mode", line
        ):
            context.add(
                Rule.NO_MODE,
                sub.heading,
                f"the block carries the git header {line!r}; only `deleted file`, `new file`, and the two rename headers stand in a record, and none carries a mode",
            )
    first = lines[0] if lines else ""
    if first == "deleted file":
        if any(line.strip() for line in lines[1:]):
            context.add(Rule.HEADERS, sub.heading, "nothing follows `deleted file`")
        return Operation("delete", diff=block)
    if first == "new file":
        if any(line and not line.startswith("+") for line in lines[1:]):
            context.add(
                Rule.HEADERS, sub.heading, "every line after `new file` is a `+` line"
            )
        return Operation("create", diff=block)
    if first.startswith("rename from "):
        second = lines[1] if len(lines) > 1 else ""
        if first[len("rename from ") :] != sub.heading:
            context.add(
                Rule.HEADERS, sub.heading, "`rename from` repeats the heading's path"
            )
        if not second.startswith("rename to "):
            context.add(Rule.HEADERS, sub.heading, "`rename to` follows `rename from`")
            return Operation("move", diff=block)
        return Operation(
            "move", rename_to=second[len("rename to ") :].strip(), diff=block
        )
    return Operation("edit", diff=block)


def diff_body(operation: Operation) -> list[str]:
    if operation.diff is None:
        return []
    lines = operation.diff.lines
    skip = {"delete": 1, "create": 1, "move": 2}.get(operation.kind, 0)
    return lines[skip:]


def target_file(context: Context, base: str | None, path: str) -> str | None:
    """Return the path whose body a subsection's line edits address."""
    if is_node(path):
        for candidate in spec_candidates(path):
            if exists_at_base(context, base, candidate):
                return candidate
        return spec_candidates(path)[0]
    return path


def check_diff_lines(
    context: Context,
    sub: Subsection,
    operation: Operation,
    base: str | None,
    read_path: str,
) -> None:
    """Judge each line of a line-edit or move diff against its Base file."""
    lines = diff_body(operation)
    file_kind = not (
        is_node(sub.heading) or is_decision(sub.heading) or is_new(sub.heading)
    )
    source = at_base(context, base, target_file(context, base, read_path))
    base_lines = {line.strip() for line in (source or "").splitlines()}
    for index, line in enumerate(lines):
        if not line:
            continue
        mark, text = line[0], line[1:].lstrip(" ") if line[0] in "+-" else line.strip()
        if mark not in "+- ":
            context.add(
                Rule.DIFF_LINES,
                sub.heading,
                f"line {line!r} opens with no `+`, `-`, or space",
            )
            continue
        if mark == "+":
            if TAG_RE.search(text):
                context.add(Rule.NO_TAG, sub.heading, f"`+` line adds a tag: {text!r}")
            linked = LINKED_SLUG_RE.match(text)
            if linked and not exists_at_base(
                context, base, f"{read_path}/{linked.group('path')}"
            ):
                context.add(
                    Rule.PLAIN_SLUG,
                    sub.heading,
                    f"slug {linked.group('slug')} links {linked.group('path')}, absent at the Base; the slug stands plain",
                )
            if not file_kind:
                check_body_line(context, sub, text)
            if text.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", text):
                following = next(
                    (
                        later[1:].strip()
                        for later in lines[index + 1 :]
                        if later[:1] in "+ "
                    ),
                    "",
                )
                if not re.match(r"^\|[\s:|-]+\|$", following):
                    first_cell = text.strip("|").split("|", 1)[0].strip()
                    if not CASE_RE.match(first_cell):
                        context.add(
                            Rule.TABLE_CASE,
                            sub.heading,
                            f"table row {text!r} holds no case slug alone in its first cell",
                        )
        elif source is not None and text and text not in base_lines:
            rule = Rule.MOVE_READS if operation.kind == "move" else Rule.DIFF_LINES
            label = "a `-` line" if mark == "-" else "a context line"
            context.add(
                rule,
                sub.heading,
                f"{label} reads no line of {read_path} at the Base: {text!r}",
            )


def check_body_line(context: Context, sub: Subsection, text: str) -> None:
    """Judge one `+` line of a Node or Decision Record body."""
    if (
        not text
        or text.startswith(("#", "|", ">"))
        or text.startswith(OPENING_KEYWORDS)
    ):
        return
    if text.startswith("- "):
        if not ROW_SLUG_RE.match(text) and not LINKED_SLUG_RE.match(text):
            context.add(
                Rule.BODY_LINES_ONLY,
                sub.heading,
                f"`+` row names no target by slug: {text!r}",
            )


def assertion_slugs(lines: list[str], marks: str) -> set[str]:
    """Slugs of the rows and Mapping subsections the marked lines declare."""
    slugs: set[str] = set()
    heading: str | None = None
    for line in lines:
        if not line:
            continue
        mark, text = line[0], line[1:].strip()
        group = GROUP_HEADING_RE.match(text)
        if group:
            subject = group.group("subject") or ""
            heading = (
                subject
                if group.group("type").endswith(("Mapping", "Evaluate", "Eval"))
                else None
            )
            if mark in marks and heading:
                slugs.add(heading)
            continue
        if mark not in marks:
            continue
        row = ROW_SLUG_RE.match(text) or LINKED_SLUG_RE.match(text)
        if row:
            slugs.add(row.group("slug"))
        elif heading and text.startswith("|"):
            slugs.add(heading)
    return slugs


def malleability(text: str | None) -> str:
    if text is None:
        return "implementation"
    match = re.search(
        r"^malleability:\s*(\S+)\s*$", text.split("\n---", 1)[0], re.MULTILINE
    )
    return match.group(1) if match else "implementation"


def check_infrastructure(
    context: Context,
    sub: Subsection,
    operation: Operation,
    base: str | None,
    blockers: list[str],
) -> None:
    """Judge the infrastructure lines of a Node subsection."""
    if not is_node(sub.heading) or operation.kind == "delete":
        return
    spec_path = target_file(context, base, sub.heading)
    before = (
        malleability(at_base(context, base, spec_path))
        if not is_new(sub.heading)
        else None
    )
    if operation.replacement is not None:
        after = malleability("\n".join(operation.replacement.lines))
        added = assertion_slugs(
            ["+" + line for line in operation.replacement.lines], "+"
        )
    else:
        source = (
            "\n".join(operation.front_matter.lines) if operation.front_matter else None
        )
        after = (
            malleability(source)
            if source and "malleability" in source
            else (before or "implementation")
        )
        added = assertion_slugs(diff_body(operation), "+")
    lines = [line for line in sub.trailing if line.startswith("Infrastructure:")]
    other = [line for line in sub.trailing if not line.startswith("Infrastructure:")]
    if other:
        context.add(
            Rule.PAYLOADS, sub.heading, f"text follows the payload: {other[0]!r}"
        )
    if after == "spec":
        if lines:
            context.add(
                Rule.SPEC_NODE_NONE,
                sub.heading,
                "an Assertion of a spec-malleable Node carries no infrastructure line",
            )
        return
    named: dict[str, str] = {}
    for line in lines:
        match = INFRA_RE.match(line)
        if not match:
            context.add(
                Rule.INFRASTRUCTURE_FORM,
                sub.heading,
                f"line {line!r} reads no `Infrastructure: <slug> <paths or none>`",
            )
            continue
        named[match.group("slug")] = match.group("paths")
        for path in CODE_PATH_RE.findall(match.group("paths")):
            if not exists_at_base(context, base, path) and not blockers:
                context.add(
                    Rule.INFRASTRUCTURE_EXISTS,
                    sub.heading,
                    f"{path} is absent at the Base and no blocking Change builds it",
                )
    hardening = (
        before is not None
        and after in MALLEABILITY_ORDER
        and before in MALLEABILITY_ORDER
        and MALLEABILITY_ORDER.index(after) > MALLEABILITY_ORDER.index(before)
    )
    required = set(added)
    if hardening:
        source = at_base(context, base, spec_path) or ""
        required |= assertion_slugs(["+" + line for line in source.splitlines()], "+")
        required -= assertion_slugs(diff_body(operation), "-") - added
    for slug in sorted(required - named.keys()):
        rule = (
            Rule.INFRASTRUCTURE_LINE
            if hardening or slug in added
            else Rule.REPLACED_ASSERTION
        )
        context.add(
            rule, sub.heading, f"Assertion {slug} carries no infrastructure line"
        )


def check_front_matter(
    context: Context, sub: Subsection, operation: Operation, base: str | None
) -> None:
    if operation.front_matter is not None:
        for line in operation.front_matter.lines:
            if line.strip() and not re.match(r"^[a-z_]+:\s*\S", line):
                context.add(
                    Rule.FRONT_MATTER_BLOCK,
                    sub.heading,
                    f"the yaml block holds {line!r}; it holds front-matter fields and their values only",
                )
            if line.startswith("id:") and not is_new(sub.heading):
                context.add(
                    Rule.FRONT_MATTER_BLOCK,
                    sub.heading,
                    "line edits never change a Node's id",
                )
    if operation.replacement is not None and not is_new(sub.heading):
        path = operation.rename_to or sub.heading
        stored = (
            at_base(context, base, target_file(context, base, sub.heading))
            if is_node(sub.heading)
            else at_base(context, base, sub.heading)
        )
        if stored is not None and is_node(sub.heading) or is_spec(path):
            old = re.search(r"^id:\s*(\S+)", stored or "", re.MULTILINE)
            new = re.search(
                r"^id:\s*(\S+)", "\n".join(operation.replacement.lines), re.MULTILINE
            )
            if old and (not new or new.group(1) != old.group(1)):
                context.add(
                    Rule.FRONT_MATTER_BLOCK,
                    sub.heading,
                    f"the replacement changes the id {old.group(1)}; a replaced spec keeps its Node's id",
                )


def check_operation_kind(
    context: Context,
    sub: Subsection,
    operation: Operation,
    base: str | None,
    tree: bool,
) -> None:
    path = sub.heading
    if not tree:
        return
    if operation.kind == "create":
        if not (is_contract(path) or is_outcome(path) or is_product_spec(path)):
            context.add(
                Rule.OPERATION_KINDS,
                path,
                "`new file` creates only a contract file, an Outcome record, or the Product spec",
            )
        if exists_at_base(context, base, path):
            context.add(
                Rule.SUBSECTION_HEADINGS,
                path,
                "`new file` names a path present at the Base",
            )
        return
    if operation.kind in ("delete", "move") and not (
        is_node(path)
        or is_decision(path)
        or is_spec(path)
        or is_contract(path)
        or is_outcome(path)
        or is_product_spec(path)
    ):
        context.add(
            Rule.OPERATION_KINDS,
            path,
            f"a {operation.kind} acts on a Node, a Decision Record, a spec, a contract file, an Outcome record, or the Product spec",
        )
    if operation.kind == "replace" and not (
        is_new(path)
        or is_decision(path)
        or is_spec(path)
        or is_contract(path)
        or is_outcome(path)
        or is_product_spec(path)
        or is_node(path)
    ):
        context.add(
            Rule.OPERATION_KINDS,
            path,
            "a replacement acts on a Decision Record, a spec, a contract file, an Outcome record, or the Product spec",
        )
    if operation.kind == "delete" and (is_product_spec(path) or is_spec(path)):
        context.add(
            Rule.SPEC_DELETION,
            path,
            "a Change deletes a spec only with its Node, and never deletes the Product spec",
        )
    if not is_node(path) and not is_new(path):
        mode = tree_mode(context, base, path)
        if mode is not None and mode not in ("100644", "100755"):
            context.add(
                Rule.OPERATION_KINDS,
                path,
                f"the file at the Base has mode {mode}; every file an operation names is a regular text file",
            )


def check_new_artifact(
    context: Context,
    sub: Subsection,
    declared_new: set[str],
    siblings: dict[tuple[str, str, str], str],
) -> None:
    path = sub.heading
    segments = path_segments(path)
    last = segments[-1] if segments else ""
    if not last.startswith("NN-"):
        prefix = new_prefix(path)
        if prefix is not None and prefix not in declared_new:
            context.add(
                Rule.NEW_PATH_REFERENCE,
                path,
                f"{prefix} names no new artifact an earlier subsection declares",
            )
        return
    declared_new.add(path)
    preamble = [line for line in sub.preamble if line.strip()]
    if not preamble or not DEPENDS_RE.match(preamble[0]):
        context.add(
            Rule.DEPENDS_ON_FORM,
            path,
            "the line below the heading of a new artifact reads `Depends on:` and code-span paths or `none`",
        )
    if is_decision(path):
        if len(preamble) < 2 or not PRECEDES_RE.match(preamble[1]):
            context.add(
                Rule.PRECEDES_FORM,
                path,
                "the line below `Depends on:` of a new Decision Record reads `Precedes:` and code-span paths or `none`",
            )
    extra = preamble[2:] if is_decision(path) else preamble[1:]
    if extra:
        context.add(
            Rule.PAYLOADS, path, f"text stands before the payload: {extra[0]!r}"
        )
    match = NODE_SEGMENT_RE.match(last) or DECISION_SEGMENT_RE.match(last)
    if match:
        key = ("/".join(segments[:-1]), match.group("slug"), match.group("kind"))
        if key in siblings:
            context.add(
                Rule.NEW_SIBLING_NAMES,
                path,
                f"{siblings[key]} and {path} share a slug and a kind",
            )
        siblings[key] = path


def check_heading(
    context: Context,
    sub: Subsection,
    operation: Operation | None,
    base: str | None,
    tree: bool,
    moved: dict[str, str],
) -> str:
    """Judge the heading's path; return the path its reads address at the Base."""
    path = sub.heading
    if tree and not path.startswith("spx/"):
        context.add(Rule.SUBSECTION_HEADINGS, path, "the heading is a path from spx/")
    if is_new(path) or (operation is not None and operation.kind == "create"):
        return path
    for new, old in moved.items():
        if path == new or path.startswith(new + "/"):
            return old + path[len(new) :]
    present = exists_at_base(context, base, path)
    if not present and base is not None:
        segments = path_segments(path)
        if (
            segments
            and re.match(r"^\d{2}", segments[-1])
            and (is_node(path) or is_decision(path))
        ):
            context.add(
                Rule.NO_INDEX,
                path,
                "the heading names an Index absent at the Base; a new artifact takes NN in place of its Index",
            )
        else:
            context.add(
                Rule.SUBSECTION_HEADINGS,
                path,
                "the heading names a path absent at the Base",
            )
    return path


def check_path_naming(
    context: Context, base: str | None, removed: list[str], headings: set[str]
) -> None:
    """Name each file at the Base that names a deleted or moved path."""
    if base is None:
        return
    for path in removed:
        result = context.git("grep", "-l", "-F", path, base, "--")
        if result.exit_code not in (0, 1):
            raise Unusable(f"`git grep` over the Base failed: {result.stderr.strip()}")
        for line in result.stdout.splitlines():
            named = line.split(":", 1)[1] if ":" in line else line
            if (
                "/knowledge/" in f"/{named}"
                or named == path
                or named.startswith(path + "/")
            ):
                continue
            holds = named.startswith("spx/") and (
                is_spec(named)
                or is_decision(named)
                or is_contract(named)
                or is_outcome(named)
                or is_product_spec(named)
            )
            if holds and not any(
                named == heading or named.startswith(heading + "/")
                for heading in headings
            ):
                context.add(
                    Rule.PATH_NAMING,
                    named,
                    f"names {path}, which the Change deletes or moves, and takes no subsection",
                )
            elif not holds:
                context.informational.append({"file": named, "names": path})


def check_declarations(
    context: Context, lines: list[str], base: str | None, blockers: list[str]
) -> list[tuple[str, Operation]]:
    """Judge every Declarations subsection; return each heading with its operation."""
    subsections = split_subsections(context, lines)
    if subsections is None:
        return []
    tree = (context.root / "spx").is_dir()
    declared_new: set[str] = set()
    siblings: dict[tuple[str, str, str], str] = {}
    moved: dict[str, str] = {}
    seen: dict[str, str] = {}
    removed: list[str] = []
    operations: list[tuple[str, Operation]] = []
    node_count = 0
    for sub in subsections:
        operation = check_payload(context, sub)
        read_path = check_heading(context, sub, operation, base, tree, moved)
        check_new_artifact(context, sub, declared_new, siblings)
        if not is_new(sub.heading) and sub.preamble:
            context.add(
                Rule.PAYLOADS,
                sub.heading,
                f"text stands before the payload: {sub.preamble[0]!r}",
            )
        in_moved = any(sub.heading.startswith(new + "/") for new in moved)
        if sub.heading in seen and not in_moved:
            context.add(
                Rule.ONE_SUBSECTION_PER_FILE,
                sub.heading,
                "two subsections write, move, or delete the same file",
            )
        seen[sub.heading] = sub.heading
        if is_node(sub.heading):
            node_count += 1
        if operation is None:
            continue
        operations.append((sub.heading, operation))
        check_operation_kind(context, sub, operation, base, tree)
        check_front_matter(context, sub, operation, base)
        if operation.kind in ("edit", "move", "create"):
            check_diff_lines(context, sub, operation, base, read_path)
        if operation.kind in ("delete", "move"):
            removed.append(sub.heading)
        if operation.kind == "move" and operation.rename_to:
            moved[operation.rename_to] = sub.heading
            if is_node(sub.heading) and is_node(operation.rename_to):
                old_slug = node_slug(path_segments(sub.heading)[-1])
                new_slug = node_slug(path_segments(operation.rename_to)[-1])
                if old_slug != new_slug:
                    stale = f"{operation.rename_to}/{old_slug}"
                    for later in subsections:
                        if later.heading.startswith(stale):
                            context.add(
                                Rule.SLUG_RENAME,
                                later.heading,
                                f"the move renames the spec and the Outcome record to {new_slug}",
                            )
        check_infrastructure(context, sub, operation, base, blockers)
    if node_count > NODE_BOUND:
        context.informational.append(
            {"nodeSubsections": str(node_count), "bound": str(NODE_BOUND)}
        )
    check_path_naming(context, base, removed, set(seen))
    return operations


def check_store(
    context: Context,
    draft: Draft,
    issue: str | None,
    read_edited_at: str | None,
    published: pathlib.Path | None,
    base: str | None,
    operations: list[tuple[str, Operation]],
) -> None:
    """Judge the publish against the Change Store and the published record."""
    if len(draft.body) > GITHUB_BODY_LIMIT:
        context.add(
            Rule.SIZE_LIMIT,
            "body",
            f"the body holds {len(draft.body)} characters; the limit of a GitHub Change Store is {GITHUB_BODY_LIMIT} characters of issue body",
        )
    if issue is not None:
        owner_repo, _, number = issue.partition("#")
        owner, _, repo = owner_repo.partition("/")
        query = "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){createdAt lastEditedAt}}}"
        result = context.runner(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={query}",
                "-f",
                f"o={owner}",
                "-f",
                f"r={repo}",
                "-F",
                f"n={number}",
            ],
            cwd=context.root,
        )
        if result.exit_code != 0:
            raise Unusable(
                f"the edit stamp of {issue} could not be read: {result.stderr.strip()}"
            )
        try:
            node = json.loads(result.stdout)["data"]["repository"]["issue"]
        except (ValueError, KeyError, TypeError) as exc:
            raise Unusable(f"the store answered no issue for {issue}") from exc
        stamp = node.get("lastEditedAt") or node.get("createdAt")
        if stamp != read_edited_at:
            context.add(
                Rule.STALE_REVISION,
                issue,
                f"the stored revision was edited at {stamp}, after the read at {read_edited_at}; read the record again and redo the publish",
            )
    if published is not None and scalar(draft.values.get("maturity", "")) == "Sliced":
        try:
            old = parse_draft(published.read_text(encoding=TEXT_ENCODING))
        except OSError as exc:
            raise Unusable(f"--published {published} cannot be read: {exc}") from exc
        old_base = scalar(old.values.get("base", ""))
        if old_base and old_base != base:
            unresolved = (
                context.git("cat-file", "-e", f"{old_base}^{{commit}}").exit_code != 0
            )
            for heading, operation in operations:
                bound = operation.kind in ("delete", "move", "replace") and (
                    is_decision(heading)
                    or (
                        is_node(heading)
                        and malleability(
                            at_base(context, base, target_file(context, base, heading))
                        )
                        != "spec"
                    )
                )
                if not bound:
                    continue
                if (
                    unresolved
                    or context.git(
                        "diff", "--quiet", old_base, base or "", "--", heading
                    ).exit_code
                    != 0
                ):
                    context.add(
                        Rule.OPERATOR_BOUND_BASE,
                        heading,
                        f"the new base changes {heading}, which the Operator's review binds; the former base {old_base} {'no longer resolves' if unresolved else 'reads it differently'}",
                    )


def check(
    root: pathlib.Path,
    draft_path: pathlib.Path,
    issue: str | None,
    read_edited_at: str | None,
    published: pathlib.Path | None,
    runner: CommandRunner,
) -> tuple[ExitCode, dict[str, object]]:
    """Run every rule over one Draft and return the exit code and result."""
    context = Context(root, runner)
    try:
        text = draft_path.read_text(encoding=TEXT_ENCODING)
    except (OSError, UnicodeDecodeError) as exc:
        raise Unusable(
            f"--draft {draft_path} cannot be read as UTF-8 text: {exc}"
        ) from exc
    draft = parse_draft(text)
    leaf = check_keys(context, draft, recorded=issue is not None)
    base = check_base(context, scalar(draft.values.get("base", ""))) if leaf else None
    declarations = check_body(context, draft, leaf)
    blockers = flow_list(draft.values.get("blockers", "")) or []
    operations = (
        check_declarations(context, declarations, base, blockers)
        if declarations is not None
        else []
    )
    check_store(context, draft, issue, read_edited_at, published, base, operations)
    status = "fail" if context.findings else "pass"
    return (
        ExitCode.FAIL if context.findings else ExitCode.PASS,
        {
            "status": status,
            "findings": [
                {"rule": str(f.rule), "location": f.location, "detail": f.detail}
                for f in context.findings
            ],
            "informational": context.informational,
        },
    )


def main(
    argv: Sequence[str] | None = None, runner: CommandRunner = run_subprocess
) -> int:
    parser = argparse.ArgumentParser(
        description="Check the form of a Change Draft before a publish."
    )
    parser.add_argument(
        "--root", required=True, help="absolute path of the Product's checkout root"
    )
    parser.add_argument("--draft", required=True, help="path of the Change Draft")
    parser.add_argument(
        "--issue", help="owner/repo#N of the stored record a publish replaces"
    )
    parser.add_argument(
        "--read-edited-at",
        help="lastEditedAt, or createdAt, the publisher read with the record",
    )
    parser.add_argument(
        "--published", help="path of a Draft composed from the stored Sliced record"
    )
    arguments = parser.parse_args(argv)
    try:
        root = pathlib.Path(arguments.root)
        if not root.is_absolute() or not root.is_dir():
            raise Unusable(
                f"--root {arguments.root} is no absolute directory; pass the Product's checkout root"
            )
        if (arguments.issue is None) != (arguments.read_edited_at is None):
            raise Unusable(
                "--issue and --read-edited-at go together; pass both for a publish that replaces a stored record"
            )
        if arguments.issue is not None and not REF_RE.match(arguments.issue):
            raise Unusable(f"--issue {arguments.issue} is no owner/repo#N reference")
        code, result = check(
            root,
            pathlib.Path(arguments.draft),
            arguments.issue,
            arguments.read_edited_at,
            pathlib.Path(arguments.published) if arguments.published else None,
            runner,
        )
    except Unusable as exc:
        print(json.dumps({"status": "unusable", "detail": str(exc)}))
        return ExitCode.UNUSABLE
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
