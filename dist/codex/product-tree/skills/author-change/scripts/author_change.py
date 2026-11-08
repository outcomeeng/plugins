"""Record, publish, split, merge, reframe, and draft Change records.

Reads one JSON request on stdin and writes one JSON result on stdout. The
request names the operation, the Change store, the Product's checkout root,
the session identity for Transition comments, and the Draft files the
operation reads. The Change store is a GitHub repository, reached only through
the injected command runner that starts `gh` and `git`.

Every operation that writes a record's body first hands the Change Draft to the
form check of the change-standards skill and writes nothing while the check
fails. Every Transition the script makes, the lower of a reframe or of a
publish that writes the body of an Applicable record and the abandoned
Transition of a merge, goes through the transition function of the
operate-change skill. Both skills are reached by a `__file__`-relative import.

Result statuses: `ok`, `failed` (the check failed, the revision changed, or a
readback differed), `blocked` (a read failed or a sibling skill is absent),
and `invalid-request`.

Portability: stdlib only; supports Python 3.13 and later.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import ModuleType
from typing import Any, Final, Protocol, TextIO

EXIT_OK: Final = 0
EXIT_FAILED: Final = 1
EXIT_INVALID_REQUEST: Final = 2
EXIT_BLOCKED: Final = 3

DEFAULT_SIZE_LIMIT: Final = 65_536
EDIT_HISTORY_DEPTH: Final = 5
BLOCKER_PAGE: Final = 100
FIELD_VALUE_LIMIT: Final = 50
ASSIGNEE_LIMIT: Final = 100
RECORDER: Final = "@me"
FRONT_MATTER_FENCE: Final = "---"
LIST_SEPARATOR: Final = ", "

STATEMENT_HEADING: Final = "## Statement of Intent"
DECLARATIONS_HEADING: Final = "## Declarations"


class Status(StrEnum):
    OK = "ok"
    FAILED = "failed"
    BLOCKED = "blocked"
    INVALID_REQUEST = "invalid-request"


class Operation(StrEnum):
    PUBLISH = "publish"
    RECORD = "record"
    SPLIT = "split"
    DRAFT = "draft"
    REFRAME = "reframe"
    MERGE = "merge"


class RequestField(StrEnum):
    OPERATION = "operation"
    STORE = "store"
    NUMBER = "number"
    DRAFT_PATH = "draft_path"
    CHECKOUT_ROOT = "checkout_root"
    SIZE_LIMIT = "size_limit"
    IDENTITY = "identity"
    REASON = "reason"
    CHILDREN = "children"
    ABSORBED = "absorbed"
    HANDOFF = "handoff"


class IdentityField(StrEnum):
    HARNESS = "harness"
    SESSION = "session"
    MACHINE = "machine"
    WORKTREE = "worktree"


class ResultField(StrEnum):
    STATUS = "status"
    DETAIL = "detail"
    FINDINGS = "findings"
    WRITES = "writes"
    NUMBER = "number"
    NUMBERS = "numbers"
    READ = "read"
    MISMATCH = "mismatch"
    RESTORED = "restored"


class Metadata(StrEnum):
    """The keys of a record's metadata, as the Change record decision names them."""

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


class RecordField(StrEnum):
    METADATA = "metadata"
    BODY = "body"


class Maturity(StrEnum):
    PROPOSED = "Proposed"
    FRAMED = "Framed"
    SLICED = "Sliced"
    APPLICABLE = "Applicable"


class Lifecycle(StrEnum):
    AVAILABLE = "Available"
    SUBMITTED = "Submitted"
    APPLIED = "Applied"
    ABANDONED = "Abandoned"


class Move(StrEnum):
    LOWER = "lower"
    ABANDONED = "abandoned"


class FormCheckOperation(StrEnum):
    RECORD = "record"
    PUBLISH = "publish"
    SPLIT = "split"
    RECORD_CHILD = "record-child"
    MERGE = "merge"


class CheckRequestField(StrEnum):
    DRAFT_TEXT = "draft_text"
    CHECKOUT_ROOT = "checkout_root"
    OPERATION = "operation"
    STORED_RECORD = "stored_record"
    BLOCKER_RECORDS = "blocker_records"
    SIZE_LIMIT = "size_limit"


class CheckResultField(StrEnum):
    STATUS = "status"
    FINDINGS = "findings"


CHECK_PASS: Final = "pass"


class TransitionRequestField(StrEnum):
    """The keys of the request the transition function of operate-change reads."""

    TRANSITION = "transition"
    STORE = "store"
    NUMBER = "number"
    MOVER = "mover"
    IDENTITY = "identity"
    TARGET = "target"
    REASON = "reason"
    LOWER_CAUSE = "lower_cause"
    HANDOFF = "handoff"
    MERGED_INTO = "merged_into"


class TransitionResultField(StrEnum):
    STATUS = "status"


class Mover(StrEnum):
    HOLDER = "holder"
    AGENT = "agent"


class LowerCause(StrEnum):
    REFRAME = "reframe"
    APPLICABLE_PUBLISH = "applicable-publish"


TRANSITION_DONE: Final = "done"

#: The sibling skills and the modules and functions the script imports from them.
FORM_CHECK_SKILL: Final = "change-standards"
FORM_CHECK_MODULE: Final = "form_check.py"
FORM_CHECK_FUNCTION: Final = "check"
TRANSITION_SKILL: Final = "operate-change"
TRANSITION_MODULE: Final = "operate_change.py"
TRANSITION_FUNCTION: Final = "transition"


class FieldName(StrEnum):
    """The organization issue fields that hold the record's metadata."""

    PRODUCT = "Product"
    MATURITY = "Maturity"
    LIFECYCLE = "Lifecycle"
    PARENT = "Parent"
    PREDECESSORS = "Predecessors"
    BASE = "Base"
    PRIORITY = "Priority"
    PRIMARY_VALUE = "Value"
    INVESTMENT = "Investment"


SINGLE_SELECT_FIELDS: Final = (
    FieldName.PRODUCT,
    FieldName.MATURITY,
    FieldName.LIFECYCLE,
    FieldName.PRIORITY,
    FieldName.PRIMARY_VALUE,
    FieldName.INVESTMENT,
)

METADATA_FIELD: Final = {
    Metadata.PRODUCT: FieldName.PRODUCT,
    Metadata.MATURITY: FieldName.MATURITY,
    Metadata.LIFECYCLE: FieldName.LIFECYCLE,
    Metadata.PARENT: FieldName.PARENT,
    Metadata.PREDECESSORS: FieldName.PREDECESSORS,
    Metadata.BASE: FieldName.BASE,
    Metadata.PRIORITY: FieldName.PRIORITY,
    Metadata.PRIMARY_VALUE: FieldName.PRIMARY_VALUE,
    Metadata.INVESTMENT: FieldName.INVESTMENT,
}

READ_QUERY: Final = (
    "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){"
    "issue(number:$n){id number title body url "
    f"assignees(first:{ASSIGNEE_LIMIT}){{nodes{{login}}}} "
    f"userContentEdits(first:{EDIT_HISTORY_DEPTH}){{nodes{{id diff}}}} "
    f"issueFieldValues(first:{FIELD_VALUE_LIMIT}){{nodes{{"
    "... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}} "
    "... on IssueFieldTextValue{value field{... on IssueFieldText{name}}} "
    "... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}"
    "}}}}}}"
)
FIELD_IDS_QUERY: Final = (
    "query($l:String!){organization(login:$l){issueFields(first:50){nodes{"
    "... on IssueFieldSingleSelect{id name options{id name}} "
    "... on IssueFieldText{id name} ... on IssueFieldNumber{id name}}}}}"
)
SET_SINGLE_SELECT: Final = (
    "mutation($i:ID!,$f:ID!,$v:ID!){setIssueFieldValue(input:{issueId:$i,"
    "issueFields:[{fieldId:$f,singleSelectOptionId:$v}]}){clientMutationId}}"
)
SET_TEXT: Final = (
    "mutation($i:ID!,$f:ID!,$v:String!){setIssueFieldValue(input:{issueId:$i,"
    "issueFields:[{fieldId:$f,textValue:$v}]}){clientMutationId}}"
)
SET_NUMBER: Final = (
    "mutation($i:ID!,$f:ID!,$v:Float!){setIssueFieldValue(input:{issueId:$i,"
    "issueFields:[{fieldId:$f,numberValue:$v}]}){clientMutationId}}"
)

STORE_PATTERN: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+$")
ISSUE_URL_PATTERN: Final = re.compile(
    r"^https://github\.com/([A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+)/issues/(\d+)$"
)
SHORT_REFERENCE_PATTERN: Final = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+)#(\d+)$"
)


class Blocked(Exception):
    """A read failed, returned unreadable output, or a sibling skill is absent."""

    def __init__(self, read: str, detail: str) -> None:
        super().__init__(detail)
        self.read = read
        self.detail = detail


class InvalidRequest(Exception):
    """The request names no operation the script makes, or lacks a value."""


class Failed(Exception):
    """A publish stopped: the check failed, the revision changed, or a readback differed."""

    def __init__(
        self,
        detail: str,
        findings: Sequence[object] = (),
        mismatch: Sequence[str] = (),
        restored: bool = False,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.findings = list(findings)
        self.mismatch = list(mismatch)
        self.restored = restored


@dataclass(frozen=True)
class CommandResult:
    """What one `gh` or `git` command returned."""

    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    """Starts `gh` or `git` with the arguments, the program first."""

    def __call__(self, arguments: Sequence[str]) -> CommandResult: ...


def subprocess_runner(arguments: Sequence[str]) -> CommandResult:
    completed = subprocess.run(
        list(arguments), capture_output=True, text=True, check=False
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


@dataclass
class Draft:
    """A Change Draft: its metadata as YAML front matter, then its body."""

    metadata: dict[str, Any]
    body: str
    text: str


@dataclass
class Edit:
    """One revision of the issue body in the edit history, newest first."""

    identifier: str
    body: str


@dataclass
class Stored:
    """The record the Change store holds for one issue."""

    number: int
    node_id: str
    url: str
    title: str
    body: str
    metadata: dict[str, Any]
    edits: list[Edit]

    def last_edit(self) -> str | None:
        return self.edits[0].identifier if self.edits else None

    def as_record(self) -> dict[str, Any]:
        return {
            RecordField.METADATA: self.metadata,
            RecordField.BODY: self.body,
        }


@dataclass
class Session:
    """What one invocation did to the store, for the result and the readback."""

    store: str
    run: CommandRunner
    identity: Mapping[str, str]
    checkout_root: str
    size_limit: int
    handoff: Mapping[str, Any] | None = None
    writes: list[str] = field(default_factory=list)
    field_ids: dict[str, tuple[str, dict[str, str]]] | None = None


def load_sibling(skill: str, module_file: str, name: str) -> ModuleType:
    """Import a sibling skill's module by a `__file__`-relative path."""
    path = Path(__file__).resolve().parents[2] / skill / "scripts" / module_file
    if not path.is_file():
        raise Blocked(skill, f"the {skill} skill's {module_file} is absent")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Blocked(skill, f"the {skill} skill's {module_file} cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def form_check(request: dict[str, Any]) -> dict[str, Any]:
    module = load_sibling(FORM_CHECK_SKILL, FORM_CHECK_MODULE, "change_form_check")
    function: Callable[[object], dict[str, Any]] = getattr(module, FORM_CHECK_FUNCTION)
    return function(request)


def transition(request: dict[str, Any]) -> dict[str, Any]:
    module = load_sibling(TRANSITION_SKILL, TRANSITION_MODULE, "change_transition")
    function: Callable[[dict[str, Any]], dict[str, Any]] = getattr(
        module, TRANSITION_FUNCTION
    )
    return function(request)


def gh(session: Session, arguments: Sequence[str], read: str) -> str:
    try:
        result = session.run(["gh", *arguments])
    except OSError as error:
        raise Blocked(read, f"gh could not start: {error}") from error
    if result.returncode != 0:
        raise Blocked(read, result.stderr.strip() or f"gh exited {result.returncode}")
    return result.stdout


def gh_json(session: Session, arguments: Sequence[str], read: str) -> Any:
    output = gh(session, arguments, read)
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise Blocked(read, "gh printed output that is not JSON") from error


def graphql(
    session: Session, query: str, variables: Mapping[str, str | int], read: str
) -> Any:
    arguments = ["api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        flag = "-F" if isinstance(value, int) else "-f"
        arguments.extend([flag, f"{name}={value}"])
    return gh_json(session, arguments, read)


def parse_front_matter_value(raw: str) -> Any:
    value = raw.strip()
    if value in ("null", "~", ""):
        return None
    if value.startswith("[") and value.endswith("]"):
        items = [item.strip() for item in value[1:-1].split(",")]
        return [item for item in items if item]
    return value.strip("\"'")


def parse_draft(text: str) -> Draft:
    lines = text.split("\n")
    if not lines or lines[0].strip() != FRONT_MATTER_FENCE:
        raise InvalidRequest("the Draft opens with no front matter")
    try:
        end = next(
            index
            for index in range(1, len(lines))
            if lines[index].strip() == FRONT_MATTER_FENCE
        )
    except StopIteration as error:
        raise InvalidRequest("the Draft's front matter has no closing fence") from error
    metadata: dict[str, Any] = {}
    index = 1
    while index < end:
        line = lines[index]
        index += 1
        if not line.strip() or ":" not in line:
            continue
        key, _, raw = line.partition(":")
        raw = raw.strip()
        if raw.startswith("[") and not raw.endswith("]"):
            collected = [raw]
            while index < end and not collected[-1].rstrip().endswith("]"):
                collected.append(lines[index].strip())
                index += 1
            raw = " ".join(collected)
        metadata[key.strip()] = parse_front_matter_value(raw)
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return Draft(metadata=metadata, body=body, text=text)


def read_draft(path: str) -> Draft:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise InvalidRequest(f"the Draft at {path} cannot be read: {error}") from error
    return parse_draft(text)


def render_draft(metadata: Mapping[str, Any], body: str) -> str:
    lines = [FRONT_MATTER_FENCE]
    for key in Metadata:
        if key == Metadata.HOLDER or key.value not in metadata:
            continue
        value = metadata[key.value]
        if value is None:
            rendered = "null"
        elif isinstance(value, list):
            rendered = "[" + LIST_SEPARATOR.join(str(item) for item in value) + "]"
        else:
            rendered = str(value)
        lines.append(f"{key.value}: {rendered}")
    lines.append(FRONT_MATTER_FENCE)
    return "\n".join(lines) + "\n\n" + body.rstrip("\n") + "\n"


def issue_reference(store: str, number: int) -> str:
    return f"https://github.com/{store}/issues/{number}"


def parse_reference(reference: str, store: str) -> int:
    for pattern in (ISSUE_URL_PATTERN, SHORT_REFERENCE_PATTERN):
        match = pattern.match(reference.strip())
        if match:
            if match.group(1) != store:
                raise InvalidRequest(
                    f"{reference} names a Change outside the store {store}"
                )
            return int(match.group(2))
    raise InvalidRequest(f"{reference} is no Change reference")


def read_field_ids(session: Session) -> dict[str, tuple[str, dict[str, str]]]:
    if session.field_ids is None:
        owner = session.store.split("/")[0]
        answer = graphql(
            session, FIELD_IDS_QUERY, {"l": owner}, "organization issue fields"
        )
        try:
            nodes = answer["data"]["organization"]["issueFields"]["nodes"]
            session.field_ids = {
                node["name"]: (
                    node["id"],
                    {
                        option["name"]: option["id"]
                        for option in node.get("options", [])
                    },
                )
                for node in nodes
                if node and "id" in node
            }
        except (KeyError, TypeError) as error:
            raise Blocked(
                "organization issue fields", "the answer holds no issue fields"
            ) from error
    return session.field_ids


def read_stored(session: Session, number: int) -> Stored:
    owner, repo = session.store.split("/")
    answer = graphql(
        session, READ_QUERY, {"o": owner, "r": repo, "n": number}, f"issue {number}"
    )
    try:
        issue = answer["data"]["repository"]["issue"]
        values = issue["issueFieldValues"]["nodes"]
        assignees = [node["login"] for node in issue["assignees"]["nodes"]]
        edits = [
            Edit(node["id"], node["diff"])
            for node in issue["userContentEdits"]["nodes"]
        ]
        if len(values) >= FIELD_VALUE_LIMIT:
            raise Blocked(f"issue {number}", f"{FIELD_VALUE_LIMIT} field values")
        by_name: dict[str, Any] = {}
        for node in values:
            if not node:
                continue
            name = node["field"]["name"]
            by_name[name] = node["name"] if "name" in node else node["value"]
    except (KeyError, TypeError) as error:
        raise Blocked(f"issue {number}", "the answer holds no issue") from error
    blockers = [
        issue_reference(session.store, entry["number"])
        for entry in blocker_entries(session, number)
    ]
    parent = by_name.get(FieldName.PARENT)
    predecessors = by_name.get(FieldName.PREDECESSORS)
    metadata: dict[str, Any] = {
        Metadata.TITLE: issue["title"],
        Metadata.PRODUCT: by_name.get(FieldName.PRODUCT),
        Metadata.MATURITY: by_name.get(FieldName.MATURITY),
        Metadata.LIFECYCLE: by_name.get(FieldName.LIFECYCLE),
        Metadata.HOLDER: assignees[0] if assignees else None,
        Metadata.PARENT: None
        if parent is None
        else issue_reference(session.store, int(float(parent))),
        Metadata.PREDECESSORS: []
        if not predecessors
        else [item for item in str(predecessors).split(LIST_SEPARATOR) if item],
        Metadata.BLOCKERS: blockers,
        Metadata.BASE: by_name.get(FieldName.BASE),
        Metadata.PRIORITY: by_name.get(FieldName.PRIORITY),
        Metadata.PRIMARY_VALUE: by_name.get(FieldName.PRIMARY_VALUE),
        Metadata.INVESTMENT: by_name.get(FieldName.INVESTMENT),
    }
    return Stored(
        number=number,
        node_id=issue["id"],
        url=issue["url"],
        title=issue["title"],
        body=issue["body"],
        metadata={key.value: value for key, value in metadata.items()},
        edits=edits,
    )


def blocker_entries(session: Session, number: int) -> list[dict[str, Any]]:
    entries = gh_json(
        session,
        [
            "api",
            f"repos/{session.store}/issues/{number}/dependencies/blocked_by",
            "--method",
            "GET",
            "-F",
            f"per_page={BLOCKER_PAGE}",
        ],
        f"blockers of issue {number}",
    )
    if not isinstance(entries, list):
        raise Blocked(f"blockers of issue {number}", "the answer is no list")
    if len(entries) >= BLOCKER_PAGE:
        raise Blocked(
            f"blockers of issue {number}", f"{BLOCKER_PAGE} blockers, one page"
        )
    return entries


def issue_id(session: Session, number: int) -> int:
    output = gh(
        session,
        ["api", f"repos/{session.store}/issues/{number}", "--jq", ".id"],
        f"issue id of {number}",
    )
    try:
        return int(output.strip())
    except ValueError as error:
        raise Blocked(f"issue id of {number}", "the answer is no number") from error


def check_form(
    session: Session,
    draft: Draft,
    operation: FormCheckOperation,
    stored: Stored | None,
    blockers: Sequence[Stored],
) -> None:
    request = {
        CheckRequestField.DRAFT_TEXT: draft.text,
        CheckRequestField.CHECKOUT_ROOT: session.checkout_root,
        CheckRequestField.OPERATION: operation.value,
        CheckRequestField.STORED_RECORD: stored.as_record() if stored else None,
        CheckRequestField.BLOCKER_RECORDS: [entry.as_record() for entry in blockers],
        CheckRequestField.SIZE_LIMIT: session.size_limit,
    }
    result = form_check({key.value: value for key, value in request.items()})
    if result.get(CheckResultField.STATUS) != CHECK_PASS:
        raise Failed(
            "the form check failed the Draft",
            findings=result.get(CheckResultField.FINDINGS, []),
        )


def read_blockers(session: Session, draft: Draft) -> list[Stored]:
    return [
        read_stored(session, parse_reference(reference, session.store))
        for reference in draft.metadata.get(Metadata.BLOCKERS, []) or []
    ]


def write_file(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


def set_field(
    session: Session, stored_node_id: str, name: FieldName, value: Any
) -> None:
    ids = read_field_ids(session)
    if name not in ids:
        raise Blocked(
            "organization issue fields", f"the organization has no field {name}"
        )
    field_id, options = ids[name]
    if name in SINGLE_SELECT_FIELDS:
        if value not in options:
            raise Blocked(
                "organization issue fields", f"the field {name} has no option {value}"
            )
        query, variable = SET_SINGLE_SELECT, options[value]
    elif name == FieldName.PARENT:
        query, variable = SET_NUMBER, value
    else:
        query, variable = SET_TEXT, value
    flag = "-F" if name == FieldName.PARENT else "-f"
    gh(
        session,
        [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-f",
            f"i={stored_node_id}",
            "-f",
            f"f={field_id}",
            flag,
            f"v={variable}",
        ],
        f"write of field {name}",
    )
    session.writes.append(f"field {name}")


def field_value(name: FieldName, value: Any, store: str) -> Any:
    if name == FieldName.PARENT:
        return None if value is None else parse_reference(str(value), store)
    if name == FieldName.PREDECESSORS:
        return LIST_SEPARATOR.join(
            f"{store}#{parse_reference(item, store)}" for item in (value or [])
        )
    return value


def edit_issue(
    session: Session,
    number: int,
    title: str | None,
    body: str | None,
    directory: Path,
) -> None:
    arguments = ["issue", "edit", str(number), "--repo", session.store]
    if title is not None:
        arguments.extend(["--title", title])
    if body is not None:
        path = write_file(directory, f"body-{number}.md", body)
        arguments.extend(["--body-file", str(path)])
    gh(session, arguments, f"edit of issue {number}")
    if title is not None:
        session.writes.append("title")
    if body is not None:
        session.writes.append("body")


def sync_blockers(session: Session, number: int, wanted: Sequence[str]) -> None:
    held = {entry["number"]: entry for entry in blocker_entries(session, number)}
    wanted_numbers = [parse_reference(reference, session.store) for reference in wanted]
    for blocker in wanted_numbers:
        if blocker not in held:
            gh(
                session,
                [
                    "api",
                    f"repos/{session.store}/issues/{number}/dependencies/blocked_by",
                    "--method",
                    "POST",
                    "-F",
                    f"issue_id={issue_id(session, blocker)}",
                ],
                f"blocker {blocker} of issue {number}",
            )
            session.writes.append(f"blocker {blocker}")
    for blocker, entry in held.items():
        if blocker not in wanted_numbers:
            gh(
                session,
                [
                    "api",
                    f"repos/{session.store}/issues/{number}/dependencies/blocked_by/{entry['id']}",
                    "--method",
                    "DELETE",
                ],
                f"blocker {blocker} of issue {number}",
            )
            session.writes.append(f"blocker {blocker} removed")


def make_transition(
    session: Session,
    move: Move,
    number: int,
    reason: str,
    *,
    target: str | None = None,
    cause: LowerCause | None = None,
    merged_into: int | None = None,
    held: bool = False,
) -> None:
    """Make one Transition through the transition function of operate-change."""
    request: dict[TransitionRequestField, Any] = {
        TransitionRequestField.TRANSITION: move.value,
        TransitionRequestField.STORE: session.store,
        TransitionRequestField.NUMBER: number,
        TransitionRequestField.MOVER: (
            Mover.AGENT if move == Move.ABANDONED else Mover.HOLDER
        ).value,
        TransitionRequestField.IDENTITY: dict(session.identity),
        TransitionRequestField.REASON: reason,
    }
    if target is not None:
        request[TransitionRequestField.TARGET] = target
    if cause is not None:
        request[TransitionRequestField.LOWER_CAUSE] = cause.value
    if merged_into is not None:
        request[TransitionRequestField.MERGED_INTO] = merged_into
    if held:
        if session.handoff is None:
            raise InvalidRequest("a held Change needs a handoff to lower")
        request[TransitionRequestField.HANDOFF] = session.handoff
    result = transition({key.value: value for key, value in request.items()})
    if result.get(TransitionResultField.STATUS) != TRANSITION_DONE:
        raise Failed(f"the {move.value} Transition did not complete: {result}")
    session.writes.append(f"transition {move.value}")


def restore_after_race(
    session: Session,
    before: Stored,
    written_body: str | None,
    directory: Path,
) -> None:
    """Read the edit history after the write; restore a revision that landed between."""
    after = read_stored(session, before.number)
    known = before.last_edit()
    ours = next(
        (index for index, edit in enumerate(after.edits) if edit.body == written_body),
        None,
    )
    if ours is None:
        return
    landed_after = after.edits[:ours]
    between: list[Edit] = []
    for edit in after.edits[ours + 1 :]:
        if edit.identifier == known:
            break
        between.append(edit)
    if between:
        edit_issue(session, before.number, None, between[0].body, directory)
        raise Failed(
            "a revision landed between the read and the write; it is restored",
            restored=True,
        )
    if landed_after:
        raise Failed("a revision landed after the write; it stands")


def intended_metadata(
    stored: Stored,
    draft: Draft,
    body_written: bool,
    lowered: str | None,
) -> dict[str, Any]:
    intended = dict(stored.metadata)
    for key in Metadata:
        if key == Metadata.HOLDER or key.value not in draft.metadata:
            continue
        if key == Metadata.BASE and not body_written:
            continue
        intended[key.value] = draft.metadata[key.value]
    if lowered is not None:
        intended[Metadata.MATURITY.value] = lowered
    return intended


def compare_readback(
    session: Session,
    number: int,
    title: str,
    body: str,
    intended: Mapping[str, Any],
) -> None:
    current = read_stored(session, number)
    mismatch: list[str] = []
    if current.title != title:
        mismatch.append(Metadata.TITLE.value)
    if current.body.rstrip("\n") != body.rstrip("\n"):
        mismatch.append(RecordField.BODY.value)
    for key in Metadata:
        if key in (Metadata.TITLE, Metadata.HOLDER) or key.value not in intended:
            continue
        expected = intended[key.value]
        observed = current.metadata.get(key.value)
        if key == Metadata.PARENT and isinstance(expected, str):
            expected = issue_reference(
                session.store, parse_reference(expected, session.store)
            )
        if key in (Metadata.BLOCKERS, Metadata.PREDECESSORS):
            expected = sorted(
                canonical(item, session.store) for item in (expected or [])
            )
            observed = sorted(
                canonical(item, session.store) for item in (observed or [])
            )
        if observed != expected:
            mismatch.append(key.value)
    if mismatch:
        raise Failed(
            "the record read back differs from the intended state", mismatch=mismatch
        )


def canonical(reference: str, store: str) -> str:
    return issue_reference(store, parse_reference(reference, store))


def publish(
    session: Session,
    number: int,
    draft: Draft,
    directory: Path,
    reframe: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    stored = read_stored(session, number)
    blockers = read_blockers(session, draft)
    check_form(session, draft, FormCheckOperation.PUBLISH, stored, blockers)
    body_changed = draft.body.rstrip("\n") != stored.body.rstrip("\n")
    stored_maturity = stored.metadata.get(Metadata.MATURITY.value)
    lowered: str | None = None
    if reframe:
        lowered = Maturity.PROPOSED.value
    elif body_changed and stored_maturity == Maturity.APPLICABLE.value:
        lowered = Maturity.SLICED.value
    latest = read_stored(session, number)
    if latest.last_edit() != stored.last_edit():
        raise Failed("the record changed since the publish read it")
    if lowered is not None:
        make_transition(
            session,
            Move.LOWER,
            number,
            reason or "the Draft's body is published over an Applicable record",
            target=lowered,
            cause=LowerCause.REFRAME if reframe else LowerCause.APPLICABLE_PUBLISH,
            held=stored.metadata.get(Metadata.HOLDER.value) is not None,
        )
    title = draft.metadata.get(Metadata.TITLE)
    title_changed = title is not None and title != stored.title
    edit_issue(
        session,
        number,
        title if title_changed else None,
        draft.body if body_changed else None,
        directory,
    )
    if body_changed:
        restore_after_race(session, stored, draft.body, directory)
    for key, name in METADATA_FIELD.items():
        if key == Metadata.MATURITY:
            continue
        if key == Metadata.BASE and not body_changed:
            continue
        if key.value not in draft.metadata:
            continue
        wanted = draft.metadata[key.value]
        if wanted == stored.metadata.get(key.value):
            continue
        if wanted is None:
            continue
        set_field(
            session, stored.node_id, name, field_value(name, wanted, session.store)
        )
    wanted_blockers = draft.metadata.get(Metadata.BLOCKERS) or []
    if sorted(canonical(item, session.store) for item in wanted_blockers) != sorted(
        stored.metadata.get(Metadata.BLOCKERS) or []
    ):
        sync_blockers(session, number, wanted_blockers)
    compare_readback(
        session,
        number,
        title or stored.title,
        draft.body if body_changed else stored.body,
        intended_metadata(stored, draft, body_changed, lowered),
    )
    return {ResultField.NUMBER: number}


def default_branch_head(session: Session) -> str:
    try:
        result = session.run(
            ["git", "-C", session.checkout_root, "rev-parse", "origin/HEAD"]
        )
    except OSError as error:
        raise Blocked("default branch head", f"git could not start: {error}") from error
    head = result.stdout.strip()
    if result.returncode != 0 or not head:
        raise Blocked("default branch head", result.stderr.strip() or "no head")
    return head


def record(
    session: Session,
    draft: Draft,
    directory: Path,
    parent_reference: str | None = None,
    operation: FormCheckOperation = FormCheckOperation.RECORD,
) -> int:
    metadata = draft.metadata
    if parent_reference is not None:
        metadata = {**metadata, Metadata.PARENT.value: parent_reference}
        draft = Draft(metadata, draft.body, render_draft(metadata, draft.body))
    blockers = read_blockers(session, draft)
    check_form(session, draft, operation, None, blockers)
    title = metadata.get(Metadata.TITLE)
    if not title:
        raise InvalidRequest("the Draft names no title")
    path = write_file(directory, "record-body.md", draft.body)
    output = gh(
        session,
        [
            "issue",
            "create",
            "--repo",
            session.store,
            "--title",
            title,
            "--body-file",
            str(path),
        ],
        "issue creation",
    )
    match = ISSUE_URL_PATTERN.match(output.strip())
    if match is None:
        raise Blocked("issue creation", "gh printed no issue URL")
    number = int(match.group(2))
    session.writes.append("create")
    created = read_stored(session, number)
    is_child = metadata.get(Metadata.PARENT.value) is not None
    leaf = DECLARATIONS_HEADING in draft.body
    wanted: dict[FieldName, Any] = {
        FieldName.PRODUCT: metadata.get(Metadata.PRODUCT.value),
        FieldName.MATURITY: Maturity.PROPOSED.value,
        FieldName.LIFECYCLE: (
            Lifecycle.AVAILABLE.value if is_child else Lifecycle.SUBMITTED.value
        ),
    }
    if is_child:
        wanted[FieldName.PARENT] = parse_reference(
            str(metadata[Metadata.PARENT.value]), session.store
        )
    if metadata.get(Metadata.PREDECESSORS.value):
        wanted[FieldName.PREDECESSORS] = field_value(
            FieldName.PREDECESSORS, metadata[Metadata.PREDECESSORS.value], session.store
        )
    if leaf:
        wanted[FieldName.BASE] = default_branch_head(session)
    for name, value in wanted.items():
        if value is not None:
            set_field(session, created.node_id, name, value)
    gh(
        session,
        [
            "issue",
            "edit",
            str(number),
            "--repo",
            session.store,
            "--add-assignee",
            RECORDER,
        ],
        "holder",
    )
    session.writes.append("holder")
    sync_blockers(session, number, metadata.get(Metadata.BLOCKERS.value) or [])
    return number


def statement_of_intent(body: str) -> str:
    start = body.find(STATEMENT_HEADING)
    end = body.find(DECLARATIONS_HEADING)
    if start < 0:
        raise InvalidRequest("the record holds no Statement of Intent")
    return body[start : end if end > start else len(body)].rstrip("\n") + "\n"


def split(
    session: Session, number: int, children: Sequence[str], directory: Path
) -> dict[str, Any]:
    stored = read_stored(session, number)
    if stored.metadata.get(Metadata.MATURITY.value) == Maturity.APPLICABLE.value:
        raise InvalidRequest("a split accepts only a Leaf below Applicable")
    if DECLARATIONS_HEADING not in stored.body:
        raise InvalidRequest("a split accepts only a Leaf")
    reference = issue_reference(session.store, number)
    created: list[int] = []
    products: list[str] = []
    for child_path in children:
        child = read_draft(child_path)
        product = child.metadata.get(Metadata.PRODUCT.value)
        if product and product not in products:
            products.append(str(product))
        created.append(
            record(
                session,
                child,
                directory,
                parent_reference=reference,
                operation=FormCheckOperation.RECORD_CHILD,
            )
        )
    edit_issue(session, number, None, statement_of_intent(stored.body), directory)
    ids = read_field_ids(session)
    base_id = ids[FieldName.BASE][0]
    gh(
        session,
        [
            "api",
            "graphql",
            "-f",
            f"query={SET_TEXT}",
            "-f",
            f"i={stored.node_id}",
            "-f",
            f"f={base_id}",
            "-f",
            "v=",
        ],
        "removal of the base",
    )
    session.writes.append("base removed")
    if products:
        set_field(
            session, stored.node_id, FieldName.PRODUCT, LIST_SEPARATOR.join(products)
        )
    return {ResultField.NUMBERS: created}


def draft_from_store(session: Session, number: int, destination: str) -> dict[str, Any]:
    stored = read_stored(session, number)
    metadata = {
        key: value for key, value in stored.metadata.items() if key != Metadata.HOLDER
    }
    Path(destination).write_text(render_draft(metadata, stored.body), encoding="utf-8")
    return {ResultField.NUMBER: number}


def merge(
    session: Session, survivor: int, absorbed: int, reason: str
) -> dict[str, Any]:
    kept = read_stored(session, survivor)
    predecessors = list(kept.metadata.get(Metadata.PREDECESSORS.value) or [])
    entry = issue_reference(session.store, absorbed)
    if entry not in predecessors:
        predecessors.append(entry)
    set_field(
        session,
        kept.node_id,
        FieldName.PREDECESSORS,
        LIST_SEPARATOR.join(
            f"{session.store}#{parse_reference(item, session.store)}"
            for item in predecessors
        ),
    )
    make_transition(session, Move.ABANDONED, absorbed, reason, merged_into=survivor)
    return {ResultField.NUMBER: survivor}


def required(request: Mapping[str, Any], key: RequestField) -> Any:
    value = request.get(key.value)
    if value is None:
        raise InvalidRequest(f"the request carries no {key.value}")
    return value


def execute(request: Mapping[str, Any], run: CommandRunner) -> dict[str, Any]:
    store = str(required(request, RequestField.STORE))
    if not STORE_PATTERN.match(store):
        raise InvalidRequest(f"{store} is no Change store")
    try:
        operation = Operation(required(request, RequestField.OPERATION))
    except ValueError as error:
        raise InvalidRequest(str(error)) from error
    session = Session(
        store=store,
        run=run,
        identity=request.get(RequestField.IDENTITY.value) or {},
        checkout_root=str(required(request, RequestField.CHECKOUT_ROOT)),
        size_limit=int(
            request.get(RequestField.SIZE_LIMIT.value) or DEFAULT_SIZE_LIMIT
        ),
        handoff=request.get(RequestField.HANDOFF.value),
    )
    with tempfile.TemporaryDirectory() as scratch:
        directory = Path(scratch)
        try:
            outcome = dispatch(operation, request, session, directory)
        except Failed as failure:
            return failure_result(failure, session)
    return {
        ResultField.STATUS: Status.OK,
        ResultField.WRITES: session.writes,
        **outcome,
    }


def dispatch(
    operation: Operation,
    request: Mapping[str, Any],
    session: Session,
    directory: Path,
) -> dict[str, Any]:
    reason = str(request.get(RequestField.REASON.value) or "")
    if operation == Operation.PUBLISH:
        draft = read_draft(str(required(request, RequestField.DRAFT_PATH)))
        return publish(
            session, int(required(request, RequestField.NUMBER)), draft, directory
        )
    if operation == Operation.REFRAME:
        draft = read_draft(str(required(request, RequestField.DRAFT_PATH)))
        return publish(
            session,
            int(required(request, RequestField.NUMBER)),
            draft,
            directory,
            reframe=True,
            reason=reason or "reframe",
        )
    if operation == Operation.RECORD:
        draft = read_draft(str(required(request, RequestField.DRAFT_PATH)))
        return {ResultField.NUMBER: record(session, draft, directory)}
    if operation == Operation.SPLIT:
        return split(
            session,
            int(required(request, RequestField.NUMBER)),
            list(required(request, RequestField.CHILDREN)),
            directory,
        )
    if operation == Operation.DRAFT:
        return draft_from_store(
            session,
            int(required(request, RequestField.NUMBER)),
            str(required(request, RequestField.DRAFT_PATH)),
        )
    return merge(
        session,
        int(required(request, RequestField.NUMBER)),
        int(required(request, RequestField.ABSORBED)),
        reason or "merged into the survivor",
    )


def failure_result(failure: Failed, session: Session) -> dict[str, Any]:
    result: dict[str, Any] = {
        ResultField.STATUS: Status.FAILED,
        ResultField.DETAIL: failure.detail,
        ResultField.WRITES: session.writes,
    }
    if failure.findings:
        result[ResultField.FINDINGS] = failure.findings
    if failure.mismatch:
        result[ResultField.MISMATCH] = failure.mismatch
    if failure.restored:
        result[ResultField.RESTORED] = True
    return result


EXIT_CODES: Final = {
    Status.OK: EXIT_OK,
    Status.FAILED: EXIT_FAILED,
    Status.INVALID_REQUEST: EXIT_INVALID_REQUEST,
    Status.BLOCKED: EXIT_BLOCKED,
}


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    run: CommandRunner = subprocess_runner,
) -> int:
    source = stdin if stdin is not None else sys.stdin
    sink = stdout if stdout is not None else sys.stdout
    try:
        request = json.loads(source.read())
        if not isinstance(request, dict):
            raise InvalidRequest("the request is no JSON object")
        result = execute(request, run)
    except json.JSONDecodeError as error:
        result = {
            ResultField.STATUS: Status.INVALID_REQUEST,
            ResultField.DETAIL: f"the request is no JSON: {error}",
        }
    except InvalidRequest as error:
        result = {
            ResultField.STATUS: Status.INVALID_REQUEST,
            ResultField.DETAIL: str(error),
        }
    except Blocked as error:
        result = {
            ResultField.STATUS: Status.BLOCKED,
            ResultField.READ: error.read,
            ResultField.DETAIL: error.detail,
        }
    sink.write(json.dumps({str(key): value for key, value in result.items()}) + "\n")
    return EXIT_CODES[Status(result[ResultField.STATUS])]


if __name__ == "__main__":
    sys.exit(main())
