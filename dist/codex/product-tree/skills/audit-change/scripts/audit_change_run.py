"""Command boundary for one audit of a Change record.

The runner reads one JSON request object on stdin, performs the requested read
or ``spx verification run`` operation from the Product's checkout root, and
writes one JSON result object on stdout. It writes no file: the SPX run journal
is the only state that persists between requests, and every request names the
Change by its store identity and the run token it acts on.

Every invocation writes exactly one result, and every result carries
``operation`` and ``status``. ``operation`` is the listed operation the request
names, or ``null`` when it names none. An ``ok`` result carries the operation's
values; a ``blocked`` result carries the reason, a detail line, and a run token:
the token of the run ``start`` created when ``start`` blocks after reading it,
otherwise the ``runToken`` string the request carries, otherwise
``not-started``. A failed command adds its exact command line, payload source,
payload key, exit code, and stderr. A filesystem, encoding, or decoding error
ends the request with a declared ``BlockReason``, never with a traceback.

``validate_request`` checks one parsed request completely before any process
starts: the field set ``REQUIRED_FIELDS`` declares for its operation, then each
field's form in the order ``_REQUEST_CHECKS`` lists. It raises ``Blocked`` with
``invalid-request``, or with ``path-rejected`` for a path that no git call can
accept.

The Change is read from the store, never from a file. ``read-record`` returns
the Change Draft the runner assembles from the stored record, which is the
record's metadata except its holder, as YAML front matter, followed by its
body, with the SHA-256 of the body and the Base the record names. ``start``
retains that Draft as the run's input, and ``reconcile`` and ``finish`` block
with ``record-changed`` when the stored body or the stored Base differs from the
retained pair, so a run judges one body at one Base.

``form-check`` passes the Draft to the one check function of the change-standards
skill, reached by a ``__file__``-relative import, with the operation ``audit``,
and returns each finding the check makes. ``format-at-close`` runs the
Product's format command, given as an argument vector that reads the text on
stdin and writes it on stdout, over each replacement the record declares, and
returns one finding for each of its three comparisons that fails. Neither
operation writes.

``read-authority`` and ``read-relations`` start ``gh`` and read the store within
the page bound ``AUTHORITY_MAX_PAGES``; a connection that keeps reporting a
further page blocks with ``page-bound-reached`` naming the bound.

Every operation that reads a repository takes the Product's checkout root as
``root``, an absolute path, and runs its ``git`` and ``spx`` commands with that
root as the working directory. A request without ``root``, or one whose
``root`` is no repository checkout root, blocks naming it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import shlex
import string
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Final, Protocol, TextIO


class Operation(StrEnum):
    """Requests the runner accepts, one per invocation."""

    TOOL_VERSION = "tool-version"
    READ_RECORD = "read-record"
    READ_AT_BASE = "read-at-base"
    START = "start"
    ADD_SCOPE = "add-scope"
    ADD_FINDING = "add-finding"
    RECONCILE = "reconcile"
    FINISH = "finish"
    FORM_CHECK = "form-check"
    FORMAT_AT_CLOSE = "format-at-close"
    READ_AUTHORITY = "read-authority"
    READ_RELATIONS = "read-relations"


class RequestField(StrEnum):
    """Fields of a request object."""

    OPERATION = "operation"
    ISSUE = "issue"
    ROOT = "root"
    BODY_SHA256 = "bodySha256"
    BASE = "base"
    PATH = "path"
    RUN_TOKEN = "runToken"
    PAYLOAD = "payload"
    TERMINAL_STATUS = "terminalStatus"
    MERGE_COMMIT = "mergeCommit"
    FORMAT_COMMAND = "formatCommand"


class ResultField(StrEnum):
    """Fields of a result object."""

    OPERATION = "operation"
    STATUS = "status"
    REASON = "reason"
    DETAIL = "detail"
    RUN_TOKEN = "runToken"
    ISSUE = "issue"
    DRAFT = "draft"
    BODY_SHA256 = "bodySha256"
    BASE = "base"
    BLOCKERS = "blockers"
    REFERENCE = "reference"
    STATE = "state"
    PATH = "path"
    KIND = "kind"
    CONTENT = "content"
    ENTRIES = "entries"
    TOOL_VERSION = "toolVersion"
    IDEMPOTENCY_KEY = "idempotencyKey"
    SEQUENCE = "sequence"
    IDEMPOTENT = "idempotent"
    RUN_STATUS = "runStatus"
    SCOPE_UNITS = "scopeUnits"
    FINDINGS = "findings"
    RUN = "run"
    RENDER_COMMAND = "renderCommand"
    COMMAND = "command"
    PAYLOAD_SOURCE = "payloadSource"
    PAYLOAD_KEY = "payloadKey"
    EXIT_CODE = "exitCode"
    STDERR = "stderr"
    RETAINED_SHA256 = "retainedSha256"
    LIVE_SHA256 = "liveSha256"
    RETAINED_BASE = "retainedBase"
    LIVE_BASE = "liveBase"
    EVENTS = "events"
    BOUND = "bound"
    CREATED_AT = "createdAt"
    ACTOR = "actor"
    FIELD = "field"
    PREVIOUS_VALUE = "previousValue"
    NEW_VALUE = "newValue"
    PRODUCT = "product"
    PARENT = "parent"
    CHILDREN = "children"
    NUMBER = "number"
    CHECK_STATUS = "checkStatus"
    RULE = "rule"
    WHERE = "where"


class ResultStatus(StrEnum):
    """Outcome of one request."""

    OK = "ok"
    BLOCKED = "blocked"


class BlockReason(StrEnum):
    """Why a request stopped without its operation's values."""

    INVALID_REQUEST = "invalid-request"
    PATH_REJECTED = "path-rejected"
    RECORD_MISSING = "record-missing"
    RECORD_CHANGED = "record-changed"
    RETAINED_INPUT_MISMATCH = "retained-input-mismatch"
    BASE_UNRESOLVED = "base-unresolved"
    COMMAND_FAILED = "command-failed"
    UNREADABLE_OUTPUT = "unreadable-output"
    PAGE_BOUND_REACHED = "page-bound-reached"
    FORM_CHECK_UNAVAILABLE = "form-check-unavailable"
    FORM_CHECK_REJECTED = "form-check-rejected"
    FORMAT_COMMAND_UNUSABLE = "format-command-unusable"


class TerminalStatus(StrEnum):
    """Terminal statuses the audit may record."""

    APPROVED = "approved"
    REJECTED = "rejected"


class AuthorityRead(StrEnum):
    """The store connection ``read-authority`` reads."""

    EVENTS = "events"


class BaseKind(StrEnum):
    """What a path names at the Base."""

    FILE = "file"
    DIRECTORY = "directory"
    MISSING = "missing"


class FormatRule(StrEnum):
    """Rule slugs of the three comparisons ``format-at-close`` makes."""

    BASE_FORMATTER = "format-base"
    MERGE_FORMATTER = "format-merge"
    DEFAULT_BRANCH = "default-branch-differs"


class ExitCode(IntEnum):
    """Process exit status for each result status."""

    OK = 0
    BLOCKED = 1
    INVALID_REQUEST = 2


class SpxField(StrEnum):
    """Fields of the ``spx verification run`` output the runner reads."""

    RUN_TOKEN = "runToken"
    LOCATOR = "locator"
    CONTENT = "content"
    SEQUENCE = "sequence"
    IDEMPOTENT = "idempotent"
    AUDIT_SCOPE_UNITS = "auditScopeUnits"
    EVENTS = "events"
    FINDINGS = "findings"
    SEQ = "seq"
    PAYLOAD = "payload"
    UNIT_ID = "unitId"
    PARENT_UNIT_ID = "parentUnitId"
    SUBJECT = "subject"
    COVERAGE_STATUS = "coverageStatus"
    RULE = "rule"
    SEVERITY = "severity"


class StoreField(StrEnum):
    """Fields of the store's GraphQL answer that the runner reads."""

    DATA = "data"
    REPOSITORY = "repository"
    ISSUE = "issue"
    TIMELINE_ITEMS = "timelineItems"
    PAGE_INFO = "pageInfo"
    HAS_NEXT_PAGE = "hasNextPage"
    END_CURSOR = "endCursor"
    NODES = "nodes"
    CREATED_AT = "createdAt"
    ACTOR = "actor"
    LOGIN = "login"
    PREVIOUS_VALUE = "previousValue"
    NEW_VALUE = "newValue"
    ISSUE_FIELD = "issueField"
    NAME = "name"
    BODY = "body"
    TITLE = "title"
    STATE = "state"
    NUMBER = "number"
    VALUE = "value"
    FIELD = "field"
    ISSUES = "issues"
    ISSUE_FIELD_VALUES = "issueFieldValues"
    ASSIGNEES = "assignees"
    BLOCKED_BY = "blockedBy"
    NAME_WITH_OWNER = "nameWithOwner"


class MetadataKey(StrEnum):
    """The metadata keys of a Change record, in the order a Draft writes them."""

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


#: The store's issue field behind each metadata key that a field holds.
FIELD_NAMES: Final[Mapping[MetadataKey, str]] = {
    MetadataKey.PRODUCT: "Product",
    MetadataKey.MATURITY: "Maturity",
    MetadataKey.LIFECYCLE: "Lifecycle",
    MetadataKey.PARENT: "Parent",
    MetadataKey.PREDECESSORS: "Predecessors",
    MetadataKey.BASE: "Base",
    MetadataKey.PRIORITY: "Priority",
    MetadataKey.PRIMARY_VALUE: "Value",
    MetadataKey.INVESTMENT: "Investment",
}
#: The keys a Change Draft writes: the record's metadata except its holder.
DRAFT_KEYS: Final = tuple(key for key in MetadataKey if key is not MetadataKey.HOLDER)

NOT_STARTED: Final = "not-started"
NOT_APPLICABLE: Final = "none"
NUL: Final = "\x00"
TEXT_ENCODING: Final = "utf-8"
PAYLOAD_FROM_STDIN: Final = "stdin"
IDEMPOTENCY_KEY_SEPARATOR: Final = ":"
RULE_ID_ALPHABET: Final = string.ascii_lowercase + string.digits
RULE_ID_SEPARATOR: Final = "-"
_RULE_ID_RUN: Final = f"[{re.escape(RULE_ID_ALPHABET)}]+"
RULE_ID_PATTERN: Final = re.compile(
    f"{_RULE_ID_RUN}(?:{re.escape(RULE_ID_SEPARATOR)}{_RULE_ID_RUN})*"
)
COMMIT_PATTERN: Final = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}")
VERIFICATION_TYPE: Final = "audit"
SCOPE_TYPE: Final = "file"
FORM_CHECK_OPERATION: Final = "audit"
FORM_CHECK_SIZE_LIMIT: Final = "github"
PATH_PLACEHOLDER: Final = "{path}"

#: Rendered-projection fields that hold evidence rather than run-level values.
EVIDENCE_FIELDS: Final = frozenset(
    {SpxField.EVENTS, SpxField.AUDIT_SCOPE_UNITS, SpxField.FINDINGS}
)

SPX_EXECUTABLE: Final = "spx"
GIT_EXECUTABLE: Final = "git"
_GIT_TOPLEVEL: Final = (GIT_EXECUTABLE, "rev-parse", "--show-toplevel")
_GIT_DEFAULT_BRANCH: Final = (
    GIT_EXECUTABLE,
    "symbolic-ref",
    "--short",
    "refs/remotes/origin/HEAD",
)
_SPX_VERSION: Final = (SPX_EXECUTABLE, "--version")
_RUN_COMMAND: Final = (SPX_EXECUTABLE, "verification", "run")
GH_EXECUTABLE: Final = "gh"
_GRAPHQL: Final = (
    GH_EXECUTABLE,
    "api",
    "graphql",
    "-H",
    "GraphQL-Features: issue_fields",
)

#: One store read takes pages of this many entries, at most this many pages.
AUTHORITY_PAGE_SIZE: Final = 100
AUTHORITY_MAX_PAGES: Final = 10
ISSUE_FIELD_VALUES_PAGE_SIZE: Final = 50
BLOCKERS_PAGE_SIZE: Final = 100

_QUERY_HEAD: Final = (
    "query($o:String!,$r:String!,$n:Int!,$after:String)"
    "{repository(owner:$o,name:$r){issue(number:$n){"
)
_AUTHORITY_QUERIES: Final[Mapping[AuthorityRead, str]] = {
    AuthorityRead.EVENTS: (
        f"{_QUERY_HEAD}{StoreField.TIMELINE_ITEMS}"
        f"(first:{AUTHORITY_PAGE_SIZE},after:$after,"
        "itemTypes:[ISSUE_FIELD_CHANGED_EVENT])"
        "{pageInfo{hasNextPage endCursor} nodes{... on IssueFieldChangedEvent"
        "{createdAt actor{login} previousValue newValue issueField"
        "{... on IssueFieldSingleSelect{name} ... on IssueFieldText{name}}}}}}}}"
    ),
}
_AUTHORITY_CONNECTIONS: Final[Mapping[AuthorityRead, StoreField]] = {
    AuthorityRead.EVENTS: StoreField.TIMELINE_ITEMS,
}
_FIELD_VALUES_SELECTION: Final = (
    f"issueFieldValues(first:{ISSUE_FIELD_VALUES_PAGE_SIZE})"
    "{pageInfo{hasNextPage} nodes{"
    "... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}"
    " ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}}"
    " ... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect"
    "{name}}}}}"
)
_RECORD_QUERY: Final = (
    "query($o:String!,$r:String!,$n:Int!)"
    "{repository(owner:$o,name:$r){issue(number:$n){...P "
    f"blockedBy(first:{BLOCKERS_PAGE_SIZE})"
    "{pageInfo{hasNextPage} nodes{...P}}}}} "
    "fragment P on Issue{number title body state repository{nameWithOwner} "
    "assignees(first:2){nodes{login}} "
    f"{_FIELD_VALUES_SELECTION}"
    "}"
)
_RELATIONS_QUERY: Final = (
    "query($o:String!,$r:String!,$after:String)"
    f"{{repository(owner:$o,name:$r){{{StoreField.ISSUES}"
    f"(first:{AUTHORITY_PAGE_SIZE},after:$after)"
    "{pageInfo{hasNextPage endCursor} nodes{number "
    f"{_FIELD_VALUES_SELECTION}"
    "}}}}"
)
PRODUCT_FIELD: Final = FIELD_NAMES[MetadataKey.PRODUCT]
PARENT_FIELD: Final = FIELD_NAMES[MetadataKey.PARENT]
PREDECESSOR_SEPARATOR: Final = ", "
ISSUE_IDENTITY_PATTERN: Final = re.compile(
    r"([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+)#([1-9][0-9]*)"
)
ISSUE_URL_TEMPLATE: Final = "https://github.com/{owner}/{repository}/issues/{number}"

#: The fields each operation's request carries besides ``operation``.
REQUIRED_FIELDS: Final[Mapping[Operation, frozenset[RequestField]]] = {
    Operation.TOOL_VERSION: frozenset(),
    Operation.READ_RECORD: frozenset({RequestField.ISSUE, RequestField.ROOT}),
    Operation.READ_AT_BASE: frozenset(
        {RequestField.ROOT, RequestField.BASE, RequestField.PATH}
    ),
    Operation.START: frozenset(
        {
            RequestField.ISSUE,
            RequestField.ROOT,
            RequestField.BODY_SHA256,
            RequestField.BASE,
        }
    ),
    Operation.ADD_SCOPE: frozenset(
        {
            RequestField.ISSUE,
            RequestField.ROOT,
            RequestField.RUN_TOKEN,
            RequestField.PAYLOAD,
        }
    ),
    Operation.ADD_FINDING: frozenset(
        {
            RequestField.ISSUE,
            RequestField.ROOT,
            RequestField.RUN_TOKEN,
            RequestField.PAYLOAD,
        }
    ),
    Operation.RECONCILE: frozenset(
        {RequestField.ISSUE, RequestField.ROOT, RequestField.RUN_TOKEN}
    ),
    Operation.FINISH: frozenset(
        {
            RequestField.ISSUE,
            RequestField.ROOT,
            RequestField.RUN_TOKEN,
            RequestField.TERMINAL_STATUS,
        }
    ),
    Operation.FORM_CHECK: frozenset({RequestField.ISSUE, RequestField.ROOT}),
    Operation.FORMAT_AT_CLOSE: frozenset(
        {
            RequestField.ISSUE,
            RequestField.ROOT,
            RequestField.MERGE_COMMIT,
            RequestField.FORMAT_COMMAND,
        }
    ),
    Operation.READ_AUTHORITY: frozenset({RequestField.ISSUE}),
    Operation.READ_RELATIONS: frozenset({RequestField.ISSUE}),
}


@dataclass(frozen=True)
class CommandResult:
    """What one external command produced."""

    exit_code: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    """Execute one external command through an injectable process boundary."""

    def __call__(
        self, argv: Sequence[str], /, *, cwd: pathlib.Path, stdin: str | None
    ) -> CommandResult: ...


def run_subprocess(
    argv: Sequence[str], /, *, cwd: pathlib.Path, stdin: str | None
) -> CommandResult:
    """Run ``argv`` without a shell and capture its output.

    Standard output must be UTF-8 when the command succeeds; otherwise this
    raises ``UnicodeDecodeError``. Standard error, and the standard output of a
    failed command, decode with every undecodable byte escaped.
    """
    completed = subprocess.run(  # noqa: S603
        list(argv),
        cwd=cwd,
        input=None if stdin is None else stdin.encode(TEXT_ENCODING),
        stdin=subprocess.DEVNULL if stdin is None else None,
        capture_output=True,
        check=False,
    )
    stdout_errors = "strict" if completed.returncode == 0 else "backslashreplace"
    return CommandResult(
        completed.returncode,
        completed.stdout.decode(TEXT_ENCODING, stdout_errors),
        completed.stderr.decode(TEXT_ENCODING, "backslashreplace"),
    )


_RENDER_HINT: Final = (
    "; rerun the run's render command by hand and confirm the installed spx "
    "version prints the rendered projection"
)
_STORE_HINT: Final = (
    "; rerun the store query by hand and confirm gh is authenticated for the "
    "store's repository"
)
_BOUND_HINT: Final = (
    "; the runner reads no further, so report this block rather than judge the "
    "unread part"
)


class Blocked(Exception):
    """A request stops with a reason and the evidence that explains it.

    ``run_token`` names a run the request itself does not name: ``start`` sets
    it once SPX has created the run. A block that leaves it unset carries the
    request's own run token, which ``execute`` supplies.
    """

    def __init__(
        self,
        reason: BlockReason,
        detail: str,
        *,
        run_token: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.run_token = run_token
        self.evidence = dict(evidence or {})


@dataclass(frozen=True)
class _Context:
    runner: CommandRunner
    cwd: pathlib.Path


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode(TEXT_ENCODING)).hexdigest()


def _system_text_defect(text: str) -> str | None:
    """Name why ``text`` cannot reach a git call or an argument vector."""
    if NUL in text:
        return "contains a NUL character"
    try:
        text.encode(TEXT_ENCODING)
    except UnicodeEncodeError:
        return "contains text that has no UTF-8 encoding"
    return None


def _command(
    context: _Context,
    argv: Sequence[str],
    *,
    cwd: pathlib.Path,
    run_token: str | None = None,
    stdin: str | None = None,
    payload_key: str = NOT_APPLICABLE,
) -> str:
    """Run one command and return its stdout, or block with its diagnostic."""
    evidence: dict[str, object] = {
        ResultField.COMMAND: shlex.join(argv),
        ResultField.PAYLOAD_SOURCE: NOT_APPLICABLE
        if stdin is None
        else PAYLOAD_FROM_STDIN,
        ResultField.PAYLOAD_KEY: payload_key,
    }
    try:
        result = context.runner(argv, cwd=cwd, stdin=stdin)
    except UnicodeDecodeError as exc:
        evidence[ResultField.EXIT_CODE] = NOT_APPLICABLE
        evidence[ResultField.STDERR] = str(exc)
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"{argv[0]} printed output that is not UTF-8; rerun the command in this result's command field by hand and confirm the installed tool prints UTF-8 text",
            run_token=run_token,
            evidence=evidence,
        ) from exc
    except (OSError, ValueError) as exc:
        evidence[ResultField.EXIT_CODE] = NOT_APPLICABLE
        evidence[ResultField.STDERR] = str(exc)
        raise Blocked(
            BlockReason.COMMAND_FAILED,
            f"{argv[0]} could not be executed; confirm {argv[0]} is installed and on PATH, then repeat the request",
            run_token=run_token,
            evidence=evidence,
        ) from exc
    if result.exit_code != 0:
        evidence[ResultField.EXIT_CODE] = result.exit_code
        evidence[ResultField.STDERR] = result.stderr
        raise Blocked(
            BlockReason.COMMAND_FAILED,
            f"{argv[0]} exited {result.exit_code}; the stderr and command fields of this result show the failure, so rerun that command by hand to reproduce it before repeating the request",
            run_token=run_token,
            evidence=evidence,
        )
    return result.stdout


def _probe(
    context: _Context, argv: Sequence[str], *, cwd: pathlib.Path
) -> CommandResult:
    """Run one command whose nonzero exit is an answer, blocking only when it cannot run."""
    try:
        return context.runner(argv, cwd=cwd, stdin=None)
    except UnicodeDecodeError as exc:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"{argv[0]} printed output that is not UTF-8; rerun `{shlex.join(argv)}` by hand and confirm the installed tool prints UTF-8 text",
        ) from exc
    except (OSError, ValueError) as exc:
        raise Blocked(
            BlockReason.COMMAND_FAILED,
            f"{argv[0]} could not be executed; confirm {argv[0]} is installed and on PATH, then repeat the request",
            evidence={
                ResultField.COMMAND: shlex.join(argv),
                ResultField.PAYLOAD_SOURCE: NOT_APPLICABLE,
                ResultField.PAYLOAD_KEY: NOT_APPLICABLE,
                ResultField.EXIT_CODE: NOT_APPLICABLE,
                ResultField.STDERR: str(exc),
            },
        ) from exc


def _json_lines(
    stdout: str, *, argv: Sequence[str], run_token: str | None = None
) -> list[dict[str, object]]:
    """Parse every non-empty stdout line as one JSON object.

    ``argv`` names the command that printed ``stdout`` so a block can say which
    command to rerun by hand.
    """
    command = " ".join(argv)
    objects: list[dict[str, object]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed a line that is not JSON ({exc.msg}); "
                "run it by hand and confirm the installed tool prints one JSON "
                "object per line",
                run_token=run_token,
            ) from exc
        except ValueError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed output that cannot be parsed ({exc}); "
                "run it by hand and confirm it prints one JSON object per line",
                run_token=run_token,
            ) from exc
        except RecursionError as exc:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed JSON nested too deeply to parse; "
                "run it by hand and confirm the installed tool version",
                run_token=run_token,
            ) from exc
        if not isinstance(value, dict):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"`{command}` printed a JSON {type(value).__name__} line "
                "where an object is required; run it by hand and confirm "
                "the installed tool version",
                run_token=run_token,
            )
        objects.append(value)
    if not objects:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{command}` printed no JSON; run it by hand and confirm it "
            "exits with output on stdout",
            run_token=run_token,
        )
    return objects


def _repository_root(context: _Context) -> pathlib.Path:
    stdout = _command(context, _GIT_TOPLEVEL, cwd=context.cwd).strip()
    if not stdout:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{' '.join(_GIT_TOPLEVEL)}` printed no repository root in "
            f"{context.cwd}; run the request from inside a git worktree",
        )
    return pathlib.Path(stdout)


def _received(request: Mapping[str, object], field_name: RequestField) -> str:
    """Describe the value a request carries for ``field_name``."""
    if field_name not in request:
        return "no value"
    return f"a {type(request[field_name]).__name__}"


def _string(request: Mapping[str, object], field_name: RequestField) -> str:
    value = request.get(field_name)
    if not isinstance(value, str) or not value:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request field {field_name.value} must be a non-empty JSON string, "
            f"received {_received(request, field_name)}; set it to a non-empty string",
        )
    return value


def _repository_path(request: Mapping[str, object]) -> str:
    """Accept only a normalized repository-relative POSIX path."""
    value = _string(request, RequestField.PATH)
    defect = _system_text_defect(value)
    if defect is not None:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path {defect}: {value!r}; pass a repository-relative path of printable UTF-8 text",
        )
    pure = pathlib.PurePosixPath(value)
    if pure.is_absolute():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path is absolute: {value}; pass the repository-relative form, "
            f"such as {value.lstrip('/')!r}",
        )
    if ".." in pure.parts:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path traverses a parent: {value}; pass a path that stays "
            "inside the repository, with no `..` segment",
        )
    if str(pure) != value or pure.parts in ((), (".",)):
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"path is not normalized: {value}; pass the normalized form "
            f"{str(pure)!r}, with no empty, `.`, or repeated-slash segment",
        )
    return value


def _checkout_root(request: Mapping[str, object]) -> pathlib.Path:
    """Return the Product's checkout root a request names, an absolute path."""
    named = _string(request, RequestField.ROOT)
    defect = _system_text_defect(named)
    if defect is not None:
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root {defect}: {named!r}; pass the absolute path of the Product's checkout root",
        )
    root = pathlib.PurePosixPath(named)
    if not root.is_absolute():
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request field {RequestField.ROOT.value} must be an absolute path, received {named!r}; pass the absolute path of the Product's checkout root",
        )
    return pathlib.Path(named)


def _commit(request: Mapping[str, object], field_name: RequestField) -> str:
    value = _string(request, field_name)
    if not COMMIT_PATTERN.fullmatch(value):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request field {field_name.value} must be a full 40-character lowercase hexadecimal commit id, received {value!r}; pass the commit id as the store holds it",
        )
    return value


def _base(request: Mapping[str, object]) -> str:
    return _commit(request, RequestField.BASE)


def _merge_commit(request: Mapping[str, object]) -> str:
    return _commit(request, RequestField.MERGE_COMMIT)


def _body_sha256(request: Mapping[str, object]) -> str:
    value = _string(request, RequestField.BODY_SHA256)
    if not SHA256_PATTERN.fullmatch(value):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request field {RequestField.BODY_SHA256.value} must be a 64-character lowercase hexadecimal SHA-256, received {value!r}; pass the bodySha256 that read-record returned",
        )
    return value


def _run_token(request: Mapping[str, object]) -> str:
    token = _string(request, RequestField.RUN_TOKEN)
    defect = _system_text_defect(token)
    if defect is not None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.RUN_TOKEN} {defect}; pass the runToken string that start returned",
        )
    return token


def _unit_id(request: Mapping[str, object]) -> str:
    payload = request.get(RequestField.PAYLOAD)
    unit_id = payload.get(SpxField.UNIT_ID) if isinstance(payload, dict) else None
    if not isinstance(unit_id, str) or not unit_id:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload must be an object with a non-empty {SpxField.UNIT_ID}; set payload.{SpxField.UNIT_ID} to the scope unit's id string",
        )
    defect = _system_text_defect(unit_id)
    if defect is not None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload {SpxField.UNIT_ID} {defect}; pass the unit id as printable UTF-8 text",
        )
    return unit_id


def _finding_rule(request: Mapping[str, object]) -> str:
    payload = request.get(RequestField.PAYLOAD)
    rule = payload.get(SpxField.RULE) if isinstance(payload, dict) else None
    if not isinstance(rule, str) or not RULE_ID_PATTERN.fullmatch(rule):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"payload {SpxField.RULE} must match {RULE_ID_PATTERN.pattern}, received {rule!r}; pass the finding's catalog rule identifier",
        )
    return rule


def _payload_text(request: Mapping[str, object]) -> str:
    try:
        return json.dumps(request.get(RequestField.PAYLOAD), separators=(",", ":"))
    except RecursionError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            "payload nests too deeply to serialize; flatten it to the fields its record declares",
        ) from exc


def _terminal_status(request: Mapping[str, object]) -> TerminalStatus:
    terminal = _string(request, RequestField.TERMINAL_STATUS)
    if terminal not in {status.value for status in TerminalStatus}:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.TERMINAL_STATUS} must be one of {', '.join(TerminalStatus)}, received {terminal!r}; pass one of those values",
        )
    return TerminalStatus(terminal)


def _issue_identity(request: Mapping[str, object]) -> tuple[str, str, str]:
    """Return ``(owner, repository, number)`` of the canonical issue identity."""
    named = request.get(RequestField.ISSUE)
    found = ISSUE_IDENTITY_PATTERN.fullmatch(named) if isinstance(named, str) else None
    if found is None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.ISSUE} must match {ISSUE_IDENTITY_PATTERN.pattern}, received {named!r}; write the issue as owner/repository#number, such as acme/changes#12",
        )
    owner, repository, number = found.groups()
    return owner, repository, number


def _format_command(request: Mapping[str, object]) -> list[str]:
    command = request.get(RequestField.FORMAT_COMMAND)
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(part, str) and part for part in command)
    ):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request field {RequestField.FORMAT_COMMAND.value} must be a non-empty array of non-empty strings, received {_received(request, RequestField.FORMAT_COMMAND)}; pass the Product's format command as an argument vector that reads the text on stdin and writes it on stdout",
        )
    for part in command:
        defect = _system_text_defect(part)
        if defect is not None:
            raise Blocked(
                BlockReason.INVALID_REQUEST,
                f"request field {RequestField.FORMAT_COMMAND.value} holds an element that {defect}; pass printable UTF-8 text",
            )
    return list(command)


#: The field checks ``validate_request`` applies to each operation, in order.
_REQUEST_CHECKS: Final[
    Mapping[Operation, tuple[Callable[[Mapping[str, object]], object], ...]]
] = {
    Operation.TOOL_VERSION: (),
    Operation.READ_RECORD: (_issue_identity, _checkout_root),
    Operation.READ_AT_BASE: (_checkout_root, _base, _repository_path),
    Operation.START: (_issue_identity, _checkout_root, _body_sha256, _base),
    Operation.ADD_SCOPE: (
        _issue_identity,
        _checkout_root,
        _run_token,
        _unit_id,
        _payload_text,
    ),
    Operation.ADD_FINDING: (
        _issue_identity,
        _checkout_root,
        _run_token,
        _unit_id,
        _finding_rule,
        _payload_text,
    ),
    Operation.RECONCILE: (_issue_identity, _checkout_root, _run_token),
    Operation.FINISH: (_issue_identity, _checkout_root, _run_token, _terminal_status),
    Operation.FORM_CHECK: (_issue_identity, _checkout_root),
    Operation.FORMAT_AT_CLOSE: (
        _issue_identity,
        _checkout_root,
        _merge_commit,
        _format_command,
    ),
    Operation.READ_AUTHORITY: (_issue_identity,),
    Operation.READ_RELATIONS: (_issue_identity,),
}


def _named_operation(request: Mapping[str, object]) -> Operation | None:
    name = request.get(RequestField.OPERATION)
    if isinstance(name, str) and name in {operation.value for operation in Operation}:
        return Operation(name)
    return None


def validate_request(request: Mapping[str, object]) -> Operation:
    """Return the operation of a well-formed request, or raise ``Blocked``.

    A request is well-formed when it names one listed operation, carries
    exactly that operation's ``REQUIRED_FIELDS`` besides ``operation``, and
    every field passes its check. The first failing check decides the reason:
    ``path-rejected`` for a path no git call accepts, ``invalid-request``
    for every other defect. No check starts a process or reads a file.
    """
    operation = _named_operation(request)
    if operation is None:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{RequestField.OPERATION} must be one of {', '.join(Operation)}, received {request.get(RequestField.OPERATION)!r}; name one of those operations",
        )
    allowed = REQUIRED_FIELDS[operation] | {RequestField.OPERATION}
    missing = sorted(name.value for name in allowed if name not in request)
    unexpected = sorted(str(name) for name in request if name not in allowed)
    if missing or unexpected:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"{operation} request fields: missing {missing}, unexpected {unexpected}; send exactly {sorted(str(name) for name in allowed)}",
        )
    for check in _REQUEST_CHECKS[operation]:
        check(request)
    return operation


def _product_root(context: _Context, named: pathlib.Path) -> pathlib.Path:
    """Return the repository checkout root ``named`` names, or block naming it."""
    if not named.is_dir():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root is not a directory: {named}; pass the absolute path of the Product's checkout root",
        )
    try:
        top = _repository_root(_Context(runner=context.runner, cwd=named))
    except Blocked as exc:
        if (
            exc.reason is BlockReason.COMMAND_FAILED
            and exc.evidence.get(ResultField.EXIT_CODE) == NOT_APPLICABLE
        ):
            raise
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root is no repository checkout: {named}; pass the absolute path of the directory that holds the Product's checkout",
        ) from exc
    if top.resolve() != named.resolve():
        raise Blocked(
            BlockReason.PATH_REJECTED,
            f"root is no repository checkout root: {named}; pass the absolute path of the directory that holds the Product's checkout",
        )
    return top


def _run_argv(verb: Sequence[str], scope: str, run_token: str) -> list[str]:
    return [
        *_RUN_COMMAND,
        *verb,
        "--verification-type",
        VERIFICATION_TYPE,
        "--scope-type",
        SCOPE_TYPE,
        "--scope",
        scope,
        "--run",
        run_token,
    ]


def render_argv(scope: str, run_token: str) -> list[str]:
    """Return the command that reproduces the complete rendered projection."""
    return _run_argv(("render",), scope, run_token)


def _run_json(
    context: _Context,
    root: pathlib.Path,
    verb: Sequence[str],
    scope: str,
    run_token: str,
) -> dict[str, object]:
    argv = _run_argv(verb, scope, run_token)
    stdout = _command(context, argv, cwd=root, run_token=run_token)
    return _json_lines(stdout, argv=argv, run_token=run_token)[-1]


def _retained_draft(
    context: _Context, root: pathlib.Path, scope: str, run_token: str
) -> str:
    replay = _run_json(context, root, ("input",), scope, run_token)
    content = replay.get(SpxField.CONTENT)
    if not isinstance(content, str):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"retained input carries no content string{_RENDER_HINT}",
            run_token=run_token,
        )
    return content


# ---------------------------------------------------------------- the record


@dataclass(frozen=True)
class _Record:
    """One Change record as the store holds it."""

    reference: str
    state: str
    metadata: dict[str, object]
    body: str
    blockers: tuple[_Record, ...] = field(default=())


def _graphql_argv(query: str, **variables: str) -> list[str]:
    argv = [*_GRAPHQL, "-f", f"query={query}"]
    for name, value in variables.items():
        flag = "-F" if name == "n" else "-f"
        argv += [flag, f"{name}={value}"]
    return argv


def _walk(answer: object, *keys: StoreField) -> object:
    node = answer
    for key in keys:
        node = node.get(key) if isinstance(node, dict) else None
    return node


def _issue_url(owner: str, repository: str, number: object) -> str:
    return ISSUE_URL_TEMPLATE.format(owner=owner, repository=repository, number=number)


def _reference_url(text: str) -> str:
    found = ISSUE_IDENTITY_PATTERN.fullmatch(text)
    return _issue_url(*found.groups()) if found else text


def _bounded(info: object, bound: str, subject: str) -> None:
    if isinstance(info, dict) and info.get(StoreField.HAS_NEXT_PAGE) is True:
        raise Blocked(
            BlockReason.PAGE_BOUND_REACHED,
            f"the {subject} read is not complete at {bound}{_BOUND_HINT}",
            evidence={ResultField.BOUND: bound},
        )


def _field_map(node: Mapping[str, object]) -> dict[str, object]:
    """Map each issue field name one store issue node carries to its value."""
    container = node.get(StoreField.ISSUE_FIELD_VALUES)
    _bounded(
        container.get(StoreField.PAGE_INFO) if isinstance(container, dict) else None,
        f"{ISSUE_FIELD_VALUES_PAGE_SIZE} issue field values per issue",
        "issue field values",
    )
    entries = container.get(StoreField.NODES) if isinstance(container, dict) else None
    values: dict[str, object] = {}
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        name = _walk(entry, StoreField.FIELD, StoreField.NAME)
        if not isinstance(name, str):
            continue
        values[name] = (
            entry.get(StoreField.VALUE)
            if StoreField.VALUE in entry
            else entry.get(StoreField.NAME)
        )
    return values


def _record_of(node: object, *, blockers: tuple[_Record, ...] = ()) -> _Record:
    """Build a record from one store issue node, or block when it is malformed."""
    if not isinstance(node, dict):
        raise Blocked(
            BlockReason.RECORD_MISSING,
            f"the store holds no such issue{_STORE_HINT}",
        )
    title = node.get(StoreField.TITLE)
    body = node.get(StoreField.BODY)
    number = node.get(StoreField.NUMBER)
    state = node.get(StoreField.STATE)
    named = _walk(node, StoreField.REPOSITORY, StoreField.NAME_WITH_OWNER)
    if (
        not isinstance(title, str)
        or not isinstance(body, str)
        or not isinstance(number, int)
        or not isinstance(state, str)
        or not isinstance(named, str)
        or "/" not in named
    ):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"store issue lacks a title, body, number, state, or repository{_STORE_HINT}",
        )
    owner, repository = named.split("/", 1)
    values = _field_map(node)
    assignees = _walk(node, StoreField.ASSIGNEES, StoreField.NODES)
    holder = (
        assignees[0].get(StoreField.LOGIN)
        if isinstance(assignees, list) and assignees and isinstance(assignees[0], dict)
        else None
    )
    parent = values.get(FIELD_NAMES[MetadataKey.PARENT])
    predecessors = values.get(FIELD_NAMES[MetadataKey.PREDECESSORS])
    metadata: dict[str, object] = {
        MetadataKey.TITLE: title,
        MetadataKey.HOLDER: holder,
        MetadataKey.PARENT: (
            _issue_url(owner, repository, int(parent))
            if isinstance(parent, int | float) and not isinstance(parent, bool)
            else None
        ),
        MetadataKey.PREDECESSORS: [
            _reference_url(item)
            for item in predecessors.split(PREDECESSOR_SEPARATOR)
            if item
        ]
        if isinstance(predecessors, str)
        else [],
        MetadataKey.BLOCKERS: [item.reference for item in blockers],
    }
    for key in (
        MetadataKey.PRODUCT,
        MetadataKey.MATURITY,
        MetadataKey.LIFECYCLE,
        MetadataKey.BASE,
        MetadataKey.PRIORITY,
        MetadataKey.PRIMARY_VALUE,
        MetadataKey.INVESTMENT,
    ):
        value = values.get(FIELD_NAMES[key])
        metadata[key] = value if isinstance(value, str) and value else None
    return _Record(
        reference=_issue_url(owner, repository, number),
        state=state,
        metadata={str(key): metadata[key] for key in MetadataKey},
        body=body,
        blockers=blockers,
    )


def _fetch_record(context: _Context, identity: tuple[str, str, str]) -> _Record:
    """Read one record and the record of each Change it names as a blocker."""
    owner, repository, number = identity
    argv = _graphql_argv(_RECORD_QUERY, o=owner, r=repository, n=number)
    answer = _json_lines(_command(context, argv, cwd=context.cwd), argv=argv)[-1]
    issue = _walk(answer, StoreField.DATA, StoreField.REPOSITORY, StoreField.ISSUE)
    if not isinstance(issue, dict):
        raise Blocked(
            BlockReason.RECORD_MISSING,
            f"the store holds no issue {owner}/{repository}#{number}; pass the identity of a Change in the declared store",
        )
    connection = issue.get(StoreField.BLOCKED_BY)
    _bounded(
        connection.get(StoreField.PAGE_INFO) if isinstance(connection, dict) else None,
        f"{BLOCKERS_PAGE_SIZE} blockers, one page",
        "blockers",
    )
    nodes = connection.get(StoreField.NODES) if isinstance(connection, dict) else None
    blockers = (
        tuple(_record_of(node) for node in nodes) if isinstance(nodes, list) else ()
    )
    return _record_of(issue, blockers=blockers)


def _yaml_value(value: object) -> str:
    return "null" if value is None else str(value)


def _draft_text(record: _Record) -> str:
    """Assemble the Change Draft: the metadata except the holder, then the body."""
    lines = ["---"]
    for key in DRAFT_KEYS:
        value = record.metadata[key]
        if isinstance(value, list):
            if value:
                lines.append(f"{key}:")
                lines += [f"  - {item}" for item in value]
            else:
                lines.append(f"{key}: []")
        else:
            lines.append(f"{key}: {_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n" + record.body


_FRONT_MATTER_PATTERN: Final = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_BASE_LINE_PATTERN: Final = re.compile(r"^base: ([0-9a-f]{40})$", re.MULTILINE)


def _bound_pair(draft: str) -> tuple[str, str | None]:
    """Return the body SHA-256 and the Base a Draft binds."""
    front = _FRONT_MATTER_PATTERN.match(draft)
    body = draft[front.end() :] if front else draft
    base = _BASE_LINE_PATTERN.search(front.group(1)) if front else None
    return _sha256(body), base.group(1) if base else None


def _record_base(record: _Record) -> str | None:
    base = record.metadata[MetadataKey.BASE]
    return base if isinstance(base, str) else None


def _block_changed(
    *,
    reason: BlockReason,
    detail: str,
    run_token: str | None,
    retained: tuple[str, str | None],
    live: tuple[str, str | None],
) -> Blocked:
    return Blocked(
        reason,
        detail,
        run_token=run_token,
        evidence={
            ResultField.RETAINED_SHA256: retained[0],
            ResultField.LIVE_SHA256: live[0],
            ResultField.RETAINED_BASE: retained[1],
            ResultField.LIVE_BASE: live[1],
        },
    )


def _read_record(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    _product_root(context, _checkout_root(request))
    record = _fetch_record(context, _issue_identity(request))
    return {
        ResultField.ISSUE: request[RequestField.ISSUE],
        ResultField.DRAFT: _draft_text(record),
        ResultField.BODY_SHA256: _sha256(record.body),
        ResultField.BASE: _record_base(record),
        ResultField.BLOCKERS: [
            {ResultField.REFERENCE: item.reference, ResultField.STATE: item.state}
            for item in record.blockers
        ],
    }


def _tool_version(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    del request
    version = _command(context, _SPX_VERSION, cwd=context.cwd).strip()
    if not version:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{' '.join(_SPX_VERSION)}` printed no version; confirm spx is "
            "installed and on PATH",
        )
    return {ResultField.TOOL_VERSION: version}


# ---------------------------------------------------------------- the Base


def _read_at_base(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    """Return what the named path holds at the Base: a file, a directory, or nothing."""
    root = _product_root(context, _checkout_root(request))
    base = _base(request)
    path = _repository_path(request)
    commit = _probe(
        context, (GIT_EXECUTABLE, "cat-file", "-e", f"{base}^{{commit}}"), cwd=root
    )
    if commit.exit_code != 0:
        raise Blocked(
            BlockReason.BASE_UNRESOLVED,
            f"the Base {base} names no commit in {root}; fetch it, then repeat the request",
        )
    revision = f"{base}:{path}"
    kind = _probe(context, (GIT_EXECUTABLE, "cat-file", "-t", revision), cwd=root)
    values: dict[str, object] = {ResultField.PATH: path, ResultField.BASE: base}
    named = kind.stdout.strip() if kind.exit_code == 0 else ""
    if named == "blob":
        values[ResultField.KIND] = BaseKind.FILE
        values[ResultField.CONTENT] = _command(
            context, (GIT_EXECUTABLE, "cat-file", "blob", revision), cwd=root
        )
    elif named == "tree":
        values[ResultField.KIND] = BaseKind.DIRECTORY
        values[ResultField.ENTRIES] = _command(
            context, (GIT_EXECUTABLE, "ls-tree", "--name-only", revision), cwd=root
        ).splitlines()
    else:
        values[ResultField.KIND] = BaseKind.MISSING
    return values


# ---------------------------------------------------------------- the run


def _start(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    identity = _issue_identity(request)
    scope = str(request[RequestField.ISSUE])
    expected_body = _body_sha256(request)
    expected_base = _base(request)
    root = _product_root(context, _checkout_root(request))
    record = _fetch_record(context, identity)
    live = (_sha256(record.body), _record_base(record))
    if live != (expected_body, expected_base):
        raise _block_changed(
            reason=BlockReason.RECORD_CHANGED,
            detail="the stored record differs from the body and Base read before the run; call read-record again and restart with the new bodySha256 and base",
            run_token=None,
            retained=(expected_body, expected_base),
            live=live,
        )
    draft = _draft_text(record)
    argv = [
        *_RUN_COMMAND,
        "start",
        "--verification-type",
        VERIFICATION_TYPE,
        "--scope-type",
        SCOPE_TYPE,
        "--scope",
        scope,
        "--input",
        PAYLOAD_FROM_STDIN,
        "--expect-content-sha256",
        _sha256(draft),
        "--change",
        scope,
    ]
    lines = _json_lines(_command(context, argv, cwd=root, stdin=draft), argv=argv)
    run_token = next(
        (
            token
            for line in lines
            if SpxField.LOCATOR in line
            and isinstance(token := line.get(SpxField.RUN_TOKEN), str)
            and token
        ),
        None,
    )
    if run_token is None:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{' '.join(argv)}` printed no line carrying a run locator and "
            "run token; confirm the installed spx version supports the run "
            "`start` verb",
        )
    retained = _retained_draft(context, root, scope, run_token)
    if retained != draft:
        raise Blocked(
            BlockReason.RETAINED_INPUT_MISMATCH,
            "retained input differs from the Draft the runner assembled; the record changed during start, so repeat read-record and start",
            run_token=run_token,
            evidence={
                ResultField.RETAINED_SHA256: _sha256(retained),
                ResultField.LIVE_SHA256: _sha256(draft),
            },
        )
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.ISSUE: scope,
        ResultField.BODY_SHA256: live[0],
        ResultField.BASE: live[1],
    }


def _append(
    context: _Context,
    request: Mapping[str, object],
    *,
    noun: str,
    idempotency_key: str,
) -> dict[str, object]:
    scope = str(request[RequestField.ISSUE])
    run_token = _run_token(request)
    argv = [
        *_run_argv((noun, "add"), scope, run_token),
        "--idempotency-key",
        idempotency_key,
        "--payload",
        PAYLOAD_FROM_STDIN,
    ]
    stdout = _command(
        context,
        argv,
        cwd=_product_root(context, _checkout_root(request)),
        stdin=_payload_text(request),
        payload_key=idempotency_key,
    )
    accepted = _json_lines(stdout, argv=argv)[-1]
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.IDEMPOTENCY_KEY: idempotency_key,
        ResultField.SEQUENCE: accepted.get(SpxField.SEQUENCE),
        ResultField.IDEMPOTENT: accepted.get(SpxField.IDEMPOTENT),
    }


def _add_scope(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    return _append(context, request, noun="scope", idempotency_key=_unit_id(request))


def finding_key(unit_id: str, rule: str) -> str:
    """Return the idempotency key of the one finding of a rule on one unit."""
    return f"{unit_id}{IDEMPOTENCY_KEY_SEPARATOR}{rule}"


def _add_finding(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    key = finding_key(_unit_id(request), _finding_rule(request))
    return _append(context, request, noun="finding", idempotency_key=key)


def _finding_entries(
    projection: Mapping[str, object],
) -> list[tuple[int, dict[str, object]]]:
    """Return every rendered finding as ``(seq, payload)`` once, in journal order."""
    groups = projection.get(SpxField.FINDINGS)
    if not isinstance(groups, dict):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"rendered projection carries no findings object{_RENDER_HINT}",
        )
    entries: dict[int, dict[str, object]] = {}
    for group in groups.values():
        if not isinstance(group, list):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"rendered findings group is not an array{_RENDER_HINT}",
            )
        for entry in group:
            seq = entry.get(SpxField.SEQ) if isinstance(entry, dict) else None
            payload = entry.get(SpxField.PAYLOAD) if isinstance(entry, dict) else None
            if not isinstance(seq, int) or not isinstance(payload, dict):
                raise Blocked(
                    BlockReason.UNREADABLE_OUTPUT,
                    f"rendered finding lacks an integer seq and a payload object{_RENDER_HINT}",
                )
            entries.setdefault(seq, payload)
    return sorted(entries.items())


def _check_binding(
    context: _Context,
    request: Mapping[str, object],
    root: pathlib.Path,
    run_token: str,
) -> tuple[str, str | None]:
    """Block unless the stored body and Base equal the pair the run retained."""
    scope = str(request[RequestField.ISSUE])
    retained = _bound_pair(_retained_draft(context, root, scope, run_token))
    record = _fetch_record(context, _issue_identity(request))
    live = (_sha256(record.body), _record_base(record))
    if live != retained:
        raise _block_changed(
            reason=BlockReason.RECORD_CHANGED,
            detail="the stored body or Base differs from the pair the run retained; the record was published after start, so call read-record again and start a new run for the changed record",
            run_token=run_token,
            retained=retained,
            live=live,
        )
    return live


def _reconcile(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    scope = str(request[RequestField.ISSUE])
    run_token = _run_token(request)
    root = _product_root(context, _checkout_root(request))
    _check_binding(context, request, root, run_token)
    run_status = _run_json(context, root, ("status",), scope, run_token)
    projection = _run_json(context, root, ("render",), scope, run_token)
    units = projection.get(SpxField.AUDIT_SCOPE_UNITS)
    if not isinstance(units, list) or not all(isinstance(unit, dict) for unit in units):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"rendered projection lacks a {SpxField.AUDIT_SCOPE_UNITS} array of objects{_RENDER_HINT}",
        )
    scope_units = [
        {
            name: unit.get(name)
            for name in (
                SpxField.UNIT_ID,
                SpxField.PARENT_UNIT_ID,
                SpxField.SUBJECT,
                SpxField.COVERAGE_STATUS,
            )
        }
        for unit in units
    ]
    findings = [
        {
            SpxField.SEQ: seq,
            SpxField.UNIT_ID: payload.get(SpxField.UNIT_ID),
            SpxField.RULE: payload.get(SpxField.RULE),
            SpxField.SEVERITY: payload.get(SpxField.SEVERITY),
        }
        for seq, payload in _finding_entries(projection)
    ]
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.RUN_STATUS: run_status,
        ResultField.SCOPE_UNITS: scope_units,
        ResultField.FINDINGS: findings,
    }


def _finish(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    scope = str(request[RequestField.ISSUE])
    run_token = _run_token(request)
    terminal = _terminal_status(request)
    root = _product_root(context, _checkout_root(request))
    bound = _check_binding(context, request, root, run_token)
    finish_argv = [
        *_run_argv(("finish",), scope, run_token),
        "--terminal-status",
        terminal,
    ]
    _command(context, finish_argv, cwd=root)
    projection = _run_json(context, root, ("render",), scope, run_token)
    return {
        ResultField.RUN_TOKEN: run_token,
        ResultField.BODY_SHA256: bound[0],
        ResultField.BASE: bound[1],
        ResultField.RUN: {
            name: value
            for name, value in projection.items()
            if name not in EVIDENCE_FIELDS
        },
        ResultField.FINDINGS: [
            payload for _seq, payload in _finding_entries(projection)
        ],
        ResultField.RENDER_COMMAND: shlex.join(render_argv(scope, run_token)),
    }


# ---------------------------------------------------------------- the form check


def _form_check_function() -> Callable[..., dict[str, object]]:
    """Return the check function of the change-standards skill, imported by path."""
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "change-standards"
        / "scripts"
        / "form_check.py"
    )
    spec = importlib.util.spec_from_file_location("change_standards_form_check", path)
    if not path.is_file() or spec is None or spec.loader is None:
        raise Blocked(
            BlockReason.FORM_CHECK_UNAVAILABLE,
            f"the change-standards form check is absent at {path}; install the product-tree plugin whole, then repeat the request",
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    check = getattr(module, "check", None)
    if not callable(check):
        raise Blocked(
            BlockReason.FORM_CHECK_UNAVAILABLE,
            f"the form check at {path} defines no check function; install the product-tree plugin whole, then repeat the request",
        )
    return check


def _stored_form(record: _Record) -> dict[str, object]:
    return {"metadata": dict(record.metadata), "body": record.body}


def _form_check(context: _Context, request: Mapping[str, object]) -> dict[str, object]:
    root = _product_root(context, _checkout_root(request))
    record = _fetch_record(context, _issue_identity(request))
    outcome = _form_check_function()(
        {
            "draft_text": _draft_text(record),
            "checkout_root": str(root),
            "operation": FORM_CHECK_OPERATION,
            "stored_record": _stored_form(record),
            "blocker_records": {
                item.reference: _stored_form(item) for item in record.blockers
            },
            "size_limit": FORM_CHECK_SIZE_LIMIT,
        }
    )
    status = outcome.get("status")
    findings = outcome.get("findings")
    if status == "invalid-request" or not isinstance(findings, list):
        raise Blocked(
            BlockReason.FORM_CHECK_REJECTED,
            f"the form check rejected its request: {outcome.get('detail')}; report this block, since the runner built the request",
        )
    return {
        ResultField.ISSUE: request[RequestField.ISSUE],
        ResultField.BODY_SHA256: _sha256(record.body),
        ResultField.BASE: _record_base(record),
        ResultField.CHECK_STATUS: status,
        ResultField.FINDINGS: [
            {
                ResultField.RULE: item.get("rule"),
                ResultField.WHERE: item.get("where"),
                ResultField.DETAIL: item.get("detail"),
            }
            for item in findings
            if isinstance(item, dict)
        ],
    }


# ---------------------------------------------------------------- format at close

_FENCE_PATTERN: Final = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_HEADING_PATTERN: Final = re.compile(r"^###[ \t]+(?P<text>.+?)[ \t]*$")
_DECLARATIONS_PATTERN: Final = re.compile(r"^##[ \t]+Declarations[ \t]*$")
_SECTION_PATTERN: Final = re.compile(r"^##[ \t]+\S")
_RENAME_TO_PATTERN: Final = re.compile(r"^rename to (?P<path>.+)$")
_LINKED_TAG_PATTERN: Final = re.compile(r"[ \t]*\(\[(?:test|eval|probe)\]\([^)]*\)\)")


@dataclass
class _Block:
    info: str
    lines: list[str]


@dataclass
class _Subsection:
    heading: str
    blocks: list[_Block] = field(default_factory=list)


def _subsections(body: str) -> list[_Subsection]:
    """Return the ``###`` subsections of the ``## Declarations`` section with their fenced blocks."""
    subsections: list[_Subsection] = []
    in_declarations = False
    block: _Block | None = None
    fence = ""
    for line in body.splitlines():
        if block is not None:
            closing = line.strip()
            if closing and set(closing) == {fence[0]} and len(closing) >= len(fence):
                block = None
            else:
                block.lines.append(line)
            continue
        opening = _FENCE_PATTERN.match(line)
        if opening is not None and in_declarations and subsections:
            fence = opening.group("fence")
            block = _Block(opening.group("info").strip(), [])
            subsections[-1].blocks.append(block)
            continue
        if _DECLARATIONS_PATTERN.match(line):
            in_declarations = True
        elif _SECTION_PATTERN.match(line):
            in_declarations = False
        elif in_declarations:
            heading = _HEADING_PATTERN.match(line)
            if heading is not None:
                subsections.append(_Subsection(heading.group("text")))
    return subsections


def _replacement_of(subsection: _Subsection) -> tuple[str, str] | None:
    """Return the file path and whole text of a replacement subsection, if it is one."""
    blocks = subsection.blocks
    path = subsection.heading.strip("`")
    diffs = [block for block in blocks if block.info == "diff"]
    if diffs:
        renames = [
            match.group("path").strip()
            for line in diffs[0].lines
            if (match := _RENAME_TO_PATTERN.match(line))
        ]
        headers_only = all(
            line.startswith(("rename from ", "rename to ")) for line in diffs[0].lines
        )
        if len(blocks) < 2 or not headers_only or not renames:
            return None
        return renames[0], "\n".join(blocks[-1].lines) + "\n"
    if len(blocks) != 1 or " " in path or "/" not in path and "." not in path:
        return None
    return path, "\n".join(blocks[0].lines) + "\n"


def _format(
    context: _Context,
    root: pathlib.Path,
    command: Sequence[str],
    path: str,
    text: str,
) -> str:
    argv = [part.replace(PATH_PLACEHOLDER, path) for part in command]
    result = _probe_with_stdin(context, argv, root, text)
    if result.exit_code != 0:
        raise Blocked(
            BlockReason.FORMAT_COMMAND_UNUSABLE,
            f"the format command exited {result.exit_code} on {path}; run it by hand over that text on stdin and confirm it writes the formatted text on stdout",
            evidence={
                ResultField.COMMAND: shlex.join(argv),
                ResultField.EXIT_CODE: result.exit_code,
                ResultField.STDERR: result.stderr,
            },
        )
    return result.stdout


def _probe_with_stdin(
    context: _Context, argv: Sequence[str], cwd: pathlib.Path, stdin: str
) -> CommandResult:
    try:
        return context.runner(argv, cwd=cwd, stdin=stdin)
    except UnicodeDecodeError as exc:
        raise Blocked(
            BlockReason.FORMAT_COMMAND_UNUSABLE,
            f"the format command printed output that is not UTF-8; rerun `{shlex.join(argv)}` by hand and confirm it prints UTF-8 text",
        ) from exc
    except (OSError, ValueError) as exc:
        raise Blocked(
            BlockReason.FORMAT_COMMAND_UNUSABLE,
            f"the format command could not be executed; confirm {argv[0]} is installed and on PATH, then repeat the request",
            evidence={
                ResultField.COMMAND: shlex.join(argv),
                ResultField.EXIT_CODE: NOT_APPLICABLE,
                ResultField.STDERR: str(exc),
            },
        ) from exc


def _plain(text: str) -> str:
    """Return ``text`` with its linked evidence tags removed."""
    return "\n".join(_LINKED_TAG_PATTERN.sub("", line) for line in text.split("\n"))


def _at_revision(context: _Context, root: pathlib.Path, revision: str) -> str | None:
    kind = _probe(context, (GIT_EXECUTABLE, "cat-file", "-t", revision), cwd=root)
    if kind.exit_code != 0 or kind.stdout.strip() != "blob":
        return None
    return _command(context, (GIT_EXECUTABLE, "cat-file", "blob", revision), cwd=root)


def _finding(rule: FormatRule, path: str, detail: str) -> dict[str, object]:
    return {
        ResultField.RULE: rule,
        ResultField.WHERE: path,
        ResultField.DETAIL: detail,
    }


def _format_at_close(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    """Make the three comparisons of the audit at close for each declared replacement."""
    root = _product_root(context, _checkout_root(request))
    merge = _merge_commit(request)
    command = _format_command(request)
    record = _fetch_record(context, _issue_identity(request))
    default = _command(context, _GIT_DEFAULT_BRANCH, cwd=root).strip()
    if not default:
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"`{' '.join(_GIT_DEFAULT_BRANCH)}` printed no default branch; run `git remote set-head origin --auto` in {root} and repeat the request",
        )
    findings: list[dict[str, object]] = []
    replacements = [
        found
        for subsection in _subsections(record.body)
        if (found := _replacement_of(subsection)) is not None
    ]
    for path, declared in replacements:
        if _format(context, root, command, path, declared) != declared:
            findings.append(
                _finding(
                    FormatRule.BASE_FORMATTER,
                    path,
                    "the format command changes the declared replacement",
                )
            )
        approved = _at_revision(context, root, f"{merge}:{path}")
        if approved is None:
            findings.append(
                _finding(
                    FormatRule.MERGE_FORMATTER,
                    path,
                    f"the merge commit {merge} holds no file at this path",
                )
            )
        elif _format(context, root, command, path, approved) != approved:
            findings.append(
                _finding(
                    FormatRule.MERGE_FORMATTER,
                    path,
                    "the format command changes the file at the merge commit",
                )
            )
        on_default = _at_revision(context, root, f"{default}:{path}")
        if on_default is None or _plain(on_default) != _plain(declared):
            findings.append(
                _finding(
                    FormatRule.DEFAULT_BRANCH,
                    path,
                    f"the file on {default} is absent or differs from the declared replacement once its linked evidence tags are removed",
                )
            )
    return {
        ResultField.ISSUE: request[RequestField.ISSUE],
        ResultField.FINDINGS: findings,
    }


# ---------------------------------------------------------------- the store


def _connection(
    answer: Mapping[str, object], kind: AuthorityRead
) -> Mapping[str, object]:
    """Return the connection of ``kind`` from one store answer, or block."""
    node = _walk(answer, StoreField.DATA, StoreField.REPOSITORY, StoreField.ISSUE)
    connection = (
        node.get(_AUTHORITY_CONNECTIONS[kind]) if isinstance(node, dict) else None
    )
    if not isinstance(connection, dict):
        raise Blocked(
            BlockReason.UNREADABLE_OUTPUT,
            f"store answer carries no {_AUTHORITY_CONNECTIONS[kind]} connection{_STORE_HINT}",
        )
    return connection


def _login(person: object) -> object:
    return person.get(StoreField.LOGIN) if isinstance(person, dict) else None


def _event(node: Mapping[str, object]) -> dict[str, object]:
    changed = node.get(StoreField.ISSUE_FIELD)
    return {
        ResultField.CREATED_AT: node.get(StoreField.CREATED_AT),
        ResultField.ACTOR: _login(node.get(StoreField.ACTOR)),
        ResultField.FIELD: changed.get(StoreField.NAME)
        if isinstance(changed, dict)
        else None,
        ResultField.PREVIOUS_VALUE: node.get(StoreField.PREVIOUS_VALUE),
        ResultField.NEW_VALUE: node.get(StoreField.NEW_VALUE),
    }


def _read_connection(
    context: _Context, kind: AuthorityRead, identity: tuple[str, str, str]
) -> list[dict[str, object]]:
    """Read every entry of one connection within the page bound, or block."""
    owner, repository, number = identity
    entries: list[dict[str, object]] = []
    cursor: str | None = None
    for _page in range(AUTHORITY_MAX_PAGES):
        argv = _graphql_argv(_AUTHORITY_QUERIES[kind], o=owner, r=repository, n=number)
        if cursor is not None:
            argv += ["-f", f"after={cursor}"]
        connection = _connection(
            _json_lines(_command(context, argv, cwd=context.cwd), argv=argv)[-1],
            kind,
        )
        nodes = connection.get(StoreField.NODES)
        info = connection.get(StoreField.PAGE_INFO)
        if not isinstance(nodes, list) or not isinstance(info, dict):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"{kind} page carries no nodes array and pageInfo object{_STORE_HINT}",
            )
        if not all(isinstance(node, dict) for node in nodes):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"{kind} page holds an entry that is not an object{_STORE_HINT}",
            )
        entries.extend(_event(node) for node in nodes)
        if info.get(StoreField.HAS_NEXT_PAGE) is not True:
            return entries
        cursor = info.get(StoreField.END_CURSOR)
        if not isinstance(cursor, str) or not cursor:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"{kind} page reports a further page and no end cursor{_STORE_HINT}",
            )
    bound = f"{AUTHORITY_PAGE_SIZE} {kind} per page, {AUTHORITY_MAX_PAGES} pages"
    raise Blocked(
        BlockReason.PAGE_BOUND_REACHED,
        f"the {kind} read is not complete at {bound}{_BOUND_HINT}",
        evidence={ResultField.BOUND: bound},
    )


def _read_authority(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    identity = _issue_identity(request)
    return {
        ResultField.ISSUE: request[RequestField.ISSUE],
        ResultField.EVENTS: _read_connection(context, AuthorityRead.EVENTS, identity),
    }


def _relation_values(node: Mapping[str, object]) -> dict[str, object]:
    """Return the Product and Parent values one store issue node carries."""
    values = _field_map(node)
    parent = values.get(PARENT_FIELD)
    return {
        PRODUCT_FIELD: values.get(PRODUCT_FIELD),
        PARENT_FIELD: int(parent)
        if isinstance(parent, int | float) and not isinstance(parent, bool)
        else None,
    }


def _read_relations(
    context: _Context, request: Mapping[str, object]
) -> dict[str, object]:
    """Return the issue's Product and Parent and the issues whose Parent it is.

    Reads every issue of the store's repository within the page bound; a child
    is an issue whose ``Parent`` number field equals the named issue's number.
    """
    owner, repository, number = _issue_identity(request)
    target = int(number)
    by_number: dict[int, dict[str, object]] = {}
    cursor: str | None = None
    for _page in range(AUTHORITY_MAX_PAGES):
        argv = _graphql_argv(_RELATIONS_QUERY, o=owner, r=repository)
        if cursor is not None:
            argv += ["-f", f"after={cursor}"]
        node = _walk(
            _json_lines(_command(context, argv, cwd=context.cwd), argv=argv)[-1],
            StoreField.DATA,
            StoreField.REPOSITORY,
            StoreField.ISSUES,
        )
        nodes = node.get(StoreField.NODES) if isinstance(node, dict) else None
        info = node.get(StoreField.PAGE_INFO) if isinstance(node, dict) else None
        if not isinstance(nodes, list) or not isinstance(info, dict):
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"relations page carries no nodes array and pageInfo object{_STORE_HINT}",
            )
        for entry in nodes:
            numbered = entry.get(StoreField.NUMBER) if isinstance(entry, dict) else None
            if not isinstance(numbered, int):
                raise Blocked(
                    BlockReason.UNREADABLE_OUTPUT,
                    f"relations page holds an entry with no issue number{_STORE_HINT}",
                )
            by_number[numbered] = _relation_values(entry)
        if info.get(StoreField.HAS_NEXT_PAGE) is not True:
            own = by_number.get(target, {})
            return {
                ResultField.ISSUE: request[RequestField.ISSUE],
                ResultField.PRODUCT: own.get(PRODUCT_FIELD),
                ResultField.PARENT: own.get(PARENT_FIELD),
                ResultField.CHILDREN: [
                    {
                        ResultField.NUMBER: child,
                        ResultField.PRODUCT: values.get(PRODUCT_FIELD),
                    }
                    for child, values in sorted(by_number.items())
                    if values.get(PARENT_FIELD) == target
                ],
            }
        cursor = info.get(StoreField.END_CURSOR)
        if not isinstance(cursor, str) or not cursor:
            raise Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                f"relations page reports a further page and no end cursor{_STORE_HINT}",
            )
    bound = f"{AUTHORITY_PAGE_SIZE} issues per page, {AUTHORITY_MAX_PAGES} pages"
    raise Blocked(
        BlockReason.PAGE_BOUND_REACHED,
        f"the issues read is not complete at {bound}{_BOUND_HINT}",
        evidence={ResultField.BOUND: bound},
    )


_HANDLERS: Final[
    Mapping[Operation, Callable[[_Context, Mapping[str, object]], dict[str, object]]]
] = {
    Operation.TOOL_VERSION: _tool_version,
    Operation.READ_RECORD: _read_record,
    Operation.READ_AT_BASE: _read_at_base,
    Operation.START: _start,
    Operation.ADD_SCOPE: _add_scope,
    Operation.ADD_FINDING: _add_finding,
    Operation.RECONCILE: _reconcile,
    Operation.FINISH: _finish,
    Operation.FORM_CHECK: _form_check,
    Operation.FORMAT_AT_CLOSE: _format_at_close,
    Operation.READ_AUTHORITY: _read_authority,
    Operation.READ_RELATIONS: _read_relations,
}


def _request_token(request: Mapping[str, object]) -> str:
    """Return the run token a request names, or ``not-started`` when it names none."""
    token = request.get(RequestField.RUN_TOKEN)
    return token if isinstance(token, str) and token else NOT_STARTED


def _parse_request(text: str) -> dict[str, object]:
    try:
        request = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request is not JSON: {exc.msg} at line {exc.lineno} column {exc.colno}; write the request as one JSON object and pass it again",
        ) from exc
    except ValueError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request cannot be parsed: {exc}; write the request as one JSON object and pass it again",
        ) from exc
    except RecursionError as exc:
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            "request nests too deeply to parse; flatten the request to the fields its operation takes",
        ) from exc
    if not isinstance(request, dict):
        raise Blocked(
            BlockReason.INVALID_REQUEST,
            f"request must be a JSON object, received a JSON "
            f"{type(request).__name__}; write the request file as "
            '`{"operation": ...}` and pass its path',
        )
    return request


def _blocked_result(
    operation: Operation | None, blocked: Blocked, request_token: str
) -> tuple[ExitCode, dict[str, object]]:
    code = (
        ExitCode.INVALID_REQUEST
        if blocked.reason is BlockReason.INVALID_REQUEST
        else ExitCode.BLOCKED
    )
    return code, {
        ResultField.OPERATION: operation,
        ResultField.STATUS: ResultStatus.BLOCKED,
        ResultField.REASON: blocked.reason,
        ResultField.DETAIL: blocked.detail,
        ResultField.RUN_TOKEN: blocked.run_token or request_token,
        **blocked.evidence,
    }


def execute(
    request_text: str, *, cwd: pathlib.Path, runner: CommandRunner
) -> tuple[ExitCode, dict[str, object]]:
    """Perform one request and return its exit code and result object.

    A blocked result carries the token of the run ``start`` created when
    ``start`` blocks after reading it, otherwise the ``runToken`` string the
    request carries, otherwise ``not-started``.
    """
    operation: Operation | None = None
    request_token = NOT_STARTED
    try:
        request = _parse_request(request_text)
        request_token = _request_token(request)
        operation = _named_operation(request)
        validated = validate_request(request)
        values = _HANDLERS[validated](_Context(runner=runner, cwd=cwd), request)
    except Blocked as blocked:
        return _blocked_result(operation, blocked, request_token)
    return ExitCode.OK, {
        ResultField.OPERATION: operation,
        ResultField.STATUS: ResultStatus.OK,
        **values,
    }


def _read_request(stdin: TextIO | None) -> str:
    if stdin is None:
        return sys.stdin.buffer.read().decode(TEXT_ENCODING)
    return stdin.read()


def _serialized(code: ExitCode, result: Mapping[str, object]) -> tuple[ExitCode, str]:
    """Serialize one result, blocking when the output it carries nests too deeply."""
    try:
        return code, json.dumps(result, sort_keys=True)
    except RecursionError:
        named = result.get(ResultField.OPERATION)
        token = result.get(ResultField.RUN_TOKEN)
        code, blocked = _blocked_result(
            Operation(named) if isinstance(named, str) else None,
            Blocked(
                BlockReason.UNREADABLE_OUTPUT,
                "result nests too deeply to serialize; report this block, since the operation's result cannot be printed",
            ),
            token if isinstance(token, str) else NOT_STARTED,
        )
        return code, json.dumps(blocked, sort_keys=True)


def main(
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    runner: CommandRunner = run_subprocess,
) -> int:
    """Read one request on stdin, write one result on stdout."""
    sink = sys.stdout if stdout is None else stdout
    try:
        request_text = _read_request(stdin)
    except UnicodeDecodeError:
        code, result = _blocked_result(
            None,
            Blocked(
                BlockReason.INVALID_REQUEST,
                "request is not UTF-8 text; write the request file as UTF-8 and pass it again",
            ),
            NOT_STARTED,
        )
    except OSError as exc:
        code, result = _blocked_result(
            None,
            Blocked(
                BlockReason.INVALID_REQUEST,
                f"request could not be read: {exc}; confirm stdin is open and readable, then repeat the request",
            ),
            NOT_STARTED,
        )
    else:
        code, result = execute(request_text, cwd=pathlib.Path(), runner=runner)
    code, text = _serialized(code, result)
    sink.write(text)
    sink.write("\n")
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
