"""Make one Transition of a Change in the record form: operate-change.

Reads one JSON request on stdin and writes one JSON result on stdout. The
request names the Transition, the Change by its store and number, the mover,
the session's identity, and the values the Transition needs: a target
Maturity, a reason, a Handoff, a Changeset, the pair the Operator's review
read, the sealed audit result, and the form check's result. The script reads
the Change from the store, refuses a Change whose state the Transition's row
does not admit with no write, and otherwise makes the Transition's writes in
the write order, reading the Change back after each write. A failed write or a
differing readback stops the Transition: no later write runs, no landed write
is undone, and the result names the writes that landed, the one that failed,
and the observed state.

The module exposes `transition`, which returns for a request the result
`main` writes for it, so a sibling Change skill's script reaches it through a
`__file__`-relative import.

The store is reached only through the `Store` protocol; `GitHubStore` binds a
GitHub repository through an injected command runner whose default owns the
`gh` and `git` subprocesses. The script deletes nothing.

Portability: stdlib only; supports Python 3.13 and later.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any, Final, Protocol, TextIO

EXIT_DONE: Final = 0
EXIT_REFUSED: Final = 1
EXIT_INVALID_REQUEST: Final = 2
EXIT_FAILED: Final = 3

ISSUE_PAGE_SIZE: Final = 100
ISSUE_MAX_PAGES: Final = 10
EDIT_PAGE_SIZE: Final = 100
EVENT_PAGE_SIZE: Final = 100
EVENT_MAX_PAGES: Final = 10
COMMENT_PAGE_SIZE: Final = 100
FIELD_VALUE_LIMIT: Final = 50
ASSIGNEE_LIMIT: Final = 10
DEPENDENCY_PAGE_SIZE: Final = 100
NODE_SUBSECTION_LIMIT: Final = 5


class Transition(StrEnum):
    CLAIM = "claim"
    RELEASE = "release"
    SUBMIT = "submit"
    ADVANCE = "advance"
    LOWER = "lower"
    APPLIED = "applied"
    ABANDONED = "abandoned"


class Maturity(StrEnum):
    PROPOSED = "Proposed"
    FRAMED = "Framed"
    SLICED = "Sliced"
    APPLICABLE = "Applicable"


MATURITY_ORDER: Final = (
    Maturity.PROPOSED,
    Maturity.FRAMED,
    Maturity.SLICED,
    Maturity.APPLICABLE,
)


class Lifecycle(StrEnum):
    AVAILABLE = "Available"
    SUBMITTED = "Submitted"
    APPLIED = "Applied"
    ABANDONED = "Abandoned"


TERMINAL: Final = frozenset({Lifecycle.APPLIED, Lifecycle.ABANDONED})


class Mover(StrEnum):
    """Who makes the move: the Operator, the Change's holder, or another agent."""

    OPERATOR = "operator"
    HOLDER = "holder"
    AGENT = "agent"


class LowerCause(StrEnum):
    """Why a lower runs, which decides who may make it and what follows it."""

    REOPENED = "reopened"
    DECISION_LINE = "decision-line"
    APPLICATION_CHECK = "application-check"
    REFRAME = "reframe"
    APPLICABLE_PUBLISH = "applicable-publish"
    BLOCKER_ABANDONED = "blocker-abandoned"


class Status(StrEnum):
    DONE = "done"
    REFUSED = "refused"
    FAILED = "failed"
    INVALID_REQUEST = "invalid-request"


class RequestKey(StrEnum):
    """The keys of a request."""

    TRANSITION = "transition"
    STORE = "store"
    NUMBER = "number"
    MOVER = "mover"
    IDENTITY = "identity"
    TARGET = "target"
    REASON = "reason"
    REOPENED = "reopened"
    LOWER_CAUSE = "lower_cause"
    HANDOFF = "handoff"
    CHANGESET = "changeset"
    REVIEW = "review"
    REVIEW_BODY = "review_body"
    AUDIT = "audit"
    AUDIT_STATUS = "audit_status"
    FORM_CHECK = "form_check"
    INFRASTRUCTURE = "infrastructure"
    CLOSE_CHECK = "close_check"
    MERGED_INTO = "merged_into"
    APPLICATION = "application"
    CHECKOUT_ROOT = "checkout_root"


class ResultKey(StrEnum):
    """The keys of a result."""

    STATUS = "status"
    TRANSITION = "transition"
    REASON = "reason"
    DETAIL = "detail"
    WRITES = "writes"
    FAILED_WRITE = "failed_write"
    OBSERVED = "observed"
    RELEASE = "release"
    COMMENT_URL = "comment_url"
    DEPENDENTS = "dependents"


class ObservedKey(StrEnum):
    """The keys of the Change state a result observes."""

    STATE = "state"
    MATURITY = "maturity"
    LIFECYCLE = "lifecycle"
    ASSIGNEES = "assignees"
    BODY_SHA256 = "body_sha256"
    BASE = "base"


class FormCheckKey(StrEnum):
    STATUS = "status"
    BODY_SHA256 = "body_sha256"


class FormStatus(StrEnum):
    """The status a form check reports for the current record."""

    PASS = "pass"
    FAIL = "fail"


class AuditStatus(StrEnum):
    """The status a sealed audit result, or the audit at close, reports."""

    APPROVED = "approved"
    REJECTED = "rejected"


class CloseCheckKey(StrEnum):
    MERGE_GATES_PASSED = "merge_gates_passed"
    RESULTS_COMPLETE = "results_complete"
    DECLARATIONS_ON_DEFAULT = "declarations_on_default"
    AUDIT_AT_CLOSE = "audit_at_close"


class InfrastructureState(StrEnum):
    """The state an infrastructure path holds when it needs no blocker."""

    PASSING = "Passing"


class WriteKind(StrEnum):
    """The writes a Transition makes, in the write order."""

    MATURITY = "maturity"
    LIFECYCLE = "lifecycle"
    ASSIGNEE = "assignee"
    COMMENT = "comment"
    STATE = "state"


WRITE_ORDER: Final = (
    WriteKind.MATURITY,
    WriteKind.LIFECYCLE,
    WriteKind.ASSIGNEE,
    WriteKind.COMMENT,
    WriteKind.STATE,
)


class IssueState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Field(StrEnum):
    """The organization issue fields a Transition reads or writes."""

    MATURITY = "Maturity"
    LIFECYCLE = "Lifecycle"
    PARENT = "Parent"
    BASE = "Base"
    PREDECESSORS = "Predecessors"


class LogKey(StrEnum):
    """The keys a Transition block may hold."""

    TRANSITION = "transition"
    MATURITY = "maturity"
    HARNESS = "harness"
    SESSION = "session"
    MACHINE = "machine"
    WORKTREE = "worktree"
    REASON = "reason"
    HANDOFF = "handoff"
    CHANGESET = "changeset"


LOG_KEYS: Final = (
    LogKey.TRANSITION,
    LogKey.MATURITY,
    LogKey.HARNESS,
    LogKey.SESSION,
    LogKey.MACHINE,
    LogKey.WORKTREE,
)
LOG_EXTRAS: Final = frozenset({LogKey.REASON, LogKey.HANDOFF, LogKey.CHANGESET})


class HandoffKey(StrEnum):
    BRANCH = "branch"
    HEAD = "head"
    NEXT = "next"
    PULL_REQUEST = "pull_request"


HANDOFF_REQUIRED: Final = (HandoffKey.BRANCH, HandoffKey.HEAD, HandoffKey.NEXT)


class ChangesetKey(StrEnum):
    URL = "url"
    MERGE_COMMIT = "merge_commit"


class Reason(StrEnum):
    """Why a Transition was refused or stopped; the result names one."""

    TERMINAL = "terminal"
    STATE = "state"
    MOVER = "mover"
    HOLDER = "holder"
    REASON_REQUIRED = "reason-required"
    HANDOFF_REQUIRED = "handoff-required"
    MATURITY_READY = "maturity-ready"
    FORM_CHECK = "form-check"
    REVIEW_BINDING = "review-binding"
    AUDIT_BINDING = "audit-binding"
    INFRASTRUCTURE = "infrastructure"
    PARENT = "parent"
    BLOCKER_CYCLE = "blocker-cycle"
    OPEN_CHILD = "open-child"
    CLOSE_CONDITION = "close-condition"
    WRITE_FAILED = "write-failed"
    READBACK = "readback"
    READ_FAILED = "read-failed"
    BOUND = "bound"
    BINDING_RACED = "binding-raced"


class InvalidRequest(Exception):
    pass


class StoreError(Exception):
    """A store read or write failed, returned unreadable output, or filled a bound."""

    def __init__(self, detail: str, *, bound: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.bound = bound


class Refusal(Exception):
    def __init__(self, reason: Reason, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


# ---------------------------------------------------------------- the Change


@dataclass(frozen=True)
class Revision:
    """One body revision the issue's edit history holds."""

    id: str
    edited_at: str
    body: str


@dataclass(frozen=True)
class FieldEvent:
    """One change event of a text or single-select issue field."""

    created_at: str
    field: str
    new_value: str | None


@dataclass(frozen=True)
class Comment:
    created_at: str
    author: str
    body: str
    url: str = ""


@dataclass(frozen=True)
class Change:
    """A Change as its store holds it."""

    number: int
    node_id: str
    state: IssueState
    title: str
    body: str
    maturity: str | None
    lifecycle: str | None
    assignees: tuple[str, ...]
    base: str | None
    parent: int | None
    children: tuple[tuple[int, IssueState], ...] = ()
    blockers: tuple[int, ...] = ()
    revisions: tuple[Revision, ...] = ()
    field_events: tuple[FieldEvent, ...] = ()
    comments: tuple[Comment, ...] = ()

    @property
    def is_parent(self) -> bool:
        return bool(self.children)

    @property
    def body_sha256(self) -> str:
        return sha256(self.body)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------- request


@dataclass(frozen=True)
class Identity:
    login: str
    harness: str
    session: str
    machine: str
    worktree: str


@dataclass(frozen=True)
class BoundPair:
    """A body revision and a Base, as a review or an audit read them."""

    body_sha256: str
    base: str


@dataclass(frozen=True)
class CloseCheck:
    """The close condition of a Leaf, as the holder established it."""

    merge_gates_passed: bool
    results_complete: bool
    declarations_on_default: bool
    audit_at_close: str


@dataclass(frozen=True)
class Request:
    transition: Transition
    store: str
    number: int
    mover: Mover
    identity: Identity
    target: Maturity | None = None
    reason: str | None = None
    reopened: str | None = None
    lower_cause: LowerCause | None = None
    handoff: Mapping[str, str] | None = None
    changeset: Mapping[str, str] | None = None
    review: BoundPair | None = None
    review_body: str | None = None
    audit: BoundPair | None = None
    audit_status: str | None = None
    form_check: Mapping[str, Any] | None = None
    infrastructure: Mapping[str, Any] = field(default_factory=dict)
    close_check: CloseCheck | None = None
    merged_into: int | None = None
    application: bool = False


def _text(raw: Mapping[str, Any], name: str, *, optional: bool = False) -> str | None:
    value = raw.get(name)
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise InvalidRequest(
            f"{name} must be a non-empty string; add a non-blank {name} to the request"
        )
    return value


def _choice[E: StrEnum](kind: type[E], name: str, value: object) -> E:
    try:
        return kind(str(value))
    except ValueError:
        options = ", ".join(member.value for member in kind)
        raise InvalidRequest(
            f"{name} must be one of {options}; the request names {value!r}"
        ) from None


def _object(raw: Mapping[str, Any], name: str, shape: str) -> Mapping[str, Any] | None:
    value = raw.get(name)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise InvalidRequest(f"{name} must be an object {shape}")
    return value


def _pair(raw: Any, name: str) -> BoundPair | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise InvalidRequest(
            f"{name} must be an object of body_sha256 and base, both non-empty strings"
        )
    return BoundPair(
        str(_text(raw, ObservedKey.BODY_SHA256)),
        str(_text(raw, ObservedKey.BASE)),
    )


def read_request(raw: object) -> Request:
    if not isinstance(raw, Mapping):
        raise InvalidRequest(
            "the request must be a JSON object holding transition, store, number, "
            "mover, and identity"
        )
    kind = _choice(Transition, RequestKey.TRANSITION, raw.get(RequestKey.TRANSITION))
    mover = _choice(Mover, RequestKey.MOVER, raw.get(RequestKey.MOVER))
    store = str(_text(raw, RequestKey.STORE))
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", store):
        raise InvalidRequest(
            f"store must read owner/repo, as in outcomeeng/changes; got {store!r}"
        )
    number = raw.get(RequestKey.NUMBER)
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise InvalidRequest(
            "number must be a positive integer, the issue number of the Change"
        )
    who = raw.get(RequestKey.IDENTITY)
    keys = ", ".join(Identity.__dataclass_fields__)
    if not isinstance(who, Mapping):
        raise InvalidRequest(
            f"identity must be an object of {keys}, each a non-empty string"
        )
    identity = Identity(
        *(str(_text(who, key)) for key in Identity.__dataclass_fields__)
    )
    target = raw.get(RequestKey.TARGET)
    cause = raw.get(RequestKey.LOWER_CAUSE)
    close = _object(
        raw,
        RequestKey.CLOSE_CHECK,
        "of " + ", ".join(CloseCheckKey),
    )
    handoff = _object(raw, RequestKey.HANDOFF, "of " + ", ".join(HandoffKey))
    changeset = _object(raw, RequestKey.CHANGESET, "of " + ", ".join(ChangesetKey))
    form_check = _object(raw, RequestKey.FORM_CHECK, "of " + ", ".join(FormCheckKey))
    infrastructure = _object(
        raw,
        RequestKey.INFRASTRUCTURE,
        "mapping each path to Passing or {blocker: number}",
    )
    request = Request(
        transition=kind,
        store=store,
        number=number,
        mover=mover,
        identity=identity,
        target=None if target is None else _choice(Maturity, RequestKey.TARGET, target),
        reason=_text(raw, RequestKey.REASON, optional=True),
        reopened=_text(raw, RequestKey.REOPENED, optional=True),
        lower_cause=None
        if cause is None
        else _choice(LowerCause, RequestKey.LOWER_CAUSE, cause),
        handoff=handoff,
        changeset=changeset,
        review=_pair(raw.get(RequestKey.REVIEW), RequestKey.REVIEW),
        review_body=raw.get(RequestKey.REVIEW_BODY),
        audit=_pair(raw.get(RequestKey.AUDIT), RequestKey.AUDIT),
        audit_status=_text(raw, RequestKey.AUDIT_STATUS, optional=True),
        form_check=form_check,
        infrastructure=infrastructure or {},
        close_check=None
        if close is None
        else CloseCheck(
            bool(close.get(CloseCheckKey.MERGE_GATES_PASSED)),
            bool(close.get(CloseCheckKey.RESULTS_COMPLETE)),
            bool(close.get(CloseCheckKey.DECLARATIONS_ON_DEFAULT)),
            str(close.get(CloseCheckKey.AUDIT_AT_CLOSE, "")),
        ),
        merged_into=raw.get(RequestKey.MERGED_INTO),
        application=bool(raw.get(RequestKey.APPLICATION, False)),
    )
    return request


# --------------------------------------------------------------- the record


SECTION_HEADING: Final = re.compile(r"^## (.+?)\s*$")
SUBSECTION_HEADING: Final = re.compile(r"^### (.+?)\s*$")
NODE_SUFFIX: Final = re.compile(
    r"\.(enabler|outcome|substrate|capability|domain|interface|surface|variant)(/|$)"
)
NEW_NODE: Final = re.compile(r"^new (\w+) `([^`]+)`, between `([^`]+)` and `([^`]+)`$")
INFRASTRUCTURE_LINE: Final = re.compile(r"^Infrastructure: (\S+) (.+)$")
CODE_SPAN: Final = re.compile(r"`([^`]+)`")
DECISION_RECORD: Final = re.compile(r"\.(adr|pdr)\.md$")


def sections(body: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in body.split("\n"):
        heading = SECTION_HEADING.match(line)
        if heading:
            current = found.setdefault(heading.group(1), [])
            continue
        if current is not None:
            current.append(line)
    return found


def subsections(body: str) -> list[tuple[str, list[str]]]:
    """Each Declarations subsection, by its heading, with its lines."""
    found: list[tuple[str, list[str]]] = []
    for line in sections(body).get("Declarations", []):
        heading = SUBSECTION_HEADING.match(line)
        if heading:
            found.append((heading.group(1).strip("`"), []))
        elif found:
            found[-1][1].append(line)
    return found


def is_node_subsection(heading: str) -> bool:
    return bool(NEW_NODE.match(heading)) or bool(NODE_SUFFIX.search(heading))


def node_subsection_count(body: str) -> int:
    return sum(1 for heading, _ in subsections(body) if is_node_subsection(heading))


def infrastructure_paths(body: str) -> list[str]:
    paths: list[str] = []
    for _, lines in subsections(body):
        for line in lines:
            match = INFRASTRUCTURE_LINE.match(line.strip())
            if match and match.group(2).strip() != "none":
                paths.extend(CODE_SPAN.findall(match.group(2)))
    return paths


# ------------------------------------------------------------- review carry


class TreeReader(Protocol):
    """Reads a Product's tree at a commit; `None` when the path or commit is absent."""

    def resolves(self, commit: str) -> bool: ...

    def read(self, commit: str, path: str) -> str | None: ...

    def list_dir(self, commit: str, path: str) -> tuple[str, ...] | None: ...


def governing_records(
    reader: TreeReader, commit: str, path: str
) -> dict[str, str] | None:
    """Each Decision Record in the directories from spx/ down to `path`, with its text."""
    parts = PurePosixPath(path).parts
    records: dict[str, str] = {}
    for depth in range(1, len(parts) + 1):
        directory = "/".join(parts[:depth])
        entries = reader.list_dir(commit, directory)
        if entries is None:
            continue
        for entry in entries:
            if DECISION_RECORD.search(entry):
                record_path = f"{directory}/{entry}"
                text = reader.read(commit, record_path)
                if text is None:
                    return None
                records[record_path] = text
    return records


def subsection_target(heading: str) -> str | None:
    """The existing path a subsection's heading names, or None for a new Node."""
    if NEW_NODE.match(heading):
        return None
    return heading


TABLE_ROW: Final = re.compile(r"^[+\- ]?\s*\|")
LIST_ITEM: Final = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
INNER_HEADING: Final = re.compile(r"^(#+)\s")

Part = tuple[str, tuple[str, ...]]


def parts(heading: str, lines: list[str]) -> list[Part]:
    """Each row, heading, or other single line of a subsection with its context.

    The context is every heading above the part, the header row of its table,
    and the line that opens its Scenario or list.
    """
    found: list[Part] = []
    headings: list[tuple[int, str]] = []
    header = ""
    opener = ""
    previous_row = False
    for line in lines:
        if not line.strip():
            previous_row = False
            continue
        level = INNER_HEADING.match(line)
        if level:
            headings = [h for h in headings if h[0] < len(level.group(1))]
            above = tuple(text for _, text in headings)
            headings.append((len(level.group(1)), line.strip()))
            found.append((line.strip(), (heading, *above)))
            header = ""
            opener = ""
            previous_row = False
            continue
        context = [heading, *(text for _, text in headings)]
        if TABLE_ROW.match(line):
            if not previous_row:
                header = line.strip()
            previous_row = True
            context.append(header)
        else:
            previous_row = False
            header = ""
        if LIST_ITEM.match(line) or line[:1].isspace():
            if opener:
                context.append(opener)
        elif not TABLE_ROW.match(line):
            opener = line.strip()
        found.append((line.strip(), tuple(context)))
    return found


def review_carries(
    reviewed_body: str,
    reviewed_base: str,
    current_body: str,
    current_base: str,
    reader: TreeReader,
) -> tuple[bool, list[str]]:
    """Whether the review of every part carries forward, and the parts that do not."""
    if not reader.resolves(reviewed_base) or not reader.resolves(current_base):
        return False, ["base"]
    reviewed = {
        part
        for heading, lines in subsections(reviewed_body)
        for part in parts(heading, lines)
    }
    lost: list[str] = []
    for heading, lines in subsections(current_body):
        for line, context in parts(heading, lines):
            if (line, context) not in reviewed:
                lost.append(f"{heading}: {line}")
        target = subsection_target(heading)
        if target is None:
            continue
        if reader.read(reviewed_base, target) != reader.read(current_base, target):
            lost.append(heading)
            continue
        if governing_records(reader, reviewed_base, target) != governing_records(
            reader, current_base, target
        ):
            lost.append(heading)
    return not lost, lost


# ------------------------------------------------------------------- writes


@dataclass(frozen=True)
class Write:
    kind: WriteKind
    value: Any


@dataclass(frozen=True)
class Plan:
    transition: Transition
    writes: tuple[Write, ...]
    comment: str
    follow: Request | None = None
    bound: BoundPair | None = None


def render_block(entries: Mapping[str, Any]) -> str:
    """One fenced YAML block holding exactly the closed set of Transition keys."""
    keys = set(entries)
    allowed = set(LOG_KEYS) | LOG_EXTRAS
    if not keys <= allowed or not set(LOG_KEYS) <= keys:
        raise ValueError(f"a Transition block holds only {sorted(allowed)}")
    lines = ["```yaml"]
    for key, value in entries.items():
        if isinstance(value, Mapping):
            lines.append(f"{key}:")
            lines.extend(f"  {inner}: {_scalar(item)}" for inner, item in value.items())
        else:
            lines.append(f"{key}: {_scalar(value)}")
    lines.append("```")
    return "\n".join(lines) + "\n"


def _scalar(value: Any) -> str:
    text = str(value)
    if re.fullmatch(r"[\w./@:+-]+", text) and text[0] not in "-:@":
        return text
    return json.dumps(text, ensure_ascii=False)


def block_entries(
    request: Request, maturity: str, extras: Mapping[LogKey, Any]
) -> dict[str, Any]:
    who = request.identity
    entries: dict[str, Any] = {
        LogKey.TRANSITION: request.transition.value,
        LogKey.MATURITY: maturity,
        LogKey.HARNESS: who.harness,
        LogKey.SESSION: who.session,
        LogKey.MACHINE: who.machine,
        LogKey.WORKTREE: who.worktree,
    }
    for key, value in extras.items():
        entries[key.value] = value
    return entries


def ordered(writes: Sequence[Write]) -> tuple[Write, ...]:
    return tuple(sorted(writes, key=lambda write: WRITE_ORDER.index(write.kind)))


# ------------------------------------------------------------------ planning


def holder_session(change: Change, login: str) -> str | None:
    """The session of the newest claim comment by `login`, or None."""
    for comment in reversed(change.comments):
        if comment.author != login:
            continue
        block = parse_block(comment.body)
        if block and block.get(LogKey.TRANSITION) == Transition.CLAIM:
            return block.get(LogKey.SESSION)
    return None


def parse_block(body: str) -> dict[str, str] | None:
    """The top-level scalar keys of a comment that is one fenced YAML block."""
    text = body.strip()
    if not (text.startswith("```yaml\n") and text.endswith("```")):
        return None
    found: dict[str, str] = {}
    for line in text.split("\n")[1:-1]:
        match = re.match(r"^(\w+): (.*)$", line)
        if match:
            found[match.group(1)] = match.group(2).strip().strip('"')
    return found


def held_by(change: Change, identity: Identity) -> bool:
    return change.assignees == (identity.login,) and (
        holder_session(change, identity.login) == identity.session
    )


def require(condition: bool, reason: Reason, detail: str) -> None:
    if not condition:
        raise Refusal(reason, detail)


def rank(maturity: str | None) -> int:
    for index, value in enumerate(MATURITY_ORDER):
        if value == maturity:
            return index
    return -1


def plan(request: Request, change: Change, context: PlanContext) -> Plan:
    """The ordered writes a Transition makes on `change`, or a Refusal."""
    require(
        change.state == IssueState.OPEN and change.lifecycle not in TERMINAL,
        Reason.TERMINAL,
        f"#{change.number} is {change.lifecycle or change.state}",
    )
    planner = PLANNERS[request.transition]
    return planner(request, change, context)


@dataclass(frozen=True)
class PlanContext:
    """What a plan reads besides the Change: its relations and the Product's tree."""

    cycle: bool = False
    reader: TreeReader | None = None
    ancestor: Callable[[str, str], bool] | None = None


def plan_claim(request: Request, change: Change, context: PlanContext) -> Plan:
    require(
        change.lifecycle == Lifecycle.AVAILABLE,
        Reason.STATE,
        "a claim takes an Available Change",
    )
    require(
        not change.assignees,
        Reason.HOLDER,
        f"#{change.number} is held by {', '.join(change.assignees)}",
    )
    if change.maturity == Maturity.APPLICABLE:
        require(
            not context.cycle,
            Reason.BLOCKER_CYCLE,
            f"#{change.number} stands in a blocker cycle",
        )
        confirm_review(request, change, context)
    comment = render_block(block_entries(request, str(change.maturity), {}))
    return Plan(
        request.transition,
        ordered(
            [
                Write(WriteKind.ASSIGNEE, (request.identity.login,)),
                Write(WriteKind.COMMENT, comment),
            ]
        ),
        comment,
    )


def plan_release(request: Request, change: Change, context: PlanContext) -> Plan:
    require(
        held_by(change, request.identity),
        Reason.HOLDER,
        f"#{change.number} is not held by this session",
    )
    require(request.mover == Mover.HOLDER, Reason.MOVER, "the holder releases")
    handoff = request.handoff
    require(
        isinstance(handoff, Mapping)
        and all(
            isinstance(handoff.get(key), str) and handoff.get(key)
            for key in HANDOFF_REQUIRED
        ),
        Reason.HANDOFF_REQUIRED,
        "a release names the branch, the head commit, and the next subsection",
    )
    assert isinstance(handoff, Mapping)
    entries = {key.value: handoff[key] for key in HandoffKey if handoff.get(key)}
    writes = [Write(WriteKind.ASSIGNEE, ())]
    if change.lifecycle == Lifecycle.SUBMITTED:
        writes.append(Write(WriteKind.LIFECYCLE, Lifecycle.AVAILABLE))
    comment = render_block(
        block_entries(request, str(change.maturity), {LogKey.HANDOFF: entries})
    )
    writes.append(Write(WriteKind.COMMENT, comment))
    return Plan(request.transition, ordered(writes), comment)


def plan_submit(request: Request, change: Change, context: PlanContext) -> Plan:
    require(
        change.lifecycle == Lifecycle.AVAILABLE,
        Reason.STATE,
        "a submit takes an Available Change",
    )
    require(held_by(change, request.identity), Reason.HOLDER, "the holder submits")
    extras = {LogKey.REASON: request.reopened} if request.reopened else {}
    comment = render_block(block_entries(request, str(change.maturity), extras))
    return Plan(
        request.transition,
        ordered(
            [
                Write(WriteKind.LIFECYCLE, Lifecycle.SUBMITTED),
                Write(WriteKind.COMMENT, comment),
            ]
        ),
        comment,
    )


def plan_advance(request: Request, change: Change, context: PlanContext) -> Plan:
    current = rank(change.maturity)
    require(current >= 0, Reason.STATE, f"#{change.number} holds no Maturity")
    require(
        current + 1 < len(MATURITY_ORDER),
        Reason.STATE,
        "an Applicable Change advances no further",
    )
    target = MATURITY_ORDER[current + 1]
    require(
        request.target in (None, target),
        Reason.STATE,
        f"an advance from {change.maturity} reaches {target}",
    )
    if change.is_parent:
        require(
            target != Maturity.APPLICABLE,
            Reason.PARENT,
            "a Parent never reaches Applicable",
        )
    bound: BoundPair | None = None
    if target == Maturity.APPLICABLE:
        require(
            change.lifecycle == Lifecycle.AVAILABLE,
            Reason.STATE,
            "a Sliced Leaf advances to Applicable",
        )
        require(
            request.mover == Mover.HOLDER and held_by(change, request.identity),
            Reason.MOVER,
            "the holder advances to Applicable",
        )
        require(
            not context.cycle,
            Reason.BLOCKER_CYCLE,
            f"#{change.number} stands in a blocker cycle",
        )
        bound = confirm_audit(request, change)
        confirm_infrastructure(request, change)
    else:
        require(
            change.lifecycle == Lifecycle.SUBMITTED,
            Reason.STATE,
            f"an advance to {target} takes a Submitted Change",
        )
        require(
            request.mover == Mover.OPERATOR,
            Reason.MOVER,
            f"only the Operator advances to {target}",
        )
        if target == Maturity.SLICED:
            require(
                not context.cycle,
                Reason.BLOCKER_CYCLE,
                f"#{change.number} stands in a blocker cycle",
            )
            if not change.is_parent:
                require(
                    node_subsection_count(change.body) <= NODE_SUBSECTION_LIMIT,
                    Reason.MATURITY_READY,
                    f"a Sliced Leaf holds at most {NODE_SUBSECTION_LIMIT} Node subsections",
                )
            bound = confirm_review(request, change, context)
        if target == Maturity.FRAMED and not change.is_parent:
            declared = [
                line
                for line in sections(change.body).get("Declarations", [])
                if line.strip()
            ]
            require(
                bool(declared),
                Reason.MATURITY_READY,
                "a Framed Leaf holds its Declarations, or none and its reason",
            )
    confirm_form_check(request, change)
    comment = render_block(block_entries(request, target.value, {}))
    return Plan(
        request.transition,
        ordered([Write(WriteKind.MATURITY, target), Write(WriteKind.COMMENT, comment)]),
        comment,
        bound=bound,
    )


def confirm_form_check(request: Request, change: Change) -> None:
    result = request.form_check
    require(
        isinstance(result, Mapping)
        and result.get(FormCheckKey.STATUS) == FormStatus.PASS,
        Reason.FORM_CHECK,
        "the form check's result for the current record is pass",
    )
    assert isinstance(result, Mapping)
    require(
        result.get(FormCheckKey.BODY_SHA256) == change.body_sha256,
        Reason.FORM_CHECK,
        "the form check judged another body revision",
    )


def confirm_review(request: Request, change: Change, context: PlanContext) -> BoundPair:
    review = request.review
    require(
        review is not None,
        Reason.REVIEW_BINDING,
        "the pair the Operator's review read is required",
    )
    assert review is not None
    current = BoundPair(change.body_sha256, change.base or "")
    if review == current:
        return current
    require(
        request.review_body is not None
        and sha256(request.review_body) == review.body_sha256,
        Reason.REVIEW_BINDING,
        "the reviewed body differs from the current body and its text is absent",
    )
    require(
        context.reader is not None,
        Reason.REVIEW_BINDING,
        "no tree reader for the carry-forward",
    )
    assert context.reader is not None and request.review_body is not None
    carries, lost = review_carries(
        request.review_body, review.base, change.body, current.base, context.reader
    )
    require(
        carries,
        Reason.REVIEW_BINDING,
        f"the review carries no part forward for: {', '.join(lost)}",
    )
    return current


def confirm_audit(request: Request, change: Change) -> BoundPair:
    audit = request.audit
    current = BoundPair(change.body_sha256, change.base or "")
    require(
        audit is not None and request.audit_status == AuditStatus.APPROVED,
        Reason.AUDIT_BINDING,
        "a sealed audit result that approved is required",
    )
    require(
        audit == current,
        Reason.AUDIT_BINDING,
        "the sealed audit result judged another body revision or Base",
    )
    return current


def confirm_infrastructure(request: Request, change: Change) -> None:
    for path in infrastructure_paths(change.body):
        state = request.infrastructure.get(path)
        passing = state == InfrastructureState.PASSING
        blocked = isinstance(state, Mapping) and state.get("blocker") in change.blockers
        require(
            passing or blocked,
            Reason.INFRASTRUCTURE,
            f"{path} is neither Passing on the default branch nor built by a blocker",
        )


def plan_lower(request: Request, change: Change, context: PlanContext) -> Plan:
    current = rank(change.maturity)
    require(
        current >= 1,
        Reason.STATE,
        "a lower takes a Framed, Sliced, or Applicable Change",
    )
    target = request.target
    require(
        target is not None and rank(target) < current,
        Reason.STATE,
        "a lower names a lower Maturity",
    )
    assert target is not None
    require(bool(request.reason), Reason.REASON_REQUIRED, "a lower names its reason")
    cause = request.lower_cause
    require(cause is not None, Reason.STATE, "a lower names its cause")
    assert cause is not None
    allowed = {
        LowerCause.REOPENED: request.mover == Mover.OPERATOR,
        LowerCause.DECISION_LINE: request.mover == Mover.HOLDER
        and held_by(change, request.identity)
        and change.maturity == Maturity.APPLICABLE
        and target == Maturity.SLICED,
        LowerCause.APPLICATION_CHECK: target == Maturity.SLICED,
        LowerCause.REFRAME: target == Maturity.PROPOSED,
        LowerCause.APPLICABLE_PUBLISH: change.maturity == Maturity.APPLICABLE
        and target == Maturity.SLICED,
        LowerCause.BLOCKER_ABANDONED: change.maturity == Maturity.APPLICABLE
        and target == Maturity.SLICED,
    }
    require(
        allowed[cause],
        Reason.MOVER,
        f"a {cause} lower does not take {change.maturity} to {target} for {request.mover}",
    )
    follow: Request | None = None
    keeps_holder = cause in (LowerCause.DECISION_LINE, LowerCause.BLOCKER_ABANDONED)
    if not keeps_holder and change.assignees:
        require(
            held_by(change, request.identity),
            Reason.HOLDER,
            "a lower that releases is made by the holder",
        )
        require(
            request.handoff is not None,
            Reason.HANDOFF_REQUIRED,
            "after this lower the holder writes a Handoff and releases",
        )
        follow = replace(request, transition=Transition.RELEASE, mover=Mover.HOLDER)
    comment = render_block(
        block_entries(request, target.value, {LogKey.REASON: request.reason})
    )
    return Plan(
        request.transition,
        ordered([Write(WriteKind.MATURITY, target), Write(WriteKind.COMMENT, comment)]),
        comment,
        follow=follow,
    )


def plan_applied(request: Request, change: Change, context: PlanContext) -> Plan:
    extras: dict[LogKey, Any] = {}
    if change.is_parent:
        require(
            request.mover == Mover.OPERATOR,
            Reason.MOVER,
            "only the Operator closes a Parent Applied",
        )
        open_children = [
            number for number, state in change.children if state == IssueState.OPEN
        ]
        require(not open_children, Reason.OPEN_CHILD, f"open Children: {open_children}")
    else:
        require(
            request.mover == Mover.HOLDER and held_by(change, request.identity),
            Reason.MOVER,
            "the holder closes a Leaf Applied",
        )
        changeset = request.changeset
        check = request.close_check
        require(
            isinstance(changeset, Mapping)
            and bool(changeset.get(ChangesetKey.URL))
            and bool(changeset.get(ChangesetKey.MERGE_COMMIT)),
            Reason.CLOSE_CONDITION,
            "an applied Leaf names its Changeset and merge commit",
        )
        assert isinstance(changeset, Mapping)
        require(
            context.ancestor is not None, Reason.CLOSE_CONDITION, "no ancestry reader"
        )
        assert context.ancestor is not None
        require(
            context.ancestor(
                changeset[ChangesetKey.URL], changeset[ChangesetKey.MERGE_COMMIT]
            ),
            Reason.CLOSE_CONDITION,
            "the merge commit is no ancestor of the default branch",
        )
        require(
            check is not None
            and check.merge_gates_passed
            and check.results_complete
            and check.declarations_on_default
            and check.audit_at_close == AuditStatus.APPROVED,
            Reason.CLOSE_CONDITION,
            "every merge gate passed, every result stands, every line stands, and the audit at close found nothing",
        )
        extras[LogKey.CHANGESET] = {
            ChangesetKey.URL.value: changeset[ChangesetKey.URL],
            ChangesetKey.MERGE_COMMIT.value: changeset[ChangesetKey.MERGE_COMMIT],
        }
    comment = render_block(block_entries(request, str(change.maturity), extras))
    return Plan(
        request.transition,
        ordered(
            [
                Write(WriteKind.LIFECYCLE, Lifecycle.APPLIED),
                Write(WriteKind.COMMENT, comment),
                Write(WriteKind.STATE, IssueState.CLOSED),
            ]
        ),
        comment,
    )


def plan_abandoned(request: Request, change: Change, context: PlanContext) -> Plan:
    require(
        request.mover == Mover.OPERATOR
        or (request.merged_into is not None and request.mover == Mover.AGENT),
        Reason.MOVER,
        "only the Operator closes a Change Abandoned, apart from the Change a directed merge absorbs",
    )
    comment = render_block(block_entries(request, str(change.maturity), {}))
    writes = [
        Write(WriteKind.LIFECYCLE, Lifecycle.ABANDONED),
        Write(WriteKind.COMMENT, comment),
        Write(WriteKind.STATE, IssueState.CLOSED),
    ]
    if change.assignees:
        writes.append(Write(WriteKind.ASSIGNEE, ()))
    return Plan(request.transition, ordered(writes), comment)


PLANNERS: Final[Mapping[Transition, Callable[[Request, Change, PlanContext], Plan]]] = {
    Transition.CLAIM: plan_claim,
    Transition.RELEASE: plan_release,
    Transition.SUBMIT: plan_submit,
    Transition.ADVANCE: plan_advance,
    Transition.LOWER: plan_lower,
    Transition.APPLIED: plan_applied,
    Transition.ABANDONED: plan_abandoned,
}


# --------------------------------------------------------------------- store


class Store(Protocol):
    """A Change Store: reads one Change and makes one write at a time.

    A read with `relations` false skips the Change's Children and blockers and
    keeps none: a readback needs only the Change's own fields and history.
    """

    def read(self, number: int, relations: bool = True) -> Change: ...

    def write(self, change: Change, write: Write) -> str | None:
        """Make one write; return the posted comment's URL for a comment write."""
        ...

    def dependents(self, number: int) -> tuple[int, ...]: ...

    def block(self, dependent: int, blocker: int) -> None: ...

    def in_cycle(self, number: int) -> bool: ...


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def __call__(
        self, args: Sequence[str], stdin: str | None = None
    ) -> CommandResult: ...


def run_command(args: Sequence[str], stdin: str | None = None) -> CommandResult:
    try:
        completed = subprocess.run(
            list(args),
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return CommandResult(127, "", str(error))
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


STATE_QUERY: Final = (
    "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){"
    "id state title body "
    f"assignees(first:{ASSIGNEE_LIMIT}){{totalCount nodes{{login}}}} "
    f"userContentEdits(first:{EDIT_PAGE_SIZE}){{totalCount nodes{{id editedAt diff}}}} "
    f"comments(last:{COMMENT_PAGE_SIZE}){{totalCount nodes{{createdAt url body author{{login}}}}}} "
    f"issueFieldValues(first:{FIELD_VALUE_LIMIT}){{pageInfo{{hasNextPage}} nodes{{"
    "... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}} "
    "... on IssueFieldTextValue{value field{... on IssueFieldText{name}}} "
    "... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}}}"
    "}}}"
)
EVENTS_QUERY: Final = (
    "query($o:String!,$r:String!,$n:Int!,$after:String){repository(owner:$o,name:$r){"
    f"issue(number:$n){{timelineItems(first:{EVENT_PAGE_SIZE},after:$after,"
    "itemTypes:[ISSUE_FIELD_CHANGED_EVENT]){pageInfo{hasNextPage endCursor} nodes{"
    "... on IssueFieldChangedEvent{createdAt newValue "
    "issueField{... on IssueFieldSingleSelect{name} ... on IssueFieldText{name}}}}}}}}"
)
CHILDREN_QUERY: Final = (
    "query($o:String!,$r:String!,$after:String){repository(owner:$o,name:$r){"
    f"issues(first:{ISSUE_PAGE_SIZE},after:$after){{pageInfo{{hasNextPage endCursor}} nodes{{"
    f"number state issueFieldValues(first:{FIELD_VALUE_LIMIT}){{nodes{{"
    "... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}}}}}}}"
)
FIELDS_QUERY: Final = (
    "query($o:String!){organization(login:$o){issueFields(first:50){nodes{"
    "... on IssueFieldSingleSelect{id name options{id name}}}}}}"
)
SET_FIELD: Final = (
    "mutation($issue:ID!,$field:ID!,$option:ID!){setIssueFieldValue(input:"
    "{issueId:$issue,issueFields:[{fieldId:$field,singleSelectOptionId:$option}]})"
    "{clientMutationId}}"
)


class GitHubStore:
    """A Change Store that is a GitHub repository, reached through `gh`."""

    def __init__(self, store: str, run: CommandRunner = run_command) -> None:
        self.owner, self.repo = store.split("/", 1)
        self.store = store
        self.run = run
        self._options: dict[str, tuple[str, dict[str, str]]] | None = None

    def _gh(self, args: Sequence[str], stdin: str | None = None) -> str:
        result = self.run(["gh", *args], stdin)
        if result.returncode != 0:
            raise StoreError(f"gh {' '.join(args[:3])} failed: {result.stderr.strip()}")
        return result.stdout

    def _graphql(self, query: str, **variables: Any) -> Any:
        args = ["api", "graphql", "-f", f"query={query}"]
        for name, value in variables.items():
            flag = "-F" if isinstance(value, int) else "-f"
            args += [flag, f"{name}={value}"]
        try:
            data = json.loads(self._gh(args))
        except json.JSONDecodeError as error:
            raise StoreError(f"unreadable store answer: {error}") from error
        if not isinstance(data, Mapping) or "data" not in data or data.get("errors"):
            raise StoreError(
                f"store answer carries errors: {data.get('errors') if isinstance(data, Mapping) else data}"
            )
        return data["data"]

    def read(self, number: int, relations: bool = True) -> Change:
        issue = self._graphql(STATE_QUERY, o=self.owner, r=self.repo, n=number)[
            "repository"
        ]["issue"]
        if issue is None:
            raise StoreError(f"{self.store}#{number} does not exist")
        for connection, limit in (
            ("assignees", ASSIGNEE_LIMIT),
            ("userContentEdits", EDIT_PAGE_SIZE),
            ("comments", COMMENT_PAGE_SIZE),
        ):
            if issue[connection]["totalCount"] > limit:
                raise StoreError(
                    f"{connection} exceed one page", bound=f"{limit} {connection}"
                )
        if issue["issueFieldValues"]["pageInfo"]["hasNextPage"]:
            raise StoreError(
                "field values exceed one page",
                bound=f"{FIELD_VALUE_LIMIT} field values",
            )
        values: dict[str, Any] = {}
        for node in issue["issueFieldValues"]["nodes"]:
            name = (node.get("field") or {}).get("name")
            if name:
                values[name] = node.get("name", node.get("value"))
        parent = values.get(Field.PARENT)
        return Change(
            number=number,
            node_id=issue["id"],
            state=IssueState(issue["state"]),
            title=issue["title"],
            body=issue["body"],
            maturity=values.get(Field.MATURITY),
            lifecycle=values.get(Field.LIFECYCLE),
            assignees=tuple(node["login"] for node in issue["assignees"]["nodes"]),
            base=values.get(Field.BASE),
            parent=None if parent is None else int(parent),
            children=self._children(number) if relations else (),
            blockers=self._blockers(number) if relations else (),
            revisions=tuple(
                Revision(node["id"], node["editedAt"], node.get("diff") or "")
                for node in issue["userContentEdits"]["nodes"]
            ),
            field_events=self._events(number),
            comments=tuple(
                Comment(
                    node["createdAt"],
                    (node.get("author") or {}).get("login", ""),
                    node["body"],
                    node.get("url", ""),
                )
                for node in issue["comments"]["nodes"]
            ),
        )

    def _events(self, number: int) -> tuple[FieldEvent, ...]:
        events: list[FieldEvent] = []
        after: str | None = None
        for _ in range(EVENT_MAX_PAGES):
            variables: dict[str, Any] = {"o": self.owner, "r": self.repo, "n": number}
            if after:
                variables["after"] = after
            items = self._graphql(EVENTS_QUERY, **variables)["repository"]["issue"][
                "timelineItems"
            ]
            for node in items["nodes"]:
                name = (node.get("issueField") or {}).get("name")
                if name:
                    events.append(
                        FieldEvent(node["createdAt"], name, node.get("newValue"))
                    )
            if not items["pageInfo"]["hasNextPage"]:
                return tuple(events)
            after = items["pageInfo"]["endCursor"]
        raise StoreError(
            "field events exceed the bound",
            bound=f"{EVENT_PAGE_SIZE} events per page, {EVENT_MAX_PAGES} pages",
        )

    def _children(self, number: int) -> tuple[tuple[int, IssueState], ...]:
        children: list[tuple[int, IssueState]] = []
        after: str | None = None
        for _ in range(ISSUE_MAX_PAGES):
            variables: dict[str, Any] = {"o": self.owner, "r": self.repo}
            if after:
                variables["after"] = after
            issues = self._graphql(CHILDREN_QUERY, **variables)["repository"]["issues"]
            for node in issues["nodes"]:
                for value in node["issueFieldValues"]["nodes"]:
                    if (
                        (value.get("field") or {}).get("name") == Field.PARENT
                        and value.get("value") is not None
                        and int(value["value"]) == number
                    ):
                        children.append((node["number"], IssueState(node["state"])))
            if not issues["pageInfo"]["hasNextPage"]:
                return tuple(children)
            after = issues["pageInfo"]["endCursor"]
        raise StoreError(
            "issues exceed the bound",
            bound=f"{ISSUE_PAGE_SIZE} issues per page, {ISSUE_MAX_PAGES} pages",
        )

    def _rest_numbers(self, path: str) -> tuple[int, ...]:
        raw = self._gh(
            [
                "api",
                "--method",
                "GET",
                f"repos/{self.store}/{path}",
                "-F",
                f"per_page={DEPENDENCY_PAGE_SIZE}",
            ]
        )
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as error:
            raise StoreError(f"unreadable dependency answer: {error}") from error
        if len(items) >= DEPENDENCY_PAGE_SIZE:
            raise StoreError(
                "dependencies fill one page",
                bound=f"{DEPENDENCY_PAGE_SIZE} dependencies, one page",
            )
        return tuple(item["number"] for item in items if item.get("state") == "open")

    def _blockers(self, number: int) -> tuple[int, ...]:
        return self._rest_numbers(f"issues/{number}/dependencies/blocked_by")

    def dependents(self, number: int) -> tuple[int, ...]:
        return self._rest_numbers(f"issues/{number}/dependencies/blocking")

    def in_cycle(self, number: int) -> bool:
        seen: set[int] = set()
        frontier = list(self._blockers(number))
        while frontier:
            current = frontier.pop()
            if current == number:
                return True
            if current in seen or len(seen) >= DEPENDENCY_PAGE_SIZE:
                continue
            seen.add(current)
            frontier.extend(self._blockers(current))
        return False

    def block(self, dependent: int, blocker: int) -> None:
        raw = self._gh(["api", f"repos/{self.store}/issues/{blocker}", "--jq", ".id"])
        self._gh(
            [
                "api",
                f"repos/{self.store}/issues/{dependent}/dependencies/blocked_by",
                "--method",
                "POST",
                "-F",
                f"issue_id={raw.strip()}",
            ]
        )

    def _option(self, field_name: str, option: str) -> tuple[str, str]:
        if self._options is None:
            try:
                nodes = self._graphql(FIELDS_QUERY, o=self.owner)["organization"][
                    "issueFields"
                ]["nodes"]
                self._options = {
                    node["name"]: (
                        node["id"],
                        {item["name"]: item["id"] for item in node["options"]},
                    )
                    for node in nodes
                    if node.get("options")
                }
            except (KeyError, TypeError) as error:
                raise StoreError(
                    f"unreadable issue fields answer for {self.owner}: {error!r}"
                ) from error
        if field_name not in self._options:
            raise StoreError(
                f"the store defines no issue field {field_name}; it defines "
                f"{', '.join(sorted(self._options)) or 'none'}"
            )
        field_id, options = self._options[field_name]
        if option not in options:
            raise StoreError(
                f"the issue field {field_name} has no option {option}; it has "
                f"{', '.join(sorted(options))}"
            )
        return field_id, options[option]

    def write(self, change: Change, write: Write) -> str | None:
        number = str(change.number)
        if write.kind in (WriteKind.MATURITY, WriteKind.LIFECYCLE):
            name = (
                Field.MATURITY if write.kind == WriteKind.MATURITY else Field.LIFECYCLE
            )
            field_id, option_id = self._option(name, str(write.value))
            self._graphql(
                SET_FIELD, issue=change.node_id, field=field_id, option=option_id
            )
            return None
        if write.kind == WriteKind.ASSIGNEE:
            for login in change.assignees:
                if login not in write.value:
                    self._gh(
                        [
                            "issue",
                            "edit",
                            number,
                            "--repo",
                            self.store,
                            "--remove-assignee",
                            login,
                        ]
                    )
            for login in write.value:
                if login not in change.assignees:
                    self._gh(
                        [
                            "issue",
                            "edit",
                            number,
                            "--repo",
                            self.store,
                            "--add-assignee",
                            login,
                        ]
                    )
            return None
        if write.kind == WriteKind.COMMENT:
            return self._gh(
                ["issue", "comment", number, "--repo", self.store, "--body-file", "-"],
                str(write.value),
            ).strip()
        reason = "completed" if change.lifecycle == Lifecycle.APPLIED else "not planned"
        self._gh(["issue", "close", number, "--repo", self.store, "--reason", reason])
        return None


class GitTreeReader:
    """Reads a Product's tree at a commit through `git` in its checkout root."""

    def __init__(self, root: str, run: CommandRunner = run_command) -> None:
        self.root = root
        self.run = run

    def resolves(self, commit: str) -> bool:
        return (
            self.run(
                ["git", "-C", self.root, "cat-file", "-e", f"{commit}^{{commit}}"]
            ).returncode
            == 0
        )

    def read(self, commit: str, path: str) -> str | None:
        """A file's text, or for a directory every file under it with its blob id."""
        tree = self.run(["git", "-C", self.root, "ls-tree", "-r", f"{commit}:{path}"])
        if tree.returncode == 0:
            return tree.stdout
        result = self.run(["git", "-C", self.root, "show", f"{commit}:{path}"])
        return result.stdout if result.returncode == 0 else None

    def list_dir(self, commit: str, path: str) -> tuple[str, ...] | None:
        result = self.run(
            ["git", "-C", self.root, "ls-tree", "--name-only", f"{commit}:{path}"]
        )
        return tuple(result.stdout.split()) if result.returncode == 0 else None


def github_ancestor(run: CommandRunner) -> Callable[[str, str], bool]:
    """Whether a merge commit is an ancestor of its repository's default branch."""

    def ancestor(changeset_url: str, merge_commit: str) -> bool:
        match = re.match(r"https://github\.com/([\w.-]+/[\w.-]+)/", changeset_url)
        if not match:
            return False
        repo = match.group(1)
        branch = run(
            [
                "gh",
                "repo",
                "view",
                repo,
                "--json",
                "defaultBranchRef",
                "--jq",
                ".defaultBranchRef.name",
            ]
        )
        if branch.returncode != 0:
            return False
        status = run(
            [
                "gh",
                "api",
                f"repos/{repo}/compare/{merge_commit}...{branch.stdout.strip()}",
                "--jq",
                ".status",
            ]
        )
        return status.returncode == 0 and status.stdout.strip() in (
            "ahead",
            "identical",
        )

    return ancestor


# ----------------------------------------------------------------- execution


def observe(change: Change) -> dict[str, Any]:
    return {
        ObservedKey.STATE: change.state.value,
        ObservedKey.MATURITY: change.maturity,
        ObservedKey.LIFECYCLE: change.lifecycle,
        ObservedKey.ASSIGNEES: list(change.assignees),
        ObservedKey.BODY_SHA256: change.body_sha256,
        ObservedKey.BASE: change.base,
    }


def landed(write: Write, change: Change) -> bool:
    if write.kind == WriteKind.MATURITY:
        return change.maturity == write.value
    if write.kind == WriteKind.LIFECYCLE:
        return change.lifecycle == write.value
    if write.kind == WriteKind.ASSIGNEE:
        return change.assignees == tuple(write.value)
    if write.kind == WriteKind.COMMENT:
        return any(
            comment.body.strip() == str(write.value).strip()
            for comment in change.comments
        )
    return change.state == write.value


def binding_at_comment(change: Change, comment_body: str) -> BoundPair | None:
    """The body revision and the Base that stood when the comment posted."""
    posted = next(
        (
            c.created_at
            for c in reversed(change.comments)
            if c.body.strip() == comment_body.strip()
        ),
        None,
    )
    if posted is None:
        return None
    revisions = [r for r in change.revisions if r.edited_at <= posted]
    body = max(revisions, key=lambda r: r.edited_at).body if revisions else change.body
    bases = [
        e
        for e in change.field_events
        if e.field == Field.BASE and e.created_at <= posted
    ]
    base = max(bases, key=lambda e: e.created_at).new_value if bases else change.base
    return BoundPair(sha256(body), base or "")


def execute(
    store: Store, change: Change, plan_: Plan, identity: Identity
) -> dict[str, Any]:
    """Make the plan's writes in order, reading the Change back after each."""
    done: list[str] = []
    current = change
    comment_url: str | None = None
    for write in plan_.writes:
        if write.kind == WriteKind.COMMENT and plan_.bound is not None:
            fresh = safe_read(store, change.number)
            if (
                fresh is None
                or BoundPair(fresh.body_sha256, fresh.base or "") != plan_.bound
            ):
                return failed(
                    Reason.BINDING_RACED,
                    "the bound pair changed before the advance comment",
                    done,
                    write,
                    fresh,
                )
            current = fresh
        try:
            url = store.write(current, write)
        except StoreError as error:
            return failed(
                Reason.WRITE_FAILED,
                error.detail,
                done,
                write,
                safe_read(store, change.number),
            )
        if url:
            comment_url = url
        try:
            current = store.read(change.number, relations=False)
        except StoreError as error:
            return failed(
                Reason.READ_FAILED, error.detail, done + [write.kind.value], None, None
            )
        if not landed(write, current):
            return failed(
                Reason.READBACK,
                f"the {write.kind} write reads back {observe(current)}",
                done,
                write,
                current,
            )
        done.append(write.kind.value)
    if (
        plan_.bound is not None
        and binding_at_comment(current, plan_.comment) != plan_.bound
    ):
        return failed(
            Reason.BINDING_RACED,
            "the pair standing at the advance comment differs from the bound pair",
            done,
            None,
            current,
        )
    if plan_.transition == Transition.CLAIM and not held_by(current, identity):
        return failed(
            Reason.HOLDER,
            "another claim comment is newer than this session's",
            done,
            None,
            current,
        )
    return {
        ResultKey.STATUS: Status.DONE.value,
        ResultKey.TRANSITION: plan_.transition.value,
        ResultKey.WRITES: done,
        ResultKey.COMMENT_URL: comment_url,
        ResultKey.OBSERVED: observe(current),
    }


def safe_read(store: Store, number: int) -> Change | None:
    try:
        return store.read(number, relations=False)
    except StoreError:
        return None


def failed(
    reason: Reason,
    detail: str,
    done: list[str],
    write: Write | None,
    change: Change | None,
) -> dict[str, Any]:
    return {
        ResultKey.STATUS: Status.FAILED.value,
        ResultKey.REASON: reason.value,
        ResultKey.DETAIL: detail,
        ResultKey.WRITES: done,
        ResultKey.FAILED_WRITE: None if write is None else write.kind.value,
        ResultKey.OBSERVED: None if change is None else observe(change),
    }


def refused(reason: Reason, detail: str, change: Change | None) -> dict[str, Any]:
    return {
        ResultKey.STATUS: Status.REFUSED.value,
        ResultKey.REASON: reason.value,
        ResultKey.DETAIL: detail,
        ResultKey.WRITES: [],
        ResultKey.OBSERVED: None if change is None else observe(change),
    }


def pass_blocks(store: Store, request: Request, change: Change) -> list[dict[str, Any]]:
    """After an abandoned close: pass each block on, or return each dependent to Refinement."""
    results: list[dict[str, Any]] = []
    for dependent in store.dependents(change.number):
        if request.merged_into is not None:
            store.block(dependent, request.merged_into)
            results.append({"dependent": dependent, "blocked_by": request.merged_into})
            continue
        other = store.read(dependent)
        if other.maturity == Maturity.APPLICABLE:
            lower = Request(
                transition=Transition.LOWER,
                store=request.store,
                number=dependent,
                mover=Mover.AGENT,
                identity=request.identity,
                target=Maturity.SLICED,
                reason=f"blocker #{change.number} closed Abandoned without a merge",
                lower_cause=LowerCause.BLOCKER_ABANDONED,
            )
            results.append({"dependent": dependent, "lower": transition(lower, store)})
    return results


def transition(
    request: object,
    store: Store | None = None,
    *,
    run: CommandRunner = run_command,
    root: str | None = None,
) -> dict[str, Any]:
    """Make one Transition and return the result `main` writes for it."""
    try:
        parsed = request if isinstance(request, Request) else read_request(request)
    except InvalidRequest as error:
        return {
            ResultKey.STATUS: Status.INVALID_REQUEST.value,
            ResultKey.DETAIL: str(error),
            ResultKey.WRITES: [],
        }
    store = store or GitHubStore(parsed.store, run)
    try:
        change = store.read(parsed.number)
    except StoreError as error:
        return refused(
            Reason.BOUND if error.bound else Reason.READ_FAILED,
            error.bound or error.detail,
            None,
        )
    try:
        cycle = parsed.transition in (
            Transition.ADVANCE,
            Transition.CLAIM,
        ) and store.in_cycle(parsed.number)
        context = PlanContext(
            cycle=cycle,
            reader=GitTreeReader(root, run) if root else None,
            ancestor=github_ancestor(run),
        )
        plan_ = plan(parsed, change, context)
    except Refusal as refusal:
        return refused(refusal.reason, refusal.detail, change)
    except StoreError as error:
        return refused(
            Reason.BOUND if error.bound else Reason.READ_FAILED,
            error.bound or error.detail,
            change,
        )
    result = execute(store, change, plan_, parsed.identity)
    if result[ResultKey.STATUS] != Status.DONE.value:
        return result
    if plan_.follow is not None:
        result[ResultKey.RELEASE] = transition(plan_.follow, store, run=run, root=root)
    if parsed.transition == Transition.ABANDONED:
        result[ResultKey.DEPENDENTS] = pass_blocks(store, parsed, change)
    return result


def exit_code(result: Mapping[str, Any]) -> int:
    return {
        Status.DONE.value: EXIT_DONE,
        Status.REFUSED.value: EXIT_REFUSED,
        Status.INVALID_REQUEST.value: EXIT_INVALID_REQUEST,
    }.get(str(result.get(ResultKey.STATUS)), EXIT_FAILED)


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    run: CommandRunner = run_command,
) -> int:
    source = stdin or sys.stdin
    sink = stdout or sys.stdout
    try:
        raw = json.loads(source.read())
    except json.JSONDecodeError as error:
        result: dict[str, Any] = {
            ResultKey.STATUS: Status.INVALID_REQUEST.value,
            ResultKey.DETAIL: str(error),
            ResultKey.WRITES: [],
        }
    else:
        root = raw.get(RequestKey.CHECKOUT_ROOT) if isinstance(raw, Mapping) else None
        result = transition(raw, run=run, root=root if isinstance(root, str) else None)
    sink.write(json.dumps(result, indent=2) + "\n")
    return exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
